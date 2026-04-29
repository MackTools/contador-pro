# web_app.py - Versión para Streamlit Cloud CON SECRETS

import streamlit as st
import pandas as pd
import hashlib
import pymongo  # ← Cambiamos a pymongo
from datetime import datetime

# ========== CONFIGURACIÓN ==========
st.set_page_config(page_title="Contador Pro", page_icon="📊", layout="wide")

# Obtener secrets de Streamlit Cloud
MONGO_URI = st.secrets["MONGO_URI"]
DB_NAME = st.secrets["DB_NAME"]

@st.cache_resource
def init_connection():
    """Conecta a MongoDB (con caché para no reconectar cada vez)"""
    try:
        client = pymongo.MongoClient(MONGO_URI)
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"Error de conexión a MongoDB: {e}")
        return None

# Inicializar conexión
client = init_connection()
if client:
    db = client[DB_NAME]
else:
    st.stop()

# ========== FUNCIONES DE BASE DE DATOS ==========
def get_usuarios():
    return db.usuarios

def get_proyectos():
    return db.proyectos

# ========== ESTADO DE SESIÓN ==========
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "proyecto_actual" not in st.session_state:
    st.session_state.proyecto_actual = None

# ========== INTERFAZ ==========
with st.sidebar:
    st.title("📊 Contador Pro")
    
    if not st.session_state.usuario:
        # Formulario de login
        with st.form("login_form"):
            st.subheader("🔐 Iniciar Sesión")
            email = st.text_input("Email")
            password = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Ingresar", use_container_width=True)
            
            if submitted:
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                usuario = get_usuarios().find_one({
                    "email": email,
                    "password": password_hash
                })
                if usuario:
                    usuario["_id"] = str(usuario["_id"])
                    st.session_state.usuario = usuario
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
        
        st.divider()
        
        with st.form("registro_form"):
            st.subheader("📝 Registrarse")
            reg_nombre = st.text_input("Nombre completo")
            reg_email = st.text_input("Email")
            reg_pass = st.text_input("Contraseña", type="password")
            reg_pass2 = st.text_input("Confirmar contraseña", type="password")
            submitted_reg = st.form_submit_button("Crear cuenta", use_container_width=True)
            
            if submitted_reg:
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
                        st.success("Cuenta creada! Ahora inicia sesión")
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.error("Las contraseñas no coinciden o son muy cortas")
    
    else:
        st.success(f"👋 Hola, {st.session_state.usuario['nombre']}")
        
        if st.button("🚪 Cerrar sesión", use_container_width=True):
            st.session_state.usuario = None
            st.session_state.proyecto_actual = None
            st.rerun()
        
        st.divider()
        
        st.subheader("📁 Mis Proyectos")
        proyectos = get_proyectos().find({
            "email_usuario": st.session_state.usuario["email"]
        })
        
        for proyecto in proyectos:
            if st.button(f"📄 {proyecto['nombre']}", key=proyecto['nombre'], use_container_width=True):
                proyecto["_id"] = str(proyecto["_id"])
                st.session_state.proyecto_actual = proyecto
                st.rerun()
        
        st.divider()
        
        st.subheader("➕ Nuevo Proyecto")
        nuevo_nombre = st.text_input("Nombre del proyecto")
        nuevo_tipo = st.selectbox("Tipo", ["Libro Diario", "Balanza de Comprobación", "Cuentas T"])
        
        if st.button("Crear Proyecto", use_container_width=True, type="primary"):
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
                    # Actualizar lista del usuario
                    get_usuarios().update_one(
                        {"email": st.session_state.usuario["email"]},
                        {"$push": {"proyectos": nuevo_nombre}}
                    )
                    st.success("Proyecto creado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# ========== ÁREA DE TRABAJO ==========
if st.session_state.proyecto_actual:
    proyecto = st.session_state.proyecto_actual
    
    st.title(f"📝 {proyecto['nombre']}")
    st.caption(f"Tipo: {proyecto.get('tipo', 'Libro Diario')}")
    
    # Obtener columnas
    columnas = proyecto.get("columnas", ["Fecha", "Descripción", "Debe", "Haber"])
    
    # Convertir datos a DataFrame
    datos = proyecto.get("datos", [])
    df = pd.DataFrame(datos, columns=columnas) if datos else pd.DataFrame(columns=columnas)
    
    # Editor de datos
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Debe": st.column_config.NumberColumn("Debe", format="$ %.2f"),
            "Haber": st.column_config.NumberColumn("Haber", format="$ %.2f"),
        }
    )
    
    # Botones
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Guardar", type="primary", use_container_width=True):
            try:
                get_proyectos().update_one(
                    {"_id": proyecto["_id"]},
                    {"$set": {
                        "datos": edited_df.fillna("").values.tolist(),
                        "ultima_modificacion": datetime.now()
                    }}
                )
                st.success("¡Guardado en la nube!")
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col2:
        if st.button("📥 Exportar Excel", use_container_width=True):
            edited_df.to_excel(f"{proyecto['nombre']}.xlsx", index=False)
            with open(f"{proyecto['nombre']}.xlsx", "rb") as f:
                st.download_button("📎 Descargar", f, file_name=f"{proyecto['nombre']}.xlsx")
    
    with col3:
        if st.button("🗑️ Eliminar", use_container_width=True):
            if st.checkbox("Confirmar"):
                get_proyectos().delete_one({"_id": proyecto["_id"]})
                get_usuarios().update_one(
                    {"email": st.session_state.usuario["email"]},
                    {"$pull": {"proyectos": proyecto["nombre"]}}
                )
                st.session_state.proyecto_actual = None
                st.success("Proyecto eliminado")
                st.rerun()
    
    # Totales
    st.divider()
    total_debe = edited_df["Debe"].sum() if "Debe" in edited_df.columns else 0
    total_haber = edited_df["Haber"].sum() if "Haber" in edited_df.columns else 0
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("💰 Total Debe", f"${total_debe:,.2f}")
    col_b.metric("💵 Total Haber", f"${total_haber:,.2f}")
    
    diferencia = total_debe - total_haber
    if abs(diferencia) < 0.01:
        col_c.metric("✅ Estado", "Cuadrado", delta="✓")
    else:
        col_c.metric("⚠️ Diferencia", f"${diferencia:,.2f}", delta="No cuadrado")

elif st.session_state.usuario:
    st.info("👈 Selecciona o crea un proyecto")

st.divider()
st.caption(f"📊 Contador Pro Cloud | Conectado a MongoDB")
