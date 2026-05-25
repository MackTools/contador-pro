import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import os
from io import BytesIO

# ========== CONFIGURACION ==========
st.set_page_config(
    page_title="Contaduria",
    page_icon="📊",
    layout="wide"
)

# ========== INICIALIZAR ESTADO ==========
if "pagina" not in st.session_state:
    st.session_state.pagina = "login"
if "usuario" not in st.session_state:
    st.session_state.usuario = ""
if "proyecto_actual" not in st.session_state:
    st.session_state.proyecto_actual = ""
if "proyectos" not in st.session_state:
    # Datos demo
    df = pd.DataFrame({
        "Fecha": ["2024-01-15", "2024-01-20", "2024-02-01"],
        "Descripcion": ["Venta servicios", "Compra materiales", "Pago nomina"],
        "Cuenta": ["Ingresos", "Gastos", "Gastos"],
        "Debe": [0, 2500.00, 5000.00],
        "Haber": [8000.00, 0, 0]
    })
    st.session_state.proyectos = {
        "Demo": {
            "columnas": df.columns.tolist(),
            "datos": df.values.tolist(),
            "fecha": datetime.now().strftime("%d/%m/%Y")
        }
    }

def guardar_proyecto(nombre, df):
    st.session_state.proyectos[nombre] = {
        "columnas": df.columns.tolist(),
        "datos": df.fillna("").values.tolist(),
        "fecha": st.session_state.proyectos.get(nombre, {}).get("fecha", datetime.now().strftime("%d/%m/%Y"))
    }

def cargar_proyecto(nombre):
    if nombre in st.session_state.proyectos:
        p = st.session_state.proyectos[nombre]
        return pd.DataFrame(p["datos"], columns=p["columnas"])
    return pd.DataFrame()

def eliminar_proyecto(nombre):
    if nombre in st.session_state.proyectos:
        del st.session_state.proyectos[nombre]

def convertir_numerico(df, col):
    try:
        return pd.to_numeric(df[col].astype(str).str.replace(',', '').str.replace('$', ''), errors='coerce').fillna(0)
    except:
        return pd.Series([0] * len(df))

# ========== PAGINA DE LOGIN ==========
def pagina_login():
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        st.title("Contaduria")
        st.markdown("Sistema de gestion contable")
        st.markdown("<br>", unsafe_allow_html=True)
        
        usuario = st.text_input("Usuario", value="demo", key="login_user")
        password = st.text_input("Contraseña", type="password", value="admin123", key="login_pass")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("Ingresar", use_container_width=True):
                # Acepta cualquier usuario/contraseña para simplificar
                st.session_state.pagina = "app"
                st.session_state.usuario = usuario if usuario else "Usuario"
                st.session_state.proyecto_actual = "Demo"
                st.rerun()
        
        with col_b:
            if st.button("Offline", use_container_width=True):
                st.session_state.pagina = "app"
                st.session_state.usuario = "Offline"
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("Usuario: demo | Contraseña: admin123")

