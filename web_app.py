# web_app.py - VERSIÓN WEB COMPLETA
# Funcionalidades: Login, CRUD proyectos, editor de datos, gráficas, estadísticas,
# exportar/importar Excel, reportes, calculadora, y botón de descarga .exe

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

# ========== CONFIGURACIÓN ==========
st.set_page_config(
    page_title="Contaduría",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
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
if "registro_abierto" not in st.session_state:
    st.session_state.registro_abierto = False
if "usuarios" not in st.session_state:
    st.session_state.usuarios = {"demo@contaduria.com": {"password": "admin123", "nombre": "Usuario Demo"}}

# ========== FUNCIONES DE UTILIDAD ==========
def hash_password(password):
    """Hash simple de contraseña"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def get_exe_download_link():
    """Genera link de descarga directa del ejecutable"""
    exe_path = "dist/contaduria.exe"
    
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
    return {"exists": False, "error": "Archivo no encontrado"}

def guardar_proyecto(nombre, df):
    """Guarda un proyecto"""
    st.session_state.projects[nombre] = {
        "nombre": nombre,
        "fecha_creacion": st.session_state.projects.get(nombre, {}).get("fecha_creacion", datetime.now().strftime("%d/%m/%Y")),
        "fecha_modificacion": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "data": df.fillna("").to_dict('records'),
        "columnas": df.columns.tolist()
    }
    st.session_state.dataframes[nombre] = df

def cargar_proyecto(nombre):
    """Carga un proyecto"""
    if nombre in st.session_state.projects:
        data = st.session_state.projects[nombre]["data"]
        columnas = st.session_state.projects[nombre]["columnas"]
        df = pd.DataFrame(data, columns=columnas)
        return df
    return pd.DataFrame(columns=["Fecha", "Descripcion", "Cuenta", "Debe", "Haber"])

def eliminar_proyecto(nombre):
    """Elimina un proyecto"""
    if nombre in st.session_state.projects:
        del st.session_state.projects[nombre]
    if nombre in st.session_state.dataframes:
        del st.session_state.dataframes[nombre]

def convertir_columna_numerica(df, columna):
    """Convierte una columna a numérica de forma segura"""
    try:
        return pd.to_numeric(df[columna].astype(str).str.replace(',', '').str.replace('$', '').str.replace('%', ''), errors='coerce').fillna(0)
    except:
        return pd.Series([0] * len(df))

# ========== CSS PERSONALIZADO ==========
st.markdown("""
<style>
    /* Fondo general */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
    }
    
    /* Botón de descarga flotante */
    .download-float {
        position: fixed;
        top: 15px;
        right: 20px;
        z-index: 9999;
        background: linear-gradient(135deg, #2c7da0, #1f5e7a);
        color: white;
        padding: 10px 20px;
        border-radius: 25px;
        text-decoration: none;
        font-size: 13px;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(44, 125, 160, 0.3);
        transition: all 0.3s ease;
        display: inline-block;
    }
    .download-float:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(44, 125, 160, 0.5);
        background: linear-gradient(135deg, #3498db, #2c7da0);
    }
    
    /* Tarjetas de bienvenida */
    .welcome-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        text-align: center;
        transition: transform 0.2s;
    }
    .welcome-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    .welcome-card h3 {
        color: #2c7da0;
        margin-bottom: 10px;
    }
    .welcome-card .icon {
        font-size: 40px;
        margin-bottom: 15px;
    }
    
    /* Botones personalizados */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%);
        border-right: 1px solid #e0e0e0;
    }
    
    /* Data editor */
    [data-testid="stDataFrame"] {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Métricas */
    [data-testid="stMetric"] {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Responsive */
    @media (max-width: 768px) {
        .download-float {
            top: 10px;
            right: 10px;
            padding: 8px 15px;
            font-size: 11px;
        }
    }
</style>
""", unsafe_allow_html=True)

# ========== BOTÓN DE DESCARGA FLOTANTE ==========
exe_info = get_exe_download_link()
if exe_info["exists"]:
    st.markdown(f'''
    <a href="data:application/octet-stream;base64,{exe_info['data']}" 
       download="{exe_info['filename']}" 
       class="download-float" 
       title="Descargar versión de escritorio">
       💻 Descargar App Escritorio ({exe_info['size_mb']:.1f} MB)
    </a>
    ''', unsafe_allow_html=True)
else:
    st.markdown('''
    <div class="download-float" style="background: #95a5a6; cursor: not-allowed; box-shadow: none;">
       ⚠️ App Escritorio no disponible
    </div>
    ''', unsafe_allow_html=True)

# ========== PÁGINA DE LOGIN ==========
if not st.session_state.logged_in:
    col_center = st.columns([1, 2, 1])
    
    with col_center[1]:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Logo y título
        st.markdown("""
        <div style="text-align: center; padding: 20px;">
            <div style="font-size: 60px;">📊</div>
            <h1 style="color: #2c7da0; margin: 0;">Contaduría</h1>
            <p style="color: #666; font-size: 16px;">Sistema de gestión contable</p>
            <p style="color: #999; font-size: 12px;">Versión Web Profesional</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Tabs de login/registro
        tab1, tab2 = st.tabs(["🔐 Iniciar sesión", "📝 Registrarse"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Correo electrónico", placeholder="demo@contaduria.com", key="login_email")
                password = st.text_input("Contraseña", type="password", placeholder="••••••••", key="login_pass")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    submitted = st.form_submit_button("🔓 Ingresar", use_container_width=True)
                with col_btn2:
                    offline = st.form_submit_button("🔌 Modo offline", use_container_width=True)
                
                if submitted:
                    if email in st.session_state.usuarios:
                        if st.session_state.usuarios[email]["password"] == password:
                            st.session_state.logged_in = True
                            st.session_state.username = st.session_state.usuarios[email]["nombre"]
                            st.rerun()
                        else:
                            st.error("❌ Contraseña incorrecta")
                    else:
                        st.error("❌ Usuario no encontrado")
                
                if offline:
                    st.session_state.logged_in = True
                    st.session_state.username = "Usuario Offline"
                    st.rerun()
            
            with st.expander("📌 Credenciales de prueba"):
                st.info("""
                **Usuario:** demo@contaduria.com  
                **Contraseña:** admin123
                """)
        
        with tab2:
            with st.form("registro_form"):
                st.markdown("### Crear cuenta gratuita")
                reg_nombre = st.text_input("Nombre completo", placeholder="Juan Pérez")
                reg_email = st.text_input("Correo electrónico", placeholder="juan@ejemplo.com")
                reg_pass = st.text_input("Contraseña", type="password", placeholder="Mínimo 6 caracteres")
                reg_pass2 = st.text_input("Confirmar contraseña", type="password")
                
                if st.form_submit_button("📝 Crear cuenta", use_container_width=True):
                    if not reg_nombre or not reg_email or not reg_pass:
                        st.error("❌ Complete todos los campos")
                    elif len(reg_pass) < 6:
                        st.error("❌ La contraseña debe tener al menos 6 caracteres")
                    elif reg_pass != reg_pass2:
                        st.error("❌ Las contraseñas no coinciden")
                    elif "@" not in reg_email or "." not in reg_email:
                        st.error("❌ Correo electrónico inválido")
                    elif reg_email in st.session_state.usuarios:
                        st.error("❌ El correo ya está registrado")
                    else:
                        st.session_state.usuarios[reg_email] = {
                            "password": reg_pass,
                            "nombre": reg_nombre
                        }
                        st.success("✅ Cuenta creada exitosamente. Ahora puede iniciar sesión.")
                        st.session_state.logged_in = True
                        st.session_state.username = reg_nombre
                        st.rerun()
    
    st.stop()

# ========== APLICACIÓN PRINCIPAL ==========

# --- SIDEBAR ---
with st.sidebar:
    # Perfil de usuario
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 10px; padding: 10px; background: #f0f4f8; border-radius: 10px; margin-bottom: 15px;">
        <div style="font-size: 30px;">👤</div>
        <div>
            <strong>{st.session_state.username}</strong><br>
            <small style="color: #666;">Contador</small>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Nuevo proyecto
    with st.expander("➕ NUEVO PROYECTO", expanded=False):
        nuevo_nombre = st.text_input("Nombre", placeholder="Ej: Empresa ABC", key="new_proj_name")
        nuevo_tipo = st.selectbox("Plantilla", ["Libro Diario", "Balanza de Comprobación", "Cuentas T / Mayor"], key="new_proj_type")
        
        if st.button("✨ Crear proyecto", use_container_width=True):
            if nuevo_nombre:
                if nuevo_nombre not in st.session_state.projects:
                    if nuevo_tipo == "Libro Diario":
                        df = pd.DataFrame(columns=["Fecha", "Descripcion", "Cuenta", "Debe", "Haber"])
                    elif nuevo_tipo == "Balanza de Comprobación":
                        df = pd.DataFrame(columns=["Código", "Cuenta", "Debe", "Haber", "Saldo Deudor", "Saldo Acreedor"])
                    else:
                        df = pd.DataFrame(columns=["Fecha", "Concepto", "Referencia", "Debe", "Haber", "Saldo"])
                    
                    guardar_proyecto(nuevo_nombre, df)
                    st.session_state.current_project = nuevo_nombre
                    st.success(f"✅ Proyecto '{nuevo_nombre}' creado")
                    st.rerun()
                else:
                    st.error("❌ El proyecto ya existe")
            else:
                st.error("❌ Ingrese un nombre")
    
    # Importar Excel
    with st.expander("📥 IMPORTAR", expanded=False):
        uploaded_file = st.file_uploader("Cargar archivo Excel", type=["xlsx", "xls"])
        if uploaded_file is not None:
            try:
                df_import = pd.read_excel(uploaded_file)
                nombre_import = uploaded_file.name.replace(".xlsx", "").replace(".xls", "")
                
                if nombre_import in st.session_state.projects:
                    nombre_import = f"{nombre_import}_{datetime.now().strftime('%H%M')}"
                
                guardar_proyecto(nombre_import, df_import)
                st.session_state.current_project = nombre_import
                st.success(f"✅ Importado: {len(df_import)} filas")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    st.markdown("---")
    
    # Lista de proyectos
    st.markdown("### 📁 MIS PROYECTOS")
    
    if st.session_state.projects:
        for nombre in list(st.session_state.projects.keys()):
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    fecha = st.session_state.projects[nombre].get("fecha_creacion", "")
                    if st.button(f"📄 {nombre}", key=f"open_{nombre}", use_container_width=True,
                                help=f"Creado: {fecha}"):
                        st.session_state.current_project = nombre
                        st.rerun()
                
                with col2:
                    n_filas = len(st.session_state.projects[nombre].get("data", []))
                    st.caption(f"{n_filas} filas")
                
                with col3:
                    if st.button("🗑️", key=f"del_{nombre}", help="Eliminar proyecto"):
                        if st.session_state.current_project == nombre:
                            st.session_state.current_project = None
                        eliminar_proyecto(nombre)
                        st.rerun()
    else:
        st.info("Sin proyectos. ¡Crea uno nuevo!")
    
    st.markdown("---")
    
    # Acciones
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key not in ["usuarios"]:
                del st.session_state[key]
        st.session_state.logged_in = False
        st.rerun()

# --- ÁREA PRINCIPAL ---
if st.session_state.current_project:
    nombre_proyecto = st.session_state.current_project
    df = cargar_proyecto(nombre_proyecto)
    
    # Encabezado del proyecto
    info_proyecto = st.session_state.projects[nombre_proyecto]
    
    col_title, col_actions = st.columns([3, 1])
    with col_title:
        st.markdown(f"## 📊 {nombre_proyecto}")
        st.caption(f"📅 Creado: {info_proyecto.get('fecha_creacion', 'N/A')} | 🔄 Modificado: {info_proyecto.get('fecha_modificacion', 'N/A')} | 📋 {len(df)} registros")
    
    with col_actions:
        # Botón de exportar
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=nombre_proyecto, index=False)
        st.download_button(
            label="📥 Descargar Excel",
            data=output.getvalue(),
            file_name=f"{nombre_proyecto}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    # Editor de datos principal
    st.markdown("### 📝 Editor de datos")
    
    # Configurar columnas numéricas para mejor visualización
    column_config = {}
    for col in df.columns:
        col_lower = col.lower()
        if any(x in col_lower for x in ["debe", "haber", "saldo", "monto", "cargos", "abonos"]):
            column_config[col] = st.column_config.NumberColumn(col, format="$ %,.2f")
        elif "fecha" in col_lower:
            column_config[col] = st.column_config.DateColumn(col)
    
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        height=450,
        column_config=column_config if column_config else None,
        key=f"editor_{nombre_proyecto}"
    )
    
    # Guardar cambios automáticamente
    if not edited_df.fillna("").equals(df.fillna("")):
        guardar_proyecto(nombre_proyecto, edited_df)
    
    # --- BARRA DE HERRAMIENTAS ---
    st.markdown("---")
    st.markdown("### 🛠️ Herramientas")
    
    # Primera fila de herramientas
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("➕ Agregar fila", use_container_width=True, key="add_row"):
            nueva_fila = {col: "" for col in edited_df.columns}
            edited_df = pd.concat([edited_df, pd.DataFrame([nueva_fila])], ignore_index=True)
            guardar_proyecto(nombre_proyecto, edited_df)
            st.rerun()
    
    with col2:
        if st.button("🗑️ Eliminar última", use_container_width=True, key="del_row"):
            if len(edited_df) > 0:
                edited_df = edited_df.iloc[:-1]
                guardar_proyecto(nombre_proyecto, edited_df)
                st.rerun()
    
    with col3:
        if st.button("🧹 Limpiar todo", use_container_width=True, key="clear_all"):
            if st.warning("¿Limpiar todos los datos?"):
                if st.button("✅ Sí, limpiar"):
                    edited_df = pd.DataFrame(columns=edited_df.columns)
                    guardar_proyecto(nombre_proyecto, edited_df)
                    st.rerun()
    
    with col4:
        if st.button("➕ Agregar columna", use_container_width=True, key="add_col"):
            nueva_col = f"Columna_{len(edited_df.columns)+1}"
            edited_df[nueva_col] = ""
            guardar_proyecto(nombre_proyecto, edited_df)
            st.rerun()
    
    with col5:
        if st.button("📊 Estadísticas", use_container_width=True, key="stats_btn"):
            st.session_state.show_stats = not st.session_state.get("show_stats", False)
    
    # Segunda fila de herramientas
    col6, col7, col8, col9, col10 = st.columns(5)
    
    with col6:
        if st.button("📈 Gráfica rápida", use_container_width=True, key="quick_chart"):
            st.session_state.show_chart = not st.session_state.get("show_chart", False)
    
    with col7:
        if st.button("🧮 Calculadora", use_container_width=True, key="calc_btn"):
            st.session_state.show_calc = not st.session_state.get("show_calc", False)
    
    with col8:
        if st.button("📋 Balance", use_container_width=True, key="balance_btn"):
            st.session_state.show_balance = not st.session_state.get("show_balance", False)
    
    with col9:
        if st.button("📄 Resultados", use_container_width=True, key="results_btn"):
            st.session_state.show_results = not st.session_state.get("show_results", False)
    
    with col10:
        if st.button("💾 Guardar", use_container_width=True, key="save_btn", type="primary"):
            guardar_proyecto(nombre_proyecto, edited_df)
            st.success("✅ Proyecto guardado")
            st.rerun()
    
    # --- PANELES EXPANDIBLES ---
    
    # Estadísticas
    if st.session_state.get("show_stats", False):
        st.markdown("---")
        st.markdown("### 📊 Estadísticas de columnas numéricas")
        
        # Identificar columnas numéricas
        cols_numericas = []
        for col in edited_df.columns:
            try:
                valores = convertir_columna_numerica(edited_df, col)
                if valores.sum() != 0 or len(valores) > 0:
                    cols_numericas.append(col)
            except:
                pass
        
        if cols_numericas:
            cols_stats = st.columns(min(len(cols_numericas), 4))
            for i, col in enumerate(cols_numericas):
                with cols_stats[i % 4]:
                    valores = convertir_columna_numerica(edited_df, col)
                    st.metric(
                        label=f"📌 {col}",
                        value=f"${valores.sum():,.2f}",
                        delta=f"Prom: ${valores.mean():,.2f}"
                    )
                    st.caption(f"Máx: ${valores.max():,.2f} | Mín: ${valores.min():,.2f}")
        else:
            st.info("No se encontraron columnas numéricas para analizar")
    
    # Gráfica
    if st.session_state.get("show_chart", False):
        st.markdown("---")
        st.markdown("### 📈 Visualización de datos")
        
        # Seleccionar tipo de gráfica
        chart_type = st.selectbox("Tipo de gráfica:", ["Barras Debe vs Haber", "Línea de evolución", "Pastel"], key="chart_type")
        
        if "Debe" in edited_df.columns and "Haber" in edited_df.columns:
            fig, ax = plt.subplots(figsize=(12, 5))
            fig.patch.set_facecolor('#f5f7fa')
            ax.set_facecolor('#ffffff')
            
            debe_vals = convertir_columna_numerica(edited_df, "Debe")
            haber_vals = convertir_columna_numerica(edited_df, "Haber")
            
            if chart_type == "Barras Debe vs Haber":
                x = range(len(edited_df))
                ax.bar(x, debe_vals, label="Debe", color="#e74c3c", alpha=0.8)
                ax.bar(x, haber_vals, label="Haber", color="#27ae60", alpha=0.8, bottom=debe_vals)
                ax.set_xlabel("Registro")
                ax.set_ylabel("Monto ($)")
                ax.set_title(f"{nombre_proyecto} - Debe vs Haber")
                
            elif chart_type == "Línea de evolución":
                ax.plot(range(len(edited_df)), debe_vals, 'o-', label="Debe", color="#e74c3c", linewidth=2)
                ax.plot(range(len(edited_df)), haber_vals, 's-', label="Haber", color="#27ae60", linewidth=2)
                ax.set_xlabel("Registro")
                ax.set_ylabel("Monto ($)")
                ax.set_title(f"{nombre_proyecto} - Evolución")
                ax.grid(True, alpha=0.3)
                
            else:
                total_debe = debe_vals.sum()
                total_haber = haber_vals.sum()
                if total_debe > 0 or total_haber > 0:
                    ax.pie([total_debe, total_haber], labels=[f"Debe\n${total_debe:,.2f}", f"Haber\n${total_haber:,.2f}"],
                          colors=["#e74c3c", "#27ae60"], autopct='%1.1f%%', explode=(0.02, 0.02))
                    ax.set_title(f"{nombre_proyecto} - Distribución")
            
            ax.legend(loc='upper right')
            plt.tight_layout()
            st.pyplot(fig)
            
            # Totales
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1:
                st.metric("💰 Total Debe", f"${debe_vals.sum():,.2f}")
            with col_t2:
                st.metric("💵 Total Haber", f"${haber_vals.sum():,.2f}")
            with col_t3:
                st.metric("⚖️ Diferencia", f"${debe_vals.sum() - haber_vals.sum():,.2f}")
        else:
            st.warning("Se requieren columnas 'Debe' y 'Haber' para graficar")
    
    # Calculadora
    if st.session_state.get("show_calc", False):
        st.markdown("---")
        st.markdown("### 🧮 Calculadora de columnas")
        
        col_c1, col_c2, col_c3 = st.columns(3)
        
        with col_c1:
            col_a = st.selectbox("Columna A:", edited_df.columns.tolist(), key="calc_col_a")
        
        with col_c2:
            operacion = st.selectbox("Operación:", ["+", "-", "*", "/"], key="calc_op")
        
        with col_c3:
            col_b = st.selectbox("Columna B:", ["(Constante)"] + edited_df.columns.tolist(), key="calc_col_b")
        
        if col_b == "(Constante)":
            constante = st.number_input("Valor constante:", value=0.0, format="%.2f")
        else:
            constante = 0
        
        nombre_resultado = st.text_input("Nombre de la nueva columna:", placeholder="Resultado")
        
        if st.button("🧮 Calcular y agregar columna", use_container_width=True):
            if nombre_resultado:
                try:
                    valores_a = convertir_columna_numerica(edited_df, col_a)
                    
                    if col_b == "(Constante)":
                        if operacion == "+":
                            resultado = valores_a + constante
                        elif operacion == "-":
                            resultado = valores_a - constante
                        elif operacion == "*":
                            resultado = valores_a * constante
                        else:
                            resultado = valores_a / constante if constante != 0 else 0
                    else:
                        valores_b = convertir_columna_numerica(edited_df, col_b)
                        if operacion == "+":
                            resultado = valores_a + valores_b
                        elif operacion == "-":
                            resultado = valores_a - valores_b
                        elif operacion == "*":
                            resultado = valores_a * valores_b
                        else:
                            resultado = valores_a / valores_b.replace(0, 1)
                    
                    edited_df[nombre_resultado] = resultado
                    guardar_proyecto(nombre_proyecto, edited_df)
                    st.success(f"✅ Columna '{nombre_resultado}' creada")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.error("❌ Ingrese un nombre para la columna resultado")
    
    # Balance General
    if st.session_state.get("show_balance", False):
        st.markdown("---")
        st.markdown("### 📋 Balance General")
        
        # Clasificación automática
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
        
        st.info(f"⚖️ **Total Pasivo + Capital:** ${pasivos + capital:,.2f} | **Diferencia:** ${activos - (pasivos + capital):,.2f}")
    
    # Estado de Resultados
    if st.session_state.get("show_results", False):
        st.markdown("---")
        st.markdown("### 📄 Estado de Resultados")
        
        ingresos = gastos = 0
        
        for _, row in edited_df.iterrows():
            desc = str(row.get('Descripcion', row.get('Concepto', ''))).lower()
            try:
                debe = float(str(row.get('Debe', 0)).replace(',', '').replace('$', '')) if pd.notna(row.get('Debe')) else 0
                haber = float(str(row.get('Haber', 0)).replace(',', '').replace('$', '')) if pd.notna(row.get('Haber')) else 0
            except:
                debe = haber = 0
            
            if any(p in desc for p in ['ingreso', 'venta', 'servicio', 'honorarios', 'abono']):
                ingresos += haber
            elif any(p in desc for p in ['gasto', 'costo', 'compra', 'sueldo', 'alquiler', 'cargo']):
                gastos += debe
        
        utilidad = ingresos - gastos
        
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            st.metric("📈 Ingresos", f"${ingresos:,.2f}")
        with col_r2:
            st.metric("📉 Gastos", f"${gastos:,.2f}")
        with col_r3:
            st.metric(
                "💎 Utilidad Neta", 
                f"${abs(utilidad):,.2f}",
                delta="🟢 Ganancia" if utilidad > 0 else ("🔴 Pérdida" if utilidad < 0 else "⚪ Equilibrio")
            )
    
    # Métricas rápidas (siempre visibles)
    if "Debe" in edited_df.columns and "Haber" in edited_df.columns:
        st.markdown("---")
        st.markdown("### 📊 Resumen rápido")
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        total_debe = convertir_columna_numerica(edited_df, "Debe").sum()
        total_haber = convertir_columna_numerica(edited_df, "Haber").sum()
        
        with col_m1:
            st.metric("💰 Total Debe", f"${total_debe:,.2f}")
        with col_m2:
            st.metric("💵 Total Haber", f"${total_haber:,.2f}")
        with col_m3:
            diferencia = total_debe - total_haber
            st.metric("⚖️ Diferencia", f"${diferencia:,.2f}")
        with col_m4:
            st.metric("📋 Registros", len(edited_df))

else:
    # Pantalla de bienvenida
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <div style="font-size: 80px;">📊</div>
        <h1 style="color: #2c7da0;">Contaduría</h1>
        <p style="color: #666; font-size: 20px;">Sistema de gestión contable profesional</p>
        <p style="color: #999;">Versión Web · Ligera · Eficaz</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tarjetas de características
    col_w1, col_w2, col_w3, col_w4 = st.columns(4)
    
    with col_w1:
        st.markdown("""
        <div class="welcome-card">
            <div class="icon">📋</div>
            <h3>Editor de datos</h3>
            <p>Edita tus registros contables directamente en la tabla interactiva</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_w2:
        st.markdown("""
        <div class="welcome-card">
            <div class="icon">📊</div>
            <h3>Gráficas y reportes</h3>
            <p>Visualiza tus datos con gráficos profesionales y genera reportes</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_w3:
        st.markdown("""
        <div class="welcome-card">
            <div class="icon">🧮</div>
            <h3>Calculadora</h3>
            <p>Operaciones entre columnas con resultados automáticos</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_w4:
        st.markdown("""
        <div class="welcome-card">
            <div class="icon">💾</div>
            <h3>Guardado automático</h3>
            <p>Tus datos se guardan automáticamente en cada cambio</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Instrucciones rápidas
    st.markdown("""
    <div style="text-align: center; padding: 30px; background: white; border-radius: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
        <h3 style="color: #2c7da0;">🚀 Comienza ahora</h3>
        <p style="color: #666;">
            1️⃣ Crea un nuevo proyecto en el menú lateral<br>
            2️⃣ Agrega tus registros contables<br>
            3️⃣ Visualiza gráficas y genera reportes<br>
            4️⃣ Exporta a Excel cuando necesites
        </p>
        <p style="color: #999; font-size: 14px;">👈 Usa el menú lateral para crear o seleccionar un proyecto</p>
    </div>
    """, unsafe_allow_html=True)

# ========== PIE DE PÁGINA ==========
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #999; padding: 10px; font-size: 12px;">
    Contaduría Web v1.0 · Desarrollado con Streamlit · 
    <a href="https://github.com" style="color: #2c7da0;">GitHub</a>
</div>
""", unsafe_allow_html=True)
