# web_app.py - Versión con diseño profesional tipo escritorio contable

import streamlit as st
import pandas as pd
import hashlib
import pymongo
from datetime import datetime
import openpyxl
from io import BytesIO

# ========== CONFIGURACIÓN DE PÁGINA ==========
st.set_page_config(
    page_title="Contaduría | Sistema Contable",
    page_icon="❤️❤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CSS PERSONALIZADO (ESTILO CONTABLE) ==========
st.markdown("""
<style>
    /* Estilo general - fondo gris muy claro tipo papel */
    .stApp {
        background-color: #f5f7fa;
    }
    
    /* Títulos principales */
    .main-header {
        font-size: 24px;
        font-weight: 600;
        color: #1e3a5f;
        border-bottom: 2px solid #cbd5e1;
        padding-bottom: 10px;
        margin-bottom: 20px;
        font-family: 'Segoe UI', 'Roboto', sans-serif;
    }
    
    /* Títulos de sección */
    .section-header {
        font-size: 18px;
        font-weight: 500;
        color: #2c3e50;
        margin-top: 15px;
        margin-bottom: 10px;
        padding-left: 5px;
        border-left: 3px solid #1e3a5f;
    }
    
    /* Tarjetas de métricas */
    .metric-card {
        background-color: white;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
    }
    
    .metric-label {
        font-size: 13px;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        font-size: 28px;
        font-weight: 600;
        color: #1e3a5f;
        margin-top: 5px;
    }
    
    /* Botones más sobrios */
    .stButton button {
        background-color: #1e3a5f;
        color: white;
        border: none;
        border-radius: 4px;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton button:hover {
        background-color: #2c5282;
        border: none;
    }
    
    /* Sidebar más limpio */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Data editor estilo tabla contable */
    [data-testid="stDataFrame"] {
        border: 1px solid #e2e8f0;
        border-radius: 6px;
    }
    
    /* Ocultar elementos innecesarios */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Inputs más compactos */
    .stTextInput input, .stSelectbox select {
        border-radius: 4px;
        border: 1px solid #cbd5e1;
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

# ========== SIDEBAR - MENÚ LATERAL ==========
with st.sidebar:
    # Logo / Título
    st.markdown("""
    <div style="text-align: center; padding: 20px 0 10px 0;">
        <span style="font-size: 28px;">😎</span>
        <h2 style="color: #1e3a5f; margin: 0;">Contaduría</h2>
        <p style="color: #64748b; font-size: 12px;">Sistema Contable</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    if not st.session_state.usuario:
        # ===== LOGIN =====
        with st.expander("🔐 Iniciar Sesión", expanded=True):
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
        
        # ===== REGISTRO =====
        with st.expander("📝 Registrarse"):
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
        # ===== USUARIO LOGUEADO =====
        st.markdown(f"""
        <div style="background-color: #e8f0fe; padding: 10px; border-radius: 8px; margin-bottom: 15px;">
            <p style="margin: 0; font-size: 13px; color: #1e3a5f;">👤 Usuario</p>
            <p style="margin: 0; font-weight: 600;">{st.session_state.usuario['nombre']}</p>
            <p style="margin: 0; font-size: 11px; color: #64748b;">{st.session_state.usuario['email']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(" Cerrar sesión", use_container_width=True):
            st.session_state.usuario = None
            st.session_state.proyecto_actual = None
            st.rerun()
        
        st.divider()
        
        # ===== LISTA DE PROYECTOS =====
        st.markdown('<p style="font-weight: 600; margin-bottom: 10px;">📁 Proyectos</p>', unsafe_allow_html=True)
        
        proyectos = list(get_proyectos().find({"email_usuario": st.session_state.usuario["email"]}))
        
        if proyectos:
            for proy in proyectos:
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(f"📄 {proy['nombre']}", key=f"proy_{proy['nombre']}", use_container_width=True):
                        proy["_id"] = str(proy["_id"])
                        st.session_state.proyecto_actual = proy
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_{proy['nombre']}"):
                        get_proyectos().delete_one({"_id": proy["_id"]})
                        st.rerun()
        else:
            st.caption("No hay proyectos. Cree uno nuevo.")
        
        st.divider()
        
        # ===== NUEVO PROYECTO =====
        st.markdown('<p style="font-weight: 600; margin-bottom: 10px;">➕ Nuevo proyecto</p>', unsafe_allow_html=True)
        nuevo_nombre = st.text_input("Nombre", key="nuevo_nombre", placeholder="Ej: Cliente ABC")
        nuevo_tipo = st.selectbox("Plantilla", ["Libro Diario", "Balanza de Comprobación", "Cuentas T"], key="nuevo_tipo")
        
        if st.button("Crear proyecto", use_container_width=True, type="primary"):
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
    
    # Encabezado del proyecto
    st.markdown(f'<div class="main-header">{proyecto["nombre"]} <span style="font-size: 14px; font-weight: normal;">({proyecto.get("tipo", "Libro Diario")})</span></div>', unsafe_allow_html=True)
    
    columnas = proyecto.get("columnas", ["Fecha", "Descripción", "Debe", "Haber"])
    datos = proyecto.get("datos", [])
    df = pd.DataFrame(datos, columns=columnas) if datos else pd.DataFrame(columns=columnas)
    
    # Editor de tabla
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        height=400,
        column_config={
            "Debe": st.column_config.NumberColumn("Debe", format="$ %.2f"),
            "Haber": st.column_config.NumberColumn("Haber", format="$ %.2f"),
            "IVA %": st.column_config.NumberColumn("IVA %", format="%.2f%%"),
            "Fecha": st.column_config.TextColumn("Fecha", placeholder="DD/MM/AAAA")
        }
    )
    
    # Botones de acción
    col_accion1, col_accion2, col_accion3, col_accion4 = st.columns([1, 1, 1, 3])
    
    with col_accion1:
        if st.button("💾 Guardar", use_container_width=True):
            try:
                get_proyectos().update_one(
                    {"_id": proyecto["_id"]},
                    {"$set": {
                        "datos": edited_df.fillna("").values.tolist(),
                        "ultima_modificacion": datetime.now()
                    }}
                )
                st.success("Guardado")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col_accion2:
        if st.button("📎 Exportar Excel", use_container_width=True):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                edited_df.to_excel(writer, sheet_name=proyecto["nombre"], index=False)
            st.download_button(
                label="Descargar",
                data=output.getvalue(),
                file_name=f"{proyecto['nombre']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    with col_accion3:
        if st.button("🗑️ Eliminar", use_container_width=True):
            if st.checkbox("Confirmar eliminación"):
                get_proyectos().delete_one({"_id": proyecto["_id"]})
                st.session_state.proyecto_actual = None
                st.rerun()
    
    # Métricas
    st.divider()
    st.markdown('<div class="section-header">Resumen</div>', unsafe_allow_html=True)
    
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
        simbolo = "✓" if abs(diferencia) < 0.01 else "⚠️"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Estado</div>
            <div class="metric-value" style="color: {color};">{simbolo} {diferencia:,.2f}</div>
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

    # web_app.py - Agregar DESPUÉS de las métricas y ANTES del Estado de Resultados

# ========== GRÁFICAS ==========
    st.markdown('<div class="section-header">📈 Análisis Gráfico</div>', unsafe_allow_html=True)

    # Verificar si hay datos para graficar
    if len(edited_df) > 0:
        # Preparar datos para gráficas
        if "Debe" in edited_df.columns and "Haber" in edited_df.columns:
            
            # Selector de tipo de gráfica
            tipo_grafica = st.selectbox(
                "Tipo de gráfico",
                ["Barras - Debe vs Haber", "Líneas - Evolución", "Pastel - Distribución", "Dona - Proporciones"],
                key="tipo_grafica"
            )
            
            col_graf1, col_graf2 = st.columns([3, 1])
            
            with col_graf1:
                # Crear DataFrame para gráficas
                df_graf = edited_df.copy()
                
                # Agregar índice para evolución
                df_graf['Registro'] = range(1, len(df_graf) + 1)
                
                if tipo_grafica == "Barras - Debe vs Haber":
                    # Gráfico de barras comparativo
                    st.bar_chart(
                        df_graf[["Debe", "Haber"]].fillna(0),
                        x_label="Registro",
                        y_label="Monto ($)",
                        color=["#e74c3c", "#27ae60"]
                    )
                    st.caption("Comparación de Débitos vs Créditos por registro")
                    
                elif tipo_grafica == "Líneas - Evolución":
                    # Gráfico de líneas
                    st.line_chart(
                        df_graf[["Debe", "Haber"]].fillna(0),
                        x_label="Registro",
                        y_label="Monto ($)"
                    )
                    st.caption("Evolución de movimientos contables")
                    
                elif tipo_grafica == "Pastel - Distribución":
                    # Distribución con matplotlib
                    import matplotlib.pyplot as plt
                    
                    total_debe_graf = df_graf["Debe"].sum()
                    total_haber_graf = df_graf["Haber"].sum()
                    
                    fig, ax = plt.subplots(figsize=(8, 6))
                    sizes = [total_debe_graf, total_haber_graf]
                    labels = [f'Debe\n${total_debe_graf:,.2f}', f'Haber\n${total_haber_graf:,.2f}']
                    colors_graf = ['#e74c3c', '#27ae60']
                    
                    ax.pie(sizes, labels=labels, colors=colors_graf, autopct='%1.1f%%', startangle=90)
                    ax.set_title('Distribución Debe vs Haber')
                    st.pyplot(fig)
                    plt.close()
                    
                else:  # Dona
                    import matplotlib.pyplot as plt
                    
                    # Clasificar cuentas si existe columna Cuenta
                    if "Cuenta" in df_graf.columns:
                        cuentas_agrupadas = df_graf.groupby("Cuenta")["Debe"].sum().sort_values(ascending=False).head(6)
                        
                        fig, ax = plt.subplots(figsize=(8, 6))
                        wedges, texts, autotexts = ax.pie(
                            cuentas_agrupadas.values,
                            labels=cuentas_agrupadas.index,
                            autopct='%1.1f%%',
                            startangle=90,
                            wedgeprops=dict(width=0.5)
                        )
                        ax.set_title('Top cuentas por movimiento (Dona)')
                        st.pyplot(fig)
                        plt.close()
                    else:
                        st.info("Agregue una columna 'Cuenta' para ver distribución por cuentas")
            
            with col_graf2:
                # Botones de exportación de gráficas
                st.markdown("##### 📥 Exportar gráfica")
                
                if st.button("📸 Exportar como PNG", use_container_width=True, key="btn_export_png"):
                    # Capturar la gráfica actual
                    fig = plt.gcf()
                    if fig:
                        buf = BytesIO()
                        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                        buf.seek(0)
                        st.download_button(
                            label="⬇️ Descargar PNG",
                            data=buf,
                            file_name=f"grafica_{proyecto['nombre']}.png",
                            mime="image/png",
                            use_container_width=True
                        )
                
                # Resumen estadístico
                st.markdown("##### 😎 Resumen")
                stats_df = pd.DataFrame({
                    "Métrica": ["Mínimo", "Máximo", "Promedio", "Suma"],
                    "Debe": [
                        f"${edited_df['Debe'].min():,.2f}" if len(edited_df) > 0 else "$0",
                        f"${edited_df['Debe'].max():,.2f}" if len(edited_df) > 0 else "$0",
                        f"${edited_df['Debe'].mean():,.2f}" if len(edited_df) > 0 else "$0",
                        f"${edited_df['Debe'].sum():,.2f}" if len(edited_df) > 0 else "$0"
                    ],
                    "Haber": [
                        f"${edited_df['Haber'].min():,.2f}" if len(edited_df) > 0 else "$0",
                        f"${edited_df['Haber'].max():,.2f}" if len(edited_df) > 0 else "$0",
                        f"${edited_df['Haber'].mean():,.2f}" if len(edited_df) > 0 else "$0",
                        f"${edited_df['Haber'].sum():,.2f}" if len(edited_df) > 0 else "$0"
                    ]
                })
                st.dataframe(stats_df, use_container_width=True, hide_index=True)
    else:
        st.info("Agregue datos a la tabla para visualizar gráficas")
    
    # Estado de Resultados (si hay datos)
    if len(edited_df) > 0 and "Descripción" in edited_df.columns:
        st.markdown('<div class="section-header">Estado de Resultados</div>', unsafe_allow_html=True)
        
        ingresos = edited_df[edited_df["Descripción"].str.contains("ingreso|venta", case=False, na=False)]["Haber"].sum() if "Haber" in edited_df.columns else 0
        gastos = edited_df[edited_df["Descripción"].str.contains("gasto|costo", case=False, na=False)]["Debe"].sum() if "Debe" in edited_df.columns else 0
        
        res1, res2, res3 = st.columns(3)
        res1.metric("Ingresos", f"${ingresos:,.2f}")
        res2.metric("Gastos", f"${gastos:,.2f}")
        utilidad = ingresos - gastos
        res3.metric("Utilidad Neta", f"${utilidad:,.2f}", 
                    delta="Ganancia" if utilidad > 0 else "Pérdida" if utilidad < 0 else None)

    elif st.session_state.usuario:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px;">
            <span style="font-size: 48px;">📊</span>
            <h2 style="color: #64748b;">Bienvenido a Contaduría</h2>
            <p style="color: #94a3b8;">Seleccione o cree un proyecto en el menú lateral</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px;">
            <span style="font-size: 48px;">📊</span>
            <h2 style="color: #64748b;">Contaduría</h2>
            <p style="color: #94a3b8;">Sistema de gestión contable</p>
            <p style="color: #cbd5e1; font-size: 14px;">Inicie sesión o regístrese para continuar</p>
        </div>
        """, unsafe_allow_html=True)

# ========== FOOTER ==========
st.divider()
st.markdown('<p style="text-align: center; color: #94a3b8; font-size: 12px;">Contaduría · Sistema Contable Profesional</p>', unsafe_allow_html=True)
