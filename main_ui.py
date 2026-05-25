# main_ui.py - VERSIÓN CORREGIDA
# Colores fijos, alineación corregida, login persistente

import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import datetime
import pandas as pd
import re
import hashlib
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from componentes_gui import TablaContableMejorada, VentanaGraficasMejorada
from logica_contable import GestionArchivosMejorado, Plantillas, FormulaEngine
from database_manager import DBManager
from cloud_manager import CloudManager

# Configuración de colores fijos (no cambian con el tema)
COLORES = {
    "principal": "#2c7da0",
    "secundario": "#5a6e7a",
    "exito": "#27ae60",
    "peligro": "#c0392b",
    "fondo": "#f5f5f5",
    "fondo_sidebar": "#ffffff",
    "texto": "#1a1a1a",
    "texto_claro": "#666666",
    "borde": "#e0e0e0"
}

# Configuración inicial
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
        self.usuario_recordado = self.cargar_usuario_recordado()
        
        # Ocultar principal hasta login
        self.withdraw()
        self.mostrar_login()
        
        # Configurar grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar - COLORES FIJOS
        self.sidebar = ctk.CTkFrame(
            self, width=200, corner_radius=0,
            fg_color=COLORES["fondo_sidebar"]
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(
            self.sidebar, 
            text="Contaduría", 
            font=("Roboto", 18, "bold"),
            text_color=COLORES["texto"]
        )
        self.logo_label.pack(pady=25, padx=20)
        
        # Botones sidebar - COLORES FIJOS
        self.btn_nuevo = ctk.CTkButton(
            self.sidebar, text="Nuevo proyecto",
            command=self.abrir_ventana_nuevo,
            fg_color=COLORES["principal"],
            hover_color="#1f5e7a",
            height=35, corner_radius=6
        )
        self.btn_nuevo.pack(pady=6, padx=20, fill="x")
        
        self.btn_importar = ctk.CTkButton(
            self.sidebar, text="Importar archivo",
            command=self.importar_archivo_general,
            fg_color=COLORES["secundario"],
            hover_color="#4a5a66",
            height=35, corner_radius=6
        )
        self.btn_importar.pack(pady=6, padx=20, fill="x")
        
        self.btn_sincronizar = ctk.CTkButton(
            self.sidebar, text="Sincronizar nube",
            command=self.sincronizar_nube,
            fg_color=COLORES["principal"],
            hover_color="#1f5e7a",
            height=35, corner_radius=6
        )
        self.btn_sincronizar.pack(pady=6, padx=20, fill="x")
        
        self.btn_reportes = ctk.CTkButton(
            self.sidebar, text="Generar reportes",
            command=self.abrir_reportes,
            fg_color=COLORES["secundario"],
            hover_color="#4a5a66",
            height=35, corner_radius=6
        )
        self.btn_reportes.pack(pady=6, padx=20, fill="x")
        
        # Botón cerrar sesión
        self.btn_logout = ctk.CTkButton(
            self.sidebar, text="Cerrar sesión",
            command=self.cerrar_sesion,
            fg_color="transparent",
            text_color=COLORES["peligro"],
            hover_color="#f0f0f0",
            height=35, corner_radius=6
        )
        self.btn_logout.pack(side="bottom", pady=(0, 20), padx=20, fill="x")
        
        # Barra de estado
        self.status_bar = ctk.CTkFrame(
            self, height=28,
            fg_color=COLORES["fondo"]
        )
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        self.status_label = ctk.CTkLabel(
            self.status_bar, text="Listo", anchor="w",
            text_color=COLORES["texto_claro"], font=("Roboto", 11)
        )
        self.status_label.pack(side="left", padx=12)
        
        # Panel principal
        self.main_panel = ctk.CTkFrame(self, fg_color=COLORES["fondo"])
        self.main_panel.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.main_panel.grid_columnconfigure(0, weight=1)
        self.main_panel.grid_rowconfigure(0, weight=1)
        
        self.tabview = ctk.CTkTabview(self.main_panel)
        self.tabview.grid(row=0, column=0, sticky="nsew")
        
        self.after(100, self.maximizar)
        self.protocol("WM_DELETE_WINDOW", self.confirmar_salida)
    
    def maximizar(self):
        """Maximizar ventana"""
        try:
            self.state('zoomed')
        except:
            self.attributes('-fullscreen', False)
            self.geometry("1300x800")
    
    def cargar_usuario_recordado(self):
        """Carga usuario guardado"""
        try:
            import os
            if os.path.exists("usuario.txt"):
                with open("usuario.txt", "r") as f:
                    return f.read().strip()
        except:
            pass
        return ""
    
    def guardar_usuario_recordado(self, email):
        """Guarda usuario para recordar"""
        try:
            with open("usuario.txt", "w") as f:
                f.write(email)
        except:
            pass
    
    def enviar_correo_recuperacion(self, email):
        """Envía email con código de recuperación"""
        # Código de 6 dígitos
        codigo = str(random.randint(100000, 999999))
        
        # Guardar código temporal (en producción usar DB)
        self.codigo_recuperacion = {email: codigo}
        
        # Configurar email (usar variables de entorno en producción)
        try:
            remitente = "contaduria@recuperacion.com"
            asunto = "Recuperación de contraseña - Contaduría"
            mensaje = f"""
            Hola,
            
            Has solicitado recuperar tu contraseña.
            Tu código de verificación es: {codigo}
            
            Ingresa este código en la aplicación para continuar.
            
            Si no solicitaste este cambio, ignora este mensaje.
            
            Saludos,
            Equipo Contaduría
            """
            
            # En desarrollo, solo mostrar el código
            messagebox.showinfo("Código de recuperación", 
                               f"Para recuperar tu contraseña, usa el código:\n\n{codigo}\n\n(En producción se enviaría por email)")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo enviar el email: {e}")
            return False
    
    def mostrar_login(self):
        """Ventana de login minimalista con recuperación"""
        login = ctk.CTkToplevel()
        login.title("Contaduría")
        login.geometry("400550")
        login.attributes("-topmost", True)
        login.grab_set()
        login.resizable(False, False)
        
        # Centrar
        login.update_idletasks()
        x = (login.winfo_screenwidth() // 2) - 200
        y = (login.winfo_screenheight() // 2) - 275
        login.geometry(f"+{x}+{y}")
        
        # Frame principal
        main_frame = ctk.CTkFrame(login, fg_color=COLORES["fondo"])
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Logo y título
        ctk.CTkLabel(
            main_frame, text="Contaduría",
            font=("Roboto", 28, "bold"),
            text_color=COLORES["principal"]
        ).pack(pady=(0, 5))
        
        ctk.CTkLabel(
            main_frame, text="Sistema de gestión contable",
            font=("Roboto", 11),
            text_color=COLORES["texto_claro"]
        ).pack(pady=(0, 25))
        
        # Tabs
        tabview = ctk.CTkTabview(main_frame, width=340)
        tabview.pack()
        
        tab_login = tabview.add("Iniciar sesión")
        tab_recuperar = tabview.add("¿Olvidó su contraseña?")
        
        # ===== TAB LOGIN =====
        ctk.CTkLabel(tab_login, text="Correo electrónico", font=("Roboto", 11)).pack(anchor="w", pady=(15, 5))
        entry_email = ctk.CTkEntry(tab_login, width=300, placeholder_text="usuario@ejemplo.com")
        entry_email.pack()
        
        # Auto-completar usuario recordado
        if self.usuario_recordado:
            entry_email.insert(0, self.usuario_recordado)
        
        ctk.CTkLabel(tab_login, text="Contraseña", font=("Roboto", 11)).pack(anchor="w", pady=(10, 5))
        entry_pass = ctk.CTkEntry(tab_login, width=300, show="•", placeholder_text="••••••••")
        entry_pass.pack()
        
        # Checkbox recordar usuario
        recordar_var = ctk.BooleanVar(value=bool(self.usuario_recordado))
        ctk.CTkCheckBox(
            tab_login, text="Recordar usuario",
            variable=recordar_var,
            checkbox_width=16, checkbox_height=16
        ).pack(anchor="w", pady=(10, 5))
        
        lbl_error = ctk.CTkLabel(tab_login, text="", text_color=COLORES["peligro"], font=("Roboto", 11))
        lbl_error.pack(pady=8)
        
        def do_login():
            email = entry_email.get().strip()
            password = entry_pass.get()
            
            if not email or not password:
                lbl_error.configure(text="Complete todos los campos")
                return
            
            # Demo: usuario demo@contaduria.com / admin123
            if email == "demo@contaduria.com" and password == "admin123":
                if recordar_var.get():
                    self.guardar_usuario_recordado(email)
                else:
                    self.guardar_usuario_recordado("")
                
                self.sesion_activa = True
                self.usuario_actual = {"email": email, "nombre": "Usuario Demo"}
                login.destroy()
                self.deiconify()
                self.status_label.configure(text=f"Bienvenido, {email}")
                self.cargar_proyectos_existentes()
                return
            
            # Intentar login real (con DB)
            success, data = self.cloud.login(email, password)
            if success:
                if recordar_var.get():
                    self.guardar_usuario_recordado(email)
                else:
                    self.guardar_usuario_recordado("")
                
                self.sesion_activa = True
                self.usuario_actual = data
                login.destroy()
                self.deiconify()
                self.status_label.configure(text=f"Bienvenido, {data.get('nombre', email)}")
                self.cargar_proyectos_existentes()
            else:
                lbl_error.configure(text=data)
        
        ctk.CTkButton(
            tab_login, text="Ingresar",
            command=do_login,
            fg_color=COLORES["principal"],
            height=38, corner_radius=6
        ).pack(pady=(15, 0), fill="x")
        
        # ===== TAB RECUPERAR CONTRASEÑA =====
        ctk.CTkLabel(tab_recuperar, text="Ingrese su correo electrónico", font=("Roboto", 11)).pack(pady=(20, 5))
        entry_rec_email = ctk.CTkEntry(tab_recuperar, width=300, placeholder_text="usuario@ejemplo.com")
        entry_rec_email.pack()
        
        lbl_rec_error = ctk.CTkLabel(tab_recuperar, text="", text_color=COLORES["peligro"], font=("Roboto", 11))
        lbl_rec_error.pack(pady=8)
        
        lbl_rec_exito = ctk.CTkLabel(tab_recuperar, text="", text_color=COLORES["exito"], font=("Roboto", 11))
        lbl_rec_exito.pack(pady=5)
        
        # Frame para código y nueva contraseña (inicialmente oculto)
        frame_codigo = ctk.CTkFrame(tab_recuperar, fg_color="transparent")
        
        def enviar_codigo():
            email = entry_rec_email.get().strip()
            if not email:
                lbl_rec_error.configure(text="Ingrese un correo válido")
                return
            
            if self.enviar_correo_recuperacion(email):
                lbl_rec_error.configure(text="")
                lbl_rec_exito.configure(text="Código enviado. Revise su correo.")
                frame_codigo.pack(fill="x", pady=(10, 0))
            else:
                lbl_rec_error.configure(text="Error al enviar el código")
        
        ctk.CTkButton(
            tab_recuperar, text="Enviar código",
            command=enviar_codigo,
            fg_color=COLORES["secundario"],
            height=35, corner_radius=6
        ).pack(pady=(10, 0), fill="x")
        
        # Campos de código y nueva contraseña
        ctk.CTkLabel(frame_codigo, text="Código de verificación", font=("Roboto", 11)).pack(anchor="w", pady=(10, 5))
        entry_codigo = ctk.CTkEntry(frame_codigo, width=300, placeholder_text="000000")
        entry_codigo.pack()
        
        ctk.CTkLabel(frame_codigo, text="Nueva contraseña", font=("Roboto", 11)).pack(anchor="w", pady=(10, 5))
        entry_nueva_pass = ctk.CTkEntry(frame_codigo, width=300, show="•")
        entry_nueva_pass.pack()
        
        ctk.CTkLabel(frame_codigo, text="Confirmar contraseña", font=("Roboto", 11)).pack(anchor="w", pady=(10, 5))
        entry_confirm_pass = ctk.CTkEntry(frame_codigo, width=300, show="•")
        entry_confirm_pass.pack()
        
        lbl_cambio_error = ctk.CTkLabel(frame_codigo, text="", text_color=COLORES["peligro"], font=("Roboto", 11))
        lbl_cambio_error.pack(pady=8)
        
        def cambiar_password():
            email = entry_rec_email.get().strip()
            codigo = entry_codigo.get().strip()
            nueva = entry_nueva_pass.get()
            confirm = entry_confirm_pass.get()
            
            if not codigo:
                lbl_cambio_error.configure(text="Ingrese el código")
                return
            if not nueva or len(nueva) < 6:
                lbl_cambio_error.configure(text="Mínimo 6 caracteres")
                return
            if nueva != confirm:
                lbl_cambio_error.configure(text="Las contraseñas no coinciden")
                return
            
            # Verificar código (demo: código 123456)
            if codigo == "123456" or (hasattr(self, 'codigo_recuperacion') and self.codigo_recuperacion.get(email) == codigo):
                # Aquí iría el cambio real en la base de datos
                messagebox.showinfo("Éxito", "Contraseña cambiada correctamente.\nAhora puede iniciar sesión.")
                tabview.set("Iniciar sesión")
                lbl_rec_exito.configure(text="")
                frame_codigo.pack_forget()
                entry_rec_email.delete(0, "end")
            else:
                lbl_cambio_error.configure(text="Código incorrecto")
        
        ctk.CTkButton(
            frame_codigo, text="Cambiar contraseña",
            command=cambiar_password,
            fg_color=COLORES["exito"],
            height=35, corner_radius=6
        ).pack(pady=(10, 0), fill="x")
        
        # ===== BOTÓN OFFLINE =====
        ctk.CTkButton(
            main_frame, text="Trabajar sin conexión",
            command=lambda: [login.destroy(), self.iniciar_offline()],
            fg_color="transparent",
            text_color=COLORES["texto_claro"],
            hover_color=COLORES["fondo"],
            height=35
        ).pack(pady=(15, 0))
    
    def iniciar_offline(self):
        """Inicia en modo offline"""
        self.sesion_activa = False
        self.deiconify()
        self.status_label.configure(text="Modo offline - Datos locales")
        self.btn_sincronizar.configure(state="disabled", fg_color="#cccccc")
        self.cargar_proyectos_existentes()
    
    def cerrar_sesion(self):
        """Cierra la sesión actual"""
        if messagebox.askyesno("Cerrar sesión", "¿Desea cerrar la sesión actual?"):
            self.sesion_activa = False
            self.usuario_actual = None
            # Limpiar pestañas
            for tab in list(self.tabview._tab_dict.keys()):
                self.tabview.delete(tab)
            self.withdraw()
            self.mostrar_login()
    
    def construir_interfaz_pestana(self, tab, nombre, carga_inicial=False, tipo_plantilla="Libro Diario"):
        """Construye la pestaña con toolbar mejorada"""
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)
        
        # Toolbar con colores fijos
        toolbar = ctk.CTkFrame(
            tab, height=45,
            fg_color=COLORES["fondo"],
            corner_radius=8
        )
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 12), padx=2)
        
        # Botones toolbar
        btn_add = ctk.CTkButton(
            toolbar, text="+ Agregar fila",
            width=100, height=32,
            fg_color=COLORES["exito"],
            corner_radius=6
        )
        btn_add.pack(side="left", padx=4)
        
        btn_remove = ctk.CTkButton(
            toolbar, text="- Eliminar última",
            width=110, height=32,
            fg_color=COLORES["peligro"],
            corner_radius=6
        )
        btn_remove.pack(side="left", padx=4)
        
        # Separador
        ctk.CTkLabel(toolbar, text="|", text_color=COLORES["borde"]).pack(side="left", padx=8)
        
        btn_formula = ctk.CTkButton(
            toolbar, text="Fórmula",
            width=80, height=32,
            fg_color=COLORES["secundario"],
            corner_radius=6
        )
        btn_formula.pack(side="left", padx=4)
        
        btn_calc = ctk.CTkButton(
            toolbar, text="Calculadora",
            width=90, height=32,
            fg_color=COLORES["secundario"],
            corner_radius=6
        )
        btn_calc.pack(side="left", padx=4)
        
        btn_stats = ctk.CTkButton(
            toolbar, text="Estadísticas",
            width=90, height=32,
            fg_color=COLORES["secundario"],
            corner_radius=6
        )
        btn_stats.pack(side="left", padx=4)
        
        btn_graficas = ctk.CTkButton(
            toolbar, text="Gráficas",
            width=80, height=32,
            fg_color=COLORES["secundario"],
            corner_radius=6
        )
        btn_graficas.pack(side="left", padx=4)
        
        # Separador
        ctk.CTkLabel(toolbar, text="|", text_color=COLORES["borde"]).pack(side="left", padx=8)
        
        ctk.CTkLabel(toolbar, text="Exportar:", font=("Roboto", 11)).pack(side="left", padx=(4, 2))
        export_menu = ctk.CTkOptionMenu(
            toolbar, values=["Excel", "PDF"],
            width=80, height=32,
            fg_color="white",
            button_color=COLORES["secundario"],
            text_color=COLORES["texto"]
        )
        export_menu.pack(side="left", padx=4)
        
        # Botones derecha
        btn_guardar = ctk.CTkButton(
            toolbar, text="Guardar",
            width=80, height=32,
            fg_color=COLORES["exito"],
            corner_radius=6
        )
        btn_guardar.pack(side="right", padx=4)
        
        btn_eliminar = ctk.CTkButton(
            toolbar, text="Eliminar proyecto",
            width=120, height=32,
            fg_color=COLORES["peligro"],
            corner_radius=6
        )
        btn_eliminar.pack(side="right", padx=4)
        
        # Tabla
        columnas = Plantillas.obtener_columnas(tipo_plantilla)
        tabla = TablaContableMejorada(tab, columnas=columnas, tipo=tipo_plantilla, nombre_proyecto=nombre)
        tabla.grid(row=2, column=0, sticky="nsew", padx=2, pady=2)
        
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
        """Gestor de fórmulas simplificado"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Fórmulas")
        dialog.geometry("550450")
        dialog.attributes("-topmost", True)
        dialog.grab_set()
        
        frame = ctk.CTkFrame(dialog, fg_color=COLORES["fondo"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            frame, text="Crear columna con fórmula",
            font=("Roboto", 16, "bold"),
            text_color=COLORES["principal"]
        ).pack(anchor="w", pady=(0, 15))
        
        # Ejemplo
        ctk.CTkLabel(
            frame, text="Ejemplo: =[Debe] - [Haber]",
            font=("Roboto", 10),
            text_color=COLORES["texto_claro"]
        ).pack(anchor="w", pady=(0, 15))
        
        ctk.CTkLabel(frame, text="Nombre de la columna", font=("Roboto", 12)).pack(anchor="w")
        entry_nombre = ctk.CTkEntry(frame, width=400, height=35)
        entry_nombre.pack(fill="x", pady=(5, 10))
        
        ctk.CTkLabel(frame, text="Fórmula", font=("Roboto", 12)).pack(anchor="w")
        entry_formula = ctk.CTkEntry(frame, width=400, height=35, placeholder_text="=[Debe] - [Haber]")
        entry_formula.pack(fill="x", pady=(5, 10))
        
        # Columnas disponibles
        ctk.CTkLabel(frame, text="Columnas disponibles:", font=("Roboto", 10), text_color=COLORES["texto_claro"]).pack(anchor="w")
        cols_frame = ctk.CTkFrame(frame, fg_color="transparent")
        cols_frame.pack(anchor="w", pady=(5, 15))
        
        for col in tabla.encabezados[:8]:  # Mostrar primeras 8
            tag = ctk.CTkLabel(
                cols_frame, text=f"[{col}]",
                font=("Roboto", 9),
                fg_color=COLORES["fondo"],
                corner_radius=4, padx=6, pady=2
            )
            tag.pack(side="left", padx=2)
        
        def crear():
            nombre = entry_nombre.get().strip()
            formula = entry_formula.get().strip()
            
            if not nombre:
                messagebox.showwarning("Aviso", "Ingrese un nombre para la columna")
                return
            if not formula:
                messagebox.showwarning("Aviso", "Ingrese una fórmula")
                return
            if not formula.startswith('='):
                messagebox.showwarning("Aviso", "La fórmula debe comenzar con '='")
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
                messagebox.showerror("Error", "Fórmula inválida.\nRevise la sintaxis.")
        
        ctk.CTkButton(
            frame, text="Crear columna",
            command=crear,
            fg_color=COLORES["principal"],
            height=38, corner_radius=6
        ).pack(pady=(10, 0), fill="x")
    
    def abrir_calculadora_rapida(self, tabla):
        """Calculadora rápida simplificada"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Calculadora rápida")
        dialog.geometry("500400")
        dialog.attributes("-topmost", True)
        dialog.grab_set()
        
        frame = ctk.CTkFrame(dialog, fg_color=COLORES["fondo"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            frame, text="Operaciones entre columnas",
            font=("Roboto", 16, "bold"),
            text_color=COLORES["principal"]
        ).pack(pady=(0, 20))
        
        # Operación
        row1 = ctk.CTkFrame(frame, fg_color="transparent")
        row1.pack(fill="x", pady=5)
        ctk.CTkLabel(row1, text="Columna A:", width=100).pack(side="left")
        col_a = ctk.CTkOptionMenu(row1, values=tabla.encabezados, width=180)
        col_a.pack(side="left", padx=5)
        
        row2 = ctk.CTkFrame(frame, fg_color="transparent")
        row2.pack(fill="x", pady=5)
        ctk.CTkLabel(row2, text="Operación:", width=100).pack(side="left")
        operacion = ctk.CTkOptionMenu(row2, values=["+", "-", "*", "/", "%"], width=180)
        operacion.pack(side="left", padx=5)
        
        row3 = ctk.CTkFrame(frame, fg_color="transparent")
        row3.pack(fill="x", pady=5)
        ctk.CTkLabel(row3, text="Columna B:", width=100).pack(side="left")
        col_b = ctk.CTkOptionMenu(row3, values=["(Constante)"] + tabla.encabezados, width=180)
        col_b.pack(side="left", padx=5)
        
        # Constante
        const_frame = ctk.CTkFrame(frame, fg_color="transparent")
        const_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(const_frame, text="Valor constante:", width=100).pack(side="left")
        entry_const = ctk.CTkEntry(const_frame, width=180)
        entry_const.insert(0, "0")
        entry_const.pack(side="left", padx=5)
        
        ctk.CTkLabel(frame, text="Nombre del resultado:", font=("Roboto", 12)).pack(anchor="w", pady=(15, 5))
        entry_nombre = ctk.CTkEntry(frame, width=400, height=35)
        entry_nombre.pack(fill="x", pady=(0, 10))
        
        def calcular():
            nombre = entry_nombre.get().strip()
            if not nombre:
                messagebox.showwarning("Aviso", "Ingrese un nombre para el resultado")
                return
            
            df = tabla.obtener_dataframe()
            try:
                if col_b.get() == "(Constante)":
                    const = float(entry_const.get() or 0)
                    col = col_a.get()
                    op = operacion.get()
                    
                    if op == "+":
                        resultado = df[col] + const
                    elif op == "-":
                        resultado = df[col] - const
                    elif op == "*":
                        resultado = df[col] * const
                    elif op == "/":
                        resultado = df[col] / const if const != 0 else 0
                    elif op == "%":
                        resultado = df[col] * (const / 100)
                else:
                    col_a_val = col_a.get()
                    col_b_val = col_b.get()
                    op = operacion.get()
                    
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
                
                messagebox.showinfo("Éxito", f"Columna '{nombre}' creada")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error: {str(e)}")
        
        ctk.CTkButton(
            frame, text="Calcular",
            command=calcular,
            fg_color=COLORES["principal"],
            height=38, corner_radius=6
        ).pack(pady=(15, 0), fill="x")
    
    def mostrar_estadisticas(self, tabla):
        """Estadísticas de columnas - CORREGIDA"""
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
                messagebox.showinfo("Info", "No hay columnas numéricas para analizar")
                return
            
            dialog = ctk.CTkToplevel(self)
            dialog.title("Estadísticas")
            dialog.geometry("700500")
            dialog.attributes("-topmost", True)
            
            scroll = ctk.CTkScrollableFrame(dialog)
            scroll.pack(fill="both", expand=True, padx=15, pady=15)
            
            for col in nums:
                frame = ctk.CTkFrame(scroll, fg_color=COLORES["fondo"], corner_radius=8)
                frame.pack(fill="x", pady=5)
                
                ctk.CTkLabel(
                    frame, text=col,
                    font=("Roboto", 13, "bold"),
                    text_color=COLORES["principal"]
                ).pack(side="left", padx=15)
                
                vals = df[col].fillna(0)
                stats = [
                    f"💰 Suma: ${vals.sum():,.2f}",
                    f"📊 Promedio: ${vals.mean():,.2f}",
                    f"📉 Mínimo: ${vals.min():,.2f}",
                    f"📈 Máximo: ${vals.max():,.2f}",
                    f"📋 Registros: {len(vals)}"
                ]
                for s in stats:
                    ctk.CTkLabel(frame, text=s, font=("Roboto", 10)).pack(side="left", padx=10)
            
            def agregar_totales():
                fila = {}
                for col in nums:
                    fila[col] = df[col].fillna(0).sum()
                for col in df.columns:
                    if col not in fila:
                        fila[col] = "=== TOTAL ==="
                tabla.añadir_fila_con_datos([str(fila.get(c, "")) for c in tabla.encabezados])
                messagebox.showinfo("Éxito", "Fila de totales agregada al final")
                dialog.destroy()
            
            ctk.CTkButton(
                dialog, text="Agregar fila de totales",
                command=agregar_totales,
                fg_color=COLORES["exito"],
                height=35, corner_radius=6
            ).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error: {str(e)}")
    
    def abrir_graficas(self, tabla, nombre):
        """Abrir gráficas"""
        datos = tabla.obtener_datos()
        if datos and len(datos) > 0:
            VentanaGraficasMejorada(self, datos, tabla.encabezados, nombre)
        else:
            messagebox.showwarning("Aviso", "No hay datos para generar gráficas.\nAgregue al menos una fila de datos.")
    
    def abrir_reportes(self):
        """Ventana de reportes"""
        top = ctk.CTkToplevel(self)
        top.title("Reportes")
        top.geometry("350280")
        top.attributes("-topmost", True)
        top.grab_set()
        
        frame = ctk.CTkFrame(top, fg_color=COLORES["fondo"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            frame, text="Reportes contables",
            font=("Roboto", 16, "bold"),
            text_color=COLORES["principal"]
        ).pack(pady=(0, 15))
        
        ctk.CTkButton(
            frame, text="📊 Balance General",
            command=lambda: [top.destroy(), self.generar_balance_mejorado()],
            fg_color=COLORES["principal"],
            height=40, corner_radius=6
        ).pack(pady=(5, 5), fill="x")
        
        ctk.CTkButton(
            frame, text="📈 Estado de Resultados",
            command=lambda: [top.destroy(), self.generar_resultados_mejorado()],
            fg_color=COLORES["secundario"],
            height=40, corner_radius=6
        ).pack(pady=(5, 15), fill="x")
        
        ctk.CTkButton(
            frame, text="Cancelar",
            command=top.destroy,
            fg_color="transparent",
            text_color=COLORES["texto_claro"],
            hover_color=COLORES["fondo"],
            height=35
        ).pack()
    
    def generar_balance_mejorado(self):
        """Genera Balance General simplificado"""
        nombre = self.tabview.get()
        if not nombre:
            messagebox.showwarning("Aviso", "Seleccione un proyecto primero")
            return
        
        tab = self.tabview.tab(nombre)
        tabla = None
        for w in tab.winfo_children():
            if isinstance(w, TablaContableMejorada):
                tabla = w
                break
        
        if not tabla:
            messagebox.showwarning("Aviso", "No se encontró la tabla")
            return
        
        df = tabla.obtener_dataframe()
        if df.empty:
            messagebox.showwarning("Aviso", "La tabla está vacía")
            return
        
        # Clasificación básica
        activos = 0
        pasivos = 0
        capital = 0
        
        palabras_activo = ['activo', 'caja', 'banco', 'efectivo', 'inventario', 'cliente']
        palabras_pasivo = ['pasivo', 'proveedor', 'deuda', 'prestamo', 'acreedor']
        palabras_capital = ['capital', 'patrimonio', 'aporte']
        
        for _, row in df.iterrows():
            texto = " ".join([str(v).lower() for v in row.values])
            
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
        
        # Mostrar resultado
        resultado = f"""
╔══════════════════════════════════════╗
║         BALANCE GENERAL              ║
╠══════════════════════════════════════╣
║ Proyecto: {nombre:<28} ║
║ Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')} ║
╠══════════════════════════════════════╣
║                                      ║
║ ACTIVOS:                    ${activos:>12,.2f} ║
║ PASIVOS:                    ${pasivos:>12,.2f} ║
║ CAPITAL:                    ${capital:>12,.2f} ║
║                                      ║
╠══════════════════════════════════════╣
║ TOTAL PASIVO + CAPITAL:     ${pasivos + capital:>12,.2f} ║
║ DIFERENCIA:                 ${activos - (pasivos + capital):>12,.2f} ║
╚══════════════════════════════════════╝
"""
        ruta = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=f"Balance_{nombre}",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")]
        )
        if ruta:
            with open(ruta, 'w', encoding='utf-8') as f:
                f.write(resultado)
            messagebox.showinfo("Éxito", f"Balance guardado en:\n{ruta}")
    
    def generar_resultados_mejorado(self):
        """Genera Estado de Resultados simplificado"""
        nombre = self.tabview.get()
        if not nombre:
            messagebox.showwarning("Aviso", "Seleccione un proyecto primero")
            return
        
        tab = self.tabview.tab(nombre)
        tabla = None
        for w in tab.winfo_children():
            if isinstance(w, TablaContableMejorada):
                tabla = w
                break
        
        if not tabla:
            messagebox.showwarning("Aviso", "No se encontró la tabla")
            return
        
        df = tabla.obtener_dataframe()
        if df.empty:
            messagebox.showwarning("Aviso", "La tabla está vacía")
            return
        
        ingresos = 0
        gastos = 0
        
        palabras_ingreso = ['ingreso', 'venta', 'servicio', 'honorarios']
        palabras_gasto = ['gasto', 'costo', 'compra', 'sueldo', 'alquiler']
        
        if 'Debe' in df.columns and 'Haber' in df.columns:
            for _, row in df.iterrows():
                desc = str(row.get('Descripcion', row.get('Concepto', ''))).lower()
                debe = row.get('Debe', 0) or 0
                haber = row.get('Haber', 0) or 0
                
                if any(p in desc for p in palabras_ingreso):
                    ingresos += haber
                elif any(p in desc for p in palabras_gasto):
                    gastos += debe
        
        utilidad = ingresos - gastos
        resultado_tipo = "🟢 GANANCIA" if utilidad > 0 else "🔴 PÉRDIDA" if utilidad < 0 else "⚪ EQUILIBRIO"
        
        resultado = f"""
╔══════════════════════════════════════╗
║       ESTADO DE RESULTADOS           ║
╠══════════════════════════════════════╣
║ Proyecto: {nombre:<28} ║
║ Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')} ║
╠══════════════════════════════════════╣
║                                      ║
║ INGRESOS:                   ${ingresos:>12,.2f} ║
║ GASTOS:                     ${gastos:>12,.2f} ║
║                                      ║
╠══════════════════════════════════════╣
║ UTILIDAD NETA:              ${utilidad:>12,.2f} ║
║ RESULTADO:                  {resultado_tipo:>12} ║
╚══════════════════════════════════════╝
"""
        ruta = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=f"Resultados_{nombre}",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")]
        )
        if ruta:
            with open(ruta, 'w', encoding='utf-8') as f:
                f.write(resultado)
            messagebox.showinfo("Éxito", f"Estado de Resultados guardado en:\n{ruta}")
    
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
        messagebox.showinfo("Éxito", f"Proyecto '{nombre}' guardado")
        self.status_label.configure(text=f"Guardado: {nombre}")
    
    def accion_eliminar(self, nombre):
        if messagebox.askyesno("Confirmar", f"¿Eliminar permanentemente el proyecto '{nombre}'?"):
            DBManager.eliminar_proyecto(nombre)
            if self.sesion_activa:
                self.cloud.eliminar_proyecto(nombre)
            self.tabview.delete(nombre)
            messagebox.showinfo("Eliminado", f"Proyecto '{nombre}' eliminado")
    
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
                if messagebox.askyesno("Confirmar", "¿Reemplazar los datos actuales por los del archivo?"):
                    tabla.encabezados = columnas
                    tabla.dibujar_encabezados()
                tabla.limpiar_tabla()
                for fila in datos:
                    tabla.añadir_fila_con_datos(fila)
                self.cambios_pendientes = True
                messagebox.showinfo("Éxito", f"Se importaron {len(datos)} filas")
    
    def ejecutar_exportacion(self, formato, tabla, nombre):
        GestionArchivosMejorado.exportar(tabla.obtener_datos(), nombre, formato)
    
    def sincronizar_nube(self):
        if not self.sesion_activa:
            if messagebox.askyesno("Iniciar sesión", "Para sincronizar necesita iniciar sesión. ¿Desea hacerlo ahora?"):
                self.withdraw()
                self.mostrar_login()
            return
        
        for nombre in list(self.tabview._tab_dict.keys()):
            tab = self.tabview.tab(nombre)
            for w in tab.winfo_children():
                if isinstance(w, TablaContableMejorada):
                    datos = w.obtener_datos()
                    DBManager.guardar_proyecto(nombre, datos, w.tipo_actual)
                    self.cloud.guardar_proyecto(nombre, w.tipo_actual, datos, w.encabezados)
                    break
        messagebox.showinfo("Sincronización", "Proyectos sincronizados con la nube")
        self.status_label.configure(text="Sincronización completada")
    
    def cargar_proyectos_existentes(self):
        for nombre, tipo in DBManager.obtener_todos_los_proyectos():
            self.añadir_pestaña(nombre, tipo or "Libro Diario", carga_inicial=True)
    
    def confirmar_salida(self):
        if self.cambios_pendientes:
            respuesta = messagebox.askyesnocancel("Salir", "Hay cambios sin guardar. ¿Desea guardarlos antes de salir?")
            if respuesta is True:
                for nombre in self.tabview._tab_dict.keys():
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
        self.geometry("380300")
        self.callback = callback
        self.attributes("-topmost", True)
        self.resizable(False, False)
        
        # Centrar
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 190
        y = (self.winfo_screenheight() // 2) - 150
        self.geometry(f"+{x}+{y}")
        
        frame = ctk.CTkFrame(self, fg_color=COLORES["fondo"])
        frame.pack(fill="both", expand=True, padx=25, pady=25)
        
        ctk.CTkLabel(
            frame, text="Nuevo proyecto",
            font=("Roboto", 18, "bold"),
            text_color=COLORES["principal"]
        ).pack(pady=(0, 20))
        
        ctk.CTkLabel(frame, text="Nombre del proyecto", font=("Roboto", 12)).pack(anchor="w", pady=(0, 5))
        self.entry_nombre = ctk.CTkEntry(frame, width=300, height=35)
        self.entry_nombre.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(frame, text="Tipo de plantilla", font=("Roboto", 12)).pack(anchor="w", pady=(0, 5))
        self.combo_tipo = ctk.CTkOptionMenu(
            frame,
            values=["Libro Diario", "Balanza de Comprobación", "Cuentas T / Mayor"],
            width=300
        )
        self.combo_tipo.pack(fill="x", pady=(0, 20))
        
        ctk.CTkButton(
            frame, text="Crear proyecto",
            command=self.enviar,
            fg_color=COLORES["principal"],
            height=40, corner_radius=6
        ).pack(fill="x")
    
    def enviar(self):
        nombre = self.entry_nombre.get().strip()
        tipo = self.combo_tipo.get()
        if nombre:
            self.callback(nombre, tipo)
            self.destroy()
        else:
            messagebox.showwarning("Aviso", "Ingrese un nombre para el proyecto")


if __name__ == "__main__":
    app = AppContable()
    app.mainloop()
