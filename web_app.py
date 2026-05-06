# web_app.py - Versión ACTUALIZADA con formato profesional

import streamlit as st
import pandas as pd
import hashlib
import pymongo
from datetime import datetime
import openpyxl
from io import BytesIO
import matplotlib.pyplot as plt

# ========== CONFIGURACIÓN DE PÁGINA ==========
st.set_page_config(
    page_title="Contaduría | Sistema Contable",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CSS PERSONALIZADO (MODO OSCURO) ==========
st.markdown("""
<style>
    /* Fondo oscuro global */
    .stApp {
        background-color: #0e1117;
    }
    
    /* Fondo del contenido principal */
    .main > div {
        background-color: #0e1117;
    }
    
    /* Títulos principales modo oscuro */
    .main-header {
        font-size: 24px;
        font-weight: 600;
        color: #ffffff;
        border-bottom: 2px solid #2d3748;
        padding-bottom: 10px;
        margin-bottom: 20px;
        font-family: 'Segoe UI', 'Roboto', sans-serif;
    }
    
    /* Títulos de sección modo oscuro */
    .section-header {
        font-size: 18px;
        font-weight: 500;
        color: #e2e8f0;
        margin-top: 15px;
        margin-bottom: 10px;
        padding-left: 5px;
        border-left: 3px solid #4299e1;
    }
    
    /* Tarjetas de métricas modo oscuro */
    .metric-card {
        background-color: #1a1e2e;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        border: 1px solid #2d3748;
    }
    
    .metric-label {
        font-size: 13px;
        color: #a0aec0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        font-size: 28px;
        font-weight: 600;
        color: #ffffff;
        margin-top: 5px;
    }
    
    /* Botones modo oscuro */
    .stButton button {
        background-color: #2d3748;
        color: #ffffff;
        border: 1px solid #4a5568;
        border-radius: 4px;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton button:hover {
        background-color: #4a5568;
        border-color: #718096;
    }
    
    /* Sidebar modo oscuro */
    [data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #2d3748;
    }
    
    /* Texto del sidebar */
    [data-testid="stSidebar"] .stMarkdown {
        color: #e2e8f0;
    }
    
    /* Data editor estilo tabla contable modo oscuro */
    [data-testid="stDataFrame"] {
        border: 1px solid #2d3748;
        border-radius: 6px;
        background-color: #1a1e2e;
    }
    
    /* Inputs modo oscuro */
    .stTextInput input, .stSelectbox select, .stTextArea textarea {
        background-color: #1a1e2e;
        border-color: #2d3748;
        color: #f7fafc;
    }
    
    .stTextInput input:focus, .stSelectbox select:focus {
        border-color: #4299e1;
    }
    
    /* Expandadores modo oscuro */
    .streamlit-expanderHeader {
        background-color: #1a1e2e;
        color: #e2e8f0;
    }
    
    /* Métricas modo oscuro */
    [data-testid="stMetricValue"] {
        color: #ffffff;
    }
    
    [data-testid="stMetricLabel"] {
        color: #a0aec0;
    }
    
    /* Dataframes y tablas */
    .stDataFrame {
        background-color: #1a1e2e;
    }
    
    /* Mensajes de info/warning/error */
    .stAlert {
        background-color: #2d3748;
    }
    
    /* Selectbox */
    .stSelectbox div[data-baseweb="select"] {
        background-color: #1a1e2e;
    }
    
    /* Ocultar elementos innecesarios */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Divider modo oscuro */
    hr {
        border-color: #2d3748;
    }
    
    /* Caption y textos pequeños */
    .stCaption, caption {
        color: #a0aec0;
    }
    
    /* Checkbox modo oscuro */
    .stCheckbox label span {
        color: #e2e8f0;
    }
    
    /* Tabs modo oscuro */
    .stTabs [data-baseweb="tab-list"] button {
        background-color: #0d1117;
        color: #a0aec0;
    }
    
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #1a1e2e;
        color: #ffffff;
    }
    
    /* Estilo para botones de confirmación */
    .stCheckbox label {
        color: #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

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

# ========== FUNCIONES AUXILIARES ==========
def get_usuarios():
    return db.usuarios

def get_proyectos():
    return db.proyectos

# ========== ESTADO DE SESIÓN ==========
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "proyecto_actual" not in st.session_state:
    st.session_state.proyecto_actual = None
if "fig_actual" not in st.session_state:
    st.session_state.fig_actual = None
if "confirmar_eliminar" not in st.session_state:
    st.session_state.confirmar_eliminar = False

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
            email = st.text_input("Email", key="login_email", placeholder="usuario@ejemplo.com")
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
                else:
                    st.warning("Complete todos los campos")
        
        with st.expander("Registrarse"):
            reg_nombre = st.text_input("Nombre completo", key="reg_nombre")
            reg_email = st.text_input("Email", key="reg_email")
            reg_pass = st.text_input("Contraseña", type="password", key="reg_pass")
            reg_pass2 = st.text_input("Confirmar contraseña", type="password", key="reg_pass2")
            
            if st.button("Crear cuenta", use_container_width=True):
                if reg_pass == reg_pass2 and len(reg_pass) >= 6:
                    password_hash = hashlib.sha256(reg_pass.encode()).hexdigest()
                    nuevo_usuario = {
                        "email": reg_email,
                        "password": password_hash,
                        "nombre": reg_nombre,
                        "proyectos": [],
                        "creado_en": datetime.now()
                    }
                    try:
                        get_usuarios().insert_one(nuevo_usuario)
                        st.success("Cuenta creada. Ahora inicie sesión.")
                    except:
                        st.error("El usuario ya existe")
                else:
                    st.error("Contraseña muy corta o no coinciden")
    
    else:
        st.markdown(f"""
        <div style="background-color: #1a1e2e; padding: 12px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #2d3748;">
            <p style="margin: 0; font-size: 12px; color: #94a3b8;">Usuario</p>
            <p style="margin: 5px 0 0 0; font-weight: 600; color: #ffffff;">{st.session_state.usuario['nombre']}</p>
            <p style="margin: 3px 0 0 0; font-size: 11px; color: #64748b;">{st.session_state.usuario['email']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Cerrar sesión", use_container_width=True):
            st.session_state.usuario = None
            st.session_state.proyecto_actual = None
            st.rerun()
        
        st.divider()
        
        st.markdown('<p style="font-weight: 600; margin-bottom: 10px; color: #e2e8f0;">Proyectos</p>', unsafe_allow_html=True)
        
        proyectos = list(get_proyectos().find({"email_usuario": st.session_state.usuario["email"]}))
        
        if proyectos:
            for proy in proyectos:
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(f"{proy['nombre']}", key=f"proy_{proy['nombre']}", use_container_width=True):
                        proy["_id"] = str(proy["_id"])
                        st.session_state.proyecto_actual = proy
                        st.rerun()
                with col2:
                    # Botón de eliminar con confirmación
                    if st.button("⌫", key=f"del_{proy['nombre']}"):
                        st.session_state[f"confirmar_del_{proy['nombre']}"] = True
                    
                    # Mostrar confirmación si está activada
                    if st.session_state.get(f"confirmar_del_{proy['nombre']}", False):
                        st.caption("¿Eliminar?")
                        col_confirm, col_cancel = st.columns(2)
                        with col_confirm:
                            if st.button("✓", key=f"confirm_{proy['nombre']}"):
                                get_proyectos().delete_one({"_id": proy["_id"]})
                                st.session_state[f"confirmar_del_{proy['nombre']}"] = False
                                st.rerun()
                        with col_cancel:
                            if st.button("✗", key=f"cancel_{proy['nombre']}"):
                                st.session_state[f"confirmar_del_{proy['nombre']}"] = False
                                st.rerun()
        else:
            st.caption("No hay proyectos. Cree uno nuevo.")
        
        st.divider()
        
        st.markdown('<p style="font-weight: 600; margin-bottom: 10px; color: #e2e8f0;">Nuevo proyecto</p>', unsafe_allow_html=True)
        nuevo_nombre = st.text_input("Nombre", key="nuevo_nombre", placeholder="Ej: Cliente ABC")
        nuevo_tipo = st.selectbox("Plantilla", ["Libro Diario", "Balanza de Comprobación", "Cuentas T"], key="nuevo_tipo")
        
        if st.button("Crear proyecto", use_container_width=True):
            if nuevo_nombre:
                columnas_tipo = {
                    "Libro Diario": ["Fecha", "Descripción", "Cuenta", "Debe", "Haber", "IVA %"],
                    "Balanza de Comprobación": ["Código", "Cuenta", "S. Inicial", "Cargos", "Abonos", "Saldo Final"],
                    "Cuentas T": ["Fecha", "Concepto", "Referencia", "Debe", "Haber", "Saldo"]
                }
                
                nuevo_proyecto = {
                    "nombre": nuevo_nombre,
                    "tipo": nuevo_tipo,
                    "datos": [],
                    "columnas": columnas_tipo[nuevo_tipo],
                    "email_usuario": st.session_state.usuario["email"],
                    "creado_en": datetime.now()
                }
                try:
                    get_proyectos().insert_one(nuevo_proyecto)
                    st.rerun()
                except:
                    st.error("Error al crear")

# ========== ÁREA PRINCIPAL ==========
if st.session_state.proyecto_actual:
    proyecto = st.session_state.proyecto_actual
    
    st.markdown(f'<div class="main-header">{proyecto["nombre"]} <span style="font-size: 14px; font-weight: normal; color: #94a3b8;">({proyecto.get("tipo", "Libro Diario")})</span></div>', unsafe_allow_html=True)
    
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
            "IVA %": st.column_config.NumberColumn("IVA %", format="%.2f%%"),
            "Fecha": st.column_config.Column("Fecha")
        }
    )
    
    # Botones de acción
    col_accion1, col_accion2, col_accion3, col_accion4 = st.columns([1, 1, 1, 3])
    
    with col_accion1:
        if st.button("Guardar", use_container_width=True):
            try:
                get_proyectos().update_one(
                    {"_id": proyecto["_id"]},
                    {"$set": {
                        "datos": edited_df.fillna("").values.tolist(),
                        "ultima_modificacion": datetime.now()
                    }}
                )
                st.success("Datos guardados correctamente")
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")
    
    with col_accion2:
        if st.button("Exportar Excel", use_container_width=True):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                edited_df.to_excel(writer, sheet_name=proyecto["nombre"], index=False)
            st.download_button(
                label="Descargar archivo",
                data=output.getvalue(),
                file_name=f"{proyecto['nombre']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="download_excel"
            )
    
    with col_accion3:
        if st.button("Eliminar proyecto", use_container_width=True):
            st.session_state.confirmar_eliminar = True
        
        if st.session_state.confirmar_eliminar:
            st.warning("¿Confirmar eliminación permanente?")
            col_conf, col_canc = st.columns(2)
            with col_conf:
                if st.button("Sí, eliminar", use_container_width=True):
                    get_proyectos().delete_one({"_id": proyecto["_id"]})
                    st.session_state.proyecto_actual = None
                    st.session_state.confirmar_eliminar = False
                    st.rerun()
            with col_canc:
                if st.button("Cancelar", use_container_width=True):
                    st.session_state.confirmar_eliminar = False
                    st.rerun()
    
    # Métricas
    st.divider()
    st.markdown('<div class="section-header">Resumen del período</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_debe = edited_df["Debe"].sum() if "Debe" in edited_df.columns else 0
    total_haber = edited_df["Haber"].sum() if "Haber" in edited_df.columns else 0
    diferencia = total_debe - total_haber
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Debe</div>
            <div class="metric-value">${total_debe:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Haber</div>
            <div class="metric-value">${total_haber:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        color = "#27ae60" if abs(diferencia) < 0.01 else "#e74c3c"
        estado_texto = "Balanceado" if abs(diferencia) < 0.01 else "Desbalanceado"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Estado contable</div>
            <div class="metric-value" style="color: {color};">{estado_texto}</div>
            <div style="font-size: 12px; color: #94a3b8;">Diferencia: ${diferencia:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        registros = len(edited_df)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Registros</div>
            <div class="metric-value">{registros}</div>
        </div>
        """, unsafe_allow_html=True)

    # ========== GRÁFICAS ==========
    st.markdown('<div class="section-header">Análisis gráfico</div>', unsafe_allow_html=True)

    if len(edited_df) > 0:
        if "Debe" in edited_df.columns and "Haber" in edited_df.columns:
            
            tipo_grafica = st.selectbox(
                "Tipo de gráfico",
                ["Barras - Debe vs Haber", "Líneas - Evolución", "Pastel - Distribución", "Dona - Proporciones"],
                key="tipo_grafica"
            )
            
            col_graf1, col_graf2 = st.columns([3, 1])
            
            with col_graf1:
                df_graf = edited_df.copy()
                df_graf['Registro'] = range(1, len(df_graf) + 1)
                
                if tipo_grafica == "Barras - Debe vs Haber":
                    st.bar_chart(
                        df_graf[["Debe", "Haber"]].fillna(0),
                        x_label="Registro",
                        y_label="Monto (USD)",
                        color=["#e74c3c", "#27ae60"]
                    )
                    st.caption("Comparación de débitos vs créditos por registro")
                    st.session_state.fig_actual = None
                    
                elif tipo_grafica == "Líneas - Evolución":
                    st.line_chart(
                        df_graf[["Debe", "Haber"]].fillna(0),
                        x_label="Registro",
                        y_label="Monto (USD)"
                    )
                    st.caption("Evolución de movimientos contables")
                    st.session_state.fig_actual = None
                    
                elif tipo_grafica == "Pastel - Distribución":
                    total_debe_graf = df_graf["Debe"].sum()
                    total_haber_graf = df_graf["Haber"].sum()
                    
                    fig, ax = plt.subplots(figsize=(8, 6))
                    sizes = [total_debe_graf, total_haber_graf]
                    labels = [f'Debe\n${total_debe_graf:,.2f}', f'Haber\n${total_haber_graf:,.2f}']
                    colors_graf = ['#e74c3c', '#27ae60']
                    
                    ax.pie(sizes, labels=labels, colors=colors_graf, autopct='%1.1f%%', startangle=90)
                    ax.set_title('Distribución Debe vs Haber', color='#e2e8f0')
                    ax.set_facecolor('#0e1117')
                    fig.patch.set_facecolor('#0e1117')
                    st.pyplot(fig)
                    st.session_state.fig_actual = fig
                    plt.close()
                    
                else:  # Dona
                    if "Cuenta" in df_graf.columns:
                        cuentas_agrupadas = df_graf.groupby("Cuenta")["Debe"].sum().sort_values(ascending=False).head(6)
                        
                        fig, ax = plt.subplots(figsize=(8, 6))
                        ax.pie(
                            cuentas_agrupadas.values,
                            labels=cuentas_agrupadas.index,
                            autopct='%1.1f%%',
                            startangle=90,
                            wedgeprops=dict(width=0.5)
                        )
                        ax.set_title('Top cuentas por movimiento', color='#e2e8f0')
                        ax.set_facecolor('#0e1117')
                        fig.patch.set_facecolor('#0e1117')
                        st.pyplot(fig)
                        st.session_state.fig_actual = fig
                        plt.close()
                    else:
                        st.info("Agregue una columna 'Cuenta' para ver distribución por cuentas")
                        st.session_state.fig_actual = None
            
            with col_graf2:
                st.markdown("##### Exportar gráfica")
                
                if st.button("Exportar como PNG", use_container_width=True, key="btn_export_png"):
                    if st.session_state.fig_actual is not None:
                        buf = BytesIO()
                        st.session_state.fig_actual.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                        buf.seek(0)
                        st.download_button(
                            label="Descargar PNG",
                            data=buf,
                            file_name=f"grafica_{proyecto['nombre']}.png",
                            mime="image/png",
                            use_container_width=True,
                            key="download_png"
                        )
                    else:
                        st.warning("Seleccione una gráfica de tipo Pastel o Dona")
                
                st.markdown("##### Resumen estadístico")
                if len(edited_df) > 0:
                    stats_df = pd.DataFrame({
                        "Métrica": ["Mínimo", "Máximo", "Promedio", "Suma"],
                        "Debe (USD)": [
                            f"{edited_df['Debe'].min():,.2f}",
                            f"{edited_df['Debe'].max():,.2f}",
                            f"{edited_df['Debe'].mean():,.2f}",
                            f"{edited_df['Debe'].sum():,.2f}"
                        ],
                        "Haber (USD)": [
                            f"{edited_df['Haber'].min():,.2f}",
                            f"{edited_df['Haber'].max():,.2f}",
                            f"{edited_df['Haber'].mean():,.2f}",
                            f"{edited_df['Haber'].sum():,.2f}"
                        ]
                    })
                    st.dataframe(stats_df, use_container_width=True, hide_index=True)
        else:
            st.info("Las columnas 'Debe' y 'Haber' son necesarias para generar gráficas")
    else:
        st.info("Agregue datos a la tabla para visualizar gráficas")
    
    # Estado de Resultados
    if len(edited_df) > 0 and "Descripción" in edited_df.columns:
        st.markdown('<div class="section-header">Estado de resultados</div>', unsafe_allow_html=True)
        
        ingresos = edited_df[edited_df["Descripción"].str.contains("ingreso|venta", case=False, na=False)]["Haber"].sum() if "Haber" in edited_df.columns else 0
        gastos = edited_df[edited_df["Descripción"].str.contains("gasto|costo", case=False, na=False)]["Debe"].sum() if "Debe" in edited_df.columns else 0
        
        res1, res2, res3 = st.columns(3)
        res1.metric("Ingresos", f"${ingresos:,.2f}")
        res2.metric("Gastos", f"${gastos:,.2f}")
        utilidad = ingresos - gastos
        res3.metric("Utilidad neta", f"${utilidad:,.2f}", 
                    delta="Positiva" if utilidad > 0 else "Negativa" if utilidad < 0 else None)

elif st.session_state.usuario:
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px;">
        <h2 style="color: #64748b;">Bienvenido a Contaduría</h2>
        <p style="color: #94a3b8;">Seleccione o cree un proyecto en el menú lateral</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px;">
        <h2 style="color: #64748b;">Contaduría</h2>
        <p style="color: #94a3b8;">Sistema de gestión contable profesional</p>
        <p style="color: #cbd5e1; font-size: 14px;">Inicie sesión o regístrese para continuar</p>
    </div>
    """, unsafe_allow_html=True)

# ========== FOOTER ==========
st.divider()
st.markdown('<p style="text-align: center; color: #64748b; font-size: 12px;">Contaduría · Sistema Contable Profesional</p>', unsafe_allow_html=True)
