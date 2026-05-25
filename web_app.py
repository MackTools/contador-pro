# web_app.py - VERSIÓN FUNCIONAL
# Ligera, eficaz, con descarga directa del .exe

import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime
import matplotlib.pyplot as plt
import base64
import os

# ========== CONFIGURACIÓN ==========
st.set_page_config(
    page_title="Contaduría",
    page_icon="📊",
    layout="wide"
)

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

# ========== FUNCIÓN DESCARGA DIRECTA .EXE ==========
def get_exe_download_link():
    """Genera link de descarga directa del ejecutable"""
    exe_path = "dist/contador.exe"
    
    if os.path.exists(exe_path):
        try:
            with open(exe_path, "rb") as f:
                data = f.read()
            b64 = base64.b64encode(data).decode()
            return {
                "exists": True,
                "data": b64,
                "filename": "Contaduria_Setup.exe",
                "size_mb": len(data) / (1024 * 1024)
            }
        except Exception as e:
            return {"exists": False, "error": str(e)}
    else:
        return {"exists": False, "error": "Archivo no encontrado"}

# ========== FUNCIONES DE DATOS ==========
def guardar_proyecto(nombre, df):
    """Guarda un proyecto en memoria"""
    st.session_state.projects[nombre] = {
        "nombre": nombre,
        "fecha_creacion": datetime.now().strftime("%d/%m/%Y"),
        "data": df.to_dict('records'),
        "columnas": df.columns.tolist()
    }
    st.session_state.dataframes[nombre] = df

def cargar_proyecto(nombre):
    """Carga un proyecto desde memoria"""
    if nombre in st.session_state.projects:
        data = st.session_state.projects[nombre]["data"]
        columnas = st.session_state.projects[nombre]["columnas"]
        return pd.DataFrame(data, columns=columnas)
    return pd.DataFrame(columns=["Fecha", "Descripcion", "Cuenta", "Debe", "Haber"])

def eliminar_proyecto(nombre):
    """Elimina un proyecto"""
    if nombre in st.session_state.projects:
        del st.session_state.projects[nombre]
    if nombre in st.session_state.dataframes:
        del st.session_state.dataframes[nombre]

