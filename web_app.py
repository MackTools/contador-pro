# web_app.py - VERSIÓN DEFINITIVA CORREGIDA
# Sin errores de removeChild, diseño minimalista

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
if "login_visible" not in st.session_state:
    st.session_state.login_visible = True

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
    .stApp { background-color: #f5f5f5; }
    .main > div { background-color: #f5f5f5; }
    
    h1, h2, h3 { color: #1a1a1a; font-weight: 500; }
    h1 { font-size: 1.8rem; border-left: 3px solid #2c7da0; padding-left: 1rem; }
    h2 { font-size: 1.4rem; border-bottom: 1px solid #e0e0e0; padding-bottom: 0.5rem; }
    
    .stButton button {
        background-color: #2c7da0;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.4rem 1rem;
    }
    .stButton button:hover { background-color: #1f5e7a; }
    
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }
    
    [data-testid="stDataFrame"] {
        border: 1px solid #e0e0e0;
        border-radius: 4px;
    }
    
    .stTextInput input, .stSelectbox select {
        background-color: #ffffff;
        border: 1px solid #cccccc;
        border-radius: 4px;
    }
    
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        padding: 1rem;
    }
    
    hr { margin: 1.5rem 0; border-color: #e0e0e0; }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ========== FUNCIONES ==========
def generar_balance(df, nombre_proyecto):
    palabras_activo = ['activo', 'caja', 'banco', 'efectivo', 'inventario', 'cliente']
    palabras_pasivo = ['pasivo', 'proveedor', 'cuenta por pagar', 'acreedor', 'prestamo']
    palabras_capital = ['capital', 'patrimonio', 'aporte']
    
    activos = pasivos = capital = 0
    
    for _, row in df.iterrows():
        texto = " ".join([str(v) for v in row.values]).lower()
        
        if 'Debe' in row and 'Haber' in row:
            valor = (row.get('Debe', 0) or 0) - (row.get('Haber', 0) or 0)
        else:
            nums = df.select_dtypes(include=['number']).columns
            valor = row[nums[0]] if len(nums) > 0 else 0
        
        if any(p in texto for p in palabras_activo):
            activos += abs(valor) if valor > 0 else 0
        elif any(p in texto for p in palabras_pasivo):
            pasivos += abs(valor) if valor < 0 else max(valor, 0)
        elif any(p in texto for p in palabras_capital):
            capital += abs(valor) if valor > 0 else 0
    
    return {
        "activos": activos,
        "pasivos": pasivos,
        "capital": capital,
        "fecha": datetime.now().strftime("%d/%m/%Y")
    }

def generar_resultados(df):
    palabras_ingreso = ['ingreso', 'venta', 'servicio', 'honorarios']
    palabras_gasto = ['gasto', 'costo', 'compra', 'sueldo', 'alquiler']
    
    ingresos = gastos = 0
    
    if 'Debe' in df.columns and 'Haber' in df.columns:
        for _, row in df.iterrows():
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
        "fecha": datetime.now().strftime("%d/%m/%Y")
    }

def aplicar_formula(df, formula, nueva_col):
    try:
        formula = formula.strip()
        if formula.startswith('='):
            formula = formula[1:]
        
        def replace_col(match):
            col = match.group(1)
            return f"df['{col}']"
        
        expr = re.sub(r'\[([^\]]+)\]', replace_col, formula)
        resultado = eval(expr)
        
        if isinstance(resultado, pd.Series):
            df[nueva_col] = resultado
        else:
            df[nueva_col] = resultado
        return df, True, None
    except Exception as e:
        return df, False, str(e)

# ========== LOGIN ==========
def mostrar_login():
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
                    if client:
                        usuario = get_usuarios().find_one({"email": email, "password": password_hash})
                        if usuario:
                            st.session_state.usuario = usuario
                            st.session_state.sesion_activa = True
                            st.session_state.login_visible = False
                        else:
                            st.error("Credenciales incorrectas")
                    else:
                        # Modo offline
                        st.session_state.usuario = {"email": email, "nombre": email.split('@')[0]}
                        st.session_state.sesion_activa = True
                        st.session_state.login_visible = False
                else:
                    st.warning("Complete todos los campos")
        
        with tab2:
            nombre = st.text_input("Nombre completo", key="reg_nombre")
            email = st.text_input("Correo electrónico", key="reg_email")
            password = st.text_input("Contraseña", type="password", key="reg_pass")
            password2 = st.text_input("Confirmar contraseña", type="password", key="reg_pass2")
            
            if st.button("Crear cuenta", key="btn_registro", use_container_width=True):
                if password == password2 and len(password) >= 6 and client:
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
            st.session_state.login_visible = False

# ========== INTERFAZ PRINCIPAL ==========
if not st.session_state.sesion_activa:
    mostrar_login()
else:
    # Sidebar
    with st.sidebar:
        st.markdown(f"**{st.session_state.usuario['nombre']}**")
        st.markdown(f"<small>{st.session_state.usuario['email']}</small>", unsafe_allow_html=True)
        st.markdown("---")
        
        if st.button("Cerrar sesión", use_container_width=True):
            st.session_state.sesion_activa = False
            st.session_state.usuario = None
            st.session_state.proyecto_actual = None
        
        st.markdown("---")
        st.markdown("### Proyectos")
        
        if client and st.session_state.usuario.get('email'):
            proyectos = list(get_proyectos().find({"email_usuario": st.session_state.usuario["email"]}))
        else:
            proyectos = []
        
        for p in proyectos:
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(p['nombre'], key=f"proy_{p['_id']}", use_container_width=True):
                    st.session_state.proyecto_actual = p
            with col2:
                if st.button("x", key=f"del_{p['_id']}"):
                    if client:
                        get_proyectos().delete_one({"_id": p["_id"]})
                    st.session_state.proyecto_actual = None
        
        st.markdown("---")
        st.markdown("### Nuevo proyecto")
        nuevo_nombre = st.text_input("Nombre", key="nuevo_nombre")
        nuevo_tipo = st.selectbox("Tipo", ["Libro Diario", "Balanza", "Cuentas T"])
        
        if st.button("Crear", use_container_width=True):
            if nuevo_nombre and client:
                columnas = {
                    "Libro Diario": ["Fecha", "Descripcion", "Cuenta", "Debe", "Haber"],
                    "Balanza": ["Codigo", "Cuenta", "Saldo Inicial", "Cargos", "Abonos"],
                    "Cuentas T": ["Fecha", "Concepto", "Referencia", "Debe", "Haber"]
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
                st.session_state.proyecto_actual = nuevo
    
    # Área principal
    if st.session_state.proyecto_actual:
        p = st.session_state.proyecto_actual
        
        st.markdown(f"# {p['nombre']}")
        st.caption(p.get('tipo', 'Libro Diario'))
        st.markdown("---")
        
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
        
        # Botones de acción (sin popovers para evitar errores)
        st.markdown("---")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("Guardar", use_container_width=True):
                if client:
                    get_proyectos().update_one(
                        {"_id": p["_id"]},
                        {"$set": {"datos": edited_df.fillna("").values.tolist()}}
                    )
                    st.success("Guardado")
        
        with col2:
            with st.expander("➕ Nueva columna por fórmula"):
                nueva_col = st.text_input("Nombre columna", key="nueva_col")
                formula = st.text_input("Fórmula", placeholder="=[Debe] - [Haber]", key="formula")
                if st.button("Aplicar", key="btn_aplicar"):
                    if nueva_col and formula:
                        df_temp, ok, error = aplicar_formula(edited_df.copy(), formula, nueva_col)
                        if ok:
                            edited_df = df_temp
                            st.success(f"Columna '{nueva_col}' creada")
                        else:
                            st.error(f"Error: {error}")
        
        with col3:
            with st.expander("📊 Estadísticas"):
                nums = edited_df.select_dtypes(include=['number']).columns
                if len(nums) > 0:
                    for col in nums:
                        st.markdown(f"**{col}**")
                        st.markdown(f"- Suma: ${edited_df[col].sum():,.2f}")
                        st.markdown(f"- Promedio: ${edited_df[col].mean():,.2f}")
                        st.markdown("---")
                else:
                    st.info("No hay columnas numéricas")
        
        with col4:
            with st.expander("📄 Reportes"):
                if st.button("Balance General"):
                    if len(edited_df) > 0:
                        bal = generar_balance(edited_df, p['nombre'])
                        st.markdown(f"**Activos:** ${bal['activos']:,.2f}")
                        st.markdown(f"**Pasivos:** ${bal['pasivos']:,.2f}")
                        st.markdown(f"**Capital:** ${bal['capital']:,.2f}")
                    else:
                        st.warning("Sin datos")
                
                if st.button("Estado Resultados"):
                    if len(edited_df) > 0:
                        res = generar_resultados(edited_df)
                        st.markdown(f"**Ingresos:** ${res['ingresos']:,.2f}")
                        st.markdown(f"**Gastos:** ${res['gastos']:,.2f}")
                        st.markdown(f"**Utilidad:** ${res['utilidad']:,.2f}")
                    else:
                        st.warning("Sin datos")
        
        with col5:
            if st.button("📈 Gráfica", use_container_width=True):
                if 'Debe' in edited_df.columns and 'Haber' in edited_df.columns:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.bar(range(len(edited_df)), edited_df['Debe'].fillna(0), label='Debe', alpha=0.7, color='#2c7da0')
                    ax.bar(range(len(edited_df)), edited_df['Haber'].fillna(0), label='Haber', alpha=0.7, color='#8b6b4d', bottom=edited_df['Debe'].fillna(0))
                    ax.set_xlabel('Registros')
                    ax.set_ylabel('Monto ($)')
                    ax.set_title(f'{p["nombre"]} - Debe vs Haber')
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    st.pyplot(fig)
                else:
                    st.warning("Se requieren columnas 'Debe' y 'Haber'")
        
        # Métricas
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
