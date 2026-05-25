# streamlit_app.py - Versión limpia, minimalista, funcional

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import base64
import os
from io import BytesIO

# ========== CONFIGURACIÓN ==========
st.set_page_config(
    page_title="Contaduría",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== ESTILO MINIMALISTA ==========
st.markdown("""
<style>
    /* Sidebar siempre visible y ancho fijo */
    [data-testid="stSidebar"] {
        min-width: 260px !important;
        max-width: 260px !important;
        background-color: #f8f9fa;
    }
    
    /* Ocultar botón de colapsar sidebar */
    button[kind="header"] {
        display: none;
    }
    
    /* Ocultar flecha de colapso */
    [data-testid="collapsedControl"] {
        display: none;
    }
    
    /* Estilo limpio */
    .stButton > button {
        border-radius: 4px;
        font-weight: 400;
        font-size: 14px;
        padding: 4px 12px;
    }
    
    /* Quitar decoraciones */
    .st-emotion-cache-1r6slb0 {
        display: none;
    }
    
    /* Ocultar menú y footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
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

# ========== DATOS DEMO ==========
if "demo_loaded" not in st.session_state:
    df_demo = pd.DataFrame({
        "Fecha": ["2024-01-15", "2024-01-20", "2024-02-01", "2024-02-15", "2024-03-01"],
        "Descripcion": ["Venta servicios", "Compra materiales", "Pago nomina", "Venta productos", "Alquiler oficina"],
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
    return pd.DataFrame()

def eliminar_proyecto(nombre):
    if nombre in st.session_state.projects:
        del st.session_state.projects[nombre]
    if nombre in st.session_state.dataframes:
        del st.session_state.dataframes[nombre]

def convertir_numerico(df, columna):
    try:
        return pd.to_numeric(df[columna].astype(str).str.replace(',', '').str.replace('$', ''), errors='coerce').fillna(0)
    except:
        return pd.Series([0] * len(df))

# ========== LOGIN ==========
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("### Contaduria")
        st.markdown("Sistema de gestion contable")
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.form("login"):
            email = st.text_input("Correo", placeholder="demo@contaduria.com")
            password = st.text_input("Contraseña", type="password", placeholder="admin123")
            
            c1, c2 = st.columns(2)
            with c1:
                login_btn = st.form_submit_button("Ingresar", use_container_width=True)
            with c2:
                offline_btn = st.form_submit_button("Offline", use_container_width=True)
            
            if login_btn:
                if email == "demo@contaduria.com" and password == "admin123":
                    st.session_state.logged_in = True
                    st.session_state.username = email
                    st.session_state.current_project = "Demo Empresa"
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
            
            if offline_btn:
                st.session_state.logged_in = True
                st.session_state.username = "Offline"
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("demo@contaduria.com / admin123")
    
    st.stop()

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown(f"**{st.session_state.username}**")
    st.divider()
    
    # Nuevo proyecto
    st.markdown("##### Nuevo proyecto")
    nombre_nuevo = st.text_input("Nombre", key="new_name", label_visibility="collapsed", placeholder="Nombre del proyecto")
    tipo_nuevo = st.selectbox("Tipo", ["Libro Diario", "Balanza", "Cuentas T"], key="new_type", label_visibility="collapsed")
    
    if st.button("Crear", use_container_width=True):
        if nombre_nuevo and nombre_nuevo not in st.session_state.projects:
            if tipo_nuevo == "Libro Diario":
                df = pd.DataFrame(columns=["Fecha", "Descripcion", "Cuenta", "Debe", "Haber"])
            elif tipo_nuevo == "Balanza":
                df = pd.DataFrame(columns=["Codigo", "Cuenta", "Debe", "Haber", "Saldo Deudor", "Saldo Acreedor"])
            else:
                df = pd.DataFrame(columns=["Fecha", "Concepto", "Referencia", "Debe", "Haber", "Saldo"])
            
            guardar_proyecto(nombre_nuevo, df)
            st.session_state.current_project = nombre_nuevo
            st.rerun()
        elif nombre_nuevo in st.session_state.projects:
            st.error("Ya existe")
    
    st.divider()
    
    # Importar
    st.markdown("##### Importar Excel")
    archivo = st.file_uploader("Archivo", type=["xlsx", "xls"], key="import_file", label_visibility="collapsed")
    if archivo:
        try:
            df_import = pd.read_excel(archivo)
            nombre_import = archivo.name.replace(".xlsx", "").replace(".xls", "")
            if nombre_import in st.session_state.projects:
                nombre_import = f"{nombre_import}_{datetime.now().strftime('%H%M')}"
            guardar_proyecto(nombre_import, df_import)
            st.session_state.current_project = nombre_import
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.divider()
    
    # Lista proyectos
    st.markdown("##### Proyectos")
    
    if st.session_state.projects:
        for nombre in list(st.session_state.projects.keys()):
            c1, c2 = st.columns([4, 1])
            with c1:
                if st.button(nombre, key=f"p_{nombre}", use_container_width=True):
                    st.session_state.current_project = nombre
                    st.rerun()
            with c2:
                if st.button("x", key=f"d_{nombre}"):
                    if st.session_state.current_project == nombre:
                        st.session_state.current_project = None
                    eliminar_proyecto(nombre)
                    st.rerun()
    else:
        st.caption("Sin proyectos")
    
    st.divider()
    
    # Descargar .exe
    if os.path.exists("dist/contaduria.exe"):
        with open("dist/contaduria.exe", "rb") as f:
            st.download_button("Descargar App", f.read(), "Contaduria.exe", "application/octet-stream", use_container_width=True)
    
    if st.button("Cerrar sesion", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ========== AREA PRINCIPAL ==========
if st.session_state.current_project:
    nombre = st.session_state.current_project
    df = cargar_proyecto(nombre)
    info = st.session_state.projects[nombre]
    
    st.markdown(f"### {nombre}")
    st.caption(f"Creado: {info.get('fecha_creacion', '')} | Modificado: {info.get('fecha_modificacion', '')} | Registros: {len(df)}")
    
    # Editor de datos
    column_config = {}
    for col in df.columns:
        if any(x in col.lower() for x in ["debe", "haber", "saldo", "monto", "cargos", "abonos"]):
            column_config[col] = st.column_config.NumberColumn(col, format="$ %.2f")
    
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        height=400,
        column_config=column_config if column_config else None,
        key=f"editor_{nombre}"
    )
    
    if not edited_df.fillna("").equals(df.fillna("")):
        guardar_proyecto(nombre, edited_df)
    
    st.divider()
    
    # Herramientas
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    
    with c1:
        if st.button("Agregar fila", use_container_width=True):
            nueva = {col: "" for col in edited_df.columns}
            edited_df = pd.concat([edited_df, pd.DataFrame([nueva])], ignore_index=True)
            guardar_proyecto(nombre, edited_df)
            st.rerun()
    
    with c2:
        if st.button("Eliminar ultima", use_container_width=True):
            if len(edited_df) > 0:
                edited_df = edited_df.iloc[:-1]
                guardar_proyecto(nombre, edited_df)
                st.rerun()
    
    with c3:
        if st.button("Agregar columna", use_container_width=True):
            edited_df[f"Columna {len(edited_df.columns)+1}"] = ""
            guardar_proyecto(nombre, edited_df)
            st.rerun()
    
    with c4:
        if st.button("Totales", use_container_width=True):
            st.session_state.show_totals = not st.session_state.get("show_totals", False)
    
    with c5:
        if st.button("Grafica", use_container_width=True):
            st.session_state.show_chart = not st.session_state.get("show_chart", False)
    
    with c6:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            edited_df.to_excel(writer, sheet_name=nombre, index=False)
        st.download_button("Exportar", output.getvalue(), f"{nombre}.xlsx", 
                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                          use_container_width=True)
    
    # Totales
    if st.session_state.get("show_totals", False):
        st.divider()
        st.markdown("#### Totales")
        
        cols_num = []
        for col in edited_df.columns:
            try:
                vals = convertir_numerico(edited_df, col)
                if vals.sum() != 0:
                    cols_num.append((col, vals))
            except:
                pass
        
        if cols_num:
            columnas = st.columns(min(len(cols_num), 4))
            for i, (col, vals) in enumerate(cols_num):
                with columnas[i % 4]:
                    st.metric(col, f"${vals.sum():,.2f}")
        else:
            st.caption("Sin datos numericos")
    
    # Grafica
    if st.session_state.get("show_chart", False):
        st.divider()
        st.markdown("#### Grafica")
        
        if "Debe" in edited_df.columns and "Haber" in edited_df.columns:
            fig, ax = plt.subplots(figsize=(10, 4))
            
            debe = convertir_numerico(edited_df, "Debe")
            haber = convertir_numerico(edited_df, "Haber")
            
            x = range(len(edited_df))
            ax.bar(x, debe, label="Debe", color="#e74c3c", alpha=0.8)
            ax.bar(x, haber, label="Haber", color="#27ae60", alpha=0.8, bottom=debe)
            ax.set_xlabel("Registro")
            ax.set_ylabel("Monto ($)")
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            st.pyplot(fig)
            
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Debe", f"${debe.sum():,.2f}")
            with m2:
                st.metric("Haber", f"${haber.sum():,.2f}")
            with m3:
                st.metric("Diferencia", f"${debe.sum() - haber.sum():,.2f}")
        else:
            st.caption("Se requieren columnas Debe y Haber")
    
    # Balance
    st.divider()
    
    c1, c2 = st.columns(2)
    
    with c1:
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
                
                if any(p in texto for p in ['activo', 'caja', 'banco', 'efectivo', 'inventario', 'cliente']):
                    activos += abs(valor) if valor > 0 else 0
                elif any(p in texto for p in ['pasivo', 'proveedor', 'deuda', 'prestamo']):
                    pasivos += abs(valor) if valor < 0 else max(valor, 0)
                elif any(p in texto for p in ['capital', 'patrimonio', 'aporte']):
                    capital += abs(valor) if valor > 0 else 0
            
            b1, b2, b3 = st.columns(3)
            with b1:
                st.metric("Activos", f"${activos:,.2f}")
            with b2:
                st.metric("Pasivos", f"${pasivos:,.2f}")
            with b3:
                st.metric("Capital", f"${capital:,.2f}")
            
            st.info(f"Pasivo + Capital: ${pasivos + capital:,.2f} | Diferencia: ${activos - (pasivos + capital):,.2f}")
    
    with c2:
        if st.button("Generar Resultados", use_container_width=True):
            ingresos = gastos = 0
            
            for _, row in edited_df.iterrows():
                desc = str(row.get('Descripcion', row.get('Concepto', ''))).lower()
                try:
                    debe = float(str(row.get('Debe', 0)).replace(',', '').replace('$', '')) if pd.notna(row.get('Debe')) else 0
                    haber = float(str(row.get('Haber', 0)).replace(',', '').replace('$', '')) if pd.notna(row.get('Haber')) else 0
                except:
                    debe = haber = 0
                
                if any(p in desc for p in ['ingreso', 'venta', 'servicio']):
                    ingresos += haber
                elif any(p in desc for p in ['gasto', 'costo', 'compra', 'sueldo', 'alquiler']):
                    gastos += debe
            
            utilidad = ingresos - gastos
            
            r1, r2, r3 = st.columns(3)
            with r1:
                st.metric("Ingresos", f"${ingresos:,.2f}")
            with r2:
                st.metric("Gastos", f"${gastos:,.2f}")
            with r3:
                st.metric("Utilidad", f"${abs(utilidad):,.2f}", 
                         delta="Ganancia" if utilidad > 0 else "Perdida")

else:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Contaduria")
    st.markdown("Sistema de gestion contable")
    st.divider()
    st.markdown("Seleccione o cree un proyecto en el menu lateral")
