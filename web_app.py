# web_app.py - Versión web completa

import streamlit as st
import pandas as pd
import hashlib
import requests
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Contador Pro Cloud", page_icon="📊", layout="wide")

# Configuración de MongoDB Data API
MONGODB_APP_ID = "data-xxxxx"  # Tu App ID
MONGODB_API_KEY = "tu-api-key"  # Tu API Key
MONGODB_URL = f"https://data.mongodb-api.com/app/{MONGODB_APP_ID}/endpoint/data/v1"

def mongodb_request(action, collection, **kwargs):
    """Petición a MongoDB Data API"""
    headers = {"api-key": MONGODB_API_KEY, "Content-Type": "application/json"}
    payload = {"dataSource": "Cluster0", "database": "contador_pro", "collection": collection}
    payload.update(kwargs)
    
    response = requests.post(f"{MONGODB_URL}/action/{action}", json=payload, headers=headers)
    return response.json()

# Inicializar estado de sesión
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "proyecto_actual" not in st.session_state:
    st.session_state.proyecto_actual = None

# ========== SIDEBAR ==========
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/calculator.png", width=60)
    st.title("📊 Contador Pro")
    
    if not st.session_state.usuario:
        # Login / Registro
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Registro"])
        
        with tab1:
            email = st.text_input("Email")
            password = st.text_input("Contraseña", type="password")
            if st.button("Iniciar Sesión", type="primary", use_container_width=True):
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                resultado = mongodb_request("findOne", "usuarios", 
                                           filter={"email": email, "password": password_hash})
                if resultado.get("document"):
                    st.session_state.usuario = resultado["document"]
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
        
        with tab2:
            reg_nombre = st.text_input("Nombre completo")
            reg_email = st.text_input("Email")
            reg_pass = st.text_input("Contraseña", type="password")
            reg_pass2 = st.text_input("Confirmar contraseña", type="password")
            if st.button("Registrarse", use_container_width=True):
                if reg_pass == reg_pass2 and len(reg_pass) >= 6:
                    password_hash = hashlib.sha256(reg_pass.encode()).hexdigest()
                    nuevo = {
                        "email": reg_email,
                        "password": password_hash,
                        "nombre": reg_nombre,
                        "proyectos": []
                    }
                    resultado = mongodb_request("insertOne", "usuarios", document=nuevo)
                    if resultado.get("insertedId"):
                        st.success("Cuenta creada! Ahora inicia sesión")
                    else:
                        st.error("Error: El usuario ya existe")
                else:
                    st.error("Las contraseñas no coinciden o son muy cortas")
    
    else:
        # Usuario logueado
        st.success(f"👋 Hola, {st.session_state.usuario['nombre']}")
        
        if st.button("🚪 Cerrar sesión", use_container_width=True):
            st.session_state.usuario = None
            st.session_state.proyecto_actual = None
            st.rerun()
        
        st.divider()
        
        # Lista de proyectos
        st.subheader("📁 Mis Proyectos")
        proyectos = mongodb_request("find", "proyectos", 
                                   filter={"email_usuario": st.session_state.usuario["email"]},
                                   limit=50)
        
        for proy in proyectos.get("documents", []):
            if st.button(f"📄 {proy['nombre']}", key=proy['nombre'], use_container_width=True):
                st.session_state.proyecto_actual = proy
                st.rerun()
        
        st.divider()
        
        # Nuevo proyecto
        nuevo_nombre = st.text_input("Nuevo proyecto")
        nuevo_tipo = st.selectbox("Tipo", ["Libro Diario", "Balanza de Comprobación", "Cuentas T"])
        if st.button("➕ Crear Proyecto", use_container_width=True, type="primary"):
            if nuevo_nombre:
                proyecto = {
                    "nombre": nuevo_nombre,
                    "tipo": nuevo_tipo,
                    "datos": [],
                    "columnas": [],
                    "email_usuario": st.session_state.usuario["email"]
                }
                mongodb_request("insertOne", "proyectos", document=proyecto)
                st.rerun()