# ========== PAGINA PRINCIPAL ==========
def pagina_app():
    # Sidebar
    with st.sidebar:
        st.markdown(f"**{st.session_state.usuario}**")
        st.divider()
        
        st.markdown("**Nuevo proyecto**")
        nombre_nuevo = st.text_input("Nombre", key="new_name", placeholder="Nombre del proyecto")
        tipo = st.selectbox("Tipo", ["Libro Diario", "Balanza", "Cuentas T"], key="new_type")
        
        if st.button("Crear proyecto", use_container_width=True):
            if nombre_nuevo and nombre_nuevo not in st.session_state.proyectos:
                if tipo == "Libro Diario":
                    df = pd.DataFrame(columns=["Fecha", "Descripcion", "Cuenta", "Debe", "Haber"])
                elif tipo == "Balanza":
                    df = pd.DataFrame(columns=["Codigo", "Cuenta", "Debe", "Haber", "Saldo Deudor", "Saldo Acreedor"])
                else:
                    df = pd.DataFrame(columns=["Fecha", "Concepto", "Referencia", "Debe", "Haber", "Saldo"])
                
                guardar_proyecto(nombre_nuevo, df)
                st.session_state.proyecto_actual = nombre_nuevo
                st.rerun()
            elif nombre_nuevo in st.session_state.proyectos:
                st.error("Ya existe")
        
        st.divider()
        
        # Importar Excel
        archivo = st.file_uploader("Importar Excel", type=["xlsx", "xls"], key="import_file")
        if archivo:
            try:
                df = pd.read_excel(archivo)
                nombre = archivo.name.replace(".xlsx", "").replace(".xls", "")
                guardar_proyecto(nombre, df)
                st.session_state.proyecto_actual = nombre
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
        
        st.divider()
        
        st.markdown("**Proyectos**")
        
        if st.session_state.proyectos:
            for nombre in list(st.session_state.proyectos.keys()):
                c1, c2 = st.columns([4, 1])
                with c1:
                    if st.button(nombre, key=f"proj_{nombre}", use_container_width=True):
                        st.session_state.proyecto_actual = nombre
                        st.rerun()
                with c2:
                    if st.button("x", key=f"del_{nombre}"):
                        if st.session_state.proyecto_actual == nombre:
                            st.session_state.proyecto_actual = ""
                        eliminar_proyecto(nombre)
                        st.rerun()
        
        st.divider()
        
        if st.button("Cerrar sesion", use_container_width=True):
            st.session_state.pagina = "login"
            st.rerun()
    
    # Contenido principal
    if st.session_state.proyecto_actual:
        nombre = st.session_state.proyecto_actual
        df = cargar_proyecto(nombre)
        
        st.markdown(f"### {nombre}")
        
        if nombre in st.session_state.proyectos:
            st.caption(f"Creado: {st.session_state.proyectos[nombre].get('fecha', '')}")
        
        # Editor de datos
        if not df.empty:
            edited_df = st.data_editor(
                df,
                num_rows="dynamic",
                use_container_width=True,
                height=350,
                key=f"edit_{nombre}"
            )
            
            if not edited_df.fillna("").equals(df.fillna("")):
                guardar_proyecto(nombre, edited_df)
        else:
            edited_df = pd.DataFrame(columns=["Fecha", "Descripcion", "Cuenta", "Debe", "Haber"])
            st.info("Proyecto vacio. Agregue datos.")
        
        st.divider()
        
        # Botones de accion
        c1, c2, c3, c4, c5 = st.columns(5)
        
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
                edited_df[f"Col {len(edited_df.columns)+1}"] = ""
                guardar_proyecto(nombre, edited_df)
                st.rerun()
        
        with c4:
            if st.button("Totales", use_container_width=True):
                st.session_state.mostrar_totales = not st.session_state.get("mostrar_totales", False)
        
        with c5:
            if st.button("Grafica", use_container_width=True):
                st.session_state.mostrar_grafica = not st.session_state.get("mostrar_grafica", False)
        
        # Exportar
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            edited_df.to_excel(writer, sheet_name=nombre, index=False)
        st.download_button("Exportar Excel", output.getvalue(), f"{nombre}.xlsx",
                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        # Panel de totales
        if st.session_state.get("mostrar_totales", False):
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
        
        # Panel de grafica
        if st.session_state.get("mostrar_grafica", False):
            st.divider()
            st.markdown("#### Grafica Debe vs Haber")
            
            if "Debe" in edited_df.columns and "Haber" in edited_df.columns:
                fig, ax = plt.subplots(figsize=(10, 4))
                
                debe = convertir_numerico(edited_df, "Debe")
                haber = convertir_numerico(edited_df, "Haber")
                
                x = range(len(edited_df))
                ax.bar(x, debe, label="Debe", color="#e74c3c")
                ax.bar(x, haber, label="Haber", color="#27ae60", bottom=debe)
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
        
        # Reportes
        st.divider()
        st.markdown("#### Reportes")
        
        col_r1, col_r2 = st.columns(2)
        
        with col_r1:
            if st.button("Balance General", use_container_width=True):
                activos = pasivos = capital = 0
                
                for _, row in edited_df.iterrows():
                    texto = " ".join([str(v).lower() for v in row.values])
                    try:
                        debe = float(str(row.get('Debe', 0)).replace(',', '').replace('$', '')) if pd.notna(row.get('Debe')) else 0
                        haber = float(str(row.get('Haber', 0)).replace(',', '').replace('$', '')) if pd.notna(row.get('Haber')) else 0
                        valor = debe - haber
                    except:
                        valor = 0
                    
                    if any(p in texto for p in ['activo', 'caja', 'banco', 'inventario']):
                        activos += valor if valor > 0 else 0
                    elif any(p in texto for p in ['pasivo', 'proveedor', 'deuda']):
                        pasivos += abs(valor) if valor < 0 else 0
                    elif any(p in texto for p in ['capital', 'patrimonio']):
                        capital += valor if valor > 0 else 0
                
                b1, b2, b3 = st.columns(3)
                with b1:
                    st.metric("Activos", f"${activos:,.2f}")
                with b2:
                    st.metric("Pasivos", f"${pasivos:,.2f}")
                with b3:
                    st.metric("Capital", f"${capital:,.2f}")
                
                st.info(f"Pasivo + Capital: ${pasivos + capital:,.2f} | Diferencia: ${activos - (pasivos + capital):,.2f}")
        
        with col_r2:
            if st.button("Estado de Resultados", use_container_width=True):
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
                    elif any(p in desc for p in ['gasto', 'costo', 'compra', 'sueldo']):
                        gastos += debe
                
                utilidad = ingresos - gastos
                
                r1, r2, r3 = st.columns(3)
                with r1:
                    st.metric("Ingresos", f"${ingresos:,.2f}")
                with r2:
                    st.metric("Gastos", f"${gastos:,.2f}")
                with r3:
                    st.metric("Utilidad", f"${abs(utilidad):,.2f}")
    
    else:
        st.markdown("### Contaduria")
        st.markdown("Seleccione un proyecto en el menu lateral o cree uno nuevo")

# ========== RUTER ==========
if st.session_state.pagina == "login":
    pagina_login()
else:
    pagina_app()
