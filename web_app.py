# web_app.py - VERSIÓN CORREGIDA (Web)

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
import time

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

# ========== ESTADO DE SESIÓN ==========
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "proyecto_actual" not in st.session_state:
    st.session_state.proyecto_actual = None
if "login_visible" not in st.session_state:
    st.session_state.login_visible = True  # CORRECCIÓN: Control de visibilidad del login
if "error_login" not in st.session_state:
    st.session_state.error_login = ""
if "mensaje_exito" not in st.session_state:
    st.session_state.mensaje_exito = ""
if "sesion_iniciada" not in st.session_state:
    st.session_state.sesion_iniciada = False

# ========== FUNCIÓN PARA FORZAR REFRESH ==========
def force_rerun():
    """Forzar recarga de la página"""
    st.rerun()

# ========== FUNCIÓN PARA MOSTRAR LOGIN ==========
def mostrar_login():
    """Muestra el formulario de login - CORREGIDO para que no se cierre permanentemente"""
    st.session_state.login_visible = True
    st.session_state.sesion_iniciada = False
    
    # CSS para el contenedor de login
    st.markdown("""
    <style>
    .login-container {
        max-width: 450px;
        margin: 50px auto;
        padding: 30px;
        background-color: #1a1e2e;
        border-radius: 12px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
        border: 1px solid #2d3748;
    }
    .login-header {
        text-align: center;
        margin-bottom: 30px;
    }
    .login-header h1 {
        color: #ffffff;
        margin-bottom: 10px;
    }
    .login-header p {
        color: #94a3b8;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container():
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            st.markdown('<div class="login-header"><h1>📊 Contaduría</h1><p>Sistema Contable Profesional</p></div>', unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["🔐 Iniciar Sesión", "📝 Registrarse"])
            
            with tab1:
                email = st.text_input("Email", key="login_email", placeholder="usuario@ejemplo.com")
                password = st.text_input("Contraseña", type="password", key="login_pass", placeholder="••••••••")
                
                if st.button("Ingresar", key="btn_login", use_container_width=True):
                    if email and password:
                        password_hash = hashlib.sha256(password.encode()).hexdigest()
                        usuario = get_usuarios().find_one({"email": email, "password": password_hash})
                        if usuario:
                            usuario["_id"] = str(usuario["_id"])
                            st.session_state.usuario = usuario
                            st.session_state.sesion_iniciada = True
                            st.session_state.login_visible = False
                            st.session_state.error_login = ""
                            st.rerun()
                        else:
                            st.session_state.error_login = "❌ Credenciales incorrectas"
                    else:
                        st.session_state.error_login = "❌ Complete todos los campos"
                
                if st.session_state.error_login:
                    st.error(st.session_state.error_login)
            
            with tab2:
                reg_nombre = st.text_input("Nombre completo", key="reg_nombre", placeholder="Tu nombre")
                reg_email = st.text_input("Email", key="reg_email", placeholder="usuario@ejemplo.com")
                reg_pass = st.text_input("Contraseña", type="password", key="reg_pass", placeholder="Mínimo 6 caracteres")
                reg_pass2 = st.text_input("Confirmar contraseña", type="password", key="reg_pass2")
                
                if st.button("Crear cuenta", key="btn_registro", use_container_width=True):
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
                            st.session_state.mensaje_exito = "✅ Cuenta creada. ¡Ahora inicia sesión!"
                            st.rerun()
                        else:
                            st.session_state.error_login = "❌ El email ya existe"
                    else:
                        st.session_state.error_login = "❌ Las contraseñas no coinciden o son muy cortas"
                
                if st.session_state.mensaje_exito:
                    st.success(st.session_state.mensaje_exito)
            
            # CORRECCIÓN: Botón para trabajar offline
            st.markdown("---")
            if st.button("💾 Trabajar sin conexión (modo demo)", use_container_width=True):
                st.session_state.sesion_iniciada = True
                st.session_state.login_visible = False
                st.session_state.usuario = {"email": "demo@demo.com", "nombre": "Usuario Demo"}
                st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)

# ========== CONEXIÓN A MONGODB ==========
MONGO_URI = st.secrets["MONGO_URI"]
DB_NAME = st.secrets["DB_NAME"]

@st.cache_resource
def init_connection():
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None

client = init_connection()
if client:
    db = client[DB_NAME]
else:
    st.warning("⚠️ No se pudo conectar a la base de datos. Algunas funciones estarán limitadas.")
    # Crear una base de datos mock para modo offline
    class MockDB:
        def __init__(self):
            self.usuarios = []
            self.proyectos = []
    db = MockDB()

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
    with st.expander("📐 Gestor de Fórmulas", expanded=False):
        tab1, tab2 = st.tabs(["➕ Nueva Columna", "📊 Sugerencias"])
        
        with tab1:
            nueva_col = st.text_input("Nombre de la nueva columna", key="nueva_col_nombre")
            formula_ejemplo = st.text_area(
                "Fórmula (ej: =[Debe] - [Haber])",
                key="formula_nueva_col",
                placeholder="Ejemplos:\n=[Debe] + [Haber]\n=[Debe] * 1.21\n=sum([Debe])"
            )
            
            if st.button("✨ Crear columna calculada", key="btn_crear_columna"):
                if nueva_col and formula_ejemplo:
                    if nueva_col in df.columns:
                        st.warning(f"⚠️ La columna '{nueva_col}' ya existe")
                    else:
                        df_temp = df.copy()
                        if formula_ejemplo.startswith('='):
                            df_temp = FormulaEngine.aplicar_formula_columna(df_temp, nueva_col, formula_ejemplo, por_fila=True)
                            st.success(f"✅ Columna '{nueva_col}' creada exitosamente")
                            return df_temp
                        else:
                            st.error("❌ Las fórmulas deben comenzar con '='")
    return df

def mostrar_calculadora_rapida(df):
    """Calculadora rápida para operaciones entre columnas"""
    with st.expander("🧮 Calculadora rápida", expanded=False):
        col_calc1, col_calc2, col_calc3 = st.columns(3)
        
        with col_calc1:
            columna_a = st.selectbox("Columna A", df.columns.tolist(), key="calc_col_a")
        with col_calc2:
            operacion = st.selectbox("Operación", ["+", "-", "*", "/", "%"], key="calc_op")
        with col_calc3:
            columna_b = st.selectbox("Columna B", ["(Constante)"] + df.columns.tolist(), key="calc_col_b")
        
        resultado_nombre = st.text_input("Nombre resultado", value=f"{columna_a}_{operacion}_resultado", key="calc_resultado_nombre")
        
        if st.button("🔢 Calcular", key="btn_calcular"):
            df_temp = df.copy()
            try:
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
                
                st.success(f"✅ Columna '{resultado_nombre}' creada")
                return df_temp
            except Exception as e:
                st.error(f"❌ Error: {e}")
    return df

def mostrar_totales_columnas(df):
    """Muestra totales y estadísticas"""
    with st.expander("📈 Estadísticas de columnas", expanded=False):
        columnas_numericas = df.select_dtypes(include=['number']).columns.tolist()
        
        if columnas_numericas:
            stats_data = []
            for col in columnas_numericas:
                stats_data.append({
                    "📊 Columna": col,
                    "💰 Suma": f"${df[col].sum():,.2f}",
                    "📈 Promedio": f"${df[col].mean():,.2f}",
                    "📉 Mínimo": f"${df[col].min():,.2f}",
                    "📈 Máximo": f"${df[col].max():,.2f}",
                })
            stats_df = pd.DataFrame(stats_data)
            st.dataframe(stats_df, use_container_width=True)
        else:
            st.info("ℹ️ No hay columnas numéricas para analizar")
    return df

# ========== FUNCIONES DE REPORTES ==========

def generar_balance_general(edited_df, nombre_proyecto):
    """Genera Balance General"""
    activos = 0
    pasivos = 0
    capital = 0
    
    palabras_activo = ['activo', 'caja', 'banco', 'efectivo', 'inventario', 'cliente', 'cuenta por cobrar', 'cuenta x cobrar']
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
    
    return {
        "activos": activos,
        "pasivos": pasivos,
        "capital": capital,
        "total_pasivo_capital": pasivos + capital,
        "diferencia": activos - (pasivos + capital),
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M")
    }

def generar_estado_resultados(edited_df):
    """Genera Estado de Resultados"""
    ingresos = 0
    gastos = 0
    
    palabras_ingreso = ['ingreso', 'venta', 'servicio', 'honorarios', 'ingresos']
    palabras_gasto = ['gasto', 'costo', 'compra', 'sueldo', 'alquiler', 'gastos']
    
    if "Debe" in edited_df.columns and "Haber" in edited_df.columns:
        for idx, row in edited_df.iterrows():
            desc = str(row.get("Descripción", row.get("Concepto", row.get("Cuenta", "")))).lower()
            debe = row.get("Debe", 0) or 0
            haber = row.get("Haber", 0) or 0
            
            if any(p in desc for p in palabras_ingreso):
                ingresos += haber if haber > 0 else debe
            elif any(p in desc for p in palabras_gasto):
                gastos += debe if debe > 0 else haber
    
    utilidad = ingresos - gastos
    
    return {
        "ingresos": ingresos,
        "gastos": gastos,
        "utilidad_neta": utilidad,
        "tipo": "🟢 GANANCIA" if utilidad > 0 else "🔴 PÉRDIDA" if utilidad < 0 else "⚪ EQUILIBRIO",
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M")
    }

def exportar_pdf_reporte(tipo, datos, nombre_proyecto):
    """Exporta reporte a PDF"""
    buffer = BytesIO()
    html_content = f"""
    <html>
    <head>
        <title>Reporte - {nombre_proyecto}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; }}
            h2 {{ color: #34495e; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #2c3e50; color: white; }}
            .total {{ font-weight: bold; background-color: #f2f2f2; }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #7f8c8d; text-align: center; }}
        </style>
    </head>
    <body>
        <h1>{'📊 BALANCE GENERAL' if tipo == 'balance' else '📈 ESTADO DE RESULTADOS'}</h1>
        <h2>{nombre_proyecto}</h2>
        <p><strong>📅 Fecha:</strong> {datos['fecha']}</p>
        <hr>
        <table>
    """
    if tipo == "balance":
        html_content += f"""
            <table><th>Concepto</th><th>Monto (USD)</th></tr>
            <tr><td><strong>ACTIVOS</strong></td><td>${datos['activos']:,.2f}</td></tr>
            <tr><td><strong>PASIVOS</strong></td><td>${datos['pasivos']:,.2f}</td></tr>
            <tr><td><strong>CAPITAL</strong></td><td>${datos['capital']:,.2f}</td></tr>
            <tr class="total"><td><strong>TOTAL PASIVO + CAPITAL</strong></td><td><strong>${datos['total_pasivo_capital']:,.2f}</strong></td></tr>
            <tr><td><strong>DIFERENCIA</strong></td><td><strong>${datos['diferencia']:,.2f}</strong></td></tr>
        </table>
        """
    else:
        html_content += f"""
            <table><th>Concepto</th><th>Monto (USD)</th></tr>
            <tr><td><strong>INGRESOS</strong></td><td>${datos['ingresos']:,.2f}</td></tr>
            <tr><td><strong>GASTOS</strong></td><td>${datos['gastos']:,.2f}</td></tr>
            <tr class="total"><td><strong>UTILIDAD NETA</strong></td><td><strong>${datos['utilidad_neta']:,.2f}</strong></td></tr>
            <tr><td><strong>RESULTADO</strong></td><td><strong>{datos['tipo']}</strong></td></tr>
        </table>
        """
    html_content += f"""
        <div class="footer">
            <p>Reporte generado por Contaduría - Sistema Contable Profesional</p>
        </div>
    </body>
    </html>
    """
    return BytesIO(html_content.encode())

# ========== INTERFAZ PRINCIPAL ==========

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 28px;
        font-weight: 600;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #1a1e2e;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #2d3748;
    }
    .stButton button {
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    hr {
        margin: 20px 0;
        border-color: #2d3748;
    }
</style>
""", unsafe_allow_html=True)

# CORRECCIÓN: Control de visualización del login
if not st.session_state.sesion_iniciada and st.session_state.login_visible:
    mostrar_login()
elif st.session_state.sesion_iniciada or st.session_state.usuario:
    # CORRECCIÓN: Botón para cerrar sesión y volver al login
    col_logout1, col_logout2 = st.columns([6, 1])
    with col_logout2:
        if st.button("🚪 Cerrar sesión", use_container_width=True):
            st.session_state.sesion_iniciada = False
            st.session_state.usuario = None
            st.session_state.proyecto_actual = None
            st.session_state.login_visible = True
            st.rerun()
    
    st.markdown(f'<div class="main-header">📊 Contaduría - {st.session_state.usuario["nombre"] if st.session_state.usuario else "Usuario"}</div>', unsafe_allow_html=True)
    
    # Sidebar con proyectos
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align: center; padding: 20px 0;">
            <h2 style="color: #ffffff;">📁 Proyectos</h2>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.usuario and st.session_state.usuario.get("email"):
            proyectos = list(get_proyectos().find({"email_usuario": st.session_state.usuario["email"]})) if client else []
        else:
            proyectos = []
        
        for proy in proyectos:
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(f"📄 {proy['nombre']}", key=f"proy_{proy['_id']}", use_container_width=True):
                    proy["_id"] = str(proy["_id"])
                    st.session_state.proyecto_actual = proy
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{proy['_id']}"):
                    if client:
                        get_proyectos().delete_one({"_id": proy["_id"]})
                    st.rerun()
        
        st.divider()
        st.markdown("### ✨ Nuevo proyecto")
        nuevo_nombre = st.text_input("Nombre", key="nuevo_nombre")
        nuevo_tipo = st.selectbox("Plantilla", ["Libro Diario", "Balanza de Comprobación", "Cuentas T / Mayor"])
        
        if st.button("🎯 Crear proyecto", use_container_width=True):
            if nuevo_nombre:
                columnas_tipo = {
                    "Libro Diario": ["Fecha", "Descripción", "Cuenta", "Debe", "Haber"],
                    "Balanza de Comprobación": ["Código", "Cuenta", "Saldo Inicial", "Cargos", "Abonos"],
                    "Cuentas T / Mayor": ["Fecha", "Concepto", "Referencia", "Debe", "Haber"]
                }
                nuevo_proyecto = {
                    "nombre": nuevo_nombre,
                    "tipo": nuevo_tipo,
                    "datos": [],
                    "columnas": columnas_tipo[nuevo_tipo],
                    "email_usuario": st.session_state.usuario["email"] if st.session_state.usuario else "demo@demo.com",
                    "creado_en": datetime.now()
                }
                if client:
                    get_proyectos().insert_one(nuevo_proyecto)
                st.rerun()
        
        st.divider()
        st.markdown("### 💡 Información")
        st.info("""
        **Atajos útiles:**
        - 📐 Fórmulas: `=[Debe] - [Haber]`
        - 🧮 Calculadora rápida para operaciones entre columnas
        - 📊 Gráficas automáticas
        - 📈 Reportes contables en PDF
        """)
    
    # Área principal
    if st.session_state.proyecto_actual:
        proyecto = st.session_state.proyecto_actual
        
        st.markdown(f"## 📋 {proyecto['nombre']}")
        st.caption(f"Tipo: {proyecto.get('tipo', 'Libro Diario')}")
        
        columnas = proyecto.get("columnas", ["Fecha", "Descripción", "Debe", "Haber"])
        datos = proyecto.get("datos", [])
        df = pd.DataFrame(datos, columns=columnas) if datos else pd.DataFrame(columns=columnas)
        
        # Editor de datos principal
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            height=400,
            column_config={
                "Debe": st.column_config.NumberColumn("💰 Debe", format="$ %.2f"),
                "Haber": st.column_config.NumberColumn("💵 Haber", format="$ %.2f"),
                "Fecha": st.column_config.DateColumn("📅 Fecha"),
            }
        )
        
        # Herramientas de análisis
        st.markdown("---")
        st.markdown("### 🛠️ Herramientas de Análisis")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if st.button("📐 Gestor Fórmulas", use_container_width=True):
                df_resultado = mostrar_gestor_formulas(edited_df)
                if df_resultado is not edited_df:
                    edited_df = df_resultado
                    st.rerun()
        with col2:
            if st.button("🧮 Calculadora", use_container_width=True):
                df_resultado = mostrar_calculadora_rapida(edited_df)
                if df_resultado is not edited_df:
                    edited_df = df_resultado
                    st.rerun()
        with col3:
            if st.button("📈 Estadísticas", use_container_width=True):
                df_resultado = mostrar_totales_columnas(edited_df)
                if df_resultado is not edited_df:
                    edited_df = df_resultado
                    st.rerun()
        with col4:
            if st.button("📊 Gráficas", use_container_width=True):
                if len(edited_df) > 0:
                    fig, ax = plt.subplots(figsize=(10, 5))
                    if "Debe" in edited_df.columns and "Haber" in edited_df.columns:
                        ax.bar(range(len(edited_df)), edited_df["Debe"].fillna(0), label="Debe", alpha=0.7, color="#e74c3c")
                        ax.bar(range(len(edited_df)), edited_df["Haber"].fillna(0), label="Haber", alpha=0.7, color="#27ae60", bottom=edited_df["Debe"].fillna(0))
                        ax.set_xlabel("Registros")
                        ax.set_ylabel("Monto ($)")
                        ax.set_title(f"Comparación Debe vs Haber - {proyecto['nombre']}")
                        ax.legend()
                        ax.grid(True, alpha=0.3)
                        st.pyplot(fig)
                    else:
                        st.warning("Se requieren columnas 'Debe' y 'Haber' para gráficas")
                else:
                    st.warning("No hay datos para graficar")
        with col5:
            if st.button("💾 Guardar", use_container_width=True):
                if client:
                    get_proyectos().update_one(
                        {"_id": proyecto["_id"]},
                        {"$set": {"datos": edited_df.fillna("").values.tolist()}}
                    )
                    st.success("✅ Datos guardados correctamente")
                else:
                    st.warning("⚠️ Modo offline - Los datos no se guardarán permanentemente")
        
        # Reportes
        st.markdown("---")
        st.markdown("### 📄 Reportes Contables")
        
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            if st.button("📊 Balance General", use_container_width=True):
                if len(edited_df) > 0:
                    balance = generar_balance_general(edited_df, proyecto["nombre"])
                    
                    # Mostrar resumen
                    st.success(f"""
                    **Balance General - {proyecto['nombre']}**
                    - Activos: ${balance['activos']:,.2f}
                    - Pasivos: ${balance['pasivos']:,.2f}
                    - Capital: ${balance['capital']:,.2f}
                    - Diferencia: ${balance['diferencia']:,.2f}
                    """)
                    
                    pdf = exportar_pdf_reporte("balance", balance, proyecto["nombre"])
                    st.download_button(
                        label="📥 Descargar PDF",
                        data=pdf,
                        file_name=f"Balance_{proyecto['nombre']}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.warning("No hay datos para generar el balance")
        
        with col_r2:
            if st.button("📈 Estado Resultados", use_container_width=True):
                if len(edited_df) > 0:
                    resultados = generar_estado_resultados(edited_df)
                    
                    # Mostrar resumen
                    st.success(f"""
                    **Estado de Resultados - {proyecto['nombre']}**
                    - Ingresos: ${resultados['ingresos']:,.2f}
                    - Gastos: ${resultados['gastos']:,.2f}
                    - Utilidad Neta: ${resultados['utilidad_neta']:,.2f}
                    - Resultado: {resultados['tipo']}
                    """)
                    
                    pdf = exportar_pdf_reporte("resultados", resultados, proyecto["nombre"])
                    st.download_button(
                        label="📥 Descargar PDF",
                        data=pdf,
                        file_name=f"Resultados_{proyecto['nombre']}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.warning("No hay datos para generar el estado de resultados")
        
        # Métricas rápidas
        st.markdown("---")
        st.markdown("### 📊 Métricas Rápidas")
        
        col_m1, col_m2, col_m3 = st.columns(3)
        total_debe = edited_df["Debe"].sum() if "Debe" in edited_df.columns else 0
        total_haber = edited_df["Haber"].sum() if "Haber" in edited_df.columns else 0
        
        with col_m1:
            st.metric("💰 Total Debe", f"${total_debe:,.2f}")
        with col_m2:
            st.metric("💵 Total Haber", f"${total_haber:,.2f}")
        with col_m3:
            diferencia = total_debe - total_haber
            st.metric("⚖️ Diferencia", f"${diferencia:,.2f}", 
                     delta=f"{'Superávit' if diferencia > 0 else 'Déficit' if diferencia < 0 else 'Equilibrio'}")
    
    else:
        st.info("👈 Selecciona o crea un proyecto en el menú lateral para comenzar")
        
        # Mostrar características
        st.markdown("---")
        st.markdown("### 🚀 Características del Sistema")
        
        col_feat1, col_feat2, col_feat3 = st.columns(3)
        with col_feat1:
            st.markdown("""
            **📐 Fórmulas Inteligentes**
            - Fórmulas tipo Excel
            - Referencias a columnas con [Nombre]
            - Cálculos automáticos
            """)
        with col_feat2:
            st.markdown("""
            **📊 Análisis Visual**
            - Gráficas interactivas
            - Estadísticas automáticas
            - Reportes profesionales
            """)
        with col_feat3:
            st.markdown("""
            **☁️ Cloud Ready**
            - Acceso desde cualquier lugar
            - Sincronización automática
            - Datos seguros
            """)

else:
    st.info("👈 Inicia sesión o regístrate para comenzar")