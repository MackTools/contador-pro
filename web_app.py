# web_app.py - VERSIÓN MEJORADA
# Diseño minimalista, sin iconos excesivos, todas las funcionalidades

import streamlit as st
import pandas as pd
import hashlib
import pymongo
from datetime import datetime
import openpyxl
from io import BytesIO
import matplotlib.pyplot as plt
import re

# ========== CONFIGURACIÓN ==========
st.set_page_config(
    page_title="Contaduría",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== ESTADO DE SESIÓN ==========
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "proyecto_actual" not in st.session_state:
    st.session_state.proyecto_actual = None
if "sesion_activa" not in st.session_state:
    st.session_state.sesion_activa = False

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
        st.error(f"Error de conexión: {e}")
        return None

client = init_connection()
if client:
    db = client[DB_NAME]

def get_usuarios():
    return db.usuarios

def get_proyectos():
    return db.proyectos

# ========== CSS MINIMALISTA ==========
st.markdown("""
<style>
    /* Estilo minimalista - sin iconos excesivos */
    .stApp { background-color: #f5f5f5; }
    .main > div { background-color: #f5f5f5; }
    
    /* Encabezados limpios */
    h1, h2, h3 { color: #1a1a1a; font-weight: 500; margin-bottom: 1rem; }
    h1 { font-size: 1.8rem; border-left: 3px solid #2c7da0; padding-left: 1rem; }
    h2 { font-size: 1.4rem; border-bottom: 1px solid #e0e0e0; padding-bottom: 0.5rem; }
    h3 { font-size: 1.1rem; color: #2c7da0; }
    
    /* Botones planos */
    .stButton button {
        background-color: #2c7da0;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.4rem 1rem;
        font-weight: 400;
        transition: all 0.2s;
    }
    .stButton button:hover {
        background-color: #1f5e7a;
        transform: none;
    }
    
    /* Botón secundario */
    .stButton button[data-testid="baseButton-secondary"] {
        background-color: #e0e0e0;
        color: #1a1a1a;
    }
    
    /* Sidebar minimalista */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }
    [data-testid="stSidebar"] .stMarkdown {
        color: #1a1a1a;
    }
    
    /* Tablas */
    [data-testid="stDataFrame"] {
        border: 1px solid #e0e0e0;
        border-radius: 4px;
    }
    
    /* Inputs */
    .stTextInput input, .stSelectbox select, .stTextArea textarea {
        background-color: #ffffff;
        border: 1px solid #cccccc;
        border-radius: 4px;
        padding: 0.5rem;
    }
    
    /* Tarjetas de métricas */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        padding: 1rem;
    }
    
    /* Dividers */
    hr { margin: 1.5rem 0; border-color: #e0e0e0; }
    
    /* Ocultar elementos no necesarios */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ========== MOTOR DE FÓRMULAS (NUEVO) ==========
class FormulaEngine:
    @staticmethod
    def aplicar_formula(df, formula, nueva_columna):
        """Aplica una fórmula a un DataFrame"""
        try:
            formula = formula.strip()
            if formula.startswith('='):
                formula = formula[1:]
            
            # Reemplazar referencias a columnas [Nombre]
            def replace_col(match):
                col = match.group(1)
                return f"df['{col}']"
            
            expr = re.sub(r'\[([^\]]+)\]', replace_col, formula)
            
            # Evaluar
            resultado = eval(expr)
            
            if isinstance(resultado, pd.Series):
                df[nueva_columna] = resultado
            else:
                df[nueva_columna] = resultado
            return df, True, None
        except Exception as e:
            return df, False, str(e)

# ========== FUNCIONES DE REPORTES ==========
def generar_balance(df, nombre_proyecto):
    """Genera balance general"""
    palabras_activo = ['activo', 'caja', 'banco', 'efectivo', 'inventario', 'cliente', 'cuenta por cobrar']
    palabras_pasivo = ['pasivo', 'proveedor', 'cuenta por pagar', 'acreedor', 'prestamo', 'deuda']
    palabras_capital = ['capital', 'patrimonio', 'aporte', 'inversion']
    
    activos = 0
    pasivos = 0
    capital = 0
    
    for idx, row in df.iterrows():
        texto = " ".join([str(v) for v in row.values]).lower()
        
        if 'debe' in df.columns and 'haber' in df.columns:
            valor = (row.get('Debe', 0) or 0) - (row.get('Haber', 0) or 0)
        else:
            num_cols = df.select_dtypes(include=['number']).columns
            valor = row[num_cols[0]] if len(num_cols) > 0 else 0
        
        if any(p in texto for p in palabras_activo):
            activos += abs(valor) if valor > 0 else 0
        elif any(p in texto for p in palabras_pasivo):
            pasivos += abs(valor) if valor < 0 else valor if valor > 0 else 0
        elif any(p in texto for p in palabras_capital):
            capital += abs(valor) if valor > 0 else 0
    
    return {
        "activos": activos,
        "pasivos": pasivos,
        "capital": capital,
        "total": activos - (pasivos + capital),
        "fecha": datetime.now().strftime("%d/%m/%Y")
    }

def generar_resultados(df):
    """Genera estado de resultados"""
    ingresos = 0
    gastos = 0
    
    palabras_ingreso = ['ingreso', 'venta', 'servicio', 'honorarios']
    palabras_gasto = ['gasto', 'costo', 'compra', 'sueldo', 'alquiler']
    
    if 'Debe' in df.columns and 'Haber' in df.columns:
        for idx, row in df.iterrows():
            desc = str(row.get('Descripcion', row.get('Concepto', ''))).lower()
            debe = row.get('Debe', 0) or 0
            haber = row.get('Haber', 0) or 0
            
            if any(p in desc for p in palabras_ingreso):
                ingresos += haber
            elif any(p in desc for p in palabras_gasto):
                gastos += debe
    
    utilidad = ingresos - gastos
    return {
        "ingresos": ingresos,
        "gastos": gastos,
        "utilidad": utilidad,
        "tipo": "GANANCIA" if utilidad > 0 else "PERDIDA" if utilidad < 0 else "EQUILIBRIO",
        "fecha": datetime.now().strftime("%d/%m/%Y")
    }

# ========== INTERFAZ DE LOGIN ==========
def mostrar_login():
    """Pantalla de login minimalista"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("## Contaduría")
        st.markdown("Sistema de gestión contable")
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["Iniciar sesión", "Registrarse"])
        
        with tab1:
            email = st.text_input("Correo electrónico", key="login_email")
            password = st.text_input("Contraseña", type="password", key="login_pass")
            
            if st.button("Ingresar", key="btn_login", use_container_width=True):
                if email and password:
                    password_hash = hashlib.sha256(password.encode()).hexdigest()
                    usuario = get_usuarios().find_one({"email": email, "password": password_hash})
                    if usuario:
                        st.session_state.usuario = usuario
                        st.session_state.sesion_activa = True
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas")
                else:
                    st.warning("Complete todos los campos")
        
        with tab2:
            nombre = st.text_input("Nombre completo", key="reg_nombre")
            email = st.text_input("Correo electrónico", key="reg_email")
            password = st.text_input("Contraseña", type="password", key="reg_pass")
            password2 = st.text_input("Confirmar contraseña", type="password", key="reg_pass2")
            
            if st.button("Crear cuenta", key="btn_registro", use_container_width=True):
                if password == password2 and len(password) >= 6:
                    password_hash = hashlib.sha256(password.encode()).hexdigest()
                    if not get_usuarios().find_one({"email": email}):
                        nuevo = {
                            "email": email,
                            "password": password_hash,
                            "nombre": nombre,
                            "creado_en": datetime.now()
                        }
                        get_usuarios().insert_one(nuevo)
                        st.success("Cuenta creada. Inicie sesión.")
                    else:
                        st.error("El email ya existe")
                else:
                    st.error("Las contraseñas no coinciden o son muy cortas")
        
        st.markdown("---")
        if st.button("Trabajar sin conexión", use_container_width=True):
            st.session_state.usuario = {"email": "demo@demo.com", "nombre": "Usuario Demo"}
            st.session_state.sesion_activa = True
            st.rerun()

# ========== INTERFAZ PRINCIPAL ==========
if not st.session_state.sesion_activa or not st.session_state.usuario:
    mostrar_login()
else:
    # Sidebar minimalista
    with st.sidebar:
        st.markdown(f"**{st.session_state.usuario['nombre']}**")
        st.markdown(f"<small>{st.session_state.usuario['email']}</small>", unsafe_allow_html=True)
        st.markdown("---")
        
        if st.button("Cerrar sesión", use_container_width=True):
            st.session_state.sesion_activa = False
            st.session_state.usuario = None
            st.session_state.proyecto_actual = None
            st.rerun()
        
        st.markdown("---")
        st.markdown("### Proyectos")
        
        proyectos = list(get_proyectos().find({"email_usuario": st.session_state.usuario["email"]}))
        
        for p in proyectos:
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(p['nombre'], key=f"proy_{p['_id']}", use_container_width=True):
                    st.session_state.proyecto_actual = p
                    st.rerun()
            with col2:
                if st.button("x", key=f"del_{p['_id']}"):
                    get_proyectos().delete_one({"_id": p["_id"]})
                    st.rerun()
        
        st.markdown("---")
        st.markdown("### Nuevo proyecto")
        nuevo_nombre = st.text_input("Nombre", key="nuevo_nombre")
        nuevo_tipo = st.selectbox("Tipo", ["Libro Diario", "Balanza", "Cuentas T"])
        
        if st.button("Crear", use_container_width=True):
            if nuevo_nombre:
                columnas = {
                    "Libro Diario": ["Fecha", "Descripcion", "Cuenta", "Debe", "Haber"],
                    "Balanza": ["Codigo", "Cuenta", "Saldo Inicial", "Cargos", "Abonos", "Saldo Final"],
                    "Cuentas T": ["Fecha", "Concepto", "Referencia", "Debe", "Haber", "Saldo"]
                }
                nuevo = {
                    "nombre": nuevo_nombre,
                    "tipo": nuevo_tipo,
                    "datos": [],
                    "columnas": columnas[nuevo_tipo],
                    "email_usuario": st.session_state.usuario["email"],
                    "creado_en": datetime.now()
                }
                get_proyectos().insert_one(nuevo)
                st.rerun()
    
    # Área principal
    if st.session_state.proyecto_actual:
        p = st.session_state.proyecto_actual
        
        st.markdown(f"# {p['nombre']}")
        st.markdown(f"<small>{p.get('tipo', 'Libro Diario')}</small>", unsafe_allow_html=True)
        st.markdown("---")
        
        # Cargar datos
        columnas = p.get("columnas", ["Fecha", "Descripcion", "Debe", "Haber"])
        datos = p.get("datos", [])
        df = pd.DataFrame(datos, columns=columnas) if datos else pd.DataFrame(columns=columnas)
        
        # Editor de datos
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
        
        # Barra de herramientas (minimalista)
        st.markdown("---")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("Guardar", use_container_width=True):
                get_proyectos().update_one(
                    {"_id": p["_id"]},
                    {"$set": {"datos": edited_df.fillna("").values.tolist()}}
                )
                st.success("Guardado")
        
        with col2:
            with st.popover("Fórmula"):
                st.markdown("#### Nueva columna por fórmula")
                nueva_col = st.text_input("Nombre columna")
                formula = st.text_input("Fórmula", placeholder="=[Debe] - [Haber]")
                if st.button("Aplicar fórmula"):
                    if nueva_col and formula:
                        df_temp, ok, error = FormulaEngine.aplicar_formula(edited_df.copy(), formula, nueva_col)
                        if ok:
                            edited_df = df_temp
                            st.rerun()
                        else:
                            st.error(f"Error: {error}")
        
        with col3:
            with st.popover("Estadísticas"):
                st.markdown("#### Resumen de datos")
                nums = edited_df.select_dtypes(include=['number']).columns
                if len(nums) > 0:
                    for col in nums:
                        st.markdown(f"**{col}**")
                        st.markdown(f"- Suma: ${edited_df[col].sum():,.2f}")
                        st.markdown(f"- Promedio: ${edited_df[col].mean():,.2f}")
                        st.markdown(f"- Máximo: ${edited_df[col].max():,.2f}")
                        st.markdown(f"- Mínimo: ${edited_df[col].min():,.2f}")
                        st.markdown("---")
                else:
                    st.info("No hay columnas numéricas")
        
        with col4:
            with st.popover("Reportes"):
                st.markdown("#### Generar reporte")
                if st.button("Balance General"):
                    if len(edited_df) > 0:
                        balance = generar_balance(edited_df, p['nombre'])
                        st.markdown(f"**Activos:** ${balance['activos']:,.2f}")
                        st.markdown(f"**Pasivos:** ${balance['pasivos']:,.2f}")
                        st.markdown(f"**Capital:** ${balance['capital']:,.2f}")
                        st.markdown(f"**Diferencia:** ${balance['total']:,.2f}")
                    else:
                        st.warning("Sin datos")
                
                if st.button("Estado de Resultados"):
                    if len(edited_df) > 0:
                        res = generar_resultados(edited_df)
                        st.markdown(f"**Ingresos:** ${res['ingresos']:,.2f}")
                        st.markdown(f"**Gastos:** ${res['gastos']:,.2f}")
                        st.markdown(f"**Utilidad:** ${res['utilidad']:,.2f}")
                        st.markdown(f"**Resultado:** {res['tipo']}")
                    else:
                        st.warning("Sin datos")
        
        with col5:
            if st.button("Gráfica", use_container_width=True):
                if 'Debe' in edited_df.columns and 'Haber' in edited_df.columns:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.bar(range(len(edited_df)), edited_df['Debe'].fillna(0), label='Debe', alpha=0.7)
                    ax.bar(range(len(edited_df)), edited_df['Haber'].fillna(0), label='Haber', alpha=0.7, bottom=edited_df['Debe'].fillna(0))
                    ax.set_xlabel('Registros')
                    ax.set_ylabel('Monto')
                    ax.set_title(f'{p["nombre"]} - Debe vs Haber')
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    st.pyplot(fig)
                else:
                    st.warning("Se requieren columnas Debe y Haber")
        
        # Métricas rápidas
        st.markdown("---")
        col_m1, col_m2, col_m3 = st.columns(3)
        total_debe = edited_df['Debe'].sum() if 'Debe' in edited_df.columns else 0
        total_haber = edited_df['Haber'].sum() if 'Haber' in edited_df.columns else 0
        
        with col_m1:
            st.metric("Total Debe", f"${total_debe:,.2f}")
        with col_m2:
            st.metric("Total Haber", f"${total_haber:,.2f}")
        with col_m3:
            st.metric("Diferencia", f"${total_debe - total_haber:,.2f}")
    
    else:
        st.markdown("# Contaduría")
        st.markdown("Seleccione o cree un proyecto en el menú lateral")
        st.markdown("---")
        st.markdown("### Características")
        st.markdown("- Tablas dinámicas editables")
        st.markdown("- Fórmulas personalizadas")
        st.markdown("- Reportes automáticos (Balance, Resultados)")
        st.markdown("- Gráficas comparativas")
        st.markdown("- Sincronización en la nube")
