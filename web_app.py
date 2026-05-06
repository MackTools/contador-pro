# web_app.py - VERSIÓN CORREGIDA

import streamlit as st
import pandas as pd
import hashlib
import pymongo
from datetime import datetime
import openpyxl
from io import BytesIO
import matplotlib.pyplot as plt
import base64
import os

# Intentar importar reportlab (opcional pero recomendado)
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# ========== CONFIGURACIÓN DE PÁGINA ==========
st.set_page_config(
    page_title="Contaduría | Sistema Contable",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== ESTADO DE SESIÓN (DEFINIDO PRIMERO) ==========
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "proyecto_actual" not in st.session_state:
    st.session_state.proyecto_actual = None
if "fig_actual" not in st.session_state:
    st.session_state.fig_actual = None
if "confirmar_eliminar" not in st.session_state:
    st.session_state.confirmar_eliminar = False

# ========== FUNCIÓN DE DESCARGA (UNA SOLA VERSIÓN) ==========
def get_desktop_app_download_link():
    """Descarga directa del ejecutable desde el servidor"""
    exe_paths = ["contaduria.exe", "dist/contaduria.exe"]
    
    for path in exe_paths:
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    data = f.read()
                b64 = base64.b64encode(data).decode()
                return {
                    "exists": True,
                    "data": b64,
                    "filename": os.path.basename(path),
                    "size": len(data)
                }
            except Exception as e:
                st.error(f"Error al leer el archivo: {e}")
    
    return {"exists": False}

# ========== CSS PERSONALIZADO ==========
st.markdown("""
<style>
    /* Fondo oscuro global */
    .stApp { background-color: #0e1117; }
    .main > div { background-color: #0e1117; }
    
    .download-btn {
        background-color: #27ae60;
        color: white;
        padding: 8px 16px;
        border-radius: 6px;
        text-decoration: none;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.2s;
        border: none;
        cursor: pointer;
    }
    
    .download-btn:hover {
        background-color: #219a52;
        transform: translateY(-1px);
    }
    
    .main-header {
        font-size: 24px;
        font-weight: 600;
        color: #ffffff;
        border-bottom: 2px solid #2d3748;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    
    .section-header {
        font-size: 18px;
        font-weight: 500;
        color: #e2e8f0;
        margin-top: 15px;
        margin-bottom: 10px;
        padding-left: 5px;
        border-left: 3px solid #4299e1;
    }
    
    .metric-card {
        background-color: #1a1e2e;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        border: 1px solid #2d3748;
    }
    
    .metric-label { font-size: 13px; color: #a0aec0; text-transform: uppercase; }
    .metric-value { font-size: 28px; font-weight: 600; color: #ffffff; margin-top: 5px; }
    
    .stButton button {
        background-color: #2d3748;
        color: #ffffff;
        border: 1px solid #4a5568;
        border-radius: 4px;
        font-weight: 500;
    }
    
    .stButton button:hover { background-color: #4a5568; }
    
    [data-testid="stSidebar"] { background-color: #0d1117; border-right: 1px solid #2d3748; }
    [data-testid="stDataFrame"] { border: 1px solid #2d3748; border-radius: 6px; background-color: #1a1e2e; }
    
    .stTextInput input, .stSelectbox select {
        background-color: #1a1e2e;
        border-color: #2d3748;
        color: #f7fafc;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    hr { border-color: #2d3748; }
    
    .float-download {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 999;
    }
</style>
""", unsafe_allow_html=True)

# ========== BARRA SUPERIOR CON BOTÓN DE DESCARGA ==========
download_info = get_desktop_app_download_link()
if download_info["exists"]:
    st.markdown(f'''
    <div class="float-download">
        <a href="data:application/octet-stream;base64,{download_info['data']}" 
           download="{download_info['filename']}" 
           class="download-btn">
            💻 Descargar {download_info['filename']} ({(download_info['size']/1024/1024):.1f} MB)
        </a>
    </div>
    ''', unsafe_allow_html=True)

# ========== CONEXIÓN A MONGODB ==========
MONGO_URI = st.secrets["MONGO_URI"]
DB_NAME = st.secrets["DB_NAME"]

@st.cache_resource
def init_connection():
    try:
        client = pymongo.MongoClient(MONGO_URI)
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

client = init_connection()
if client:
    db = client[DB_NAME]
else:
    st.stop()

def get_usuarios():
    return db.usuarios

def get_proyectos():
    return db.proyectos

# ========== SISTEMA DE FÓRMULAS Y COLUMNAS DINÁMICAS ==========

class FormulaEngine:
    """Motor de fórmulas para la tabla contable"""
    
    @staticmethod
    def evaluar_formula(formula, df, columna_actual=None):
        try:
            formula = str(formula).strip()
            if not formula.startswith('='):
                return None
            
            expr = formula[1:].strip()
            import re
            
            def replace_column(match):
                col_name = match.group(1)
                if col_name in df.columns:
                    return f"df['{col_name}']"
                return match.group(0)
            
            expr = re.sub(r'\[([^\]]+)\]', replace_column, expr)
            
            safe_dict = {
                'df': df,
                'sum': sum,
                'mean': lambda x: sum(x)/len(x) if len(x) > 0 else 0,
                'max': max,
                'min': min,
                'abs': abs,
                'round': round,
                'len': len,
                '__builtins__': {}
            }
            
            result = eval(expr, safe_dict)
            
            if hasattr(result, 'iloc'):
                return result
            return result
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    @staticmethod
    def aplicar_formula_columna(df, nombre_columna, formula, por_fila=True):
        try:
            if por_fila:
                resultados = []
                for idx, row in df.iterrows():
                    temp_df = pd.DataFrame([row.to_dict()])
                    resultado = FormulaEngine.evaluar_formula(formula, temp_df)
                    if isinstance(resultado, (int, float)):
                        resultados.append(resultado)
                    elif hasattr(resultado, 'iloc'):
                        resultados.append(resultado.iloc[0])
                    else:
                        resultados.append(resultado)
                df[nombre_columna] = resultados
            else:
                resultado = FormulaEngine.evaluar_formula(formula, df)
                if isinstance(resultado, (int, float)):
                    df[nombre_columna] = resultado
                elif hasattr(resultado, '__len__') and len(resultado) == len(df):
                    df[nombre_columna] = resultado
            return df
        except Exception as e:
            st.error(f"Error al aplicar fórmula: {e}")
            return df

def mostrar_gestor_formulas(df):
    """Interfaz para gestionar fórmulas"""
    st.markdown("### Gestor de Fórmulas")
    
    tab1, tab2 = st.tabs(["Nueva Columna", "Aplicar Fórmula"])
    
    with tab1:
        nueva_col = st.text_input("Nombre de la nueva columna", key="nueva_col_nombre")
        formula_ejemplo = st.text_area(
            "Fórmula (ej: =[Debe] - [Haber])",
            key="formula_nueva_col",
            placeholder="Ejemplos:\n=[Debe] + [Haber]\n=[Debe] * 1.21\n=sum([Debe])"
        )
        
        if st.button("Crear columna calculada", key="btn_crear_columna"):
            if nueva_col and formula_ejemplo:
                if nueva_col in df.columns:
                    st.warning(f"La columna '{nueva_col}' ya existe")
                else:
                    df_temp = df.copy()
                    if formula_ejemplo.startswith('='):
                        df_temp = FormulaEngine.aplicar_formula_columna(df_temp, nueva_col, formula_ejemplo, por_fila=True)
                        st.success(f"Columna '{nueva_col}' creada exitosamente")
                        return df_temp
                    else:
                        st.error("Las fórmulas deben comenzar con '='")
    return df

def mostrar_calculadora_rapida(df):
    """Calculadora rápida para operaciones entre columnas"""
    with st.expander("Calculadora rápida"):
        col_calc1, col_calc2, col_calc3 = st.columns(3)
        
        with col_calc1:
            columna_a = st.selectbox("Columna A", df.columns.tolist(), key="calc_col_a")
        with col_calc2:
            operacion = st.selectbox("Operación", ["+", "-", "*", "/", "%"], key="calc_op")
        with col_calc3:
            columna_b = st.selectbox("Columna B", ["(Constante)"] + df.columns.tolist(), key="calc_col_b")
        
        resultado_nombre = st.text_input("Nombre resultado", value=f"{columna_a}_{operacion}_resultado", key="calc_resultado_nombre")
        
        if st.button("Calcular", key="btn_calcular"):
            df_temp = df.copy()
            if columna_b == "(Constante)":
                valor_constante = st.number_input("Valor constante", value=0.0, key="calc_constante", label_visibility="collapsed")
                if operacion == "+":
                    df_temp[resultado_nombre] = df_temp[columna_a] + valor_constante
                elif operacion == "-":
                    df_temp[resultado_nombre] = df_temp[columna_a] - valor_constante
                elif operacion == "*":
                    df_temp[resultado_nombre] = df_temp[columna_a] * valor_constante
                elif operacion == "/":
                    df_temp[resultado_nombre] = df_temp[columna_a] / valor_constante if valor_constante != 0 else 0
                elif operacion == "%":
                    df_temp[resultado_nombre] = df_temp[columna_a] * (valor_constante / 100)
            else:
                if operacion == "+":
                    df_temp[resultado_nombre] = df_temp[columna_a] + df_temp[columna_b]
                elif operacion == "-":
                    df_temp[resultado_nombre] = df_temp[columna_a] - df_temp[columna_b]
                elif operacion == "*":
                    df_temp[resultado_nombre] = df_temp[columna_a] * df_temp[columna_b]
                elif operacion == "/":
                    df_temp[resultado_nombre] = df_temp[columna_a] / df_temp[columna_b].replace(0, 1)
                elif operacion == "%":
                    df_temp[resultado_nombre] = (df_temp[columna_a] / df_temp[columna_b].replace(0, 1)) * 100
            
            st.success(f"Columna '{resultado_nombre}' creada")
            return df_temp
    return df

def mostrar_totales_columnas(df):
    """Muestra totales y estadísticas"""
    with st.expander("Estadísticas de columnas"):
        columnas_numericas = df.select_dtypes(include=['number']).columns.tolist()
        
        if columnas_numericas:
            stats_data = []
            for col in columnas_numericas:
                stats_data.append({
                    "Columna": col,
                    "Suma": df[col].sum(),
                    "Promedio": df[col].mean(),
                    "Mínimo": df[col].min(),
                    "Máximo": df[col].max(),
                })
            stats_df = pd.DataFrame(stats_data)
            st.dataframe(stats_df, use_container_width=True)
    return df

# ========== FUNCIONES DE REPORTES ==========

def generar_balance_general(edited_df, nombre_proyecto):
    """Genera Balance General"""
    activos = 0
    pasivos = 0
    capital = 0
    
    palabras_activo = ['activo', 'caja', 'banco', 'efectivo', 'inventario', 'cliente', 'cuenta por cobrar']
    palabras_pasivo = ['pasivo', 'proveedor', 'cuenta por pagar', 'acreedor', 'préstamo', 'deuda']
    palabras_capital = ['capital', 'patrimonio', 'aporte', 'inversión']
    
    columnas_numericas = edited_df.select_dtypes(include=['number']).columns.tolist()
    
    for idx, row in edited_df.iterrows():
        texto_completo = " "
        for col in edited_df.columns:
            if col not in columnas_numericas:
                texto_completo += str(row.get(col, "")).lower() + " "
        
        valor = 0
        if 'Debe' in row and 'Haber' in row:
            valor = (row.get('Debe', 0) or 0) - (row.get('Haber', 0) or 0)
        else:
            for col in columnas_numericas:
                if row.get(col, 0) != 0:
                    valor = row.get(col, 0) or 0
                    break
        
        if any(p in texto_completo for p in palabras_activo):
            activos += abs(valor) if valor > 0 else 0
        elif any(p in texto_completo for p in palabras_pasivo):
            pasivos += abs(valor) if valor < 0 else valor if valor > 0 else 0
        elif any(p in texto_completo for p in palabras_capital):
            capital += abs(valor) if valor > 0 else 0
    
    if activos == 0 and pasivos == 0 and capital == 0:
        if 'Debe' in edited_df.columns:
            activos = edited_df['Debe'].sum()
        if 'Haber' in edited_df.columns:
            pasivos = edited_df['Haber'].sum()
    
    st.info(f"Activos: ${activos:,.2f} | Pasivos: ${pasivos:,.2f} | Capital: ${capital:,.2f}")
    
    return {
        "activos": activos,
        "pasivos": pasivos,
        "capital": capital,
        "total_pasivo_capital": pasivos + capital,
        "diferencia": activos - (pasivos + capital),
        "fecha": datetime.now().strftime("%d/%m/%Y")
    }

def generar_estado_resultados(edited_df):
    """Genera Estado de Resultados"""
    ingresos = 0
    gastos = 0
    
    palabras_ingreso = ['ingreso', 'venta', 'servicio', 'honorarios']
    palabras_gasto = ['gasto', 'costo', 'compra', 'sueldo', 'alquiler']
    
    if "Debe" in edited_df.columns and "Haber" in edited_df.columns:
        for idx, row in edited_df.iterrows():
            desc = str(row.get("Descripción", row.get("Concepto", row.get("Cuenta", "")))).lower()
            debe = row.get("Debe", 0) or 0
            haber = row.get("Haber", 0) or 0
            
            if any(p in desc for p in palabras_ingreso):
                ingresos += haber
            elif any(p in desc for p in palabras_gasto):
                gastos += debe
    
    utilidad = ingresos - gastos
    
    return {
        "ingresos": ingresos,
        "gastos": gastos,
        "utilidad_neta": utilidad,
        "tipo": "Ganancia" if utilidad > 0 else "Pérdida" if utilidad < 0 else "Equilibrio",
        "fecha": datetime.now().strftime("%d/%m/%Y")
    }

def exportar_pdf_reporte(tipo, datos, nombre_proyecto):
    """Exporta reporte a PDF"""
    buffer = BytesIO()
    html_content = f"""
    <html>
    <head><title>Reporte - {nombre_proyecto}</title></head>
    <body>
        <h1>{'BALANCE GENERAL' if tipo == 'balance' else 'ESTADO DE RESULTADOS'}</h1>
        <h2>{nombre_proyecto}</h2>
        <p>Fecha: {datos['fecha']}</p>
        <hr>
        <table border="1" cellpadding="8">
    """
    if tipo == "balance":
        html_content += f"""
            <tr><th>Concepto</th><th>Monto (USD)</th></tr>
            <tr><td>ACTIVOS</td><td>${datos['activos']:,.2f}</td></tr>
            <tr><td>PASIVOS</td><td>${datos['pasivos']:,.2f}</td></tr>
            <tr><td>CAPITAL</td><td>${datos['capital']:,.2f}</td></tr>
            <tr><td><b>TOTAL</b></td><td><b>${datos['total_pasivo_capital']:,.2f}</b></td></tr>
        </table>
        """
    else:
        html_content += f"""
            <tr><th>Concepto</th><th>Monto (USD)</th></tr>
            <tr><td>INGRESOS</td><td>${datos['ingresos']:,.2f}</td></tr>
            <tr><td>GASTOS</td><td>${datos['gastos']:,.2f}</td></tr>
            <tr><td><b>UTILIDAD NETA</b></td><td><b>${datos['utilidad_neta']:,.2f}</b></td></tr>
            <tr><td>RESULTADO</td><td>{datos['tipo']}</td></tr>
        </table>
        """
    html_content += "</body></html>"
    return BytesIO(html_content.encode())

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 20px 0 10px 0;">
        <h2 style="color: #ffffff; margin: 0;">Contaduría</h2>
        <p style="color: #94a3b8; font-size: 12px;">Sistema Contable Profesional</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    if not st.session_state.usuario:
        with st.expander("Iniciar Sesión", expanded=True):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Contraseña", type="password", key="login_pass")
            
            if st.button("Ingresar", use_container_width=True):
                if email and password:
                    password_hash = hashlib.sha256(password.encode()).hexdigest()
                    usuario = get_usuarios().find_one({"email": email, "password": password_hash})
                    if usuario:
                        usuario["_id"] = str(usuario["_id"])
                        st.session_state.usuario = usuario
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas")
        
        with st.expander("Registrarse"):
            reg_nombre = st.text_input("Nombre completo", key="reg_nombre")
            reg_email = st.text_input("Email", key="reg_email")
            reg_pass = st.text_input("Contraseña", type="password", key="reg_pass")
            reg_pass2 = st.text_input("Confirmar contraseña", type="password", key="reg_pass2")
            
            if st.button("Crear cuenta", use_container_width=True):
                if reg_pass == reg_pass2 and len(reg_pass) >= 6:
                    password_hash = hashlib.sha256(reg_pass.encode()).hexdigest()
                    if not get_usuarios().find_one({"email": reg_email}):
                        nuevo_usuario = {
                            "email": reg_email,
                            "password": password_hash,
                            "nombre": reg_nombre,
                            "creado_en": datetime.now()
                        }
                        get_usuarios().insert_one(nuevo_usuario)
                        st.success("Cuenta creada. Inicie sesión.")
                    else:
                        st.error("El email ya existe")
    
    else:
        st.markdown(f"""
        <div style="background-color: #1a1e2e; padding: 12px; border-radius: 8px;">
            <p style="color: #94a3b8;">{st.session_state.usuario['nombre']}</p>
            <p style="color: #64748b; font-size: 11px;">{st.session_state.usuario['email']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Cerrar sesión", use_container_width=True):
            st.session_state.usuario = None
            st.session_state.proyecto_actual = None
            st.rerun()
        
        st.divider()
        st.markdown("**Proyectos**")
        
        proyectos = list(get_proyectos().find({"email_usuario": st.session_state.usuario["email"]}))
        
        for proy in proyectos:
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(proy['nombre'], key=f"proy_{proy['_id']}", use_container_width=True):
                    proy["_id"] = str(proy["_id"])
                    st.session_state.proyecto_actual = proy
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{proy['_id']}"):
                    get_proyectos().delete_one({"_id": proy["_id"]})
                    st.rerun()
        
        st.divider()
        st.markdown("**Nuevo proyecto**")
        nuevo_nombre = st.text_input("Nombre", key="nuevo_nombre")
        nuevo_tipo = st.selectbox("Plantilla", ["Libro Diario", "Balanza de Comprobación", "Cuentas T"])
        
        if st.button("Crear", use_container_width=True):
            if nuevo_nombre:
                columnas_tipo = {
                    "Libro Diario": ["Fecha", "Descripción", "Cuenta", "Debe", "Haber"],
                    "Balanza de Comprobación": ["Código", "Cuenta", "Saldo Inicial", "Cargos", "Abonos"],
                    "Cuentas T": ["Fecha", "Concepto", "Referencia", "Debe", "Haber"]
                }
                nuevo_proyecto = {
                    "nombre": nuevo_nombre,
                    "tipo": nuevo_tipo,
                    "datos": [],
                    "columnas": columnas_tipo[nuevo_tipo],
                    "email_usuario": st.session_state.usuario["email"],
                    "creado_en": datetime.now()
                }
                get_proyectos().insert_one(nuevo_proyecto)
                st.rerun()

# ========== ÁREA PRINCIPAL ==========
if st.session_state.proyecto_actual:
    proyecto = st.session_state.proyecto_actual
    
    st.markdown(f'<div class="main-header">{proyecto["nombre"]} ({proyecto.get("tipo", "Libro Diario")})</div>', unsafe_allow_html=True)
    
    columnas = proyecto.get("columnas", ["Fecha", "Descripción", "Debe", "Haber"])
    datos = proyecto.get("datos", [])
    df = pd.DataFrame(datos, columns=columnas) if datos else pd.DataFrame(columns=columnas)
    
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        height=400,
        column_config={
            "Debe": st.column_config.NumberColumn("Debe", format="$ %.2f"),
            "Haber": st.column_config.NumberColumn("Haber", format="$ %.2f"),
        }
    )
    
    # Herramientas de cálculo
    st.markdown("---")
    st.markdown('<div class="section-header">Herramientas de cálculo</div>', unsafe_allow_html=True)
    
    col_calc1, col_calc2, col_calc3 = st.columns(3)
    with col_calc1:
        if st.button("Nueva columna fórmula", use_container_width=True):
            df_resultado = mostrar_gestor_formulas(edited_df)
            if df_resultado is not edited_df:
                edited_df = df_resultado
                st.rerun()
    with col_calc2:
        if st.button("Calculadora rápida", use_container_width=True):
            df_resultado = mostrar_calculadora_rapida(edited_df)
            if df_resultado is not edited_df:
                edited_df = df_resultado
                st.rerun()
    with col_calc3:
        if st.button("Ver estadísticas", use_container_width=True):
            df_resultado = mostrar_totales_columnas(edited_df)
            if df_resultado is not edited_df:
                edited_df = df_resultado
                st.rerun()
    
    # Botones de acción
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Guardar", use_container_width=True):
            get_proyectos().update_one(
                {"_id": proyecto["_id"]},
                {"$set": {"datos": edited_df.fillna("").values.tolist()}}
            )
            st.success("Guardado")
    
    with col2:
        if st.button("Balance General", use_container_width=True):
            if len(edited_df) > 0:
                balance = generar_balance_general(edited_df, proyecto["nombre"])
                pdf = exportar_pdf_reporte("balance", balance, proyecto["nombre"])
                st.download_button("Descargar PDF", data=pdf, file_name=f"Balance_{proyecto['nombre']}.pdf", mime="application/pdf")
    
    with col3:
        if st.button("Estado Resultados", use_container_width=True):
            if len(edited_df) > 0:
                resultados = generar_estado_resultados(edited_df)
                pdf = exportar_pdf_reporte("resultados", resultados, proyecto["nombre"])
                st.download_button("Descargar PDF", data=pdf, file_name=f"Resultados_{proyecto['nombre']}.pdf", mime="application/pdf")
    
    with col4:
        if st.button("Eliminar", use_container_width=True):
            get_proyectos().delete_one({"_id": proyecto["_id"]})
            st.session_state.proyecto_actual = None
            st.rerun()
    
    # Métricas
    st.divider()
    col_m1, col_m2, col_m3 = st.columns(3)
    total_debe = edited_df["Debe"].sum() if "Debe" in edited_df.columns else 0
    total_haber = edited_df["Haber"].sum() if "Haber" in edited_df.columns else 0
    col_m1.metric("Total Debe", f"${total_debe:,.2f}")
    col_m2.metric("Total Haber", f"${total_haber:,.2f}")
    col_m3.metric("Diferencia", f"${total_debe - total_haber:,.2f}")

elif st.session_state.usuario:
    st.markdown("""
    <div style="text-align: center; padding: 60px;">
        <h2>Bienvenido a Contaduría</h2>
        <p>Seleccione o cree un proyecto en el menú lateral</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="text-align: center; padding: 60px;">
        <h2>Contaduría</h2>
        <p>Sistema de gestión contable profesional</p>
        <p>Inicie sesión o regístrese para continuar</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()
st.markdown('<p style="text-align: center; color: #64748b;">Contaduría · Sistema Contable Profesional</p>', unsafe_allow_html=True)
