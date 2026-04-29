# main_ui.py - CORREGIDO

import customtkinter as ctk
from tkinter import messagebox
from tkinter import filedialog
from componentes_gui import TablaContable
from logica_contable import GestionArchivos, Plantillas
from database_manager import DBManager
from cloud_manager import CloudManager

class AppContable(ctk.CTk):
    def __init__(self):
        super().__init__()
        DBManager.inicializar()
        self.cloud = CloudManager()
        self.cloud.crear_sesion() 
        
        self.title("Contador Pro - Sistema de Gestión v2.0")
        self.geometry("1400x900")
        self.cambios_pendientes = False

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="CONTADOR PRO", font=("Roboto", 20, "bold"))
        self.logo_label.pack(pady=30, padx=20)

        self.btn_nuevo = ctk.CTkButton(self.sidebar, text="+ Nuevo Cliente", 
                                     command=self.abrir_ventana_nuevo,
                                     fg_color="#27ae60")
        self.btn_nuevo.pack(pady=10, padx=20, fill="x")

        self.btn_import_global = ctk.CTkButton(self.sidebar, text="Importar Excel/CSV", 
                                             command=self.importar_archivo_general,
                                             fg_color="#5d6d7e")
        self.btn_import_global.pack(pady=10, padx=20, fill="x")

        self.btn_cloud = ctk.CTkButton(self.sidebar, text="Sincronizar Nube", 
                             command=self.sincronizar_nube,
                             fg_color="#3498db")
        
        self.btn_cloud.pack(pady=10, padx=20, fill="x")

        self.status_bar = ctk.CTkFrame(self, height=25, fg_color=("gray90", "gray16"))
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.status_label = ctk.CTkLabel(self.status_bar, text="Listo", anchor="w")
        self.status_label.pack(side="left", padx=10)

        self.switch_tema = ctk.CTkSwitch(self.sidebar, text="Modo Oscuro", command=self.cambiar_tema)
        self.switch_tema.select() 
        self.switch_tema.pack(side="bottom", pady=20)

        # Panel principal
        self.main_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.main_panel.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_panel.grid_columnconfigure(0, weight=1)
        self.main_panel.grid_rowconfigure(0, weight=1)

        self.btn_reportes = ctk.CTkButton(
            self.sidebar,
            text="Generar Reportes",
            command=self.abrir_reportes,
            fg_color="#8e44ad"
        )
        self.btn_reportes.pack(pady=10, padx=20, fill="x")

        self.tabview = ctk.CTkTabview(self.main_panel)
        self.tabview.grid(row=0, column=0, sticky="nsew")

        self.cargar_proyectos_existentes()
        self.after(0, lambda: self.state('zoomed')) 
        self.protocol("WM_DELETE_WINDOW", self.confirmar_salida)
   
    def mostrar_login(self):
        """Ventana de inicio de sesión"""
        # Cerrar ventana principal temporalmente
        self.withdraw()
        
        login_win = ctk.CTkToplevel()
        login_win.title("Contador Pro - Iniciar Sesión")
        login_win.geometry("450x550")
        login_win.attributes("-topmost", True)
        login_win.grab_set()
        
        # Centrar ventana
        login_win.update_idletasks()
        x = (login_win.winfo_screenwidth() // 2) - 225
        y = (login_win.winfo_screenheight() // 2) - 275
        login_win.geometry(f"+{x}+{y}")
        
        # Frame principal
        main_frame = ctk.CTkFrame(login_win, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Logo y título
        ctk.CTkLabel(main_frame, text="📊", font=("Roboto", 48)).pack(pady=10)
        ctk.CTkLabel(main_frame, text="CONTADOR PRO", font=("Roboto", 28, "bold")).pack()
        ctk.CTkLabel(main_frame, text="Sistema de Gestión Contable Cloud", 
                    font=("Roboto", 12), text_color="gray").pack(pady=(0, 30))
        
        # Pestañas Login / Registro
        tabview = ctk.CTkTabview(main_frame, width=350)
        tabview.pack()
        
        tab_login = tabview.add("Iniciar Sesión")
        tab_registro = tabview.add("Registrarse")
        
        # ===== TAB LOGIN =====
        ctk.CTkLabel(tab_login, text="Email").pack(pady=(20, 5))
        entry_email = ctk.CTkEntry(tab_login, width=280, placeholder_text="usuario@ejemplo.com")
        entry_email.pack()
        
        ctk.CTkLabel(tab_login, text="Contraseña").pack(pady=(15, 5))
        entry_password = ctk.CTkEntry(tab_login, width=280, show="*", placeholder_text="••••••••")
        entry_password.pack()
        
        lbl_error = ctk.CTkLabel(tab_login, text="", text_color="#e74c3c")
        lbl_error.pack(pady=5)
        
        def do_login():
            email = entry_email.get().strip()
            password = entry_password.get()
            
            if not email or not password:
                lbl_error.configure(text="Completa todos los campos")
                return
            
            lbl_error.configure(text="Conectando...", text_color="#3498db")
            login_win.update()
            
            success, resultado = self.cloud.login(email, password)
            
            if success:
                login_win.destroy()
                self.deiconify()  # Mostrar ventana principal
                self.status_label.configure(text=f"Bienvenido, {resultado.get('nombre', email)}")
                self.cargar_proyectos_existentes()  # Cargar proyectos del usuario
                messagebox.showinfo("Bienvenido", f"Has iniciado sesión como {email}")
            else:
                lbl_error.configure(text=resultado, text_color="#e74c3c")
        
        ctk.CTkButton(tab_login, text="INGRESAR", command=do_login, 
                    fg_color="#27ae60", height=40).pack(pady=20)
        
        # ===== TAB REGISTRO =====
        ctk.CTkLabel(tab_registro, text="Nombre completo").pack(pady=(20, 5))
        reg_nombre = ctk.CTkEntry(tab_registro, width=280, placeholder_text="Tu nombre")
        reg_nombre.pack()
        
        ctk.CTkLabel(tab_registro, text="Email").pack(pady=(15, 5))
        reg_email = ctk.CTkEntry(tab_registro, width=280, placeholder_text="usuario@ejemplo.com")
        reg_email.pack()
        
        ctk.CTkLabel(tab_registro, text="Contraseña").pack(pady=(15, 5))
        reg_password = ctk.CTkEntry(tab_registro, width=280, show="*", placeholder_text="Mínimo 6 caracteres")
        reg_password.pack()
        
        ctk.CTkLabel(tab_registro, text="Confirmar contraseña").pack(pady=(15, 5))
        reg_password2 = ctk.CTkEntry(tab_registro, width=280, show="*")
        reg_password2.pack()
        
        lbl_reg_error = ctk.CTkLabel(tab_registro, text="", text_color="#e74c3c")
        lbl_reg_error.pack(pady=5)
        
        def do_registro():
            nombre = reg_nombre.get().strip()
            email = reg_email.get().strip()
            password = reg_password.get()
            password2 = reg_password2.get()
            
            if not all([nombre, email, password]):
                lbl_reg_error.configure(text="Completa todos los campos")
                return
            
            if len(password) < 6:
                lbl_reg_error.configure(text="La contraseña debe tener al menos 6 caracteres")
                return
            
            if password != password2:
                lbl_reg_error.configure(text="Las contraseñas no coinciden")
                return
            
            lbl_reg_error.configure(text="Creando cuenta...", text_color="#3498db")
            login_win.update()
            
            success, mensaje = self.cloud.registrar_usuario(email, password, nombre)
            
            if success:
                lbl_reg_error.configure(text="Cuenta creada! Ahora inicia sesión", text_color="#27ae60")
                tabview.set("Iniciar Sesión")
                entry_email.delete(0, "end")
                entry_email.insert(0, email)
            else:
                lbl_reg_error.configure(text=mensaje, text_color="#e74c3c")
        
        ctk.CTkButton(tab_registro, text="CREAR CUENTA", command=do_registro,
                    fg_color="#3498db", height=40).pack(pady=20)
        
        # Botón offline (para trabajar sin conexión)
        ctk.CTkButton(main_frame, text="💾 Trabajar sin conexión", 
                    command=lambda: [login_win.destroy(), self.deiconify()],
                    fg_color="transparent", hover_color="#555").pack(pady=10)

    def generar_balance(self):
        """Genera reporte de Balance General"""
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        
        # Obtener datos del proyecto actual
        nombre_proyecto = self.tabview.get()
        if not nombre_proyecto:
            
            messagebox.showwarning("Aviso", "Selecciona un proyecto primero")
            return
        
        tab = self.tabview.tab(nombre_proyecto)
        tabla = None
        for widget in tab.winfo_children():
            if isinstance(widget, TablaContable):
                tabla = widget
                break
        
        if not tabla:
            messagebox.showwarning("Aviso", "No hay datos para generar reporte")
            return
        
        datos = tabla.obtener_datos()
        
        # Calcular activos, pasivos, capital
        total_activos = 0
        total_pasivos = 0
        total_capital = 0
        
        # Buscar columnas relevantes
        idx_debe = next((i for i, c in enumerate(tabla.encabezados) if c.lower() == "debe"), -1)
        idx_haber = next((i for i, c in enumerate(tabla.encabezados) if c.lower() == "haber"), -1)
        
        for fila in datos:
            if idx_debe >= 0 and idx_debe < len(fila):
                try:
                    valor = float(fila[idx_debe].replace(',', '') or 0)
                    # Clasificación simple (puedes mejorarla con keywords)
                    desc = " ".join(fila).lower()
                    if "activo" in desc or "caja" in desc or "banco" in desc:
                        total_activos += valor
                    elif "pasivo" in desc or "cuenta por pagar" in desc:
                        total_pasivos += valor
                    else:
                        total_capital += valor
                except:
                    pass
        
        # Generar PDF
        ruta = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"Balance_{nombre_proyecto}"
        )
        
        if ruta:
            doc = SimpleDocTemplate(ruta, pagesize=letter)
            styles = getSampleStyleSheet()
            elementos = []
            
            titulo = Paragraph(f"<b>BALANCE GENERAL</b><br/>{nombre_proyecto}", styles['Title'])
            elementos.append(titulo)
            elementos.append(Spacer(1, 20))
            
            # Tabla de balance
            balance_data = [
                ["ACTIVOS", f"${total_activos:,.2f}"],
                ["PASIVOS", f"${total_pasivos:,.2f}"],
                ["CAPITAL", f"${total_capital:,.2f}"],
                ["", ""],
                ["TOTAL ACTIVO = PASIVO + CAPITAL", f"${total_activos:,.2f} = ${total_pasivos + total_capital:,.2f}"]
            ]
            
            t = Table(balance_data, colWidths=[300, 150])
            t.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#34495e")),
                ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#2c3e50")),
                ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor("#34495e")),
                ('TEXTCOLOR', (0, 0), (-1, 2), colors.whitesmoke),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elementos.append(t)
            
            doc.build(elementos)
            messagebox.showinfo("Éxito", f"Balance guardado en {ruta}")

    def generar_resultados(self):
        """Genera reporte de Estado de Resultados"""
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        
        nombre_proyecto = self.tabview.get()
        if not nombre_proyecto:
            messagebox.showwarning("Aviso", "Selecciona un proyecto primero")
            return
        
        tab = self.tabview.tab(nombre_proyecto)
        tabla = None
        for widget in tab.winfo_children():
            if isinstance(widget, TablaContable):
                tabla = widget
                break
        
        if not tabla:
            messagebox.showwarning("Aviso", "No hay datos para generar reporte")
            return
        
        datos = tabla.obtener_datos()
        
        total_ingresos = 0
        total_gastos = 0
        
        idx_debe = next((i for i, c in enumerate(tabla.encabezados) if c.lower() == "debe"), -1)
        idx_haber = next((i for i, c in enumerate(tabla.encabezados) if c.lower() == "haber"), -1)
        
        for fila in datos:
            texto = " ".join(fila).lower()
            valor = 0
            if idx_debe >= 0 and idx_debe < len(fila):
                try:
                    valor = float(fila[idx_debe].replace(',', '') or 0)
                except:
                    pass
            
            if "ingreso" in texto or "venta" in texto:
                total_ingresos += valor
            elif "gasto" in texto or "costo" in texto:
                total_gastos += valor
        
        utilidad_neta = total_ingresos - total_gastos
        
        ruta = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"Resultados_{nombre_proyecto}"
        )
        
        if ruta:
            doc = SimpleDocTemplate(ruta, pagesize=letter)
            styles = getSampleStyleSheet()
            elementos = []
            
            titulo = Paragraph(f"<b>ESTADO DE RESULTADOS</b><br/>{nombre_proyecto}", styles['Title'])
            elementos.append(titulo)
            elementos.append(Spacer(1, 20))
            
            resultados_data = [
                ["INGRESOS", f"${total_ingresos:,.2f}"],
                ["GASTOS", f"${total_gastos:,.2f}"],
                ["", ""],
                ["UTILIDAD NETA", f"${utilidad_neta:,.2f}", 
                "(Utilidad)" if utilidad_neta > 0 else "(Pérdida)"]
            ]
            
            t = Table(resultados_data, colWidths=[300, 100, 100])
            t.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#27ae60")),
                ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#e74c3c")),
                ('TEXTCOLOR', (0, 0), (-1, 1), colors.whitesmoke),
                ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor("#34495e") if utilidad_neta > 0 else colors.HexColor("#c0392b")),
                ('TEXTCOLOR', (0, 3), (-1, 3), colors.whitesmoke),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elementos.append(t)
            
            doc.build(elementos)
            messagebox.showinfo("Éxito", f"Estado de Resultados guardado en {ruta}")

    def set_status(self, message, duration=3000):
        self.status_label.configure(text=message)
        self.after(duration, lambda: self.status_label.configure(text="Listo"))

    def confirmar_salida(self):
        if self.cambios_pendientes:
            msg = messagebox.askyesnocancel("Salir", "¿Deseas guardar los cambios antes de salir?")
            if msg is True:
                messagebox.showinfo("Guardado", "Todo se ha guardado.")
                self.destroy()
            elif msg is False:
                self.destroy()
        else:
            self.destroy()
   
    def abrir_reportes(self):
        top = ctk.CTkToplevel(self)
        top.title("Reportes Contables")
        top.geometry("400x300")
        top.attributes("-topmost", True)
        top.grab_set()
        
        # Frame principal
        frame = ctk.CTkFrame(top)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Generar Reportes", font=("Roboto", 16, "bold")).pack(pady=10)
        ctk.CTkFrame(frame, height=2, fg_color="gray").pack(fill="x", pady=10)
        
        btn_balance = ctk.CTkButton(frame, text="📊 Balance General", 
                                    command=lambda: [top.destroy(), self.generar_balance()],
                                    fg_color="#2c3e50", height=50, font=("Roboto", 14))
        btn_balance.pack(pady=10, fill="x")
        
        btn_resultados = ctk.CTkButton(frame, text="📈 Estado de Resultados",
                                    command=lambda: [top.destroy(), self.generar_resultados()],
                                    fg_color="#27ae60", height=50, font=("Roboto", 14))
        btn_resultados.pack(pady=10, fill="x")
        
        btn_cancel = ctk.CTkButton(frame, text="Cancelar", 
                                command=top.destroy,
                                fg_color="transparent", hover_color="#e74c3c")
        btn_cancel.pack(pady=10)
    
    def handle_errors(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error: {str(e)}")
                return None
        return wrapper

    def construir_interfaz_pestana(self, tab, nombre, carga_inicial=False, tipo_plantilla="Libro Diario"):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        
        # Barra superior
        sub_bar = ctk.CTkFrame(tab, height=50, fg_color=("gray90", "gray16"))
        sub_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10), padx=5)
        
        # Botón Añadir Fila (izquierda)
        btn_add = ctk.CTkButton(sub_bar, text="+ Fila", width=80)
        btn_add.pack(side="left", padx=10)
        
        # Botón ELIMINAR PROYECTO (junto al guardar)
        btn_delete_proyecto = ctk.CTkButton(sub_bar, text="Eliminar Proyecto", fg_color="#c0392b", width=120,
                                           command=lambda: self.accion_eliminar(nombre))
        btn_delete_proyecto.pack(side="right", padx=5)
        
        # Botón Guardar
        btn_guardar = ctk.CTkButton(sub_bar, text="Guardar", fg_color="#1e8449", width=90)
        btn_guardar.pack(side="right", padx=5)
        
        # Menú de Exportar
        ctk.CTkLabel(sub_bar, text="Exportar:").pack(side="right", padx=5)
        export_menu = ctk.CTkOptionMenu(sub_bar, values=["Excel", "PDF"], width=100)
        export_menu.pack(side="right", padx=5)
        
        # Crear tabla
        columnas = Plantillas.obtener_columnas(tipo_plantilla)
        tabla = TablaContable(tab, columnas=columnas, tipo=tipo_plantilla)
        tabla.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Conectar eventos después de crear la tabla
        btn_add.configure(command=tabla.añadir_fila)
        btn_guardar.configure(command=lambda: self.accion_guardar(tabla, nombre))
        export_menu.configure(command=lambda v: self.ejecutar_exportacion(v, tabla, nombre))
        
        if carga_inicial:
            datos = DBManager.obtener_datos_proyecto(nombre)
            if datos:
                tabla.limpiar_tabla()
                for fila in datos:
                    tabla.añadir_fila_con_datos(fila)

    def abrir_ventana_nuevo(self):
        VentanaNuevoTrabajo(self, self.añadir_pestaña)

    def importar_archivo_general(self):
        nombre_cliente = self.tabview.get()
        if not nombre_cliente:
            messagebox.showwarning("Aviso", "Primero selecciona o crea una pestaña de cliente.")
            return

        columnas, datos = GestionArchivos.leer_archivo_para_importar()

        if datos:
            try:
                tab_objeto = self.tabview.tab(nombre_cliente)
                tabla_activa = None
                for widget in tab_objeto.winfo_children():
                    if isinstance(widget, TablaContable):
                        tabla_activa = widget
                        break
            
                if tabla_activa:
                    if messagebox.askyesno("Confirmar", "¿Deseas reemplazar las columnas actuales por las del archivo?"):
                        tabla_activa.encabezados = columnas
                        tabla_activa.dibujar_encabezados()
                    
                    tabla_activa.limpiar_tabla()
                    for fila in datos:
                        tabla_activa.añadir_fila(datos=fila)
                    
                    self.cambios_pendientes = True
                    messagebox.showinfo("Éxito", f"Se han importado {len(datos)} filas en '{nombre_cliente}'.")
                
            except Exception as e:
                messagebox.showerror("Error de Interfaz", f"Error al volcar datos en la tabla: {e}")
            
    def añadir_pestaña(self, nombre, tipo="Libro Diario", carga_inicial=False):
        if nombre in self.tabview._tab_dict:
            messagebox.showwarning("Aviso", "Este cliente ya está abierto.")
            return
        
        tab = self.tabview.add(nombre)
        self.construir_interfaz_pestana(tab, nombre, carga_inicial=carga_inicial, tipo_plantilla=tipo)
        self.tabview.set(nombre)

    def accion_guardar(self, tabla, nombre):
        datos = tabla.obtener_datos()
        DBManager.guardar_proyecto(nombre, datos, tabla.tipo_actual)
        self.cambios_pendientes = False
        messagebox.showinfo("Éxito", f"Datos de {nombre} guardados.")

    def sincronizar_nube(self):
        """Sincroniza TODOS los proyectos con la nube"""
        
        # Mostrar ventana de progreso
        progress = ctk.CTkToplevel(self)
        progress.title("Sincronizando")
        progress.geometry("300x100")
        progress.attributes('-topmost', True)
        
        ctk.CTkLabel(progress, text="Subiendo proyectos a la nube...").pack(pady=20)
        bar = ctk.CTkProgressBar(progress, mode="indeterminate")
        bar.pack(pady=10, padx=20, fill="x")
        bar.start()
        
        def guardar_proyecto(tab, nombre, tipo, tabla):
            """Guarda un proyecto individual"""
            datos = tabla.obtener_datos()
            columnas = tabla.encabezados
            
            # Usar el callback para saber cuando termina
            def on_complete(success, message):
                if success:
                    print(f"✓ {nombre} sincronizado")
                else:
                    print(f"✗ {nombre}: {message}")
            
            self.cloud.guardar_proyecto(nombre, tipo, datos, columnas, on_complete)
        
        # Sincronizar cada pestaña abierta
        for nombre in self.tabview._tab_dict.keys():
            tab = self.tabview.tab(nombre)
            # Buscar la tabla en la pestaña
            for widget in tab.winfo_children():
                if isinstance(widget, TablaContable):
                    guardar_proyecto(tab, nombre, widget.tipo_actual, widget)
                    break
        
        # Cerrar ventana después de un momento
        self.after(2000, lambda: [bar.stop(), progress.destroy(), 
                                messagebox.showinfo("Sincronización", 
                                "Proyectos sincronizados con la nube")])

    def cambiar_tema(self):
        mode = "dark" if self.switch_tema.get() == 1 else "light"
        ctk.set_appearance_mode(mode)

    def accion_eliminar(self, nombre):
        if messagebox.askyesno("Confirmar", f"¿Eliminar permanentemente el proyecto '{nombre}'?"):
            DBManager.eliminar_proyecto(nombre)
            self.tabview.delete(nombre)
            messagebox.showinfo("Eliminado", f"Proyecto '{nombre}' eliminado.")

    def cargar_proyectos_existentes(self):
        """Carga proyectos de la base de datos local Y de la nube"""
        
        # Primero cargar locales
        for nombre, tipo in DBManager.obtener_todos_los_proyectos():
            self.añadir_pestaña(nombre, tipo or "Libro Diario", carga_inicial=True)
        
        # Luego cargar de la nube (en segundo plano)
        def on_cloud_load(success, proyectos):
            if success and proyectos:
                for proyecto in proyectos:
                    nombre = proyecto["name"]
                    # Si no existe localmente, agregarlo
                    if nombre not in self.tabview._tab_dict:
                        self.añadir_pestaña(
                            nombre, 
                            proyecto.get("type", "Libro Diario"), 
                            carga_inicial=False
                        )
                        # Cargar los datos en la nueva pestaña
                        tab = self.tabview.tab(nombre)
                        for widget in tab.winfo_children():
                            if isinstance(widget, TablaContable):
                                widget.limpiar_tabla()
                                for fila in proyecto.get("data", []):
                                    widget.añadir_fila_con_datos(fila)
                                break
        
        self.cloud.cargar_proyectos(on_cloud_load)

    def ejecutar_exportacion(self, formato, tabla, nombre):
        GestionArchivos.exportar(tabla.obtener_datos(), nombre, formato)


class VentanaNuevoTrabajo(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("Nuevo Proyecto")
        self.geometry("400x300")
        self.callback = callback
        self.attributes('-topmost', True)

        ctk.CTkLabel(self, text="Nombre del Cliente:").pack(pady=(20,5))
        self.ent_nombre = ctk.CTkEntry(self, width=250)
        self.ent_nombre.pack(pady=5)

        ctk.CTkLabel(self, text="Tipo de Plantilla:").pack(pady=(10,5))
        self.combo_tipo = ctk.CTkOptionMenu(self, values=["Libro Diario", "Balanza de Comprobación", "Cuentas T / Mayor"])
        self.combo_tipo.pack(pady=5)

        ctk.CTkButton(self, text="CREAR", fg_color="#27ae60", command=self.enviar).pack(pady=20)

    def enviar(self):
        n = self.ent_nombre.get().strip()
        t = self.combo_tipo.get()
        if n:
            self.callback(n, t)
            self.destroy()


if __name__ == "__main__":
    app = AppContable()
    app.mainloop()