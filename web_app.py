# streamlit_app.py - VERSIÓN WEB COMPLETA Y FUNCIONAL
# Tema oscuro, sidebar siempre visible, 100% práctico

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import base64
import os
import io
from io import BytesIO

# ========== CONFIGURACIÓN OBLIGATORIA ==========
st.set_page_config(
    page_title="Contaduría Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"  # Sidebar SIEMPRE visible
)

# ========== TEMA OSCURO ==========
st.markdown("""
<style>
    /* Tema oscuro completo */
    .stApp {
        background-color: #0f1117;
    }
    
    /* Sidebar oscuro */
    [data-testid="stSidebar"] {
        background-color: #1a1d2e;
        border-right: 1px solid #2d3148;
    }
    
    [data-testid="stSidebar"] * {
        color: #e0e0e0 !important;
    }
    
    /* Sidebar SIEMPRE visible - eliminar botón de colapso */
    [data-testid="stSidebarCollapseButton"] {
        display: none;
    }
    
    /* Sidebar no colapsable */
    [data-testid="stSidebar"] {
        min-width: 280px !important;
        max-width: 280px !important;
    }
    
    /* Textos */
    h1, h2, h3, h4, h5, h6, p, label, span, div {
        color: #e0e0e0 !important;
    }
    
    /* Data editor */
    [data-testid="stDataFrame"] {
        background-color: #1a1d2e;
        border: 1px solid #2d3148;
        border-radius: 8px;
    }
    
    /* Inputs */
    .stTextInput input, .stSelectbox select, .stNumberInput input {
        background-color: #1a1d2e;
        color: #e0e0e0;
        border: 1px solid #2d3148;
        border-radius: 6px;
    }
    
    /* Botones */
    .stButton > button {
        background-color: #2563eb;
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: #1d4ed8;
        transform: translateY(-1px);
    }
    
    /* Botón primario */
    .stButton > button[kind="primary"] {
        background-color: #059669;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #047857;
    }
    
    /* Botón peligro */
    .stButton > button[kind="secondary"] {
        background-color: #dc2626;
    }
    
    /* Métricas */
    [data-testid="stMetric"] {
        background-color: #1a1d2e;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #2d3148;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #1a1d2e;
        border-radius: 6px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1a1d2e;
        border-radius: 8px;
    }
    
    /* Info, warning, error */
    .stAlert {
        background-color: #1a1d2e;
        border: 1px solid #2d3148;
    }
    
    /* Separadores */
    hr {
        border-color: #2d3148;
    }
    
    /* Ocultar elementos innecesarios */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0f1117;
    }
    ::-webkit-scrollbar-thumb {
        background: #2d3148;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ========== ESTADO DE SESIÓN ==========
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "current_project" not in st.session_state:
    st.session_state.current_project = None
if "projects" not in st.session_state:
    st.session_state.projects = {}
if "dataframes" not in st.session_state:
    st.session_state.dataframes = {}

# Datos de ejemplo para demo
if "demo_loaded" not in st.session_state:
    # Crear proyecto demo
    df_demo = pd.DataFrame({
        "Fecha": ["2024-01-15", "2024-01-20", "2024-02-01", "2024-02-15", "2024-03-01"],
        "Descripcion": ["Venta servicios", "Compra materiales", "Pago nómina", "Venta productos", "Alquiler oficina"],
        "Cuenta": ["Ingresos", "Gastos", "Gastos", "Ingresos", "Gastos"],
        "Debe": [0, 2500.00, 5000.00, 0, 1500.00],
        "Haber": [8000.00, 0, 0, 12000.00, 0]
    })
    
    st.session_state.projects["Demo Empresa"] = {
        "nombre": "Demo Empresa",
        "fecha_creacion": datetime.now().strftime("%d/%m/%Y"),
        "fecha_modificacion": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "data": df_demo.fillna("").to_dict('records'),
        "columnas": df_demo.columns.tolist()
    }
    st.session_state.dataframes["Demo Empresa"] = df_demo
    st.session_state.demo_loaded = True

# ========== FUNCIONES ==========
def guardar_proyecto(nombre, df):
    st.session_state.projects[nombre] = {
        "nombre": nombre,
        "fecha_creacion": st.session_state.projects.get(nombre, {}).get("fecha_creacion", datetime.now().strftime("%d/%m/%Y")),
        "fecha_modificacion": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "data": df.fillna("").to_dict('records'),
        "columnas": df.columns.tolist()
    }
    st.session_state.dataframes[nombre] = df

def cargar_proyecto(nombre):
    if nombre in st.session_state.projects:
        data = st.session_state.projects[nombre]["data"]
        columnas = st.session_state.projects[nombre]["columnas"]
        return pd.DataFrame(data, columns=columnas)
    return pd.DataFrame(columns=["Fecha", "Descripcion", "Cuenta", "Debe", "Haber"])

def eliminar_proyecto(nombre):
    if nombre in st.session_state.projects:
        del st.session_state.projects[nombre]
    if nombre in st.session_state.dataframes:
        del st.session_state.dataframes[nombre]

def convertir_numerico(df, columna):
    try:
        return pd.to_numeric(df[columna].astype(str).str.replace(',', '').str.replace('$', '').str.replace('%', ''), errors='coerce').fillna(0)
    except:
        return pd.Series([0] * len(df))

def get_exe_download_link():
    exe_path = "dist/contaduria.exe"
    if os.path.exists(exe_path):
        try:
            with open(exe_path, "rb") as f:
                data = f.read()
            b64 = base64.b64encode(data).decode()
            return {"exists": True, "data": b64, "filename": "Contaduria.exe", "size_mb": len(data) / (1024 * 1024)}
        except:
            pass
    return {"exists": False}

# ========== LOGIN ==========
if not st.session_state.logged_in:
    col_center = st.columns([1, 2, 1])
    
    with col_center[1]:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style="text-align: center; padding: 20px;">
            <h1 style="color: #60a5fa; margin: 0;">📊 Contaduría Pro</h1>
            <p style="color: #94a3b8;">Sistema de gestión contable</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Iniciar sesión", "Registrarse"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Correo electrónico", placeholder="demo@contaduria.com")
                password = st.text_input("Contraseña", type="password", placeholder="admin123")
                
                col1, col2 = st.columns(2)
                with col1:
                    login_btn = st.form_submit_button("Ingresar", use_container_width=True)
                with col2:
                    offline_btn = st.form_submit_button("Modo offline", use_container_width=True)
                
                if login_btn:
                    if email == "demo@contaduria.com" and password == "admin123":
                        st.session_state.logged_in = True
                        st.session_state.username = "Usuario Demo"
                        st.session_state.current_project = "Demo Empresa"
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas")
                
                if offline_btn:
                    st.session_state.logged_in = True
                    st.session_state.username = "Usuario Offline"
                    st.rerun()
            
            st.caption("Usuario: demo@contaduria.com | Contraseña: admin123")
        
        with tab2:
            with st.form("registro_form"):
                st.subheader("Crear cuenta")
                reg_nombre = st.text_input("Nombre completo")
                reg_email = st.text_input("Correo electrónico")
                reg_pass = st.text_input("Contraseña", type="password")
                reg_pass2 = st.text_input("Confirmar contraseña", type="password")
                
                if st.form_submit_button("Crear cuenta", use_container_width=True):
                    if not reg_nombre or not reg_email or not reg_pass:
                        st.error("Complete todos los campos")
                    elif len(reg_pass) < 6:
                        st.error("Contraseña: mínimo 6 caracteres")
                    elif reg_pass != reg_pass2:
                        st.error("Las contraseñas no coinciden")
                    elif "@" not in reg_email:
                        st.error("Correo inválido")
                    else:
                        st.session_state.logged_in = True
                        st.session_state.username = reg_nombre
                        st.success("Cuenta creada")
                        st.rerun()
    
    st.stop()

# ========== SIDEBAR SIEMPRE VISIBLE ==========
with st.sidebar:
    st.markdown(f"## 👤 {st.session_state.username}")
    st.markdown("---")
    
    # NUEVO PROYECTO
    with st.expander("➕ NUEVO PROYECTO", expanded=False):
        nombre_nuevo = st.text_input("Nombre del proyecto", key="new_name")
        tipo_nuevo = st.selectbox("Plantilla", ["Libro Diario", "Balanza de Comprobación", "Cuentas T"], key="new_type")
        
        if st.button("Crear proyecto", use_container_width=True):
            if nombre_nuevo and nombre_nuevo not in st.session_state.projects:
                if tipo_nuevo == "Libro Diario":
                    df = pd.DataFrame(columns=["Fecha", "Descripcion", "Cuenta", "Debe", "Haber"])
                elif tipo_nuevo == "Balanza de Comprobación":
                    df = pd.DataFrame(columns=["Código", "Cuenta", "Debe", "Haber", "Saldo Deudor", "Saldo Acreedor"])
                else:
                    df = pd.DataFrame(columns=["Fecha", "Concepto", "Referencia", "Debe", "Haber", "Saldo"])
                
                guardar_proyecto(nombre_nuevo, df)
                st.session_state.current_project = nombre_nuevo
                st.success(f"Proyecto '{nombre_nuevo}' creado")
                st.rerun()
            elif nombre_nuevo in st.session_state.projects:
                st.error("Ya existe")
            else:
                st.error("Ingrese un nombre")
    
    # IMPORTAR EXCEL
    with st.expander("📥 IMPORTAR EXCEL", expanded=False):
        archivo = st.file_uploader("Cargar archivo", type=["xlsx", "xls"], key="import_file")
        if archivo:
            try:
                df_import = pd.read_excel(archivo)
                nombre_import = archivo.name.replace(".xlsx", "").replace(".xls", "")
                if nombre_import in st.session_state.projects:
                    nombre_import = f"{nombre_import}_{datetime.now().strftime('%H%M')}"
                guardar_proyecto(nombre_import, df_import)
                st.session_state.current_project = nombre_import
                st.success(f"Importado: {len(df_import)} filas")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.markdown("---")
    
    # LISTA DE PROYECTOS
    st.markdown("### 📁 Mis proyectos")
    
    if st.session_state.projects:
        for nombre in list(st.session_state.projects.keys()):
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(f"📄 {nombre}", key=f"proj_{nombre}", use_container_width=True,
                           help=f"Creado: {st.session_state.projects[nombre].get('fecha_creacion', '')}"):
                    st.session_state.current_project = nombre
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{nombre}", help="Eliminar"):
                    if st.session_state.current_project == nombre:
                        st.session_state.current_project = None
                    eliminar_proyecto(nombre)
                    st.rerun()
    else:
        st.info("Sin proyectos")
    
    st.markdown("---")
    
    # BOTÓN DE DESCARGA .EXE
    exe_info = get_exe_download_link()
    if exe_info["exists"]:
        st.download_button(
            label="💻 Descargar App Escritorio",
            data=base64.b64decode(exe_info["data"]),
            file_name=exe_info["filename"],
            mime="application/octet-stream",
            use_container_width=True
        )
    
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ========== ÁREA PRINCIPAL ==========
if st.session_state.current_project:
    nombre = st.session_state.current_project
    df = cargar_proyecto(nombre)
    info = st.session_state.projects[nombre]
    
    # Encabezado
    st.markdown(f"## 📊 {nombre}")
    st.caption(f"Creado: {info.get('fecha_creacion', 'N/A')} | Modificado: {info.get('fecha_modificacion', 'N/A')} | Registros: {len(df)}")
    
    # Editor de datos
    st.markdown("### Editor de datos")
    
    column_config = {}
    for col in df.columns:
        col_lower = col.lower()
        if any(x in col_lower for x in ["debe", "haber", "saldo", "monto", "cargos", "abonos"]):
            column_config[col] = st.column_config.NumberColumn(col, format="$ %,.2f")
        elif "fecha" in col_lower:
            column_config[col] = st.column_config.TextColumn(col)
    
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        height=400,
        column_config=column_config if column_config else None,
        key=f"editor_{nombre}"
    )
    
    # Guardar cambios
    if not edited_df.fillna("").equals(df.fillna("")):
        guardar_proyecto(nombre, edited_df)
    
    # Barra de herramientas
    st.markdown("---")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        if st.button("➕ Fila", use_container_width=True):
            nueva_fila = {col: "" for col in edited_df.columns}
            edited_df = pd.concat([edited_df, pd.DataFrame([nueva_fila])], ignore_index=True)
            guardar_proyecto(nombre, edited_df)
            st.rerun()
    
    with col2:
        if st.button("🗑️ Última", use_container_width=True):
            if len(edited_df) > 0:
                edited_df = edited_df.iloc[:-1]
                guardar_proyecto(nombre, edited_df)
                st.rerun()
    
    with col3:
        if st.button("➕ Columna", use_container_width=True):
            nueva_col = f"Columna_{len(edited_df.columns)+1}"
            edited_df[nueva_col] = ""
            guardar_proyecto(nombre, edited_df)
            st.rerun()
    
    with col4:
        if st.button("📊 Totales", use_container_width=True):
            st.session_state.show_totals = not st.session_state.get("show_totals", False)
    
    with col5:
        if st.button("📈 Gráfica", use_container_width=True):
            st.session_state.show_chart = not st.session_state.get("show_chart", False)
    
    with col6:
        # Exportar Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            edited_df.to_excel(writer, sheet_name=nombre, index=False)
        st.download_button(
            label="📥 Excel",
            data=output.getvalue(),
            file_name=f"{nombre}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    # Panel de totales
    if st.session_state.get("show_totals", False):
        st.markdown("---")
        st.markdown("### 📊 Totales")
        
        cols_numericas = []
        for col in edited_df.columns:
            try:
                vals = convertir_numerico(edited_df, col)
                if vals.sum() != 0:
                    cols_numericas.append((col, vals))
            except:
                pass
        
        if cols_numericas:
            columnas_totales = st.columns(min(len(cols_numericas), 4))
            for i, (col, vals) in enumerate(cols_numericas):
                with columnas_totales[i % 4]:
                    st.metric(f"💰 {col}", f"${vals.sum():,.2f}")
                    st.caption(f"Prom: ${vals.mean():,.2f} | Máx: ${vals.max():,.2f}")
        else:
            st.info("No hay columnas numéricas")
    
    # Panel de gráfica
    if st.session_state.get("show_chart", False):
        st.markdown("---")
        st.markdown("### 📈 Gráfica Debe vs Haber")
        
        if "Debe" in edited_df.columns and "Haber" in edited_df.columns:
            fig, ax = plt.subplots(figsize=(10, 4))
            fig.patch.set_facecolor('#0f1117')
            ax.set_facecolor('#1a1d2e')
            ax.tick_params(colors='white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.title.set_color('white')
            ax.spines['bottom'].set_color('#2d3148')
            ax.spines['top'].set_color('#2d3148')
            ax.spines['left'].set_color('#2d3148')
            ax.spines['right'].set_color('#2d3148')
            
            debe_vals = convertir_numerico(edited_df, "Debe")
            haber_vals = convertir_numerico(edited_df, "Haber")
            
            x = range(len(edited_df))
            ax.bar(x, debe_vals, label="Debe", color="#ef4444", alpha=0.8)
            ax.bar(x, haber_vals, label="Haber", color="#22c55e", alpha=0.8, bottom=debe_vals)
            ax.set_xlabel("Registro")
            ax.set_ylabel("Monto ($)")
            ax.set_title(f"{nombre} - Debe vs Haber")
            ax.legend(facecolor='#1a1d2e', edgecolor='#2d3148', labelcolor='white')
            ax.grid(True, alpha=0.2, color='#2d3148')
            
            plt.tight_layout()
            st.pyplot(fig)
            
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("💰 Total Debe", f"${debe_vals.sum():,.2f}")
            with col_m2:
                st.metric("💵 Total Haber", f"${haber_vals.sum():,.2f}")
            with col_m3:
                st.metric("⚖️ Diferencia", f"${debe_vals.sum() - haber_vals.sum():,.2f}")
        else:
            st.warning("Se requieren columnas 'Debe' y 'Haber'")
    
    # Balance General
    st.markdown("---")
    st.markdown("### 📋 Balance General")
    
    if st.button("Generar Balance", use_container_width=True):
        activos = pasivos = capital = 0
        
        for _, row in edited_df.iterrows():
            texto = " ".join([str(v).lower() for v in row.values])
            try:
                debe = float(str(row.get('Debe', 0)).replace(',', '').replace('$', '')) if pd.notna(row.get('Debe')) else 0
                haber = float(str(row.get('Haber', 0)).replace(',', '').replace('$', '')) if pd.notna(row.get('Haber')) else 0
                valor = debe - haber
            except:
                valor = 0
            
            if any(p in texto for p in ['activo', 'caja', 'banco', 'efectivo', 'inventario', 'cliente', 'deudor']):
                activos += abs(valor) if valor > 0 else 0
            elif any(p in texto for p in ['pasivo', 'proveedor', 'deuda', 'prestamo', 'acreedor']):
                pasivos += abs(valor) if valor < 0 else max(valor, 0)
            elif any(p in texto for p in ['capital', 'patrimonio', 'aporte']):
                capital += abs(valor) if valor > 0 else 0
        
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            st.metric("💰 Activos", f"${activos:,.2f}")
        with col_b2:
            st.metric("💳 Pasivos", f"${pasivos:,.2f}")
        with col_b3:
            st.metric("🏦 Capital", f"${capital:,.2f}")
        
        st.info(f"⚖️ Pasivo + Capital: ${pasivos + capital:,.2f} | Diferencia: ${activos - (pasivos + capital):,.2f}")
    
    # Estado de Resultados
    st.markdown("### 📄 Estado de Resultados")
    
    if st.button("Generar Resultados", use_container_width=True):
        ingresos = gastos = 0
        
        for _, row in edited_df.iterrows():
            desc = str(row.get('Descripcion', row.get('Concepto', ''))).lower()
            try:
                debe = float(str(row.get('Debe', 0)).replace(',', '').replace('$', '')) if pd.notna(row.get('Debe')) else 0
                haber = float(str(row.get('Haber', 0)).replace(',', '').replace('$', '')) if pd.notna(row.get('Haber')) else 0
            except:
                debe = haber = 0
            
            if any(p in desc for p in ['ingreso', 'venta', 'servicio', 'honorarios']):
                ingresos += haber
            elif any(p in desc for p in ['gasto', 'costo', 'compra', 'sueldo', 'alquiler']):
                gastos += debe
        
        utilidad = ingresos - gastos
        resultado = "🟢 Ganancia" if utilidad > 0 else ("🔴 Pérdida" if utilidad < 0 else "⚪ Equilibrio")
        
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            st.metric("📈 Ingresos", f"${ingresos:,.2f}")
        with col_r2:
            st.metric("📉 Gastos", f"${gastos:,.2f}")
        with col_r3:
            st.metric("💎 Utilidad Neta", f"${abs(utilidad):,.2f}", delta=resultado)

else:
    # Pantalla de bienvenida
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; padding: 40px;">
        <h1 style="color: #60a5fa;">📊 Contaduría Pro</h1>
        <p style="color: #94a3b8; font-size: 18px;">Sistema de gestión contable profesional</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background: #1a1d2e; padding: 20px; border-radius: 10px; border: 1px solid #2d3148; text-align: center;">
            <h3>📋 Editor</h3>
            <p style="color: #94a3b8;">Edita datos directamente en la tabla</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: #1a1d2e; padding: 20px; border-radius: 10px; border: 1px solid #2d3148; text-align: center;">
            <h3>📊 Reportes</h3>
            <p style="color: #94a3b8;">Gráficas y balances automáticos</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: #1a1d2e; padding: 20px; border-radius: 10px; border: 1px solid #2d3148; text-align: center;">
            <h3>💾 Guardado</h3>
            <p style="color: #94a3b8;">Autosave en cada cambio</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("👈 Selecciona o crea un proyecto en el menú lateral")

# Pie de página
st.markdown("---")
st.caption("Contaduría Pro v2.0 | Streamlit Cloud")