# ========== ÁREA DE TRABAJO PRINCIPAL ==========
if st.session_state.proyecto_actual:
    proy = st.session_state.proyecto_actual
    
    st.title(f"📝 {proy['nombre']}")
    st.caption(f"Tipo: {proy.get('tipo', 'Libro Diario')}")
    
    # Columnas según tipo
    columnas_por_tipo = {
        "Libro Diario": ["Fecha", "Descripción", "Cuenta", "Debe", "Haber", "IVA %"],
        "Balanza de Comprobación": ["Código", "Cuenta", "S. Inicial", "Cargos", "Abonos", "Saldo Final"],
        "Cuentas T": ["Fecha", "Concepto", "Referencia", "Debe", "Haber", "Saldo"]
    }
    
    columnas = proy.get("columnas") or columnas_por_tipo.get(proy.get("tipo"), ["Fecha", "Descripción", "Debe", "Haber"])
    
    # Convertir datos a DataFrame
    datos = proy.get("datos", [])
    df = pd.DataFrame(datos, columns=columnas) if datos else pd.DataFrame(columns=columnas)
    
    # Editor de tabla interactivo
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Debe": st.column_config.NumberColumn("Debe", format="$ %.2f"),
            "Haber": st.column_config.NumberColumn("Haber", format="$ %.2f"),
            "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY")
        }
    )
    
    # Botones de acción
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Guardar", type="primary", use_container_width=True):
            # Actualizar en MongoDB
            mongodb_request("updateOne", "proyectos",
                           filter={"nombre": proy["nombre"], "email_usuario": st.session_state.usuario["email"]},
                           update={"$set": {
                               "datos": edited_df.fillna("").values.tolist(),
                               "columnas": list(edited_df.columns)
                           }})
            st.success("Proyecto guardado!")
            st.rerun()
    
    with col2:
        # Exportar a Excel
        if st.button("📥 Exportar Excel", use_container_width=True):
            edited_df.to_excel(f"{proy['nombre']}.xlsx", index=False)
            st.success(f"Descargado como {proy['nombre']}.xlsx")
    
    with col3:
        if st.button("📊 Reportes", use_container_width=True):
            st.session_state.mostrar_reportes = True
    
    # Totales
    st.divider()
    col_a, col_b, col_c = st.columns(3)
    
    total_debe = edited_df["Debe"].sum() if "Debe" in edited_df.columns else 0
    total_haber = edited_df["Haber"].sum() if "Haber" in edited_df.columns else 0
    
    col_a.metric("Total Debe", f"${total_debe:,.2f}")
    col_b.metric("Total Haber", f"${total_haber:,.2f}")
    
    diferencia = total_debe - total_haber
    col_c.metric("Diferencia", f"${diferencia:,.2f}", 
                delta="Cuadrado" if abs(diferencia) < 0.01 else "No cuadrado",
                delta_color="normal" if abs(diferencia) < 0.01 else "inverse")
    
    # Reportes
    if st.session_state.get("mostrar_reportes", False):
        with st.expander("📈 Estado de Resultados", expanded=True):
            ingresos = edited_df[edited_df["Descripción"].str.contains("ingreso|venta", case=False, na=False)]["Debe"].sum() if "Descripción" in edited_df.columns else 0
            gastos = edited_df[edited_df["Descripción"].str.contains("gasto|costo", case=False, na=False)]["Haber"].sum() if "Descripción" in edited_df.columns else 0
            
            st.metric("Total Ingresos", f"${ingresos:,.2f}")
            st.metric("Total Gastos", f"${gastos:,.2f}")
            st.metric("Utilidad Neta", f"${ingresos - gastos:,.2f}",
                     delta="Ganancia" if ingresos - gastos > 0 else "Pérdida")
        
        if st.button("Cerrar Reportes"):
            st.session_state.mostrar_reportes = False
            st.rerun()

elif st.session_state.usuario:
    st.info("👈 Selecciona o crea un proyecto en el menú lateral")
else:
    st.info("🔐 Inicia sesión o regístrate para comenzar")

# Footer
st.divider()
st.caption("📊 Contador Pro Cloud | Datos sincronizados con MongoDB Atlas")