# main_ui.py - VERSIÓN CORREGIDA (Escritorio)

import customtkinter as ctk
from tkinter import messagebox, filedialog, Toplevel, simpledialog
from datetime import datetime
import re
import pandas as pd
from io import BytesIO

# Importar módulos existentes
from componentes_gui import TablaContableMejorada, VentanaGraficasMejorada
from logica_contable import GestionArchivosMejorado, Plantillas, FormulaEngine
from database_manager import DBManager
from cloud_manager import CloudManager

class AppContable(ctk.CTk):
    def __init__(self):
        super().__init__()
        DBManager.inicializar()
        self.cloud = CloudManager()
        
        # CORRECCIÓN 4: Sesión persistente
        self.sesion_activa = False
        self.usuario_actual = None
        
        self.title("Contaduria - Sistema de contabilidad v3.0")
        self.geometry("1400x900")
        self.cambios_pendientes = False
        
        # Ocultar ventana principal hasta login
        self.withdraw()
        
        # Mostrar login primero
        self.mostrar_login()
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="CONTADURIA", font=("Roboto", 22, "bold"))
        self.logo_label.pack(pady=30, padx=20)
        
        self.btn_nuevo = ctk.CTkButton(self.sidebar, text="Nuevo Cliente", 
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
        
        self.btn_reportes = ctk.CTkButton(
            self.sidebar,
            text="Generar Reportes",
            command=self.abrir_reportes,
            fg_color="#8e44ad"
        )
        self.btn_reportes.pack(pady=10, padx=20, fill="x")
        
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
        
        self.tabview = ctk.CTkTabview(self.main_panel)
        self.tabview.grid(row=0, column=0, sticky="nsew")
        
        self.after(0, lambda: self.state('zoomed'))
        self.protocol("WM_DELETE_WINDOW", self.confirmar_salida)
    
    def mostrar_login(self):
        """Ventana de inicio de sesión CORREGIDA - No se cierra completamente"""
        login_win = ctk.CTkToplevel()
        login_win.title("Contaduria - Iniciar Sesión")
        login_win.geometry("450x550")
        login_win.attributes("-topmost", True)
        login_win.grab_set()
        
        # Referencia para poder cerrar después
        self.login_ventana = login_win
        
        login_win.update_idletasks()
        x = (login_win.winfo_screenwidth() // 2) - 225
        y = (login_win.winfo_screenheight() // 2) - 275
        login_win.geometry(f"+{x}+{y}")
        
        main_frame = ctk.CTkFrame(login_win, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=40, pady=40)
        
        ctk.CTkLabel(main_frame, text="CONTADURIA", font=("Roboto", 32, "bold")).pack(pady=10)
        ctk.CTkLabel(main_frame, text="Sistema de Gestión Contable Cloud", 
                    font=("Roboto", 12), text_color="gray").pack(pady=(0, 30))
        
        tabview = ctk.CTkTabview(main_frame, width=350)
        tabview.pack()
        
        tab_login = tabview.add("Iniciar Sesión")
        tab_registro = tabview.add("Registrarse")
        
        # Login
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
                lbl_error.configure(text="Complete todos los campos")
                return
            
            lbl_error.configure(text="Conectando...", text_color="#3498db")
            login_win.update()
            
            success, resultado = self.cloud.login(email, password)
            if success:
                self.sesion_activa = True
                self.usuario_actual = email
                login_win.destroy()
                self.deiconify()
                self.status_label.configure(text=f"Bienvenido, {resultado.get('nombre', email)}")
                self.cargar_proyectos_existentes()
                messagebox.showinfo("Bienvenido", f"Has iniciado sesión como {email}")
            else:
                lbl_error.configure(text=resultado, text_color="#e74c3c")
        
        ctk.CTkButton(tab_login, text="INGRESAR", command=do_login, 
                    fg_color="#27ae60", height=40).pack(pady=20)
        
        # Registro
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
                lbl_reg_error.configure(text="Complete todos los campos")
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
        
        # CORRECCIÓN: Opción para trabajar offline
        def trabajar_offline():
            login_win.destroy()
            self.sesion_activa = False
            self.deiconify()
            self.status_label.configure(text="Modo offline - Los datos no se sincronizarán")
            self.btn_cloud.configure(state="disabled", text="Modo Offline")
            self.cargar_proyectos_existentes()
        
        ctk.CTkButton(main_frame, text="Trabajar sin conexión", 
                    command=trabajar_offline,
                    fg_color="transparent", hover_color="#555").pack(pady=10)
    
    def construir_interfaz_pestana(self, tab, nombre, carga_inicial=False, tipo_plantilla="Libro Diario"):
        """Construye la pestaña con la tabla mejorada"""
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)
        
        # Barra superior de herramientas
        toolbar = ctk.CTkFrame(tab, height=50, fg_color=("gray90", "gray16"))
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10), padx=5)
        
        # Botones de filas
        btn_add = ctk.CTkButton(toolbar, text="+ Fila", width=80)
        btn_add.pack(side="left", padx=5)
        
        btn_remove_last = ctk.CTkButton(toolbar, text="- Última", width=80, fg_color="#e67e22")
        btn_remove_last.pack(side="left", padx=5)
        
        # Herramientas de cálculo
        ctk.CTkLabel(toolbar, text="   |   Cálculos:").pack(side="left", padx=5)
        
        btn_formula = ctk.CTkButton(toolbar, text="Fórmula", width=80, fg_color="#8e44ad")
        btn_formula.pack(side="left", padx=5)
        
        btn_calculadora = ctk.CTkButton(toolbar, text="Calculadora", width=90, fg_color="#16a085")
        btn_calculadora.pack(side="left", padx=5)
        
        btn_estadisticas = ctk.CTkButton(toolbar, text="Estadísticas", width=90, fg_color="#2980b9")
        btn_estadisticas.pack(side="left", padx=5)
        
        btn_graficas = ctk.CTkButton(toolbar, text="Gráficas", width=80, fg_color="#c0392b")
        btn_graficas.pack(side="left", padx=5)
        
        # Separador
        ctk.CTkLabel(toolbar, text="   |   ").pack(side="left", padx=5)
        
        # Exportar
        ctk.CTkLabel(toolbar, text="Exportar:").pack(side="left", padx=5)
        export_menu = ctk.CTkOptionMenu(toolbar, values=["Excel", "PDF"], width=100)
        export_menu.pack(side="left", padx=5)
        
        # Botones derecha
        btn_guardar = ctk.CTkButton(toolbar, text="Guardar", fg_color="#1e8449", width=90)
        btn_guardar.pack(side="right", padx=5)
        
        btn_delete_proyecto = ctk.CTkButton(toolbar, text="Eliminar Proyecto", fg_color="#c0392b", width=120,
                                           command=lambda: self.accion_eliminar(nombre))
        btn_delete_proyecto.pack(side="right", padx=5)
        
        # Crear tabla mejorada
        columnas = Plantillas.obtener_columnas(tipo_plantilla)
        tabla = TablaContableMejorada(tab, columnas=columnas, tipo=tipo_plantilla, nombre_proyecto=nombre)
        tabla.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        
        # Conectar eventos
        btn_add.configure(command=tabla.añadir_fila)
        btn_remove_last.configure(command=tabla.eliminar_ultima_fila)
        btn_formula.configure(command=lambda: self.abrir_gestor_formulas(tabla))
        btn_calculadora.configure(command=lambda: self.abrir_calculadora_rapida(tabla))
        # CORRECCIÓN 2: Pasar la referencia correcta de tabla
        btn_estadisticas.configure(command=lambda t=tabla: self.mostrar_estadisticas(t))
        btn_graficas.configure(command=lambda: self.abrir_graficas(tabla, nombre))
        btn_guardar.configure(command=lambda: self.accion_guardar(tabla, nombre))
        export_menu.configure(command=lambda v: self.ejecutar_exportacion(v, tabla, nombre))
        
        if carga_inicial:
            datos = DBManager.obtener_datos_proyecto(nombre)
            if datos:
                tabla.limpiar_tabla()
                for fila in datos:
                    tabla.añadir_fila_con_datos(fila)
    
    def abrir_gestor_formulas(self, tabla):
        """Abre el gestor de fórmulas"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Gestor de Fórmulas")
        dialog.geometry("600x500")
        dialog.attributes("-topmost", True)
        dialog.grab_set()
        
        notebook = ctk.CTkTabview(dialog)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # TAB 1: Nueva columna
        tab_nueva = notebook.add("Nueva Columna")
        ctk.CTkLabel(tab_nueva, text="Nombre de la nueva columna:").pack(pady=10)
        entry_nombre = ctk.CTkEntry(tab_nueva, width=300)
        entry_nombre.pack()
        
        ctk.CTkLabel(tab_nueva, text="Fórmula (ej: =[Debe] - [Haber]):").pack(pady=10)
        entry_formula = ctk.CTkEntry(tab_nueva, width=500)
        entry_formula.pack()
        
        # Mostrar columnas disponibles
        ctk.CTkLabel(tab_nueva, text="Columnas disponibles:", font=("Roboto", 10)).pack(pady=5)
        cols_frame = ctk.CTkFrame(tab_nueva)
        cols_frame.pack(pady=5)
        for col in tabla.encabezados:
            ctk.CTkLabel(cols_frame, text=f"[{col}]", font=("Roboto", 9)).pack(side="left", padx=5)
        
        def crear_columna():
            nombre = entry_nombre.get().strip()
            formula = entry_formula.get().strip()
            if nombre and formula:
                df = tabla.obtener_dataframe()
                if formula.startswith('='):
                    formula = formula[1:]
                resultado = FormulaEngine.aplicar_formula_columna(df, nombre, formula, por_fila=True)
                if resultado is not None:
                    # Agregar columna a la tabla
                    tabla.agregar_columna(nombre)
                    for idx, valor in enumerate(resultado):
                        if idx < len(tabla.filas):
                            tabla.filas[idx][-1].delete(0, "end")
                            tabla.filas[idx][-1].insert(0, str(valor) if not isinstance(valor, (int, float)) else f"{valor:,.2f}")
                    messagebox.showinfo("Éxito", f"Columna '{nombre}' creada")
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "Fórmula inválida")
        
        ctk.CTkButton(tab_nueva, text="Crear Columna", command=crear_columna, fg_color="#27ae60").pack(pady=20)
        
        # TAB 2: Sugerencias
        tab_sugerencias = notebook.add("Sugerencias")
        sugerencias = FormulaEngine.sugerir_formulas(pd.DataFrame(columns=tabla.encabezados))
        
        for sug in sugerencias:
            frame = ctk.CTkFrame(tab_sugerencias)
            frame.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(frame, text=f"{sug['nombre']}: {sug['descripcion']}", font=("Roboto", 11)).pack(side="left", padx=10)
            ctk.CTkLabel(frame, text=sug['formula'], font=("Roboto", 10, "italic")).pack(side="left", padx=10)
    
    def abrir_calculadora_rapida(self, tabla):
        """Abre la calculadora rápida"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Calculadora Rápida")
        dialog.geometry("500x400")
        dialog.attributes("-topmost", True)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Operaciones entre columnas", font=("Roboto", 14, "bold")).pack(pady=10)
        
        # Selectores de columnas
        cols_frame = ctk.CTkFrame(dialog)
        cols_frame.pack(pady=10)
        
        ctk.CTkLabel(cols_frame, text="Columna A:").grid(row=0, column=0, padx=5)
        col_a = ctk.CTkOptionMenu(cols_frame, values=tabla.encabezados, width=120)
        col_a.grid(row=1, column=0, padx=5)
        
        ctk.CTkLabel(cols_frame, text="Operación:").grid(row=0, column=1, padx=5)
        operacion = ctk.CTkOptionMenu(cols_frame, values=["+", "-", "*", "/", "%"], width=80)
        operacion.grid(row=1, column=1, padx=5)
        
        ctk.CTkLabel(cols_frame, text="Columna B:").grid(row=0, column=2, padx=5)
        col_b = ctk.CTkOptionMenu(cols_frame, values=["(Constante)"] + tabla.encabezados, width=120)
        col_b.grid(row=1, column=2, padx=5)
        
        ctk.CTkLabel(dialog, text="Nombre del resultado:").pack(pady=10)
        entry_resultado = ctk.CTkEntry(dialog, width=300)
        entry_resultado.pack()
        
        # Constante
        frame_const = ctk.CTkFrame(dialog)
        frame_const.pack(pady=10)
        ctk.CTkLabel(frame_const, text="Valor constante:").pack(side="left", padx=5)
        entry_const = ctk.CTkEntry(frame_const, width=100)
        entry_const.pack(side="left", padx=5)
        entry_const.insert(0, "0")
        
        def calcular():
            nombre = entry_resultado.get().strip()
            if not nombre:
                messagebox.showwarning("Aviso", "Ingrese un nombre para el resultado")
                return
            
            df = tabla.obtener_dataframe()
            col_a_val = col_a.get()
            op = operacion.get()
            col_b_val = col_b.get()
            
            try:
                if col_b_val == "(Constante)":
                    constante = float(entry_const.get() or 0)
                    if op == "+":
                        resultado = df[col_a_val] + constante
                    elif op == "-":
                        resultado = df[col_a_val] - constante
                    elif op == "*":
                        resultado = df[col_a_val] * constante
                    elif op == "/":
                        resultado = df[col_a_val] / constante if constante != 0 else 0
                    elif op == "%":
                        resultado = df[col_a_val] * (constante / 100)
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
                
                # Agregar columna
                tabla.agregar_columna(nombre)
                for idx, valor in enumerate(resultado):
                    if idx < len(tabla.filas):
                        tabla.filas[idx][-1].delete(0, "end")
                        tabla.filas[idx][-1].insert(0, f"{float(valor):,.2f}")
                
                messagebox.showinfo("Éxito", f"Columna '{nombre}' creada")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al calcular: {str(e)}")
        
        ctk.CTkButton(dialog, text="Calcular", command=calcular, fg_color="#27ae60").pack(pady=20)
    
    # CORRECCIÓN 2: Mostrar estadísticas corregido
    def mostrar_estadisticas(self, tabla):
        """Muestra estadísticas de las columnas numéricas - CORREGIDO"""
        try:
            # Verificar que tabla existe
            if not tabla:
                messagebox.showerror("Error", "No se encontró la tabla activa")
                return
            
            df = tabla.obtener_dataframe()
            
            if df.empty or len(df) == 0:
                messagebox.showinfo("Info", "No hay datos para analizar")
                return
            
            columnas_numericas = df.select_dtypes(include=['number']).columns.tolist()
            
            if not columnas_numericas:
                # Intentar convertir columnas que parecen numéricas
                for col in df.columns:
                    try:
                        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
                        if df[col].notna().any():
                            columnas_numericas.append(col)
                    except:
                        pass
            
            if not columnas_numericas:
                messagebox.showinfo("Info", "No hay columnas numéricas para analizar")
                return
            
            dialog = ctk.CTkToplevel(self)
            dialog.title("Estadísticas de Columnas")
            dialog.geometry("700x500")
            dialog.attributes("-topmost", True)
            
            # Crear frame con scroll
            scroll_frame = ctk.CTkScrollableFrame(dialog)
            scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            for col in columnas_numericas:
                frame = ctk.CTkFrame(scroll_frame)
                frame.pack(fill="x", pady=5)
                
                # Limpiar valores NaN
                valores_limpios = df[col].fillna(0)
                
                ctk.CTkLabel(frame, text=col, font=("Roboto", 12, "bold")).pack(side="left", padx=10)
                
                stats = [
                    f"Suma: ${valores_limpios.sum():,.2f}",
                    f"Promedio: ${valores_limpios.mean():,.2f}",
                    f"Mín: ${valores_limpios.min():,.2f}",
                    f"Máx: ${valores_limpios.max():,.2f}",
                    f"Registros: {len(valores_limpios)}"
                ]
                
                for stat in stats:
                    ctk.CTkLabel(frame, text=stat, font=("Roboto", 10)).pack(side="left", padx=10)
            
            # Botón para agregar fila de totales
            def agregar_totales():
                total_row = {}
                for col in columnas_numericas:
                    total_row[col] = df[col].fillna(0).sum()
                for col in df.columns:
                    if col not in total_row:
                        total_row[col] = "TOTAL"
                tabla.añadir_fila_con_datos([str(total_row.get(c, "")) for c in tabla.encabezados])
                messagebox.showinfo("Éxito", "Fila de totales agregada")
                dialog.destroy()
            
            ctk.CTkButton(dialog, text="Agregar fila de totales", command=agregar_totales, fg_color="#27ae60").pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al mostrar estadísticas: {str(e)}")
    
    def abrir_graficas(self, tabla, nombre_proyecto):
        """Abre la ventana de gráficas mejorada"""
        datos = tabla.obtener_datos()
        if datos and len(datos) > 0:
            VentanaGraficasMejorada(self, datos, tabla.encabezados, nombre_proyecto)
        else:
            messagebox.showwarning("Aviso", "No hay datos para generar gráficas")
    
    def generar_balance_mejorado(self):
        """Genera Balance General mejorado"""
        nombre_proyecto = self.tabview.get()
        if not nombre_proyecto:
            messagebox.showwarning("Aviso", "Selecciona un proyecto primero")
            return
        
        tab = self.tabview.tab(nombre_proyecto)
        tabla = None
        # Buscar la tabla en los widgets de la pestaña
        for widget in tab.winfo_children():
            if isinstance(widget, TablaContableMejorada):
                tabla = widget
                break
            # Buscar también dentro de frames anidados
            if hasattr(widget, 'winfo_children'):
                for child in widget.winfo_children():
                    if isinstance(child, TablaContableMejorada):
                        tabla = child
                        break
        
        if not tabla:
            messagebox.showwarning("Aviso", "No hay datos para generar reporte")
            return
        
        df = tabla.obtener_dataframe()
        
        if df.empty:
            messagebox.showwarning("Aviso", "No hay datos en la tabla")
            return
        
        # Palabras clave para clasificación
        palabras_activo = ['activo', 'caja', 'banco', 'efectivo', 'inventario', 'cliente', 'cuenta por cobrar', 'cuenta x cobrar', 'debe']
        palabras_pasivo = ['pasivo', 'proveedor', 'cuenta por pagar', 'acreedor', 'préstamo', 'deuda', 'haber']
        palabras_capital = ['capital', 'patrimonio', 'aporte', 'inversión']
        
        activos = 0
        pasivos = 0
        capital = 0
        
        columnas_numericas = df.select_dtypes(include=['number']).columns.tolist()
        
        for idx, row in df.iterrows():
            texto_completo = " ".join([str(row.get(c, "")) for c in df.columns if c not in columnas_numericas]).lower()
            
            valor = 0
            if 'Debe' in row and 'Haber' in row:
                valor = (row.get('Debe', 0) or 0) - (row.get('Haber', 0) or 0)
            elif columnas_numericas:
                valor = row.get(columnas_numericas[0], 0) or 0
            
            if any(p in texto_completo for p in palabras_activo):
                activos += abs(valor) if valor > 0 else 0
            elif any(p in texto_completo for p in palabras_pasivo):
                pasivos += abs(valor) if valor < 0 else valor if valor > 0 else 0
            elif any(p in texto_completo for p in palabras_capital):
                capital += abs(valor) if valor > 0 else 0
            else:
                if valor > 0:
                    activos += valor
                elif valor < 0:
                    pasivos += abs(valor)
        
        # Mostrar resultados
        resultado_texto = f"""
        === BALANCE GENERAL ===
        Proyecto: {nombre_proyecto}
        Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        
        ACTIVOS: ${activos:,.2f}
        PASIVOS: ${pasivos:,.2f}
        CAPITAL: ${capital:,.2f}
        
        TOTAL PASIVO + CAPITAL: ${pasivos + capital:,.2f}
        DIFERENCIA: ${activos - (pasivos + capital):,.2f}
        """
        
        # Guardar a archivo
        ruta = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("PDF", "*.pdf")],
            initialfile=f"Balance_{nombre_proyecto}"
        )
        
        if ruta:
            with open(ruta, 'w', encoding='utf-8') as f:
                f.write(resultado_texto)
            messagebox.showinfo("Éxito", f"Balance guardado en {ruta}")
    
    def generar_resultados_mejorado(self):
        """Genera Estado de Resultados mejorado"""
        nombre_proyecto = self.tabview.get()
        if not nombre_proyecto:
            messagebox.showwarning("Aviso", "Selecciona un proyecto primero")
            return
        
        tab = self.tabview.tab(nombre_proyecto)
        tabla = None
        for widget in tab.winfo_children():
            if isinstance(widget, TablaContableMejorada):
                tabla = widget
                break
            if hasattr(widget, 'winfo_children'):
                for child in widget.winfo_children():
                    if isinstance(child, TablaContableMejorada):
                        tabla = child
                        break
        
        if not tabla:
            messagebox.showwarning("Aviso", "No hay datos para generar reporte")
            return
        
        df = tabla.obtener_dataframe()
        
        if df.empty:
            messagebox.showwarning("Aviso", "No hay datos en la tabla")
            return
        
        palabras_ingreso = ['ingreso', 'venta', 'servicio', 'honorarios', 'ingresos']
        palabras_gasto = ['gasto', 'costo', 'compra', 'sueldo', 'alquiler', 'gastos']
        
        ingresos = 0
        gastos = 0
        
        if "Debe" in df.columns and "Haber" in df.columns:
            for idx, row in df.iterrows():
                desc = str(row.get("Descripción", row.get("Concepto", row.get("Cuenta", "")))).lower()
                debe = row.get("Debe", 0) or 0
                haber = row.get("Haber", 0) or 0
                
                if any(p in desc for p in palabras_ingreso):
                    ingresos += haber if haber > 0 else debe
                elif any(p in desc for p in palabras_gasto):
                    gastos += debe if debe > 0 else haber
        
        utilidad = ingresos - gastos
        
        resultado_texto = f"""
        === ESTADO DE RESULTADOS ===
        Proyecto: {nombre_proyecto}
        Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        
        INGRESOS: ${ingresos:,.2f}
        GASTOS: ${gastos:,.2f}
        
        UTILIDAD NETA: ${utilidad:,.2f}
        RESULTADO: {"GANANCIA" if utilidad > 0 else "PÉRDIDA" if utilidad < 0 else "EQUILIBRIO"}
        """
        
        ruta = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("PDF", "*.pdf")],
            initialfile=f"Resultados_{nombre_proyecto}"
        )
        
        if ruta:
            with open(ruta, 'w', encoding='utf-8') as f:
                f.write(resultado_texto)
            messagebox.showinfo("Éxito", f"Estado de Resultados guardado en {ruta}")
    
    def abrir_reportes(self):
        """Ventana de reportes mejorada"""
        top = ctk.CTkToplevel(self)
        top.title("Reportes Contables")
        top.geometry("400x350")
        top.attributes("-topmost", True)
        top.grab_set()
        
        frame = ctk.CTkFrame(top)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Generar Reportes", font=("Roboto", 16, "bold")).pack(pady=10)
        ctk.CTkFrame(frame, height=2, fg_color="gray").pack(fill="x", pady=10)
        
        btn_balance = ctk.CTkButton(frame, text="Balance General", 
                                    command=lambda: [top.destroy(), self.generar_balance_mejorado()],
                                    fg_color="#2c3e50", height=50, font=("Roboto", 14))
        btn_balance.pack(pady=10, fill="x")
        
        btn_resultados = ctk.CTkButton(frame, text="Estado de Resultados",
                                    command=lambda: [top.destroy(), self.generar_resultados_mejorado()],
                                    fg_color="#27ae60", height=50, font=("Roboto", 14))
        btn_resultados.pack(pady=10, fill="x")
        
        btn_cancel = ctk.CTkButton(frame, text="Cancelar", 
                                command=top.destroy,
                                fg_color="transparent", hover_color="#e74c3c")
        btn_cancel.pack(pady=10)
    
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
    
    def importar_archivo_general(self):
        nombre_cliente = self.tabview.get()
        if not nombre_cliente:
            messagebox.showwarning("Aviso", "Primero selecciona o crea una pestaña de cliente.")
            return
        
        columnas, datos = GestionArchivosMejorado.leer_archivo_para_importar()
        if datos:
            tab_objeto = self.tabview.tab(nombre_cliente)
            tabla_activa = None
            for widget in tab_objeto.winfo_children():
                if isinstance(widget, TablaContableMejorada):
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
    
    def ejecutar_exportacion(self, formato, tabla, nombre):
        GestionArchivosMejorado.exportar(tabla.obtener_datos(), nombre, formato)
    
    # CORRECCIÓN 4: Sincronización mejorada
    def sincronizar_nube(self):
        """Sincroniza con la nube - CORREGIDO"""
        if not self.sesion_activa:
            respuesta = messagebox.askyesno("Iniciar sesión", 
                                           "Para sincronizar necesitas iniciar sesión.\n¿Deseas iniciar sesión ahora?")
            if respuesta:
                self.mostrar_login()
            return
        
        # Crear ventana de progreso
        progress = ctk.CTkToplevel(self)
        progress.title("Sincronizando")
        progress.geometry("350x150")
        progress.attributes('-topmost', True)
        progress.grab_set()
        
        ctk.CTkLabel(progress, text="Guardando proyectos locales...").pack(pady=15)
        bar = ctk.CTkProgressBar(progress, mode="indeterminate")
        bar.pack(pady=10, padx=20, fill="x")
        bar.start()
        
        def sync_thread():
            try:
                # Primero guardar todos los proyectos localmente
                for nombre in list(self.tabview._tab_dict.keys()):
                    tab = self.tabview.tab(nombre)
                    for widget in tab.winfo_children():
                        if isinstance(widget, TablaContableMejorada):
                            datos = widget.obtener_datos()
                            DBManager.guardar_proyecto(nombre, datos, widget.tipo_actual)
                            # Subir a la nube
                            self.cloud.guardar_proyecto(nombre, widget.tipo_actual, datos, widget.encabezados)
                            break
                
                self.after(0, lambda: self.sync_complete(progress, True, "Proyectos sincronizados con la nube"))
            except Exception as e:
                self.after(0, lambda: self.sync_complete(progress, False, f"Error: {str(e)}"))
        
        import threading
        threading.Thread(target=sync_thread, daemon=True).start()
    
    def sync_complete(self, progress, success, message):
        """Callback de sincronización completa"""
        progress.destroy()
        if success:
            messagebox.showinfo("Sincronización", message)
            self.status_label.configure(text=message)
        else:
            messagebox.showerror("Error", message)
    
    def cambiar_tema(self):
        mode = "dark" if self.switch_tema.get() == 1 else "light"
        ctk.set_appearance_mode(mode)
    
    def accion_eliminar(self, nombre):
        if messagebox.askyesno("Confirmar", f"¿Eliminar permanentemente el proyecto '{nombre}'?"):
            DBManager.eliminar_proyecto(nombre)
            if self.sesion_activa:
                self.cloud.eliminar_proyecto(nombre)
            self.tabview.delete(nombre)
            messagebox.showinfo("Eliminado", f"Proyecto '{nombre}' eliminado.")
    
    def cargar_proyectos_existentes(self):
        for nombre, tipo in DBManager.obtener_todos_los_proyectos():
            self.añadir_pestaña(nombre, tipo or "Libro Diario", carga_inicial=True)
    
    def confirmar_salida(self):
        if self.cambios_pendientes:
            msg = messagebox.askyesnocancel("Salir", "¿Deseas guardar los cambios antes de salir?")
            if msg is True:
                # Guardar todos los proyectos abiertos
                for nombre in self.tabview._tab_dict.keys():
                    tab = self.tabview.tab(nombre)
                    for widget in tab.winfo_children():
                        if isinstance(widget, TablaContableMejorada):
                            self.accion_guardar(widget, nombre)
                            break
                self.destroy()
            elif msg is False:
                self.destroy()
        else:
            self.destroy()
    
    def abrir_ventana_nuevo(self):
        VentanaNuevoTrabajo(self, self.añadir_pestaña)
    
    def set_status(self, message, duration=3000):
        self.status_label.configure(text=message)
        self.after(duration, lambda: self.status_label.configure(text="Listo"))


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