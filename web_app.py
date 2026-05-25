import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import os
import random
from io import BytesIO

# ========== CONFIGURACION ==========
st.set_page_config(
    page_title="Contaduria",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== INICIALIZAR ESTADO ==========
if "pagina" not in st.session_state:
    st.session_state.pagina = "login"
if "usuario" not in st.session_state:
    st.session_state.usuario = ""
if "email_usuario" not in st.session_state:
    st.session_state.email_usuario = ""
if "proyecto_actual" not in st.session_state:
    st.session_state.proyecto_actual = ""
if "proyectos" not in st.session_state:
    df = pd.DataFrame({
        "Fecha": ["2024-01-15", "2024-01-20", "2024-02-01", "2024-02-15", "2024-03-01"],
        "Descripcion": ["Venta servicios", "Compra materiales", "Pago nomina", "Venta productos", "Alquiler oficina"],
        "Cuenta": ["Ingresos", "Gastos", "Gastos", "Ingresos", "Gastos"],
        "Debe": [0, 2500.00, 5000.00, 0, 1500.00],
        "Haber": [8000.00, 0, 0, 12000.00, 0]
    })
    st.session_state.proyectos = {
        "Demo Empresa": {
            "columnas": df.columns.tolist(),
            "datos": df.values.tolist(),
            "fecha": datetime.now().strftime("%d/%m/%Y"),
            "modificado": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
    }
if "usuarios_registrados" not in st.session_state:
    st.session_state.usuarios_registrados = {
        "demo@contaduria.com": {"password": "admin123", "nombre": "Usuario Demo"}
    }
if "codigos_recuperacion" not in st.session_state:
    st.session_state.codigos_recuperacion = {}

# ========== ESTILO CSS ==========
st.markdown("""
<style>
    .btn-descarga {
        position: fixed;
        top: 14px;
        right: 24px;
        z-index: 999999;
        background: #2563eb;
        color: white !important;
        padding: 9px 20px;
        border-radius: 8px;
        text-decoration: none;
        font-size: 13px;
        font-weight: 500;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
        transition: all 0.2s;
    }
    .btn-descarga:hover {
        background: #1d4ed8;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
        transform: translateY(-1px);
    }
    
    /* === SIDEBAR - NO COLAPSABLE === */
    [data-testid="stSidebar"] {
        min-width: 270px !important;
        max-width: 270px !important;
    }
    
    /* Ocultar TODOS los botones de colapso */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"],
    button[kind="header"],
    [data-testid="stSidebarNav"] button {
        display: none !important;
    }
    
    /* === TABLAS === */
    [data-testid="stDataFrame"] {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        overflow: hidden;
    }
    [data-testid="stDataFrame"] th {
        background-color: #f8fafc !important;
        color: #334155 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        padding: 10px 14px !important;
        border-bottom: 2px solid #e5e7eb !important;
    }
    [data-testid="stDataFrame"] td {
        padding: 8px 14px !important;
        font-size: 13px !important;
        border-bottom: 1px solid #f1f5f9 !important;
    }
    [data-testid="stDataFrame"] tr:hover td {
        background-color: #f8fafc !important;
    }
    
    /* === INPUTS === */
    input, select, textarea {
        border-radius: 6px !important;
        border: 1px solid #d1d5db !important;
        padding: 8px 12px !important;
    }
    input:focus, select:focus, textarea:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1) !important;
    }
    
    /* === BOTONES === */
    .stButton > button {
        border-radius: 6px;
        font-size: 13px;
        padding: 6px 16px;
        font-weight: 500;
        border: 1px solid #d1d5db;
        background-color: white;
        color: #374151;
        transition: all 0.15s;
    }
    .stButton > button:hover {
        background-color: #f3f4f6;
        border-color: #9ca3af;
    }
    
    /* === METRICAS === */
    [data-testid="stMetric"] {
        background-color: white;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
    }
    
    /* === EXPANDER === */
    .streamlit-expanderHeader {
        border-radius: 6px;
        font-weight: 500;
    }
    
    /* === OCULTAR === */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* === SCROLLBAR === */
    ::-webkit-scrollbar {width: 6px;}
    ::-webkit-scrollbar-track {background: transparent;}
    ::-webkit-scrollbar-thumb {background: #d1d5db; border-radius: 3px;}
    
    /* === PREVENIR COLAPSO CON JS === */
</style>

<script>
    // Prevenir que la sidebar se colapse
    const observer = new MutationObserver(function() {
        const sidebar = parent.document.querySelector('[data-testid="stSidebar"]');
        if (sidebar) {
            sidebar.style.display = 'block';
            sidebar.style.visibility = 'visible';
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });
</script>
""", unsafe_allow_html=True)

# ========== BOTON DESCARGA ==========
# URL de descarga (cambia esto por tu enlace de Google Drive, Dropbox, etc.)
URL_DESCARGA_EXE = "https://drive.google.com/uc?export=download&id=TU_ID_DE_ARCHIVO"

st.markdown(f"""
<a href="{URL_DESCARGA_EXE}" target="_blank" class="btn-descarga">
    📥 Descargar App Escritorio
</a>
""", unsafe_allow_html=True)

# ========== FUNCIONES ==========
def guardar_proyecto(nombre, df):
    st.session_state.proyectos[nombre] = {
        "columnas": df.columns.tolist(),
        "datos": df.fillna("").values.tolist(),
        "fecha": st.session_state.proyectos.get(nombre, {}).get("fecha", datetime.now().strftime("%d/%m/%Y")),
        "modificado": datetime.now().strftime("%d/%m/%Y %H:%M")
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

def enviar_email_recuperacion(destinatario, codigo):
    try:
        st.session_state.codigos_recuperacion[destinatario] = {
            "codigo": codigo,
            "expiracion": datetime.now().timestamp() + 1800
        }
        return True, "Codigo enviado (simulado)"
    except Exception as e:
        return False, str(e)

# ========== PAGINA DE LOGIN ==========
def pagina_login():
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.6, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 10px 0 30px 0;">
            <h1 style="color: #1e293b; margin: 0; font-size: 28px;">Contaduria</h1>
            <p style="color: #64748b; margin: 5px 0 0 0; font-size: 15px;">Sistema de gestion contable</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["Iniciar sesion", "Registrarse", "Recuperar contrasena"])
        
        with tab1:
            with st.form("form_login"):
                email = st.text_input("Correo electronico", placeholder="demo@contaduria.com")
                password = st.text_input("Contrasena", type="password", placeholder="••••••••")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    submit = st.form_submit_button("Ingresar", use_container_width=True)
                with col_b:
                    offline = st.form_submit_button("Modo offline", use_container_width=True)
                
                if submit:
                    usuarios = st.session_state.usuarios_registrados
                    if email in usuarios and usuarios[email]["password"] == password:
                        st.session_state.pagina = "app"
                        st.session_state.usuario = usuarios[email]["nombre"]
                        st.session_state.email_usuario = email
                        st.session_state.proyecto_actual = "Demo Empresa"
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas")
                
                if offline:
                    st.session_state.pagina = "app"
                    st.session_state.usuario = "Offline"
                    st.session_state.email_usuario = ""
                    st.rerun()
            
            st.caption("Demo: demo@contaduria.com / admin123")
        
        with tab2:
            with st.form("form_registro"):
                st.markdown("**Crear cuenta gratuita**")
                nombre = st.text_input("Nombre completo", placeholder="Juan Perez")
                email_reg = st.text_input("Correo electronico", placeholder="juan@ejemplo.com")
                pass_reg = st.text_input("Contrasena", type="password", placeholder="Minimo 6 caracteres")
                pass_reg2 = st.text_input("Confirmar contrasena", type="password")
                
                if st.form_submit_button("Crear cuenta", use_container_width=True):
                    errores = []
                    if not nombre:
                        errores.append("Ingrese su nombre")
                    if not email_reg or "@" not in email_reg:
                        errores.append("Correo electronico invalido")
                    if len(pass_reg) < 6:
                        errores.append("Contrasena: minimo 6 caracteres")
                    if pass_reg != pass_reg2:
                        errores.append("Las contrasenas no coinciden")
                    if email_reg in st.session_state.usuarios_registrados:
                        errores.append("Este correo ya esta registrado")
                    
                    if errores:
                        for e in errores:
                            st.error(e)
                    else:
                        st.session_state.usuarios_registrados[email_reg] = {
                            "password": pass_reg,
                            "nombre": nombre
                        }
                        st.success("Cuenta creada exitosamente")
                        st.info("Ahora puede iniciar sesion desde la pestana 'Iniciar sesion'")
        
        with tab3:
            st.markdown("**Recuperar contrasena**")
            st.caption("Ingrese su correo para recibir un codigo")
            
            email_rec = st.text_input("Correo electronico", placeholder="su@correo.com", key="rec_email")
            
            if st.button("Enviar codigo de verificacion", use_container_width=True):
                if email_rec and "@" in email_rec:
                    if email_rec in st.session_state.usuarios_registrados:
                        codigo = str(random.randint(100000, 999999))
                        exito, msg = enviar_email_recuperacion(email_rec, codigo)
                        if exito:
                            st.success(f"Codigo enviado a {email_rec}")
                            st.info(f"Codigo de verificacion: **{codigo}**")
                            st.session_state.rec_email_temp = email_rec
                        else:
                            st.error(msg)
                    else:
                        st.error("Correo no registrado")
                else:
                    st.error("Ingrese un correo valido")
            
            if hasattr(st.session_state, 'rec_email_temp'):
                st.divider()
                st.markdown("**Verificar codigo**")
                codigo_ingresado = st.text_input("Codigo recibido", placeholder="000000")
                nueva_pass = st.text_input("Nueva contrasena", type="password", placeholder="Minimo 6 caracteres")
                
                if st.button("Cambiar contrasena", use_container_width=True):
                    email = st.session_state.rec_email_temp
                    if email in st.session_state.codigos_recuperacion:
                        info = st.session_state.codigos_recuperacion[email]
                        if datetime.now().timestamp() > info["expiracion"]:
                            st.error("El codigo ha expirado. Solicite uno nuevo.")
                        elif codigo_ingresado == info["codigo"]:
                            if len(nueva_pass) >= 6:
                                st.session_state.usuarios_registrados[email]["password"] = nueva_pass
                                del st.session_state.codigos_recuperacion[email]
                                del st.session_state.rec_email_temp
                                st.success("Contrasena cambiada exitosamente")
                                st.info("Ahora puede iniciar sesion")
                            else:
                                st.error("Contrasena: minimo 6 caracteres")
                        else:
                            st.error("Codigo incorrecto")

# ========== PAGINA PRINCIPAL ==========
def pagina_app():
    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 8px 0;">
            <strong style="font-size: 15px;">{st.session_state.usuario}</strong><br>
            <small style="color: #64748b;">{st.session_state.email_usuario if st.session_state.email_usuario else 'Modo offline'}</small>
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        
        with st.expander("➕ Nuevo proyecto", expanded=False):
            nombre_nuevo = st.text_input("Nombre", key="new_name", placeholder="Nombre del proyecto")
            tipo = st.selectbox("Plantilla", ["Libro Diario", "Balanza de Comprobacion", "Cuentas T"], key="new_type")
            
            if st.button("Crear proyecto", use_container_width=True):
                if nombre_nuevo:
                    if nombre_nuevo not in st.session_state.proyectos:
                        if tipo == "Libro Diario":
                            df = pd.DataFrame(columns=["Fecha", "Descripcion", "Cuenta", "Debe", "Haber"])
                        elif tipo == "Balanza de Comprobacion":
                            df = pd.DataFrame(columns=["Codigo", "Cuenta", "Debe", "Haber", "Saldo Deudor", "Saldo Acreedor"])
                        else:
                            df = pd.DataFrame(columns=["Fecha", "Concepto", "Referencia", "Debe", "Haber", "Saldo"])
                        
                        guardar_proyecto(nombre_nuevo, df)
                        st.session_state.proyecto_actual = nombre_nuevo
                        st.rerun()
                    else:
                        st.error("El proyecto ya existe")
                else:
                    st.error("Ingrese un nombre")
        
        with st.expander("📥 Importar Excel", expanded=False):
            archivo = st.file_uploader("Seleccionar archivo", type=["xlsx", "xls"], key="import_file", label_visibility="collapsed")
            if archivo:
                try:
                    df = pd.read_excel(archivo)
                    nombre = archivo.name.replace(".xlsx", "").replace(".xls", "")
                    if nombre in st.session_state.proyectos:
                        nombre = f"{nombre}_{datetime.now().strftime('%H%M')}"
                    guardar_proyecto(nombre, df)
                    st.session_state.proyecto_actual = nombre
                    st.success(f"Importado: {len(df)} filas")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        
        st.divider()
        st.markdown("**📁 Proyectos**")
        
        if st.session_state.proyectos:
            for nombre in list(st.session_state.proyectos.keys()):
                info = st.session_state.proyectos[nombre]
                n_filas = len(info["datos"])
                
                cols = st.columns([5, 1])
                with cols[0]:
                    if st.button(f"{nombre} ({n_filas})", key=f"proj_{nombre}", use_container_width=True):
                        st.session_state.proyecto_actual = nombre
                        st.rerun()
                with cols[1]:
                    if st.button("×", key=f"del_{nombre}", help="Eliminar"):
                        if st.session_state.proyecto_actual == nombre:
                            st.session_state.proyecto_actual = ""
                        eliminar_proyecto(nombre)
                        st.rerun()
        else:
            st.caption("Sin proyectos")
        
        st.divider()
        
        if st.button("Cerrar sesion", use_container_width=True):
            st.session_state.pagina = "login"
            st.session_state.proyecto_actual = ""
            st.rerun()
    
    # Contenido principal
    if st.session_state.proyecto_actual:
        nombre = st.session_state.proyecto_actual
        df = cargar_proyecto(nombre)
        info = st.session_state.proyectos.get(nombre, {})
        
        st.markdown(f"### {nombre}")
        st.caption(f"Creado: {info.get('fecha', 'N/A')} | Modificado: {info.get('modificado', 'N/A')} | Registros: {len(df)}")
        
        if not df.empty:
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
                height=380,
                column_config=column_config if column_config else None,
                key=f"edit_{nombre}",
                hide_index=True
            )
            
            if not edited_df.fillna("").equals(df.fillna("")):
                guardar_proyecto(nombre, edited_df)
        else:
            edited_df = pd.DataFrame(columns=["Fecha", "Descripcion", "Cuenta", "Debe", "Haber"])
            st.info("Proyecto vacio. Use 'Agregar fila' para comenzar")
        
        st.divider()
        
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        
        with c1:
            if st.button("+ Fila", use_container_width=True):
                nueva = {col: "" for col in edited_df.columns}
                edited_df = pd.concat([edited_df, pd.DataFrame([nueva])], ignore_index=True)
                guardar_proyecto(nombre, edited_df)
                st.rerun()
        
        with c2:
            if st.button("- Ultima", use_container_width=True):
                if len(edited_df) > 0:
                    edited_df = edited_df.iloc[:-1]
                    guardar_proyecto(nombre, edited_df)
                    st.rerun()
        
        with c3:
            if st.button("+ Columna", use_container_width=True):
                n = len(edited_df.columns) + 1
                edited_df[f"Columna {n}"] = ""
                guardar_proyecto(nombre, edited_df)
                st.rerun()
        
        with c4:
            if st.button("Estadisticas", use_container_width=True):
                st.session_state.show_stats = not st.session_state.get("show_stats", False)
        
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
        
        if st.session_state.get("show_stats", False):
            st.divider()
            st.markdown("#### Estadisticas")
            
            cols_num = []
            for col in edited_df.columns:
                try:
                    vals = convertir_numerico(edited_df, col)
                    if vals.notna().any():
                        cols_num.append((col, vals))
                except:
                    pass
            
            if cols_num:
                columnas = st.columns(min(len(cols_num), 3))
                for i, (col, vals) in enumerate(cols_num):
                    with columnas[i % 3]:
                        st.metric(col, f"${vals.sum():,.2f}", delta=f"Prom: ${vals.mean():,.2f}")
                        st.caption(f"Max: ${vals.max():,.2f} | Min: ${vals.min():,.2f}")
        
        if st.session_state.get("show_chart", False):
            st.divider()
            
            tipo_graf = st.selectbox("Tipo:", ["Barras", "Linea", "Pastel"], key="tipo_graf")
            
            if "Debe" in edited_df.columns and "Haber" in edited_df.columns:
                fig, ax = plt.subplots(figsize=(10, 4))
                fig.patch.set_facecolor('white')
                
                debe = convertir_numerico(edited_df, "Debe")
                haber = convertir_numerico(edited_df, "Haber")
                
                if tipo_graf == "Barras":
                    x = range(len(edited_df))
                    ax.bar(x, debe, label="Debe", color="#ef4444", alpha=0.85)
                    ax.bar(x, haber, label="Haber", color="#22c55e", alpha=0.85, bottom=debe)
                    ax.legend()
                    ax.grid(True, alpha=0.3, axis='y')
                elif tipo_graf == "Linea":
                    ax.plot(range(len(edited_df)), debe, 'o-', label="Debe", color="#ef4444", linewidth=2, markersize=5)
                    ax.plot(range(len(edited_df)), haber, 's-', label="Haber", color="#22c55e", linewidth=2, markersize=5)
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                else:
                    total_debe = debe.sum()
                    total_haber = haber.sum()
                    if total_debe > 0 or total_haber > 0:
                        ax.pie([total_debe, total_haber], 
                               labels=[f"Debe\n${total_debe:,.2f}", f"Haber\n${total_haber:,.2f}"],
                               colors=["#ef4444", "#22c55e"], autopct='%1.1f%%')
                
                ax.set_xlabel("Registro")
                ax.set_ylabel("Monto ($)")
                ax.set_title(f"{nombre} - Debe vs Haber")
                plt.tight_layout()
                st.pyplot(fig)
                
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("Total Debe", f"${debe.sum():,.2f}")
                with m2:
                    st.metric("Total Haber", f"${haber.sum():,.2f}")
                with m3:
                    st.metric("Diferencia", f"${debe.sum() - haber.sum():,.2f}")
        
        st.divider()
        st.markdown("#### Reportes")
        
        col_r1, col_r2 = st.columns(2)
        
        with col_r1:
            with st.expander("Balance General"):
                if st.button("Generar Balance", use_container_width=True, key="btn_balance"):
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
                    
                    b1, b2, b3 = st.columns(3)
                    with b1:
                        st.metric("Activos", f"${activos:,.2f}")
                    with b2:
                        st.metric("Pasivos", f"${pasivos:,.2f}")
                    with b3:
                        st.metric("Capital", f"${capital:,.2f}")
                    
                    st.info(f"Pasivo + Capital: ${pasivos + capital:,.2f} | Diferencia: ${activos - (pasivos + capital):,.2f}")
        
        with col_r2:
            with st.expander("Estado de Resultados"):
                if st.button("Generar Resultados", use_container_width=True, key="btn_resultados"):
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
                    estado = "Ganancia" if utilidad > 0 else ("Perdida" if utilidad < 0 else "Equilibrio")
                    
                    r1, r2, r3 = st.columns(3)
                    with r1:
                        st.metric("Ingresos", f"${ingresos:,.2f}")
                    with r2:
                        st.metric("Gastos", f"${gastos:,.2f}")
                    with r3:
                        st.metric("Utilidad Neta", f"${abs(utilidad):,.2f}", delta=estado)
    
    else:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px;">
            <h2 style="color: #334155;">Contaduria</h2>
            <p style="color: #64748b;">Sistema de gestion contable</p>
            <br>
            <p style="color: #94a3b8;">Seleccione un proyecto del menu lateral o cree uno nuevo</p>
        </div>
        """, unsafe_allow_html=True)

# ========== ROUTER ==========
if st.session_state.pagina == "login":
    pagina_login()
else:
    pagina_app()
