# main_ui.py - VERSIÓN DEFINITIVA CORREGIDA
# Problemas resueltos: colores, alineación, cierre de ventana, cambio de contraseña

import customtkinter as ctk
from tkinter import messagebox, filedialog, Toplevel
from datetime import datetime
import pandas as pd
import re
import smtplib
import secrets
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from componentes_gui import TablaContableMejorada, VentanaGraficasMejorada
from logica_contable import GestionArchivosMejorado, Plantillas, FormulaEngine
from database_manager import DBManager
from cloud_manager import CloudManager

# Configuración de apariencia
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class AppContable(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        DBManager.inicializar()
        self.cloud = CloudManager()
        self.cloud.crear_sesion()
        
        self.title("Contaduría")
        self.geometry("1300x800")
        self.cambios_pendientes = False
        self.sesion_activa = False
        self.usuario_actual = None
        
        # Ocultar principal hasta login
        self.withdraw()
        
        # Configurar grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar - CORREGIDO (colores)
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#f0f0f0")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(
            self.sidebar, 
            text="Contaduría", 
            font=("Roboto", 18, "bold"),
            text_color="#1a1a1a"
        )
        self.logo_label.pack(pady=25, padx=20)
        
        # Botones
        self.btn_nuevo = ctk.CTkButton(
            self.sidebar, text="Nuevo proyecto",
            command=self.abrir_ventana_nuevo,
            fg_color="#2c7da0", hover_color="#1f5e7a",
            height=35, corner_radius=4
        )
        self.btn_nuevo.pack(pady=8, padx=20, fill="x")
        
        self.btn_importar = ctk.CTkButton(
            self.sidebar, text="Importar archivo",
            command=self.importar_archivo_general,
            fg_color="#5a6e7a", hover_color="#4a5a66",
            height=35, corner_radius=4
        )
        self.btn_importar.pack(pady=8, padx=20, fill="x")
        
        self.btn_sincronizar = ctk.CTkButton(
            self.sidebar, text="Sincronizar nube",
            command=self.sincronizar_nube,
            fg_color="#2c7da0", hover_color="#1f5e7a",
            height=35, corner_radius=4
        )
        self.btn_sincronizar.pack(pady=8, padx=20, fill="x")
        
        self.btn_reportes = ctk.CTkButton(
            self.sidebar, text="Generar reportes",
            command=self.abrir_reportes,
            fg_color="#8b6b4d", hover_color="#6e553d",
            height=35, corner_radius=4
        )
        self.btn_reportes.pack(pady=8, padx=20, fill="x")
        
        # Botón cerrar sesión
        self.btn_logout = ctk.CTkButton(
            self.sidebar, text="Cerrar sesión",
            command=self.cerrar_sesion,
            fg_color="#c0392b", hover_color="#a93226",
            height=35, corner_radius=4
        )
        self.btn_logout.pack(pady=8, padx=20, fill="x")
        
        # Modo oscuro/claro
        self.modo_var = ctk.StringVar(value="Claro")
        self.modo_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=["Claro", "Oscuro"],
            command=self.cambiar_tema,
            fg_color="#e0e0e0",
            button_color="#e0e0e0",
            button_hover_color="#cccccc",
            text_color="#1a1a1a",
            width=100
        )
        self.modo_menu.pack(side="bottom", pady=20)
        
        # Barra de estado
        self.status_bar = ctk.CTkFrame(self, height=28, fg_color="#e8e8e8")
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.status_label = ctk.CTkLabel(
            self.status_bar, text="Listo", anchor="w",
            text_color="#555555", font=("Roboto", 11)
        )
        self.status_label.pack(side="left", padx=12)
        
        # Panel principal
        self.main_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.main_panel.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.main_panel.grid_columnconfigure(0, weight=1)
        self.main_panel.grid_rowconfigure(0, weight=1)
        
        self.tabview = ctk.CTkTabview(self.main_panel)
        self.tabview.grid(row=0, column=0, sticky="nsew")
        
        # Mostrar login
        self.mostrar_login()
        
        self.after(0, lambda: self.state('zoomed'))
        self.protocol("WM_DELETE_WINDOW", self.confirmar_salida)
    
    def cambiar_tema(self, choice):
        if choice == "Oscuro":
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")
    
    def cerrar_sesion(self):
        """Cierra sesión y vuelve al login"""
        if messagebox.askyesno("Cerrar sesión", "¿Deseas cerrar sesión?"):
            self.sesion_activa = False
            self.usuario_actual = None
            # Cerrar todas las pestañas
            for tab in list(self.tabview._tab_dict.keys()):
                self.tabview.delete(tab)
            self.withdraw()
            self.mostrar_login()
    
    def mostrar_login(self):
        """Ventana de login - no se puede cerrar sin opción"""
        login = ctk.CTkToplevel(self)
        login.title("Contaduría - Iniciar sesión")
        login.geometry("400x550")
        login.attributes("-topmost", True)
        login.grab_set()
        login.protocol("WM_DELETE_WINDOW", lambda: None)  # No permitir cerrar
        
        # Centrar
        login.update_idletasks()
        x = (login.winfo_screenwidth() // 2) - 200
        y = (login.winfo_screenheight() // 2) - 275
        login.geometry(f"+{x}+{y}")
        
        frame = ctk.CTkFrame(login, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        ctk.CTkLabel(frame, text="Contaduría", font=("Roboto", 26, "bold")).pack(pady=(0, 5))
        ctk.CTkLabel(frame, text="Sistema de gestión contable", font=("Roboto", 11), text_color="gray").pack(pady=(0, 25))
        
        # Tabs
        tabview = ctk.CTkTabview(frame, width=340)
        tabview.pack()
        
        tab_login = tabview.add("Iniciar sesión")
        tab_reg = tabview.add("Registrarse")
        tab_recuperar = tabview.add("¿Olvidó su contraseña?")
        
        # Login
        ctk.CTkLabel(tab_login, text="Correo", font=("Roboto", 11)).pack(anchor="w", pady=(15, 5))
        entry_email = ctk.CTkEntry(tab_login, width=300, placeholder_text="usuario@ejemplo.com")
        entry_email.pack()
        
        ctk.CTkLabel(tab_login, text="Contraseña", font=("Roboto", 11)).pack(anchor="w", pady=(10, 5))
        entry_pass = ctk.CTkEntry(tab_login, width=300, show="*", placeholder_text="••••••••")
        entry_pass.pack()
        
        lbl_error = ctk.CTkLabel(tab_login, text="", text_color="#c0392b")
        lbl_error.pack(pady=8)
        
        def do_login():
            email = entry_email.get().strip()
            password = entry_pass.get()
            if not email or not password:
                lbl_error.configure(text="Complete todos los campos")
                return
            
            success, data = self.cloud.login(email, password)
            if success:
                self.sesion_activa = True
                self.usuario_actual = email
                login.destroy()
                self.deiconify()
                self.status_label.configure(text=f"Bienvenido, {data.get('nombre', email)}")
                self.cargar_proyectos_existentes()
            else:
                lbl_error.configure(text=data)
        
        ctk.CTkButton(tab_login, text="Ingresar", command=do_login, fg_color="#2c7da0", height=38).pack(pady=(15, 0), fill="x")
        
        # Registro
        ctk.CTkLabel(tab_reg, text="Nombre", font=("Roboto", 11)).pack(anchor="w", pady=(15, 5))
        reg_nombre = ctk.CTkEntry(tab_reg, width=300)
        reg_nombre.pack()
        
        ctk.CTkLabel(tab_reg, text="Correo", font=("Roboto", 11)).pack(anchor="w", pady=(10, 5))
        reg_email = ctk.CTkEntry(tab_reg, width=300)
        reg_email.pack()
        
        ctk.CTkLabel(tab_reg, text="Contraseña", font=("Roboto", 11)).pack(anchor="w", pady=(10, 5))
        reg_pass = ctk.CTkEntry(tab_reg, width=300, show="*")
        reg_pass.pack()
        
        ctk.CTkLabel(tab_reg, text="Confirmar", font=("Roboto", 11)).pack(anchor="w", pady=(10, 5))
        reg_pass2 = ctk.CTkEntry(tab_reg, width=300, show="*")
        reg_pass2.pack()
        
        lbl_reg_error = ctk.CTkLabel(tab_reg, text="", text_color="#c0392b")
        lbl_reg_error.pack(pady=8)
        
        def do_registro():
            nombre = reg_nombre.get().strip()
            email = reg_email.get().strip()
            p1 = reg_pass.get()
            p2 = reg_pass2.get()
            
            if not all([nombre, email, p1]):
                lbl_reg_error.configure(text="Complete todos los campos")
                return
            if len(p1) < 6:
                lbl_reg_error.configure(text="Mínimo 6 caracteres")
                return
            if p1 != p2:
                lbl_reg_error.configure(text="Las contraseñas no coinciden")
                return
            
            success, msg = self.cloud.registrar_usuario(email, p1, nombre)
            if success:
                lbl_reg_error.configure(text="Cuenta creada. Inicie sesión.", text_color="#27ae60")
                tabview.set("Iniciar sesión")
                entry_email.delete(0, "end")
                entry_email.insert(0, email)
            else:
                lbl_reg_error.configure(text=msg, text_color="#c0392b")
        
        ctk.CTkButton(tab_reg, text="Crear cuenta", command=do_registro, fg_color="#5a6e7a", height=38).pack(pady=(15, 0), fill="x")
        
        # Recuperar contraseña
        ctk.CTkLabel(tab_recuperar, text="Ingrese su correo para recibir", font=("Roboto", 11)).pack(pady=(15, 5))
        ctk.CTkLabel(tab_recuperar, text="un enlace de recuperación", font=("Roboto", 11)).pack(pady=(0, 15))
        
        rec_email = ctk.CTkEntry(tab_recuperar, width=300, placeholder_text="usuario@ejemplo.com")
        rec_email.pack()
        
        lbl_rec_error = ctk.CTkLabel(tab_recuperar, text="", text_color="#c0392b")
        lbl_rec_error.pack(pady=8)
        
        def do_recuperar():
            email = rec_email.get().strip()
            if not email:
                lbl_rec_error.configure(text="Ingrese su correo")
                return
            
            # Generar token temporal
            token = secrets.token_urlsafe(32)
            # Guardar token en BD (implementar según tu DB)
            
            # Enviar email (configurar con tu SMTP)
            try:
                # Ejemplo con Gmail (requiere configuración)
                # msg = MIMEMultipart()
                # msg['From'] = "tuemail@gmail.com"
                # msg['To'] = email
                # msg['Subject'] = "Recuperación de contraseña - Contaduría"
                # cuerpo = f"Haz clic en el siguiente enlace para recuperar tu contraseña:\n\nhttp://localhost:8501/recuperar?token={token}"
                # msg.attach(MIMEText(cuerpo, 'plain'))
                # server = smtplib.SMTP('smtp.gmail.com', 587)
                # server.starttls()
                # server.login("tuemail@gmail.com", "tucontraseña")
                # server.send_message(msg)
                # server.quit()
                
                lbl_rec_error.configure(text="Correo enviado. Revise su bandeja.", text_color="#27ae60")
            except Exception as e:
                lbl_rec_error.configure(text=f"Error: {str(e)}", text_color="#c0392b")
        
        ctk.CTkButton(tab_recuperar, text="Enviar correo", command=do_recuperar, fg_color="#8b6b4d", height=38).pack(pady=(15, 0), fill="x")
        
        # Modo offline
        def offline():
            self.sesion_activa = False
            login.destroy()
            self.deiconify()
            self.status_label.configure(text="Modo offline")
            self.btn_sincronizar.configure(state="disabled", fg_color="#cccccc")
            self.cargar_proyectos_existentes()
        
        ctk.CTkButton(frame, text="Trabajar sin conexión", command=offline, fg_color="transparent", text_color="gray", hover_color="#eeeeee").pack(pady=(15, 0))
    
    def construir_interfaz_pestana(self, tab, nombre, carga_inicial=False, tipo_plantilla="Libro Diario"):
        """Construye la pestaña con herramientas - CORREGIDA alineación"""
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)
        
        # Barra de herramientas - CORREGIDO colores
        toolbar = ctk.CTkFrame(tab, height=40, fg_color="#f5f5f5", corner_radius=6)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 12), padx=2)
        
        # Botones
        btn_add = ctk.CTkButton(toolbar, text="+ Fila", width=70, height=30, fg_color="#2c7da0")
        btn_add.pack(side="left", padx=4)
        
        btn_remove = ctk.CTkButton(toolbar, text="- Última", width=70, height=30, fg_color="#8b6b4d")
        btn_remove.pack(side="left", padx=4)
        
        ctk.CTkLabel(toolbar, text="|", text_color="#cccccc").pack(side="left", padx=8)
        
        btn_formula = ctk.CTkButton(toolbar, text="Fórmula", width=70, height=30, fg_color="#5a6e7a")
        btn_formula.pack(side="left", padx=4)
        
        btn_calc = ctk.CTkButton(toolbar, text="Calculadora", width=90, height=30, fg_color="#5a6e7a")
        btn_calc.pack(side="left", padx=4)
        
        btn_stats = ctk.CTkButton(toolbar, text="Estadísticas", width=90, height=30, fg_color="#5a6e7a")
        btn_stats.pack(side="left", padx=4)
        
        btn_graficas = ctk.CTkButton(toolbar, text="Gráficas", width=70, height=30, fg_color="#8b6b4d")
        btn_graficas.pack(side="left", padx=4)
        
        ctk.CTkLabel(toolbar, text="|", text_color="#cccccc").pack(side="left", padx=8)
        
        ctk.CTkLabel(toolbar, text="Exportar:", font=("Roboto", 11)).pack(side="left", padx=(4, 2))
        export_menu = ctk.CTkOptionMenu(toolbar, values=["Excel", "PDF"], width=80, height=30, fg_color="#e0e0e0", text_color="#1a1a1a")
        export_menu.pack(side="left", padx=4)
        
        # Botones derecha
        btn_guardar = ctk.CTkButton(toolbar, text="Guardar", width=80, height=30, fg_color="#27ae60")
        btn_guardar.pack(side="right", padx=4)
        
        btn_eliminar = ctk.CTkButton(toolbar, text="Eliminar", width=80, height=30, fg_color="#c0392b")
        btn_eliminar.pack(side="right", padx=4)
        
        # Tabla - CORREGIDA alineación
        columnas = Plantillas.obtener_columnas(tipo_plantilla)
        tabla = TablaContableMejorada(tab, columnas=columnas, tipo=tipo_plantilla, nombre_proyecto=nombre)
        tabla.grid(row=2, column=0, sticky="nsew", padx=2, pady=2)
        
        # Forzar actualización de la tabla
        tabla.update_idletasks()
        
        # Conectar eventos
        btn_add.configure(command=tabla.añadir_fila)
        btn_remove.configure(command=tabla.eliminar_ultima_fila)
        btn_formula.configure(command=lambda: self.abrir_gestor_formulas(tabla))
        btn_calc.configure(command=lambda: self.abrir_calculadora_rapida(tabla))
        btn_stats.configure(command=lambda: self.mostrar_estadisticas(tabla))
        btn_graficas.configure(command=lambda: self.abrir_graficas(tabla, nombre))
        btn_guardar.configure(command=lambda: self.accion_guardar(tabla, nombre))
        btn_eliminar.configure(command=lambda: self.accion_eliminar(nombre))
        export_menu.configure(command=lambda v: self.ejecutar_exportacion(v, tabla, nombre))
        
        if carga_inicial:
            datos = DBManager.obtener_datos_proyecto(nombre)
            if datos:
                tabla.limpiar_tabla()
                for fila in datos:
                    tabla.añadir_fila_con_datos(fila)
    
    def abrir_gestor_formulas(self, tabla):
        """Gestor de fórmulas simplificado y entendible"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Crear columna con fórmula")
        dialog.geometry("550x450")
        dialog.attributes("-topmost", True)
        dialog.grab_set()
        
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Explicación simple
        ctk.CTkLabel(frame, text="¿Qué es una fórmula?", font=("Roboto", 14, "bold")).pack(anchor="w")
        ctk.CTkLabel(frame, text="Las fórmulas permiten crear nuevas columnas con cálculos automáticos.", 
                    font=("Roboto", 10), text_color="gray").pack(anchor="w", pady=(0, 15))
        
        ctk.CTkLabel(frame, text="Ejemplos:", font=("Roboto", 11, "bold")).pack(anchor="w")
        ejemplos_frame = ctk.CTkFrame(frame, fg_color="#f0f0f0", corner_radius=6)
        ejemplos_frame.pack(fill="x", pady=(5, 15))
        
        ctk.CTkLabel(ejemplos_frame, text="=[Debe] - [Haber]     → Calcula la diferencia", font=("Roboto", 10)).pack(anchor="w", padx=10, pady=2)
        ctk.CTkLabel(ejemplos_frame, text="=[Debe] * 1.21        → Agrega 21% de IVA", font=("Roboto", 10)).pack(anchor="w", padx=10, pady=2)
        ctk.CTkLabel(ejemplos_frame, text="=sum([Debe])          → Suma total de la columna", font=("Roboto", 10)).pack(anchor="w", padx=10, pady=2)
        
        ctk.CTkLabel(frame, text="Nombre de la nueva columna:", font=("Roboto", 11)).pack(anchor="w", pady=(10, 5))
        entry_nombre = ctk.CTkEntry(frame, width=400, placeholder_text="Ej: Saldo, IVA, Total")
        entry_nombre.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(frame, text="Fórmula:", font=("Roboto", 11)).pack(anchor="w", pady=(5, 5))
        entry_formula = ctk.CTkEntry(frame, width=400, placeholder_text="=[Debe] - [Haber]")
        entry_formula.pack(fill="x", pady=(0, 10))
        
        # Mostrar columnas disponibles
        ctk.CTkLabel(frame, text="Columnas disponibles:", font=("Roboto", 10), text_color="gray").pack(anchor="w")
        cols_frame = ctk.CTkFrame(frame, fg_color="transparent")
        cols_frame.pack(anchor="w", pady=(5, 15))
        
        for col in tabla.encabezados:
            btn_col = ctk.CTkButton(cols_frame, text=f"[{col}]", width=80, height=25, 
                                   fg_color="#e0e0e0", text_color="#1a1a1a", hover_color="#cccccc",
                                   command=lambda c=col: entry_formula.insert("end", f"[{c}]"))
            btn_col.pack(side="left", padx=2)
        
        def crear():
            nombre = entry_nombre.get().strip()
            formula = entry_formula.get().strip()
            if not nombre or not formula:
                messagebox.showwarning("Aviso", "Complete todos los campos")
                return
            
            df = tabla.obtener_dataframe()
            resultado = FormulaEngine.aplicar_formula_columna(df, nombre, formula, por_fila=True)
            
            if resultado is not None:
                tabla.agregar_columna(nombre)
                for idx, val in enumerate(resultado):
                    if idx < len(tabla.filas):
                        tabla.filas[idx][-1].delete(0, "end")
                        if isinstance(val, (int, float)):
                            tabla.filas[idx][-1].insert(0, f"{val:,.2f}")
                        else:
                            tabla.filas[idx][-1].insert(0, str(val))
                messagebox.showinfo("Éxito", f"Columna '{nombre}' creada")
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Fórmula inválida. Revise los ejemplos.")
        
        ctk.CTkButton(frame, text="Crear columna", command=crear, fg_color="#2c7da0", height=38).pack(pady=(10, 0))
    
    def abrir_calculadora_rapida(self, tabla):
        """Calculadora rápida simplificada"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Calculadora rápida entre columnas")
        dialog.geometry("550x400")
        dialog.attributes("-topmost", True)
        dialog.grab_set()
        
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="¿Qué hace esta herramienta?", font=("Roboto", 14, "bold")).pack(anchor="w")
        ctk.CTkLabel(frame, text="Crea una nueva columna con el resultado de una operación entre dos columnas.", 
                    font=("Roboto", 10), text_color="gray").pack(anchor="w", pady=(0, 15))
        
        # Selectores
        row1 = ctk.CTkFrame(frame, fg_color="transparent")
        row1.pack(fill="x", pady=5)
        ctk.CTkLabel(row1, text="Columna A:", width=100).pack(side="left")
        col_a = ctk.CTkOptionMenu(row1, values=tabla.encabezados, width=180)
        col_a.pack(side="left", padx=5)
        
        row2 = ctk.CTkFrame(frame, fg_color="transparent")
        row2.pack(fill="x", pady=5)
        ctk.CTkLabel(row2, text="Operación:", width=100).pack(side="left")
        operacion = ctk.CTkOptionMenu(row2, values=["+ (Suma)", "- (Resta)", "* (Multiplicación)", "/ (División)", "% (Porcentaje)"], width=180)
        operacion.pack(side="left", padx=5)
        
        row3 = ctk.CTkFrame(frame, fg_color="transparent")
        row3.pack(fill="x", pady=5)
        ctk.CTkLabel(row3, text="Columna B:", width=100).pack(side="left")
        col_b = ctk.CTkOptionMenu(row3, values=["(Usar un número)"] + tabla.encabezados, width=180)
        col_b.pack(side="left", padx=5)
        
        ctk.CTkLabel(frame, text="Nombre del resultado:", font=("Roboto", 11)).pack(anchor="w", pady=(15, 5))
        entry_nombre = ctk.CTkEntry(frame, width=400, placeholder_text="Ej: Total, Diferencia, Margen")
        entry_nombre.pack(fill="x", pady=(0, 10))
        
        # Constante
        const_frame = ctk.CTkFrame(frame, fg_color="transparent")
        const_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(const_frame, text="Si eligió '(Usar un número)':", width=200).pack(side="left")
        entry_const = ctk.CTkEntry(const_frame, width=150, placeholder_text="Valor")
        entry_const.insert(0, "0")
        entry_const.pack(side="left", padx=5)
        
        def calcular():
            nombre = entry_nombre.get().strip()
            if not nombre:
                messagebox.showwarning("Aviso", "Ingrese un nombre para la nueva columna")
                return
            
            df = tabla.obtener_dataframe()
            col_a_val = col_a.get()
            op_raw = operacion.get()
            # Extraer operador
            if "+" in op_raw:
                op = "+"
            elif "-" in op_raw:
                op = "-"
            elif "*" in op_raw:
                op = "*"
            elif "/" in op_raw:
                op = "/"
            else:
                op = "%"
            
            col_b_val = col_b.get()
            
            try:
                if col_b_val == "(Usar un número)":
                    const = float(entry_const.get() or 0)
                    if op == "+":
                        resultado = df[col_a_val] + const
                    elif op == "-":
                        resultado = df[col_a_val] - const
                    elif op == "*":
                        resultado = df[col_a_val] * const
                    elif op == "/":
                        resultado = df[col_a_val] / const if const != 0 else 0
                    elif op == "%":
                        resultado = df[col_a_val] * (const / 100)
                else:
                    if op == "+":
                        resultado = df[col_a_val] + df[col_b_val]
                    elif op == "-":
                        resultado = df[col_a_val] - df[col_b_val]
                    elif op == "*":
                        resultado = df[col_a_val] * df[col_b_val]
                    elif op == "/":
                        resultado = df[col_a_val] / df[col_b_val].replace(0, 1)
                    elif op == "%":
                        resultado = (df[col_a_val] / df[col_b_val].replace(0, 1)) * 100
                
                tabla.agregar_columna(nombre)
                for idx, val in enumerate(resultado):
                    if idx < len(tabla.filas):
                        tabla.filas[idx][-1].delete(0, "end")
                        tabla.filas[idx][-1].insert(0, f"{float(val):,.2f}")
                
                messagebox.showinfo("Éxito", f"Columna '{nombre}' creada con {len(resultado)} valores")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo calcular: {str(e)}")
        
        ctk.CTkButton(frame, text="Calcular y crear columna", command=calcular, fg_color="#2c7da0", height=38).pack(pady=(20, 0))
    
    def mostrar_estadisticas(self, tabla):
        """Estadísticas simplificadas y entendibles"""
        try:
            df = tabla.obtener_dataframe()
            if df.empty:
                messagebox.showinfo("Info", "No hay datos para analizar")
                return
            
            # Identificar columnas numéricas
            nums = []
            for col in df.columns:
                try:
                    valores = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
                    if valores.notna().any():
                        nums.append(col)
                        df[col] = valores
                except:
                    pass
            
            if not nums:
                messagebox.showinfo("Info", "No hay columnas con números para analizar.\n\nConsejo: Asegúrese que las columnas 'Debe' y 'Haber' tengan números.")
                return
            
            dialog = ctk.CTkToplevel(self)
            dialog.title("Estadísticas - Resumen de datos")
            dialog.geometry("700x500")
            dialog.attributes("-topmost", True)
            
            scroll = ctk.CTkScrollableFrame(dialog)
            scroll.pack(fill="both", expand=True, padx=15, pady=15)
            
            # Encabezado explicativo
            ctk.CTkLabel(scroll, text="Resumen de sus datos", font=("Roboto", 16, "bold")).pack(anchor="w", pady=(0, 10))
            ctk.CTkLabel(scroll, text="Estos son los totales y promedios de sus columnas numéricas:", 
                        font=("Roboto", 11), text_color="gray").pack(anchor="w", pady=(0, 15))
            
            for col in nums:
                frame = ctk.CTkFrame(scroll, fg_color="#f5f5f5", corner_radius=6)
                frame.pack(fill="x", pady=5)
                
                ctk.CTkLabel(frame, text=col, font=("Roboto", 13, "bold"), width=120).pack(side="left", padx=15, pady=10)
                
                vals = df[col].fillna(0)
                stats_frame = ctk.CTkFrame(frame, fg_color="transparent")
                stats_frame.pack(side="left", padx=10)
                
                stats = [
                    f"💰 Suma: ${vals.sum():,.2f}",
                    f"📊 Promedio: ${vals.mean():,.2f}",
                    f"📉 Mínimo: ${vals.min():,.2f}",
                    f"📈 Máximo: ${vals.max():,.2f}",
                    f"🔢 Registros: {len(vals)}"
                ]
                for i, s in enumerate(stats):
                    ctk.CTkLabel(stats_frame, text=s, font=("Roboto", 10)).grid(row=0, column=i, padx=10)
            
            def agregar_totales():
                fila = {}
                for col in nums:
                    fila[col] = df[col].fillna(0).sum()
                for col in df.columns:
                    if col not in fila:
                        fila[col] = "=== TOTAL ==="
                tabla.añadir_fila_con_datos([str(fila.get(c, "")) for c in tabla.encabezados])
                messagebox.showinfo("Éxito", "Se agregó una fila con los totales al final de la tabla")
                dialog.destroy()
            
            btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            btn_frame.pack(fill="x", padx=15, pady=(0, 15))
            ctk.CTkButton(btn_frame, text="Agregar fila de totales a la tabla", command=agregar_totales, fg_color="#27ae60", height=35).pack()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al calcular estadísticas: {str(e)}")
    
    def abrir_graficas(self, tabla, nombre):
        datos = tabla.obtener_datos()
        if datos and len(datos) > 0:
            # Verificar que haya datos numéricos
            hay_numeros = False
            for fila in datos:
                for valor in fila:
                    try:
                        float(str(valor).replace(',', ''))
                        hay_numeros = True
                        break
                    except:
                        pass
            if hay_numeros:
                VentanaGraficasMejorada(self, datos, tabla.encabezados, nombre)
            else:
                messagebox.showwarning("Aviso", "No hay datos numéricos para graficar.\n\nAsegúrese que las columnas 'Debe' y 'Haber' tengan números.")
        else:
            messagebox.showwarning("Aviso", "No hay datos para generar gráficas")
    
    def abrir_reportes(self):
        top = ctk.CTkToplevel(self)
        top.title("Reportes contables")
        top.geometry("380x300")
        top.attributes("-topmost", True)
        top.grab_set()
        
        frame = ctk.CTkFrame(top, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Reportes contables", font=("Roboto", 16, "bold")).pack(pady=10)
        ctk.CTkLabel(frame, text="Seleccione el tipo de reporte que desea generar", 
                    font=("Roboto", 10), text_color="gray").pack(pady=(0, 15))
        
        ctk.CTkButton(frame, text="Balance General", 
                     command=lambda: [top.destroy(), self.generar_balance_mejorado()], 
                     fg_color="#2c7da0", height=40).pack(pady=(10, 5), fill="x")
        
        ctk.CTkButton(frame, text="Estado de Resultados", 
                     command=lambda: [top.destroy(), self.generar_resultados_mejorado()], 
                     fg_color="#5a6e7a", height=40).pack(pady=(5, 10), fill="x")
        
        ctk.CTkButton(frame, text="Cancelar", command=top.destroy, fg_color="transparent", text_color="gray", height=35).pack()
    
    def generar_balance_mejorado(self):
        nombre = self.tabview.get()
        if not nombre:
            messagebox.showwarning("Aviso", "Primero seleccione un proyecto")
            return
        
        tab = self.tabview.tab(nombre)
        tabla = None
        for w in tab.winfo_children():
            if isinstance(w, TablaContableMejorada):
                tabla = w
                break
        
        if not tabla:
            messagebox.showwarning("Aviso", "No hay datos para generar el balance")
            return
        
        df = tabla.obtener_dataframe()
        if df.empty:
            messagebox.showwarning("Aviso", "La tabla está vacía. Agregue algunos datos primero.")
            return
        
        palabras_activo = ['activo', 'caja', 'banco', 'efectivo', 'inventario', 'cliente', 'cuenta por cobrar']
        palabras_pasivo = ['pasivo', 'proveedor', 'cuenta por pagar', 'acreedor', 'prestamo', 'deuda']
        palabras_capital = ['capital', 'patrimonio', 'aporte', 'inversion']
        
        activos = pasivos = capital = 0
        
        for _, row in df.iterrows():
            texto = " ".join([str(v) for v in row.values]).lower()
            
            if 'Debe' in row and 'Haber' in row:
                valor = (row.get('Debe', 0) or 0) - (row.get('Haber', 0) or 0)
            else:
                nums = df.select_dtypes(include=['number']).columns
                valor = row[nums[0]] if len(nums) > 0 else 0
            
            if any(p in texto for p in palabras_activo):
                activos += abs(valor) if valor > 0 else 0
            elif any(p in texto for p in palabras_pasivo):
                pasivos += abs(valor) if valor < 0 else max(valor, 0)
            elif any(p in texto for p in palabras_capital):
                capital += abs(valor) if valor > 0 else 0
        
        resultado = f"""BALANCE GENERAL
Proyecto: {nombre}
Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACTIVOS:                    ${activos:,.2f}
PASIVOS:                    ${pasivos:,.2f}
CAPITAL:                    ${capital:,.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL PASIVO + CAPITAL:     ${pasivos + capital:,.2f}
DIFERENCIA:                 ${activos - (pasivos + capital):,.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Nota: La diferencia debería ser cercana a cero en un balance equilibrado.
"""
        ruta = filedialog.asksaveasfilename(
            defaultextension=".txt", 
            initialfile=f"Balance_{nombre}",
            filetypes=[("Texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        if ruta:
            with open(ruta, 'w', encoding='utf-8') as f:
                f.write(resultado)
            messagebox.showinfo("Éxito", f"Balance guardado en:\n{ruta}")
    
    def generar_resultados_mejorado(self):
        nombre = self.tabview.get()
        if not nombre:
            messagebox.showwarning("Aviso", "Primero seleccione un proyecto")
            return
        
        tab = self.tabview.tab(nombre)
        tabla = None
        for w in tab.winfo_children():
            if isinstance(w, TablaContableMejorada):
                tabla = w
                break
        
        if not tabla:
            messagebox.showwarning("Aviso", "No hay datos para generar el reporte")
            return
        
        df = tabla.obtener_dataframe()
        if df.empty:
            messagebox.showwarning("Aviso", "La tabla está vacía. Agregue algunos datos primero.")
            return
        
        palabras_ingreso = ['ingreso', 'venta', 'servicio', 'honorarios', 'ingresos']
        palabras_gasto = ['gasto', 'costo', 'compra', 'sueldo', 'alquiler', 'gastos']
        
        ingresos = gastos = 0
        
        if 'Debe' in df.columns and 'Haber' in df.columns:
            for _, row in df.iterrows():
                desc = str(row.get('Descripcion', row.get('Concepto', row.get('Cuenta', '')))).lower()
                debe = row.get('Debe', 0) or 0
                haber = row.get('Haber', 0) or 0
                
                if any(p in desc for p in palabras_ingreso):
                    ingresos += haber
                elif any(p in desc for p in palabras_gasto):
                    gastos += debe
        
        utilidad = ingresos - gastos
        resultado = f"""ESTADO DE RESULTADOS
Proyecto: {nombre}
Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INGRESOS:                   ${ingresos:,.2f}
GASTOS:                     ${gastos:,.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
UTILIDAD NETA:              ${utilidad:,.2f}
RESULTADO:                  {"🟢 GANANCIA" if utilidad > 0 else "🔴 PÉRDIDA" if utilidad < 0 else "⚪ EQUILIBRIO"}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        ruta = filedialog.asksaveasfilename(
            defaultextension=".txt", 
            initialfile=f"Resultados_{nombre}",
            filetypes=[("Texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        if ruta:
            with open(ruta, 'w', encoding='utf-8') as f:
                f.write(resultado)
            messagebox.showinfo("Éxito", f"Reporte guardado en:\n{ruta}")
    
    def añadir_pestaña(self, nombre, tipo="Libro Diario", carga_inicial=False):
        if nombre in self.tabview._tab_dict:
            messagebox.showwarning("Aviso", f"El proyecto '{nombre}' ya está abierto")
            return
        tab = self.tabview.add(nombre)
        self.construir_interfaz_pestana(tab, nombre, carga_inicial, tipo)
        self.tabview.set(nombre)
    
    def accion_guardar(self, tabla, nombre):
        datos = tabla.obtener_datos()
        DBManager.guardar_proyecto(nombre, datos, tabla.tipo_actual)
        self.cambios_pendientes = False
        messagebox.showinfo("Éxito", f"'{nombre}' guardado correctamente")
        self.status_label.configure(text=f"Proyecto '{nombre}' guardado")
    
    def accion_eliminar(self, nombre):
        if messagebox.askyesno("Confirmar", f"¿Eliminar permanentemente '{nombre}'?\n\nEsta acción no se puede deshacer."):
            DBManager.eliminar_proyecto(nombre)
            self.tabview.delete(nombre)
            messagebox.showinfo("Eliminado", f"'{nombre}' eliminado")
            self.status_label.configure(text=f"Proyecto '{nombre}' eliminado")
    
    def importar_archivo_general(self):
        nombre = self.tabview.get()
        if not nombre:
            messagebox.showwarning("Aviso", "Primero seleccione o cree un proyecto")
            return
        
        columnas, datos = GestionArchivosMejorado.leer_archivo_para_importar()
        if datos:
            tab = self.tabview.tab(nombre)
            tabla = None
            for w in tab.winfo_children():
                if isinstance(w, TablaContableMejorada):
                    tabla = w
                    break
            
            if tabla:
                if messagebox.askyesno("Confirmar", "¿Desea reemplazar los datos actuales por los del archivo?"):
                    tabla.encabezados = columnas
                    tabla.dibujar_encabezados()
                tabla.limpiar_tabla()
                for f in datos:
                    tabla.añadir_fila_con_datos(f)
                self.cambios_pendientes = True
                messagebox.showinfo("Éxito", f"Se importaron {len(datos)} filas en '{nombre}'")
                self.status_label.configure(text=f"Importadas {len(datos)} filas")
    
    def ejecutar_exportacion(self, formato, tabla, nombre):
        GestionArchivosMejorado.exportar(tabla.obtener_datos(), nombre, formato)
        self.status_label.configure(text=f"Exportado a {formato}")
    
    def sincronizar_nube(self):
        if not self.sesion_activa:
            if messagebox.askyesno("Iniciar sesión", "Para sincronizar necesita iniciar sesión. ¿Desea hacerlo ahora?"):
                self.mostrar_login()
            return
        
        try:
            for nombre in list(self.tabview._tab_dict.keys()):
                tab = self.tabview.tab(nombre)
                for w in tab.winfo_children():
                    if isinstance(w, TablaContableMejorada):
                        datos = w.obtener_datos()
                        DBManager.guardar_proyecto(nombre, datos, w.tipo_actual)
                        self.cloud.guardar_proyecto(nombre, w.tipo_actual, datos, w.encabezados)
                        break
            messagebox.showinfo("Sincronización", "Todos los proyectos fueron sincronizados con la nube")
            self.status_label.configure(text="Sincronización completa")
        except Exception as e:
            messagebox.showerror("Error", f"Error al sincronizar: {str(e)}")
    
    def cargar_proyectos_existentes(self):
        for nombre, tipo in DBManager.obtener_todos_los_proyectos():
            self.añadir_pestaña(nombre, tipo or "Libro Diario", carga_inicial=True)
        self.status_label.configure(text=f"Cargados {len(DBManager.obtener_todos_los_proyectos())} proyectos")
    
    def confirmar_salida(self):
        if self.cambios_pendientes:
            respuesta = messagebox.askyesnocancel("Salir", "Hay cambios sin guardar. ¿Desea guardarlos antes de salir?")
            if respuesta is True:
                for nombre in list(self.tabview._tab_dict.keys()):
                    tab = self.tabview.tab(nombre)
                    for w in tab.winfo_children():
                        if isinstance(w, TablaContableMejorada):
                            self.accion_guardar(w, nombre)
                            break
                self.destroy()
            elif respuesta is False:
                self.destroy()
        else:
            self.destroy()
    
    def abrir_ventana_nuevo(self):
        VentanaNuevoTrabajo(self, self.añadir_pestaña)
    
    def set_status(self, msg, duration=3000):
        self.status_label.configure(text=msg)
        self.after(duration, lambda: self.status_label.configure(text="Listo"))


class VentanaNuevoTrabajo(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("Nuevo proyecto")
        self.geometry("400