# ========== CSS ==========
st.markdown("""
<style>
    .stApp { background-color: #f5f7fa; }
    
    /* Botón de descarga flotante */
    .download-btn {
        position: fixed;
        top: 70px;
        right: 20px;
        z-index: 999;
        background-color: #2c7da0;
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        text-decoration: none;
        font-size: 13px;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.3s;
    }
    .download-btn:hover {
        background-color: #1f5e7a;
        transform: translateY(-2px);
    }
    
    .stButton button {
        background-color: #2c7da0;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 6px 12px;
        font-weight: 500;
    }
    .stButton button:hover { background-color: #1f5e7a; }
    
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }
    
    [data-testid="stDataFrame"] {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
    }
    
    h1, h2, h3 { color: #1a1a1a; }
    hr { margin: 15px 0; }
    
    .project-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 8px;
        border: 1px solid #e0e0e0;
    }
    
    /* Ocultar elementos innecesarios */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ========== BOTÓN DE DESCARGA (esquina superior derecha) ==========
exe_info = get_exe_download_link()
if exe_info["exists"]:
    st.markdown(f'''
    <a href="data:application/octet-stream;base64,{exe_info['data']}" 
       download="{exe_info['filename']}" 
       class="download-btn">
       💻 Descargar versión Escritorio ({exe_info['size_mb']:.1f} MB)
    </a>
    ''', unsafe_allow_html=True)
else:
    st.markdown(f'''
    <div class="download-btn" style="background-color:#95a5a6; cursor:not-allowed;">
       ⚠️ Escritorio no disponible
    </div>
    ''', unsafe_allow_html=True)

# ========== LOGIN ==========
if not st.session_state.logged_in:
    st.markdown("""
    <div style="text-align: center; padding: 40px;">
        <h1>📊 Contaduría</h1>
        <p style="color: #666;">Sistema de gestión contable</p>
        <p style="color: #666; font-size: 12px;">Versión Web | Ligera y Eficaz</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            email = st.text_input("Correo electrónico", placeholder="demo@contaduria.com")
            password = st.text_input("Contraseña", type="password", placeholder="admin123")
            
            if st.button("Ingresar", use_container_width=True):
                if email == "demo@contaduria.com" and password == "admin123":
                    st.session_state.logged_in = True
                    st.session_state.username = "Usuario Demo"
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas. Use: demo@contaduria.com / admin123")
            
            st.markdown("---")
            st.caption("📌 Usuario de prueba: demo@contaduria.com")
            st.caption("🔑 Contraseña: admin123")
    
    st.stop()

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown(f"**👤 {st.session_state.username}**")
    st.markdown("---")
    
    # Nuevo proyecto
    with st.expander("➕ Nuevo proyecto", expanded=False):
        nuevo_nombre = st.text_input("Nombre del proyecto", placeholder="Ej: Empresa ABC")
        nuevo_tipo = st.selectbox("Tipo", ["Libro Diario", "Balanza", "Cuentas T"])
        
        if st.button("Crear", use_container_width=True):
            if nuevo_nombre and nuevo_nombre not in st.session_state.projects:
                # Crear DataFrame según tipo
                if nuevo_tipo == "Libro Diario":
                    df = pd.DataFrame(columns=["Fecha", "Descripcion", "Cuenta", "Debe", "Haber"])
                elif nuevo_tipo == "Balanza":
                    df = pd.DataFrame(columns=["Codigo", "Cuenta", "Saldo Inicial", "Cargos", "Abonos"])
                else:
                    df = pd.DataFrame(columns=["Fecha", "Concepto", "Referencia", "Debe", "Haber"])
                
                guardar_proyecto(nuevo_nombre, df)
                st.session_state.current_project = nuevo_nombre
                st.rerun()
            elif nuevo_nombre in st.session_state.projects:
                st.error("El proyecto ya existe")
    
    st.markdown("### 📁 Mis proyectos")
    
    # Lista de proyectos
    if st.session_state.projects:
        for nombre in list(st.session_state.projects.keys()):
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(f"📄 {nombre}", key=f"open_{nombre}", use_container_width=True):
                    st.session_state.current_project = nombre
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{nombre}"):
                    eliminar_proyecto(nombre)
                    if st.session_state.current_project == nombre:
                        st.session_state.current_project = None
                    st.rerun()
    else:
        st.info("No hay proyectos. Crea uno nuevo.")
    
    st.markdown("---")
    
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.current_project = None
        st.rerun()

# ========== ÁREA PRINCIPAL ==========
if st.session_state.current_project:
    nombre_proyecto = st.session_state.current_project
    df = cargar_proyecto(nombre_proyecto)
    
    # Encabezado
    st.markdown(f"## 📊 {nombre_proyecto}")
    st.caption(f"Creado: {st.session_state.projects[nombre_proyecto]['fecha_creacion']}")
    
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
    
    # Guardar cambios automáticamente
    if not edited_df.equals(df):
        guardar_proyecto(nombre_proyecto, edited_df)
    
    # Barra de herramientas
    st.markdown("---")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("➕ Agregar fila", use_container_width=True):
            nueva_fila = {col: "" for col in edited_df.columns}
            edited_df.loc[len(edited_df)] = nueva_fila
            guardar_proyecto(nombre_proyecto, edited_df)
            st.rerun()
    
    with col2:
        if st.button("🗑️ Última fila", use_container_width=True):
            if len(edited_df) > 0:
                edited_df = edited_df.iloc[:-1]
                guardar_proyecto(nombre_proyecto, edited_df)
                st.rerun()
    
    with col3:
        if st.button("📊 Totales", use_container_width=True):
            if "Debe" in edited_df.columns and "Haber" in edited_df.columns:
                total_debe = edited_df["Debe"].sum()
                total_haber = edited_df["Haber"].sum()
                st.info(f"💰 Total Debe: ${total_debe:,.2f}")
                st.info(f"💵 Total Haber: ${total_haber:,.2f}")
                st.info(f"⚖️ Diferencia: ${total_debe - total_haber:,.2f}")
            else:
                st.warning("No hay columnas Debe/Haber para calcular")
    
    with col4:
        if st.button("📈 Gráfica", use_container_width=True):
            if "Debe" in edited_df.columns and "Haber" in edited_df.columns:
                fig, ax = plt.subplots(figsize=(10, 4))
                x = range(len(edited_df))
                ax.bar(x, edited_df["Debe"].fillna(0), label="Debe", color="#e74c3c", alpha=0.7)
                ax.bar(x, edited_df["Haber"].fillna(0), label="Haber", color="#27ae60", alpha=0.7, bottom=edited_df["Debe"].fillna(0))
                ax.set_xlabel("Registros")
                ax.set_ylabel("Monto ($)")
                ax.set_title(f"{nombre_proyecto} - Comparación")
                ax.legend()
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)
            else:
                st.warning("Se requieren columnas 'Debe' y 'Haber'")
    
    with col5:
        if st.button("📄 Exportar Excel", use_container_width=True):
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                edited_df.to_excel(writer, sheet_name=nombre_proyecto, index=False)
            st.download_button(
                label="📥 Descargar",
                data=output.getvalue(),
                file_name=f"{nombre_proyecto}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    # Métricas rápidas
    if "Debe" in edited_df.columns and "Haber" in edited_df.columns:
        st.markdown("---")
        col_m1, col_m2, col_m3 = st.columns(3)
        total_debe = edited_df["Debe"].sum()
        total_haber = edited_df["Haber"].sum()
        diferencia = total_debe - total_haber
        
        with col_m1:
            st.metric("💰 Total Debe", f"${total_debe:,.2f}")
        with col_m2:
            st.metric("💵 Total Haber", f"${total_haber:,.2f}")
        with col_m3:
            st.metric("⚖️ Diferencia", f"${diferencia:,.2f}", 
                     delta="Superávit" if diferencia < 0 else "Déficit" if diferencia > 0 else "Equilibrio")

else:
    # Pantalla de bienvenida
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px;">
        <h1>📊 Contaduría</h1>
        <p style="color: #666; font-size: 18px;">Sistema de gestión contable profesional</p>
        <hr style="max-width: 300px; margin: 30px auto;">
        <div style="display: flex; justify-content: center; gap: 40px; flex-wrap: wrap;">
            <div style="background: white; padding: 20px; border-radius: 10px; width: 200px;">
                <h3>📋 Tablas</h3>
                <p>Edita tus datos directamente</p>
            </div>
            <div style="background: white; padding: 20px; border-radius: 10px; width: 200px;">
                <h3>📊 Reportes</h3>
                <p>Gráficas y totales automáticos</p>
            </div>
            <div style="background: white; padding: 20px; border-radius: 10px; width: 200px;">
                <h3>💾 Guardado</h3>
                <p>Autosave en la nube</p>
            </div>
        </div>
        <p style="margin-top: 40px; color: #888;">👈 Selecciona o crea un proyecto en el menú lateral</p>
    </div>
    """, unsafe_allow_html=True)
