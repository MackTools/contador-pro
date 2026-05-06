# web_app.py - VERSIÓN COMPLETA CORREGIDA

import streamlit as st
import pandas as pd
import hashlib
import pymongo
from datetime import datetime
import openpyxl
from io import BytesIO
import matplotlib.pyplot as plt
import base64
import os

# Intentar importar reportlab (opcional pero recomendado)
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    st.warning("ReportLab no está instalado. Los reportes PDF se exportarán como HTML.")

# ========== CONFIGURACIÓN DE PÁGINA ==========
st.set_page_config(
    page_title="Contaduría | Sistema Contable",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== FUNCIÓN PARA GENERAR ENLACE DE DESCARGA DEL EXE ==========
def get_desktop_app_download_link():
    """Genera un enlace para descargar la versión de escritorio"""
    # El archivo .exe debe estar en la raíz del repositorio
    exe_path = "ContadorProSetup.exe"  # Cambia por el nombre de tu archivo
    
    if os.path.exists(exe_path):
        with open(exe_path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="ContadorProSetup.exe" style="text-decoration: none;">'
        return href
    return None

# ========== CSS PERSONALIZADO (MODO OSCURO) ==========
st.markdown("""
<style>
    /* Fondo oscuro global */
    .stApp {
        background-color: #0e1117;
    }
    
    .main > div {
        background-color: #0e1117;
    }
    
    /* Header superior con botón de descarga */
    .top-bar {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        padding: 10px 20px;
        background-color: #0d1117;
        border-bottom: 1px solid #2d3748;
        margin-bottom: 20px;
    }
    
    .download-btn {
        background-color: #27ae60;
        color: white;
        padding: 8px 16px;
        border-radius: 6px;
        text-decoration: none;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.2s;
        border: none;
        cursor: pointer;
    }
    
    .download-btn:hover {
        background-color: #219a52;
        transform: translateY(-1px);
    }
    
    .main-header {
        font-size: 24px;
        font-weight: 600;
        color: #ffffff;
        border-bottom: 2px solid #2d3748;
        padding-bottom: 10px;
        margin-bottom: 20px;
        font-family: 'Segoe UI', 'Roboto', sans-serif;
    }
    
    .section-header {
        font-size: 18px;
        font-weight: 500;
        color: #e2e8f0;
        margin-top: 15px;
        margin-bottom: 10px;
        padding-left: 5px;
        border-left: 3px solid #4299e1;
    }
    
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
    
    [data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #2d3748;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #e2e8f0;
    }
    
    [data-testid="stDataFrame"] {
        border: 1px solid #2d3748;
        border-radius: 6px;
        background-color: #1a1e2e;
    }
    
    .stTextInput input, .stSelectbox select, .stTextArea textarea {
        background-color: #1a1e2e;
        border-color: #2d3748;
        color: #f7fafc;
    }
    
    .stTextInput input:focus, .stSelectbox select:focus {
        border-color: #4299e1;
    }
    
    .streamlit-expanderHeader {
        background-color: #1a1e2e;
        color: #e2e8f0;
    }
    
    [data-testid="stMetricValue"] {
        color: #ffffff;
    }
    
    [data-testid="stMetricLabel"] {
        color: #a0aec0;
    }
    
    .stDataFrame {
        background-color: #1a1e2e;
    }
    
    .stAlert {
        background-color: #2d3748;
    }
    
    .stSelectbox div[data-baseweb="select"] {
        background-color: #1a1e2e;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    hr {
        border-color: #2d3748;
    }
    
    .stCaption, caption {
        color: #a0aec0;
    }
    
    .stCheckbox label span {
        color: #e2e8f0;
    }
    
    .stTabs [data-baseweb="tab-list"] button {
        background-color: #0d1117;
        color: #a0aec0;
    }
    
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #1a1e2e;
        color: #ffffff;
    }
    
    .stCheckbox label {
        color: #e2e8f0;
    }
    
    /* Botón flotante para descarga */
    .float-download {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 999;
    }
</style>
""", unsafe_allow_html=True)

# ========== BARRA SUPERIOR CON BOTÓN DE DESCARGA ==========
top_bar_col1, top_bar_col2 = st.columns([5, 1])
with top_bar_col2:
    # Verificar si existe el archivo .exe
    exe_link = get_desktop_app_download_link()
    if exe_link:
        st.markdown(f'''
        <div class="float-download">
            <a href="{exe_link}" class="download-btn" download>
                💻 Descargar versión escritorio
            </a>
        </div>
        ''', unsafe_allow_html=True)
    else:
        # Si no existe el archivo local, mostrar enlace a GitHub Releases
        st.markdown('''
        <div class="float-download">
            <a href="https://github.com/tuusuario/contador-pro/releases/latest" target="_blank" class="download-btn" style="background-color: #3498db;">
                💻 Versión escritorio
            </a>
        </div>
        ''', unsafe_allow_html=True)

# ========== CONEXIÓN A MONGODB ==========
MONGO_URI = st.secrets["MONGO_URI"]
DB_NAME = st.secrets["DB_NAME"]

def get_desktop_app_download_link():
    """Genera enlace de descarga directa del .exe"""
    # El archivo debe estar en la raíz del repositorio
    exe_path = "contaduria.exe"  # Cambia por el nombre exacto
    
    # Verificar si el archivo existe en el servidor
    if os.path.exists(exe_path):
        with open(exe_path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        # Enlace directo con data URI
        return f'data:application/octet-stream;base64,{b64}'
    return None

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

# ========== FUNCIONES DE REPORTES ==========

def generar_balance_general(edited_df, nombre_proyecto):
    """Genera un Balance General profesional con Activos, Pasivos y Capital"""
    
    activos = 0
    pasivos = 0
    capital = 0
    
    # Palabras clave por tipo de cuenta
    palabras_activo = ['activo', 'caja', 'banco', 'efectivo', 'inventario', 'mercadería', 
                       'cliente', 'cuenta por cobrar', 'deudor', 'propiedad', 'equipo', 
                       'vehículo', 'mueble', 'inmueble', 'depósito', 'iva crédito']
    
    palabras_pasivo = ['pasivo', 'proveedor', 'cuenta por pagar', 'acreedor', 'préstamo', 
                       'deuda', 'obligación', 'hipoteca', 'iva débito', 'salario por pagar', 
                       'impuesto por pagar', 'anticipo de cliente']
    
    palabras_capital = ['capital', 'patrimonio', 'utilidad retenida', 'reserva', 
                        'aporte', 'inversión', 'acción', 'resultado acumulado']
    
    if "Debe" in edited_df.columns and "Haber" in edited_df.columns:
        for idx, row in edited_df.iterrows():
            desc = str(row.get("Descripción", row.get("Cuenta", row.get("Concepto", "")))).lower()
            debe = row.get("Debe", 0) or 0
            haber = row.get("Haber", 0) or 0
            saldo_normal = debe - haber
            
            es_activo = any(p in desc for p in palabras_activo)
            es_pasivo = any(p in desc for p in palabras_pasivo)
            es_capital = any(p in desc for p in palabras_capital)
            
            if es_activo:
                activos += saldo_normal
            elif es_pasivo:
                pasivos += (haber - debe)
            elif es_capital:
                capital += (haber - debe)
            else:
                if saldo_normal > 0:
                    activos += saldo_normal
                else:
                    pasivos += abs(saldo_normal)
    
    total_pasivo_capital = pasivos + capital
    
    return {
        "activos": activos,
        "pasivos": pasivos, 
        "capital": capital,
        "total_pasivo_capital": total_pasivo_capital,
        "diferencia": activos - total_pasivo_capital,
        "fecha": datetime.now().strftime("%d/%m/%Y")
    }

def generar_estado_resultados(edited_df):
    """Genera Estado de Resultados con Ingresos, Gastos y Utilidad Neta"""
    
    ingresos = 0
    gastos = 0
    
    palabras_ingreso = ['ingreso', 'venta', 'ingresos', 'ventas', 'honorarios', 
                        'servicio', 'alquiler recibido', 'interés ganado', 
                        'comisión', 'utilidad', 'ingreso extraordinario']
    
    palabras_gasto = ['gasto', 'costo', 'compra', 'gastos', 'costo de venta', 
                      'alquiler pagado', 'sueldo', 'salario', 'servicio básico', 
                      'luz', 'agua', 'teléfono', 'internet', 'publicidad', 
                      'seguro', 'mantenimiento', 'depreciación', 'amortización',
                      'interés pagado', 'gasto bancario', 'impuesto', 'suministro']
    
    if "Debe" in edited_df.columns and "Haber" in edited_df.columns:
        for idx, row in edited_df.iterrows():
            desc = str(row.get("Descripción", row.get("Concepto", row.get("Cuenta", "")))).lower()
            debe = row.get("Debe", 0) or 0
            haber = row.get("Haber", 0) or 0
            
            es_ingreso = any(p in desc for p in palabras_ingreso)
            es_gasto = any(p in desc for p in palabras_gasto)
            
            if es_ingreso:
                ingresos += haber
            elif es_gasto:
                gastos += debe
            else:
                if haber > debe:
                    ingresos += haber
                elif debe > haber:
                    gastos += debe
    
    utilidad_neta = ingresos - gastos
    
    return {
        "ingresos": ingresos,
        "gastos": gastos,
        "utilidad_neta": utilidad_neta,
        "tipo": "Ganancia" if utilidad_neta > 0 else "Pérdida" if utilidad_neta < 0 else "Equilibrio",
        "margen": (utilidad_neta / ingresos * 100) if ingresos > 0 else 0,
        "fecha": datetime.now().strftime("%d/%m/%Y")
    }

def exportar_pdf_reporte(tipo, datos, nombre_proyecto):
    """Exporta reporte a PDF usando ReportLab"""
    
    if not REPORTLAB_AVAILABLE:
        # Fallback a HTML
        if tipo == "balance":
            html_content = f"""
            <html>
            <head><title>Balance General - {nombre_proyecto}</title></head>
            <body>
                <h1>BALANCE GENERAL</h1>
                <h2>{nombre_proyecto}</h2>
                <p>Fecha: {datos['fecha']}</p>
                <hr>
                <table border="1" cellpadding="8">
                    <tr><th>Concepto</th><th>Monto (USD)</th></tr>
                    <tr><td>ACTIVOS</td><td>${datos['activos']:,.2f}</td></tr>
                    <tr><td>PASIVOS</td><td>${datos['pasivos']:,.2f}</td></tr>
                    <tr><td>CAPITAL</td><td>${datos['capital']:,.2f}</td></tr>
                    <tr><td><b>TOTAL PASIVO + CAPITAL</b></td><td><b>${datos['total_pasivo_capital']:,.2f}</b></td></tr>
                    <tr><td><b>DIFERENCIA</b></td><td><b>${datos['diferencia']:,.2f}</b></td></tr>
                </table>
            </body>
            </html>
            """
            return BytesIO(html_content.encode())
        else:
            html_content = f"""
            <html>
            <head><title>Estado de Resultados - {nombre_proyecto}</title></head>
            <body>
                <h1>ESTADO DE RESULTADOS</h1>
                <h2>{nombre_proyecto}</h2>
                <p>Fecha: {datos['fecha']}</p>
                <hr>
                <table border="1" cellpadding="8">
                    <tr><th>Concepto</th><th>Monto (USD)</th><th>%</th></tr>
                    <tr><td>INGRESOS</td><td>${datos['ingresos']:,.2f}</td><td>100%</td></tr>
                    <tr><td>GASTOS</td><td>${datos['gastos']:,.2f}</td><td>{datos['gastos']/datos['ingresos']*100 if datos['ingresos'] > 0 else 0:.1f}%</td></tr>
                    <tr><td><b>UTILIDAD NETA</b></td><td><b>${datos['utilidad_neta']:,.2f}</b></td><td><b>{datos['margen']:.1f}%</b></td></tr>
                    <tr><td><b>RESULTADO</b></td><td colspan="2"><b>{datos['tipo']}</b></td></tr>
                </table>
            </body>
            </html>
            """
            return BytesIO(html_content.encode())
    
    # Si ReportLab está disponible
    buffer = BytesIO()
    
    if tipo == "balance":
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        titulo_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=16,
            textColor=colors.HexColor('#1a1e2e'),
            alignment=1,
            spaceAfter=30
        )
        
        elementos = []
        
        elementos.append(Paragraph(f"<b>BALANCE GENERAL</b>", titulo_style))
        elementos.append(Paragraph(f"{nombre_proyecto}", styles['Normal']))
        elementos.append(Paragraph(f"Fecha: {datos['fecha']}", styles['Normal']))
        elementos.append(Spacer(1, 0.2*inch))
        
        data = [
            ['Concepto', 'Monto (USD)'],
            ['ACTIVOS', f'${datos["activos"]:,.2f}'],
            ['', ''],
            ['PASIVOS', f'${datos["pasivos"]:,.2f}'],
            ['CAPITAL', f'${datos["capital"]:,.2f}'],
            ['', ''],
            ['TOTAL PASIVO + CAPITAL', f'${datos["total_pasivo_capital"]:,.2f}'],
            ['', ''],
            ['DIFERENCIA', f'${datos["diferencia"]:,.2f}']
        ]
        
        tabla = Table(data, colWidths=[4*inch, 2*inch])
        tabla.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        elementos.append(tabla)
        doc.build(elementos)
        
    elif tipo == "resultados":
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        titulo_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=16,
            textColor=colors.HexColor('#1a1e2e'),
            alignment=1,
            spaceAfter=30
        )
        
        elementos = []
        
        elementos.append(Paragraph(f"<b>ESTADO DE RESULTADOS</b>", titulo_style))
        elementos.append(Paragraph(f"{nombre_proyecto}", styles['Normal']))
        elementos.append(Paragraph(f"Fecha: {datos['fecha']}", styles['Normal']))
        elementos.append(Spacer(1, 0.2*inch))
        
        data = [
            ['Concepto', 'Monto (USD)', '%'],
            ['INGRESOS', f'${datos["ingresos"]:,.2f}', '100%'],
            ['GASTOS', f'${datos["gastos"]:,.2f}', f'{datos["gastos"]/datos["ingresos"]*100 if datos["ingresos"] > 0 else 0:.1f}%'],
            ['', '', ''],
            ['UTILIDAD NETA', f'${datos["utilidad_neta"]:,.2f}', f'{datos["margen"]:.1f}%'],
            ['', '', ''],
            ['RESULTADO', datos["tipo"], '']
        ]
        
        tabla = Table(data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        tabla.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        elementos.append(tabla)
        doc.build(elementos)
    
    buffer.seek(0)
    return buffer

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
                    
                    if get_usuarios().find_one({"email": reg_email}):
                        st.error("El email ya está registrado")
                    else:
                        nuevo_usuario = {
                            "email": reg_email,
                            "password": password_hash,
                            "nombre": reg_nombre,
                            "creado_en": datetime.now()
                        }
                        try:
                            get_usuarios().insert_one(nuevo_usuario)
                            st.success("Cuenta creada exitosamente. Ahora puede iniciar sesión.")
                        except Exception as e:
                            st.error(f"Error al crear cuenta: {e}")
                else:
                    st.error("Las contraseñas no coinciden o son muy cortas (mínimo 6 caracteres)")
    
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
        
        email_usuario = st.session_state.usuario["email"]
        proyectos = list(get_proyectos().find({"email_usuario": email_usuario}))
        
        if proyectos:
            for proy in proyectos:
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(f"{proy['nombre']}", key=f"proy_{proy['nombre']}_{proy['_id']}", use_container_width=True):
                        proy["_id"] = str(proy["_id"])
                        st.session_state.proyecto_actual = proy
                        st.rerun()
                with col2:
                    if st.button("⌫", key=f"del_{proy['nombre']}_{proy['_id']}"):
                        st.session_state[f"confirmar_del_{proy['_id']}"] = True
                    
                    if st.session_state.get(f"confirmar_del_{proy['_id']}", False):
                        st.caption("¿Eliminar?")
                        col_confirm, col_cancel = st.columns(2)
                        with col_confirm:
                            if st.button("✓", key=f"confirm_{proy['_id']}"):
                                get_proyectos().delete_one({"_id": proy["_id"]})
                                st.session_state[f"confirmar_del_{proy['_id']}"] = False
                                if st.session_state.proyecto_actual and st.session_state.proyecto_actual.get("_id") == str(proy["_id"]):
                                    st.session_state.proyecto_actual = None
                                st.rerun()
                        with col_cancel:
                            if st.button("✗", key=f"cancel_{proy['_id']}"):
                                st.session_state[f"confirmar_del_{proy['_id']}"] = False
                                st.rerun()
        else:
            st.caption("No hay proyectos. Cree uno nuevo.")
        
        st.divider()
        
        st.markdown('<p style="font-weight: 600; margin-bottom: 10px; color: #e2e8f0;">Nuevo proyecto</p>', unsafe_allow_html=True)
        nuevo_nombre = st.text_input("Nombre del proyecto", key="nuevo_nombre", placeholder="Ej: Cliente ABC")
        nuevo_tipo = st.selectbox("Plantilla", ["Libro Diario", "Balanza de Comprobación", "Cuentas T"], key="nuevo_tipo")
        
        if st.button("Crear proyecto", use_container_width=True):
            if nuevo_nombre:
                existe = get_proyectos().find_one({
                    "nombre": nuevo_nombre,
                    "email_usuario": email_usuario
                })
                
                if existe:
                    st.error(f"Ya existe un proyecto con el nombre '{nuevo_nombre}'")
                else:
                    columnas_tipo = {
                        "Libro Diario": ["Fecha", "Descripción", "Cuenta", "Debe", "Haber", "IVA %"],
                        "Balanza de Comprobación": ["Código", "Cuenta", "Saldo Inicial", "Cargos", "Abonos", "Saldo Final"],
                        "Cuentas T": ["Fecha", "Concepto", "Referencia", "Debe", "Haber", "Saldo"]
                    }
                    
                    nuevo_proyecto = {
                        "nombre": nuevo_nombre,
                        "tipo": nuevo_tipo,
                        "datos": [],
                        "columnas": columnas_tipo[nuevo_tipo],
                        "email_usuario": email_usuario,
                        "creado_en": datetime.now(),
                        "ultima_modificacion": datetime.now()
                    }
                    
                    try:
                        resultado = get_proyectos().insert_one(nuevo_proyecto)
                        st.success(f"Proyecto '{nuevo_nombre}' creado exitosamente")
                        nuevo_proyecto["_id"] = str(resultado.inserted_id)
                        st.session_state.proyecto_actual = nuevo_proyecto
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al crear proyecto: {e}")
            else:
                st.warning("Ingrese un nombre para el proyecto")

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
        st.markdown("---")
        st.markdown('<div class="section-header"> Herramientas de cálculo</div>', unsafe_allow_html=True)

        col_calc1, col_calc2, col_calc3, col_calc4 = st.columns(4)

        with col_calc1:
            if st.button("Nueva columna fórmula", use_container_width=True):
                df = mostrar_gestor_formulas(edited_df)
                edited_df = df

        with col_calc2:
            if st.button("Calculadora rápida", use_container_width=True):
                df = mostrar_calculadora_rapida(edited_df)
                edited_df = df

        with col_calc3:
            if st.button("Ver estadísticas", use_container_width=True):
                df = mostrar_totales_columnas(edited_df)
                edited_df = df

        with col_calc4:
            if st.button("Agregar columna vacía", use_container_width=True):
                nueva_col = st.text_input("Nombre nueva columna", key="temp_new_col")
                if nueva_col:
                    edited_df[nueva_col] = ""
                    st.success(f"Columna '{nueva_col}' agregada")
                    st.rerun()
    )

    
    # ========== BOTONES DE ACCIÓN CORREGIDOS ==========
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])
    
    with col1:
        if st.button("Guardar", use_container_width=True, key="btn_guardar"):
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
    
    with col2:
        if st.button("Exportar Excel", use_container_width=True, key="btn_excel"):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                edited_df.to_excel(writer, sheet_name=proyecto["nombre"], index=False)
            st.download_button(
                label="Descargar",
                data=output.getvalue(),
                file_name=f"{proyecto['nombre']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="download_excel_btn"
            )
    
    with col3:
        if st.button("Balance General", use_container_width=True, key="btn_balance"):
            if len(edited_df) > 0:
                with st.spinner("Generando Balance General..."):
                    balance = generar_balance_general(edited_df, proyecto["nombre"])
                    pdf_buffer = exportar_pdf_reporte("balance", balance, proyecto["nombre"])
                    st.download_button(
                        label="📥 Descargar PDF",
                        data=pdf_buffer,
                        file_name=f"Balance_{proyecto['nombre']}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="download_balance_btn"
                    )
            else:
                st.warning("No hay datos para generar el Balance General")
    
    with col4:
        if st.button("Estado Resultados", use_container_width=True, key="btn_resultados"):
            if len(edited_df) > 0:
                with st.spinner("Generando Estado de Resultados..."):
                    resultados = generar_estado_resultados(edited_df)
                    pdf_buffer = exportar_pdf_reporte("resultados", resultados, proyecto["nombre"])
                    st.download_button(
                        label="📥 Descargar PDF",
                        data=pdf_buffer,
                        file_name=f"Resultados_{proyecto['nombre']}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="download_resultados_btn"
                    )
            else:
                st.warning("No hay datos para generar el Estado de Resultados")
    
    with col5:
        if st.button("Eliminar proyecto", use_container_width=True, key="btn_eliminar"):
            st.session_state.confirmar_eliminar = True
        
        if st.session_state.confirmar_eliminar:
            st.warning("¿Eliminar este proyecto permanentemente?")
            col_conf, col_canc = st.columns(2)
            with col_conf:
                if st.button("Sí, eliminar", use_container_width=True):
                    try:
                        get_proyectos().delete_one({"_id": proyecto["_id"]})
                        st.session_state.proyecto_actual = None
                        st.session_state.confirmar_eliminar = False
                        st.success("Proyecto eliminado")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al eliminar: {e}")
            with col_canc:
                if st.button("Cancelar", use_container_width=True):
                    st.session_state.confirmar_eliminar = False
                    st.rerun()
    
    # Métricas
    st.divider()
    st.markdown('<div class="section-header">Resumen del período</div>', unsafe_allow_html=True)
    
    col_met1, col_met2, col_met3, col_met4 = st.columns(4)
    
    total_debe = edited_df["Debe"].sum() if "Debe" in edited_df.columns and len(edited_df) > 0 else 0
    total_haber = edited_df["Haber"].sum() if "Haber" in edited_df.columns and len(edited_df) > 0 else 0
    diferencia = total_debe - total_haber
    
    with col_met1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Debe</div>
            <div class="metric-value">${total_debe:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_met2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Haber</div>
            <div class="metric-value">${total_haber:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_met3:
        color = "#27ae60" if abs(diferencia) < 0.01 else "#e74c3c"
        estado_texto = "Balanceado" if abs(diferencia) < 0.01 else "Desbalanceado"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Estado contable</div>
            <div class="metric-value" style="color: {color};">{estado_texto}</div>
            <div style="font-size: 12px; color: #94a3b8;">Diferencia: ${diferencia:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_met4:
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
                    
                elif tipo_grafica == "Líneas - Evolución":
                    st.line_chart(
                        df_graf[["Debe", "Haber"]].fillna(0),
                        x_label="Registro",
                        y_label="Monto (USD)"
                    )
                    st.caption("Evolución de movimientos contables")
                    
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
                    plt.close()
                    
                else:
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
                        plt.close()
                    else:
                        st.info("Agregue una columna 'Cuenta' para ver distribución por cuentas")
            
            with col_graf2:
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


# ========== SISTEMA DE FÓRMULAS Y COLUMNAS DINÁMICAS ==========

class FormulaEngine:
    """Motor de fórmulas para la tabla contable"""
    
    @staticmethod
    def evaluar_formula(formula, df, columna_actual=None):
        """Evalúa una fórmula estilo Excel"""
        try:
            # Limpiar la fórmula
            formula = str(formula).strip()
            if not formula.startswith('='):
                return None
            
            # Quitar el signo =
            expr = formula[1:].strip()
            
            # Reemplazar referencias a columnas (ej: [Debe] + [Haber])
            import re
            
            def replace_column(match):
                col_name = match.group(1)
                if col_name in df.columns:
                    # Retornar la serie de pandas
                    return f"df['{col_name}']"
                return match.group(0)
            
            # Buscar patrones [NombreColumna]
            expr = re.sub(r'\[([^\]]+)\]', replace_column, expr)
            
            # Operaciones matemáticas básicas
            # Permitir: +, -, *, /, %, **
            safe_dict = {
                'df': df,
                'sum': sum,
                'mean': lambda x: sum(x)/len(x) if len(x) > 0 else 0,
                'max': max,
                'min': min,
                'abs': abs,
                'round': round,
                'len': len,
                '__builtins__': {}
            }
            
            # Ejecutar la expresión
            result = eval(expr, safe_dict)
            
            # Si el resultado es una serie, aplicarla fila por fila
            if hasattr(result, 'iloc'):
                return result
            return result
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    @staticmethod
    def aplicar_formula_columna(df, nombre_columna, formula, por_fila=True):
        """Aplica una fórmula a toda una columna"""
        try:
            if por_fila:
                # Aplicar fórmula fila por fila
                resultados = []
                for idx, row in df.iterrows():
                    # Crear un DataFrame de una sola fila para la evaluación
                    temp_df = pd.DataFrame([row.to_dict()])
                    resultado = FormulaEngine.evaluar_formula(formula, temp_df)
                    if isinstance(resultado, (int, float)):
                        resultados.append(resultado)
                    elif hasattr(resultado, 'iloc'):
                        resultados.append(resultado.iloc[0])
                    else:
                        resultados.append(resultado)
                
                df[nombre_columna] = resultados
            else:
                # Aplicar fórmula a toda la columna (sumas totales, etc)
                resultado = FormulaEngine.evaluar_formula(formula, df)
                if isinstance(resultado, (int, float)):
                    df[nombre_columna] = resultado
                elif hasattr(resultado, '__len__') and len(resultado) == len(df):
                    df[nombre_columna] = resultado
            
            return df
        except Exception as e:
            st.error(f"Error al aplicar fórmula: {e}")
            return df
    
    @staticmethod
    def sugerir_formulas(df):
        """Sugiere fórmulas comunes basadas en las columnas"""
        sugerencias = []
        
        if 'Debe' in df.columns and 'Haber' in df.columns:
            sugerencias.append({
                'nombre': 'Saldo',
                'formula': '=[Debe] - [Haber]',
                'descripcion': 'Calcula la diferencia entre Debe y Haber'
            })
            sugerencias.append({
                'nombre': 'Total Movimiento',
                'formula': '=[Debe] + [Haber]',
                'descripcion': 'Suma de Debe y Haber'
            })
            
        if 'IVA %' in df.columns and 'Debe' in df.columns:
            sugerencias.append({
                'nombre': 'IVA Calculado',
                'formula': '=[Debe] * ([IVA %] / 100)',
                'descripcion': 'Calcula el IVA basado en el porcentaje'
            })
        
        if 'Cantidad' in df.columns and 'Precio' in df.columns:
            sugerencias.append({
                'nombre': 'Subtotal',
                'formula': '=[Cantidad] * [Precio]',
                'descripcion': 'Multiplica cantidad por precio'
            })
        
        # Fórmulas de totales
        sugerencias.append({
            'nombre': 'Total General',
            'formula': 'sum([Debe])',
            'descripcion': 'Suma total de la columna Debe',
            'es_total': True
        })
        
        sugerencias.append({
            'nombre': 'Promedio Debe',
            'formula': 'mean([Debe])',
            'descripcion': 'Promedio de la columna Debe',
            'es_total': True
        })
        
        return sugerencias

def mostrar_gestor_formulas(df):
    """Interfaz para gestionar fórmulas"""
    
    st.markdown("### Gestor de Fórmulas")
    
    tab1, tab2, tab3 = st.tabs([" Nueva Columna", " Aplicar Fórmula", "💡 Sugerencias"])
    
    with tab1:
        st.markdown("#### Crear nueva columna calculada")
        nueva_col = st.text_input("Nombre de la nueva columna", key="nueva_col_nombre")
        
        col1_f, col2_f = st.columns(2)
        with col1_f:
            formula_ejemplo = st.text_area(
                "Fórmula (ej: =[Debe] - [Haber])", 
                key="formula_nueva_col",
                placeholder="Ejemplos:\n=[Debe] + [Haber]\n=[Debe] * 1.21\n=sum([Debe])\n=mean([Debe])"
            )
        with col2_f:
            st.markdown("**Referencia de columnas disponibles:**")
            for col in df.columns:
                st.code(f"[{col}]", language="text")
            st.caption("Operadores: +, -, *, /, %")
            st.caption("Funciones: sum(), mean(), max(), min(), abs(), round()")
        
        if st.button("Crear columna calculada", key="btn_crear_columna"):
            if nueva_col and formula_ejemplo:
                if nueva_col in df.columns:
                    st.warning(f"La columna '{nueva_col}' ya existe")
                else:
                    df_temp = df.copy()
                    if formula_ejemplo.startswith('='):
                        # Determinar si es fórmula fila por fila o total
                        if any(func in formula_ejemplo for func in ['sum(', 'mean(', 'max(', 'min(']):
                            # Fórmula total (un solo valor para toda la columna)
                            resultado = FormulaEngine.evaluar_formula(formula_ejemplo, df_temp)
                            if isinstance(resultado, (int, float)):
                                df_temp[nueva_col] = resultado
                                st.success(f"Columna '{nueva_col}' creada con valor constante: {resultado}")
                            else:
                                df_temp[nueva_col] = resultado
                        else:
                            # Fórmula fila por fila
                            df_temp = FormulaEngine.aplicar_formula_columna(df_temp, nueva_col, formula_ejemplo, por_fila=True)
                            st.success(f"Columna '{nueva_col}' creada exitosamente")
                        
                        return df_temp
                    else:
                        st.error("Las fórmulas deben comenzar con '='")
            else:
                st.warning("Complete todos los campos")
    
    with tab2:
        st.markdown("#### Aplicar fórmula a columna existente")
        columna_existente = st.selectbox("Seleccionar columna", df.columns.tolist() if len(df.columns) > 0 else ["No hay columnas"])
        
        formula_aplicar = st.text_area(
            "Fórmula", 
            key="formula_aplicar",
            placeholder=f"Ejemplo para modificar '{columna_existente}':\n=[Debe] * 1.21\n=[Debe] + [Haber]\n=abs([{columna_existente}])"
        )
        
        if st.button("Aplicar fórmula", key="btn_aplicar_formula"):
            if formula_aplicar.startswith('='):
                df_temp = df.copy()
                df_temp = FormulaEngine.aplicar_formula_columna(df_temp, columna_existente, formula_aplicar, por_fila=True)
                st.success(f"Fórmula aplicada a '{columna_existente}'")
                return df_temp
            else:
                st.error("Las fórmulas deben comenzar con '='")
    
    with tab3:
        st.markdown("#### Fórmulas sugeridas")
        sugerencias = FormulaEngine.sugerir_formulas(df)
        
        if sugerencias:
            for sug in sugerencias:
                with st.expander(f"📊 {sug['nombre']} - {sug['descripcion']}"):
                    st.code(sug['formula'], language="text")
                    if st.button(f"Usar {sug['nombre']}", key=f"usar_{sug['nombre']}"):
                        df_temp = df.copy()
                        if sug.get('es_total', False):
                            resultado = FormulaEngine.evaluar_formula(sug['formula'], df_temp)
                            st.info(f"Resultado: {resultado}")
                        else:
                            df_temp = FormulaEngine.aplicar_formula_columna(df_temp, sug['nombre'], sug['formula'], por_fila=True)
                            st.success(f"Columna '{sug['nombre']}' agregada")
                        return df_temp
        else:
            st.info("No hay sugerencias disponibles con las columnas actuales")
            st.markdown("**Para obtener sugerencias, asegúrate de tener columnas como:**")
            st.markdown("- Debe y Haber (para saldos)")
            st.markdown("- Cantidad y Precio (para subtotales)")
            st.markdown("- IVA % (para cálculo de impuestos)")
    
    return df  # Devolver el df sin cambios si no se aplicó nada

def mostrar_calculadora_rapida(df):
    """Calculadora rápida para operaciones entre columnas"""
    
    with st.expander("🔢 Calculadora rápida"):
        st.markdown("#### Operaciones entre columnas")
        
        col_calc1, col_calc2, col_calc3 = st.columns(3)
        
        with col_calc1:
            columna_a = st.selectbox("Columna A", df.columns.tolist(), key="calc_col_a")
        with col_calc2:
            operacion = st.selectbox("Operación", ["+", "-", "*", "/", "%"], key="calc_op")
        with col_calc3:
            columna_b = st.selectbox("Columna B", ["(Constante)"] + df.columns.tolist(), key="calc_col_b")
        
        if columna_b == "(Constante)":
            valor_constante = st.number_input("Valor constante", value=0.0, step=0.01, key="calc_constante")
            resultado_nombre = st.text_input("Nombre resultado", value=f"{columna_a}_{operacion}_constante", key="calc_resultado_nombre")
            
            if st.button("Calcular", key="btn_calcular"):
                df_temp = df.copy()
                if operacion == "+":
                    df_temp[resultado_nombre] = df_temp[columna_a] + valor_constante
                elif operacion == "-":
                    df_temp[resultado_nombre] = df_temp[columna_a] - valor_constante
                elif operacion == "*":
                    df_temp[resultado_nombre] = df_temp[columna_a] * valor_constante
                elif operacion == "/":
                    df_temp[resultado_nombre] = df_temp[columna_a] / valor_constante if valor_constante != 0 else 0
                elif operacion == "%":
                    df_temp[resultado_nombre] = df_temp[columna_a] * (valor_constante / 100)
                
                st.success(f"Columna '{resultado_nombre}' creada")
                return df_temp
        else:
            resultado_nombre = st.text_input("Nombre resultado", value=f"{columna_a}_{operacion}_{columna_b}", key="calc_resultado_nombre2")
            
            if st.button("Calcular", key="btn_calcular2"):
                df_temp = df.copy()
                if operacion == "+":
                    df_temp[resultado_nombre] = df_temp[columna_a] + df_temp[columna_b]
                elif operacion == "-":
                    df_temp[resultado_nombre] = df_temp[columna_a] - df_temp[columna_b]
                elif operacion == "*":
                    df_temp[resultado_nombre] = df_temp[columna_a] * df_temp[columna_b]
                elif operacion == "/":
                    df_temp[resultado_nombre] = df_temp[columna_a] / df_temp[columna_b].replace(0, 1)
                elif operacion == "%":
                    df_temp[resultado_nombre] = (df_temp[columna_a] / df_temp[columna_b].replace(0, 1)) * 100
                
                st.success(f"Columna '{resultado_nombre}' creada")
                return df_temp
        
        # Mostrar porcentajes
        st.markdown("---")
        st.markdown("#### Porcentajes")
        
        col_porc1, col_porc2 = st.columns(2)
        with col_porc1:
            col_porcentaje = st.selectbox("Columna base", df.columns.tolist(), key="porc_col")
        with col_porc2:
            porcentaje_aplicar = st.number_input("Porcentaje %", value=21.0, step=1.0, key="porc_valor")
        
        if st.button("Calcular porcentaje", key="btn_porcentaje"):
            df_temp = df.copy()
            col_nueva = f"{col_porcentaje}_{porcentaje_aplicar}%"
            df_temp[col_nueva] = df_temp[col_porcentaje] * (porcentaje_aplicar / 100)
            st.success(f"Columna '{col_nueva}' creada")
            return df_temp
    
    return df

def mostrar_totales_columnas(df):
    """Muestra totales, promedios y estadísticas de columnas numéricas"""
    
    with st.expander("📊 Estadísticas de columnas"):
        # Identificar columnas numéricas
        columnas_numericas = df.select_dtypes(include=['number']).columns.tolist()
        
        if columnas_numericas:
            stats_data = []
            for col in columnas_numericas:
                stats_data.append({
                    "Columna": col,
                    "Suma": df[col].sum(),
                    "Promedio": df[col].mean(),
                    "Mínimo": df[col].min(),
                    "Máximo": df[col].max(),
                    "Mediana": df[col].median(),
                })
            
            stats_df = pd.DataFrame(stats_data)
            st.dataframe(stats_df, use_container_width=True)
            
            # Opción de crear columna con total
            if st.button("➕ Agregar fila de totales", key="btn_totales"):
                df_temp = df.copy()
                total_row = {}
                for col in columnas_numericas:
                    total_row[col] = df_temp[col].sum()
                for col in df_temp.columns:
                    if col not in total_row:
                        total_row[col] = "TOTAL"
                df_temp.loc[len(df_temp)] = total_row
                st.success("Fila de totales agregada")
                return df_temp
        else:
            st.info("No hay columnas numéricas para mostrar estadísticas")
    
    return df
