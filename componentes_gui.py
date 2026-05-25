# componentes_gui_final.py - VERSIÓN COMPLETA CORREGIDA

import customtkinter as ctk
from tkcalendar import DateEntry
from tkinter import messagebox, Toplevel
from datetime import datetime
import re
import pandas as pd

class CeldaInteligente(ctk.CTkEntry):
    def __init__(self, master, tipo="texto", **kwargs):
        super().__init__(master, **kwargs)
        self.tipo = tipo
        self.configure(height=30, width=140)
        
        if self.tipo == "dinero":
            self.configure(placeholder_text="0.00")
            self.bind("<FocusOut>", self.formatear_moneda)
            vcmd = (self.register(self.validar_numero), '%P')
            self.configure(validate="key", validatecommand=vcmd)
        elif self.tipo == "dinero_positivo":
            self.configure(placeholder_text="0.00")
            self.bind("<FocusOut>", self.formatear_moneda)
            vcmd = (self.register(self.validar_numero_positivo), '%P')
            self.configure(validate="key", validatecommand=vcmd)
        elif self.tipo == "dinero_negativo":
            self.configure(placeholder_text="0.00")
            self.bind("<FocusOut>", self.formatear_moneda)
            vcmd = (self.register(self.validar_numero_negativo), '%P')
            self.configure(validate="key", validatecommand=vcmd)
        elif self.tipo == "entero":
            self.configure(placeholder_text="0")
            vcmd = (self.register(self.validar_entero), '%P')
            self.configure(validate="key", validatecommand=vcmd)
        elif self.tipo == "porcentaje":
            self.configure(placeholder_text="0%")
            self.bind("<FocusOut>", self.formatear_porcentaje)
            vcmd = (self.register(self.validar_porcentaje), '%P')
            self.configure(validate="key", validatecommand=vcmd)
        elif self.tipo == "fecha":
            self.configure(placeholder_text="DD/MM/AAAA")
            self.bind("<FocusOut>", self.validar_fecha)
            self.bind("<Button-1>", self.abrir_calendario)
        else:
            self.bind("<KeyRelease>", self.verificar_formula)
    
    def verificar_formula(self, event):
        texto = self.get()
        if texto.startswith('='):
            self.evaluar_formula_celda(texto[1:])
    
    def evaluar_formula_celda(self, formula):
        try:
            def reemplazar_celda(match):
                ref = match.group(0)
                root = self.winfo_toplevel()
                for widget in root.winfo_children():
                    if hasattr(widget, 'obtener_valor_celda'):
                        return str(widget.obtener_valor_celda(ref))
                return "0"
            
            formula_procesada = re.sub(r'[A-Z]+\d+', reemplazar_celda, formula)
            formula_procesada = formula_procesada.replace(',', '.')
            resultado = eval(formula_procesada)
            
            if self.tipo in ["dinero", "dinero_positivo", "dinero_negativo"]:
                self.delete(0, "end")
                self.insert(0, f"{resultado:,.2f}")
                self.formatear_moneda(None)
            else:
                self.delete(0, "end")
                self.insert(0, str(resultado))
        except Exception as e:
            self.configure(text_color="#e74c3c")
            self.after(2000, lambda: self.configure(text_color=("black", "white")))
    
    def formatear_moneda(self, event):
        valor = self.get().replace(',', '').strip()
        try:
            if valor:
                num = float(valor)
                self.delete(0, "end")
                self.insert(0, f"{num:,.2f}")
                if num < 0:
                    self.configure(text_color="#e74c3c")
                elif num > 0:
                    self.configure(text_color="#27ae60")
        except ValueError:
            pass
    
    def formatear_porcentaje(self, event):
        valor = self.get().replace('%', '').strip()
        try:
            if valor:
                num = float(valor)
                self.delete(0, "end")
                self.insert(0, f"{num:.2f}%")
        except ValueError:
            pass
    
    def validar_numero(self, value):
        if value == "" or value == "-":
            return True
        patron = r'^-?\d*\.?\d*$'
        return bool(re.match(patron, value))
    
    def validar_numero_positivo(self, value):
        if value == "":
            return True
        patron = r'^\d*\.?\d*$'
        return bool(re.match(patron, value))
    
    def validar_numero_negativo(self, value):
        if value == "" or value == "-":
            return True
        patron = r'^-\d*\.?\d*$'
        return bool(re.match(patron, value))
    
    def validar_entero(self, value):
        if value == "":
            return True
        patron = r'^\d*$'
        return bool(re.match(patron, value))
    
    def validar_porcentaje(self, value):
        if value == "":
            return True
        valor_limpio = value.replace('%', '')
        patron = r'^\d*\.?\d*$'
        return bool(re.match(patron, valor_limpio))
    
    def abrir_calendario(self, event):
        top = ctk.CTkToplevel(self)
        top.title("Seleccionar Fecha")
        top.geometry("250x250")
        top.attributes("-topmost", True)
        top.grab_set()
        
        cal = DateEntry(top, width=12, background='darkblue', 
                       foreground='white', borderwidth=2, 
                       date_pattern='dd/mm/yyyy')
        cal.pack(padx=10, pady=20)
        
        def set_date():
            self.delete(0, "end")
            self.insert(0, cal.get())
            top.destroy()
        
        ctk.CTkButton(top, text="Confirmar", command=set_date, fg_color="#27ae60").pack(pady=10)
    
    def validar_fecha(self, event):
        texto = self.get()
        if len(texto) == 10 and '/' in texto:
            try:
                datetime.strptime(texto, '%d/%m/%Y')
                self.configure(text_color="#27ae60")
            except:
                self.configure(text_color="#e74c3c")


class VentanaCalculadoraAvanzada(ctk.CTkToplevel):
    """Calculadora avanzada que permite múltiples columnas y constantes"""
    
    def __init__(self, parent, tabla):
        super().__init__(parent)
        self.title("Calculadora Avanzada")
        self.geometry("700x550")
        self.attributes("-topmost", True)
        self.grab_set()
        
        self.tabla = tabla
        self.columnas = tabla.encabezados
        self.operandos = []  # Lista de (tipo, valor/columna)
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        ctk.CTkLabel(main_frame, text="Calculadora Avanzada", font=("Roboto", 18, "bold")).pack(pady=10)
        
        # Frame para la expresión
        expr_frame = ctk.CTkFrame(main_frame)
        expr_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(expr_frame, text="Expresión:").pack(side="left", padx=5)
        self.entry_expresion = ctk.CTkEntry(expr_frame, width=400, placeholder_text="Ej: [Debe] + [Haber] * 1.21")
        self.entry_expresion.pack(side="left", padx=5, fill="x", expand=True)
        
        # Frame para operandos
        ops_frame = ctk.CTkFrame(main_frame)
        ops_frame.pack(fill="both", expand=True, pady=10)
        
        ctk.CTkLabel(ops_frame, text="Agregar operandos:", font=("Roboto", 12, "bold")).pack(anchor="w", pady=5)
        
        # Selector de tipo de operando
        tipo_frame = ctk.CTkFrame(ops_frame)
        tipo_frame.pack(fill="x", pady=5)
        
        self.tipo_operando = ctk.CTkOptionMenu(tipo_frame, values=["Columna", "Constante", "Porcentaje"], width=120)
        self.tipo_operando.pack(side="left", padx=5)
        self.tipo_operando.set("Columna")
        
        self.valor_columna = ctk.CTkOptionMenu(tipo_frame, values=self.columnas, width=150)
        self.valor_columna.pack(side="left", padx=5)
        
        self.valor_constante = ctk.CTkEntry(tipo_frame, width=120, placeholder_text="Valor")
        self.valor_constante.pack(side="left", padx=5)
        self.valor_constante.pack_forget()  # Ocultar inicialmente
        
        # Operador
        ctk.CTkLabel(tipo_frame, text="Operador:").pack(side="left", padx=5)
        self.operador = ctk.CTkOptionMenu(tipo_frame, values=["+", "-", "*", "/", "^", "%"], width=80)
        self.operador.pack(side="left", padx=5)
        
        def on_tipo_change(*args):
            if self.tipo_operando.get() == "Columna":
                self.valor_columna.pack(side="left", padx=5)
                self.valor_constante.pack_forget()
            else:
                self.valor_columna.pack_forget()
                self.valor_constante.pack(side="left", padx=5)
        
        self.tipo_operando.configure(command=on_tipo_change)
        
        # Botón agregar
        ctk.CTkButton(tipo_frame, text="Agregar", command=self.agregar_operando, fg_color="#27ae60", width=80).pack(side="left", padx=10)
        
        # Lista de operandos
        ctk.CTkLabel(ops_frame, text="Operandos agregados:", font=("Roboto", 12, "bold")).pack(anchor="w", pady=(10, 5))
        
        self.lista_frame = ctk.CTkScrollableFrame(ops_frame, height=150)
        self.lista_frame.pack(fill="both", expand=True, pady=5)
        
        self.operandos_labels = []
        
        # Frame para resultado
        resultado_frame = ctk.CTkFrame(main_frame)
        resultado_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(resultado_frame, text="Nombre resultado:").pack(side="left", padx=5)
        self.entry_resultado = ctk.CTkEntry(resultado_frame, width=200, placeholder_text="Nombre de la nueva columna")
        self.entry_resultado.pack(side="left", padx=5)
        
        self.lbl_resultado = ctk.CTkLabel(resultado_frame, text="", font=("Roboto", 14, "bold"))
        self.lbl_resultado.pack(side="left", padx=20)
        
        # Botones de acción
        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(btn_frame, text="Calcular", command=self.calcular, fg_color="#3498db", width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Limpiar", command=self.limpiar, fg_color="#e67e22", width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Aplicar a columna", command=self.aplicar_columna, fg_color="#27ae60", width=150).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Cerrar", command=self.destroy, fg_color="gray", width=100).pack(side="right", padx=5)
        
        # Funciones rápidas
        rapidas_frame = ctk.CTkFrame(main_frame)
        rapidas_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(rapidas_frame, text="Funciones rápidas:").pack(anchor="w")
        
        func_frame = ctk.CTkFrame(rapidas_frame)
        func_frame.pack(fill="x", pady=5)
        
        funciones = [
            ("SUMA", "sum([Debe])"),
            ("PROMEDIO", "mean([Debe])"),
            ("IVA 21%", "[Debe] * 0.21"),
            ("DESCUENTO 10%", "[Debe] * 0.9"),
            ("DIFERENCIA", "[Debe] - [Haber]"),
        ]
        
        for texto, formula in funciones:
            btn = ctk.CTkButton(func_frame, text=texto, width=100,
                               command=lambda f=formula: self.entry_expresion.insert("end", f))
            btn.pack(side="left", padx=5)
    
    def agregar_operando(self):
        tipo = self.tipo_operando.get()
        operador = self.operador.get()
        
        if tipo == "Columna":
            valor = self.valor_columna.get()
            texto = f"[{valor}]"
        elif tipo == "Constante":
            valor = self.valor_constante.get()
            try:
                float(valor)
                texto = valor
            except:
                messagebox.showerror("Error", "Constante inválida")
                return
        else:  # Porcentaje
            valor = self.valor_constante.get()
            try:
                num = float(valor)
                texto = f"({num}/100)"
            except:
                messagebox.showerror("Error", "Porcentaje inválido")
                return
        
        self.operandos.append({"tipo": tipo, "valor": valor, "operador": operador, "texto": texto})
        self.actualizar_lista()
        
        # Actualizar expresión sugerida
        expr = ""
        for i, op in enumerate(self.operandos):
            if i > 0:
                expr += f" {op['operador']} "
            expr += op['texto']
        self.entry_expresion.delete(0, "end")
        self.entry_expresion.insert(0, expr)
        
        # Limpiar campos
        self.valor_constante.delete(0, "end")
    
    def actualizar_lista(self):
        for widget in self.lista_frame.winfo_children():
            widget.destroy()
        
        self.operandos_labels = []
        for i, op in enumerate(self.operandos):
            frame = ctk.CTkFrame(self.lista_frame)
            frame.pack(fill="x", pady=2)
            
            texto = f"{op['operador'] if i > 0 else ''} {op['texto']}"
            ctk.CTkLabel(frame, text=texto).pack(side="left", padx=5)
            
            btn_remove = ctk.CTkButton(frame, text="X", width=30, height=25, fg_color="#c0392b",
                                       command=lambda idx=i: self.remover_operando(idx))
            btn_remove.pack(side="right", padx=5)
    
    def remover_operando(self, idx):
        self.operandos.pop(idx)
        self.actualizar_lista()
    
    def limpiar(self):
        self.operandos = []
        self.actualizar_lista()
        self.entry_expresion.delete(0, "end")
        self.lbl_resultado.configure(text="")
    
    def calcular(self):
        try:
            expresion = self.entry_expresion.get().strip()
            if not expresion:
                if not self.operandos:
                    messagebox.showwarning("Aviso", "Ingrese una expresión o agregue operandos")
                    return
                expresion = ""
                for i, op in enumerate(self.operandos):
                    if i > 0:
                        expresion += f" {op['operador']} "
                    expresion += op['texto']
            
            # Evaluar expresión
            df = self.tabla.obtener_dataframe()
            
            # Reemplazar referencias a columnas
            def replace_col(match):
                col_name = match.group(1)
                if col_name in df.columns:
                    # Devolver la suma de la columna para la vista previa
                    return str(df[col_name].sum())
                return "0"
            
            expr_eval = re.sub(r'\[([^\]]+)\]', replace_col, expresion)
            
            # Reemplazar operadores
            expr_eval = expr_eval.replace('^', '**')
            
            # Evaluar
            resultado = eval(expr_eval)
            
            if isinstance(resultado, (int, float)):
                self.lbl_resultado.configure(text=f"Resultado: ${resultado:,.2f}", text_color="#27ae60")
            else:
                self.lbl_resultado.configure(text=f"Resultado: {resultado}", text_color="#27ae60")
                
        except Exception as e:
            self.lbl_resultado.configure(text=f"Error: {str(e)}", text_color="#e74c3c")
    
    def aplicar_columna(self):
        nombre = self.entry_resultado.get().strip()
        if not nombre:
            messagebox.showwarning("Aviso", "Ingrese un nombre para la nueva columna")
            return
        
        expresion = self.entry_expresion.get().strip()
        if not expresion:
            if not self.operandos:
                messagebox.showwarning("Aviso", "Ingrese una expresión")
                return
            expresion = ""
            for i, op in enumerate(self.operandos):
                if i > 0:
                    expresion += f" {op['operador']} "
                expresion += op['texto']
        
        try:
            # Agregar columna
            self.tabla.agregar_columna(nombre)
            
            # Evaluar fila por fila
            df = self.tabla.obtener_dataframe()
            
            for idx, row in df.iterrows():
                expr_fila = expresion
                # Reemplazar referencias a columnas con valores de la fila
                for col in df.columns:
                    if f"[{col}]" in expr_fila:
                        valor = row[col] if pd.notna(row[col]) else 0
                        expr_fila = expr_fila.replace(f"[{col}]", str(valor))
                
                expr_fila = expr_fila.replace('^', '**')
                try:
                    resultado = eval(expr_fila)
                    if idx < len(self.tabla.filas):
                        self.tabla.filas[idx][-1].delete(0, "end")
                        if isinstance(resultado, (int, float)):
                            self.tabla.filas[idx][-1].insert(0, f"{resultado:,.2f}")
                        else:
                            self.tabla.filas[idx][-1].insert(0, str(resultado))
                except:
                    pass
            
            messagebox.showinfo("Éxito", f"Columna '{nombre}' creada")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al aplicar: {str(e)}")


class VentanaConfigurarColumna(ctk.CTkToplevel):
    """Ventana para configurar el tipo de columna"""
    
    def __init__(self, parent, columna_idx, tabla):
        super().__init__(parent)
        self.title(f"Configurar columna")
        self.geometry("350x400")
        self.attributes("-topmost", True)
        self.grab_set()
        
        self.columna_idx = columna_idx
        self.tabla = tabla
        self.nombre_actual = tabla.encabezados[columna_idx]
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(main_frame, text="Configuración de Columna", font=("Roboto", 16, "bold")).pack(pady=10)
        
        # Nombre
        ctk.CTkLabel(main_frame, text="Nombre:").pack(anchor="w", pady=(10, 5))
        self.entry_nombre = ctk.CTkEntry(main_frame, width=300)
        self.entry_nombre.insert(0, self.nombre_actual)
        self.entry_nombre.pack(fill="x")
        
        # Tipo
        ctk.CTkLabel(main_frame, text="Tipo de dato:").pack(anchor="w", pady=(10, 5))
        
        self.tipo_var = ctk.StringVar(value="texto")
        
        tipos = [
            ("Texto", "texto"),
            ("Moneda (+/-)", "dinero"),
            ("Moneda (solo +)", "dinero_positivo"),
            ("Moneda (solo -)", "dinero_negativo"),
            ("Número entero", "entero"),
            ("Porcentaje", "porcentaje"),
            ("Fecha", "fecha"),
        ]
        
        for texto, valor in tipos:
            rb = ctk.CTkRadioButton(main_frame, text=texto, variable=self.tipo_var, value=valor)
            rb.pack(anchor="w", pady=2)
        
        ctk.CTkButton(main_frame, text="Aplicar", command=self.aplicar, fg_color="#27ae60").pack(pady=20)
    
    def aplicar(self):
        nuevo_nombre = self.entry_nombre.get().strip()
        nuevo_tipo = self.tipo_var.get()
        
        if nuevo_nombre and nuevo_nombre != self.nombre_actual:
            self.tabla.encabezados[self.columna_idx] = nuevo_nombre
            self.tabla.dibujar_encabezados()
        
        # Cambiar tipo de todas las celdas de esta columna
        for fila in self.tabla.filas:
            if self.columna_idx < len(fila):
                valor = fila[self.columna_idx].get()
                fila[self.columna_idx].destroy()
                nueva_celda = CeldaInteligente(self.tabla.rows_frame, tipo=nuevo_tipo, width=140)
                nueva_celda.insert(0, valor)
                fila[self.columna_idx] = nueva_celda
                nueva_celda.grid(row=self.tabla.filas.index(fila), column=self.columna_idx, padx=1, pady=1)
        
        self.tabla.reorganizar_grid()
        self.destroy()
        messagebox.showinfo("Éxito", f"Columna actualizada a '{nuevo_tipo}'")


class VentanaGraficasMejorada(ctk.CTkToplevel):
    def __init__(self, parent, datos, encabezados, nombre_proyecto):
        super().__init__(parent)
        self.title(f"Gráficas - {nombre_proyecto}")
        self.geometry("1000x700")
        self.attributes('-topmost', True)
        self.grab_set()
        
        self.datos = datos
        self.encabezados = encabezados
        self.nombre_proyecto = nombre_proyecto
        
        import pandas as pd
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        self.pd = pd
        self.plt = plt
        self.FigureCanvasTkAgg = FigureCanvasTkAgg
        
        # Crear DataFrame y convertir columnas numéricas
        self.df = pd.DataFrame(datos, columns=encabezados) if datos and len(datos) > 0 else pd.DataFrame()
        
        # Convertir columnas numéricas correctamente
        for col in self.df.columns:
            try:
                # Intentar convertir a número (quitando comas y signos)
                self.df[col] = pd.to_numeric(self.df[col].astype(str).str.replace(',', ''), errors='ignore')
            except:
                pass
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        panel_sup = ctk.CTkFrame(main_frame)
        panel_sup.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(panel_sup, text="Tipo de gráfico:", font=("Roboto", 12)).pack(side="left", padx=10)
        
        self.tipo_grafica = ctk.CTkOptionMenu(
            panel_sup,
            values=["Barras - Debe vs Haber", "Líneas - Evolución", "Pastel - Distribución"],
            command=self.actualizar_grafica,
            width=200
        )
        self.tipo_grafica.pack(side="left", padx=10)
        
        # Selector de columna
        ctk.CTkLabel(panel_sup, text="Columna:").pack(side="left", padx=(20, 5))
        self.columna_selector = ctk.CTkOptionMenu(panel_sup, values=self.encabezados, width=150)
        self.columna_selector.pack(side="left", padx=5)
        
        ctk.CTkButton(panel_sup, text="Exportar PNG", command=self.exportar_grafica, 
                     fg_color="#2c3e50").pack(side="right", padx=10)
        
        self.frame_grafica = ctk.CTkFrame(main_frame)
        self.frame_grafica.pack(fill="both", expand=True)
        
        self.frame_stats = ctk.CTkFrame(main_frame)
        self.frame_stats.pack(fill="x", pady=(15, 0))
        
        self.actualizar_grafica()
    
    def actualizar_grafica(self, *args):
        for widget in self.frame_grafica.winfo_children():
            widget.destroy()
        
        tipo = self.tipo_grafica.get()
        columna = self.columna_selector.get()
        
        self.fig, self.ax = self.plt.subplots(figsize=(10, 6))
        
        if self.df.empty or len(self.df) == 0:
            self.ax.text(0.5, 0.5, "Sin datos para graficar", ha="center", va="center")
        else:
            self.fig.patch.set_facecolor('#1e1e2e')
            self.ax.set_facecolor('#2d2d3d')
            self.ax.tick_params(colors='white', labelcolor='white')
            self.ax.title.set_color('white')
            self.ax.xaxis.label.set_color('white')
            self.ax.yaxis.label.set_color('white')
            
            if tipo == "Barras - Debe vs Haber" and "Debe" in self.df.columns:
                x = range(len(self.df))
                # Asegurar que los valores sean numéricos
                debe_vals = self.df["Debe"].fillna(0).astype(float)
                self.ax.bar(x, debe_vals, label='Debe', color='#e74c3c', alpha=0.7)
                
                if "Haber" in self.df.columns:
                    haber_vals = self.df["Haber"].fillna(0).astype(float)
                    self.ax.bar(x, haber_vals, label='Haber', color='#27ae60', alpha=0.7, bottom=debe_vals)
                
                self.ax.set_xlabel('Registro')
                self.ax.set_ylabel('Monto ($)')
                self.ax.set_title('Comparación Debe vs Haber')
                self.ax.legend()
                
            elif tipo == "Líneas - Evolución" and columna in self.df.columns:
                valores = self.df[columna].fillna(0).astype(float)
                self.ax.plot(range(len(self.df)), valores, 'o-', color='#3498db', linewidth=2, markersize=6)
                self.ax.set_xlabel('Registro')
                self.ax.set_ylabel('Monto ($)')
                self.ax.set_title(f'Evolución de {columna}')
                self.ax.grid(True, alpha=0.3)
                
            elif tipo == "Pastel - Distribución" and "Debe" in self.df.columns and "Haber" in self.df.columns:
                total_debe = float(self.df["Debe"].fillna(0).sum())
                total_haber = float(self.df["Haber"].fillna(0).sum())
                self.ax.pie([total_debe, total_haber], 
                           labels=[f'Debe\n${total_debe:,.2f}', f'Haber\n${total_haber:,.2f}'], 
                           colors=['#e74c3c', '#27ae60'], autopct='%1.1f%%')
                self.ax.set_title('Distribución Debe vs Haber')
        
        self.plt.tight_layout()
        
        canvas = self.FigureCanvasTkAgg(self.fig, self.frame_grafica)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        self.mostrar_estadisticas()
    
    def mostrar_estadisticas(self):
        for widget in self.frame_stats.winfo_children():
            widget.destroy()
        
        if not self.df.empty:
            stats_frame = ctk.CTkFrame(self.frame_stats)
            stats_frame.pack(fill="x", padx=10, pady=10)
            
            stats = []
            if "Debe" in self.df.columns:
                try:
                    total_debe = float(self.df["Debe"].fillna(0).sum())
                    stats.append(f"Total Debe: ${total_debe:,.2f}")
                except:
                    stats.append(f"Total Debe: {self.df['Debe'].sum()}")
            
            if "Haber" in self.df.columns:
                try:
                    total_haber = float(self.df["Haber"].fillna(0).sum())
                    stats.append(f"Total Haber: ${total_haber:,.2f}")
                except:
                    stats.append(f"Total Haber: {self.df['Haber'].sum()}")
            
            stats.append(f"Registros: {len(self.df)}")
            
            for i, stat in enumerate(stats):
                if stat:
                    ctk.CTkLabel(stats_frame, text=stat, font=("Roboto", 12)).grid(row=0, column=i, padx=20)
    
    def exportar_grafica(self):
        if hasattr(self, 'fig'):
            from tkinter import filedialog
            ruta = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG", "*.png")],
                initialfile=f"grafica_{self.nombre_proyecto}"
            )
            if ruta:
                self.fig.savefig(ruta, dpi=150, bbox_inches='tight', facecolor='#1e1e2e')
                messagebox.showinfo("Éxito", f"Gráfica guardada en:\n{ruta}")


class TablaContableMejorada(ctk.CTkFrame):
    def __init__(self, master, columnas=None, tipo="Libro Diario", nombre_proyecto="", **kwargs):
        super().__init__(master, **kwargs)
        self.encabezados = columnas if columnas else ["Fecha", "Descripcion", "Cuenta", "Debe", "Haber", "IVA %"]
        self.tipo_actual = tipo
        self.nombre_proyecto = nombre_proyecto
        self.filas = []
        self.coords_map = {}
        self.reverse_map = {}
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.header_frame = ctk.CTkFrame(self, fg_color=("gray85", "gray18"), height=45)
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 2))
        
        self.body_canvas = ctk.CTkScrollableFrame(self, orientation="vertical")
        self.body_canvas.grid(row=1, column=0, sticky="nsew")
        
        self.rows_frame = ctk.CTkFrame(self.body_canvas, fg_color="transparent")
        self.rows_frame.pack(fill="x")
        
        self.footer_frame = ctk.CTkFrame(self, height=45, fg_color=("gray85", "gray18"))
        self.footer_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        
        self.lbl_total_1 = ctk.CTkLabel(self.footer_frame, text="Total Debe: 0.00", font=("Roboto", 12, "bold"))
        self.lbl_total_1.pack(side="left", padx=20)
        
        self.lbl_total_2 = ctk.CTkLabel(self.footer_frame, text="Total Haber: 0.00", font=("Roboto", 12, "bold"))
        self.lbl_total_2.pack(side="left", padx=20)
        
        self.dibujar_encabezados()
        self.añadir_fila()
    
    def dibujar_encabezados(self):
        for widget in self.header_frame.winfo_children():
            widget.destroy()
        
        header_inner = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        header_inner.pack(fill="x")
        
        for i, col in enumerate(self.encabezados):
            frame = ctk.CTkFrame(header_inner, fg_color="transparent")
            frame.grid(row=0, column=i, padx=1, pady=2)
            
            lbl = ctk.CTkLabel(frame, text=col, font=("Roboto", 12, "bold"), anchor="center", width=140, height=35)
            lbl.pack(side="left")
            
            # Botón de configuración (engranaje)
            btn_config = ctk.CTkButton(frame, text="⚙️", width=25, height=25, fg_color="transparent",
                                      command=lambda idx=i: self.abrir_configuracion_columna(idx))
            btn_config.pack(side="left")
    
    def abrir_configuracion_columna(self, col_idx):
        VentanaConfigurarColumna(self, col_idx, self)
    
    def abrir_calculadora_avanzada(self):
        VentanaCalculadoraAvanzada(self.winfo_toplevel(), self)
    
    def menu_columnas(self, event, col_idx):
        menu = ctk.CTkToplevel(self)
        menu.wm_overrideredirect(True)
        menu.geometry(f"180x220+{event.x_root}+{event.y_root}")
        menu.attributes("-topmost", True)
        
        btn_config = ctk.CTkButton(menu, text="Configurar tipo", command=lambda: [menu.destroy(), self.abrir_configuracion_columna(col_idx)])
        btn_config.pack(pady=5, padx=10, fill="x")
        
        btn_rename = ctk.CTkButton(menu, text="Renombrar", command=lambda: self.renombrar_columna(col_idx, menu))
        btn_rename.pack(pady=5, padx=10, fill="x")
        
        btn_insert = ctk.CTkButton(menu, text="Insertar columna", command=lambda: self.insertar_columna(col_idx, menu))
        btn_insert.pack(pady=5, padx=10, fill="x")
        
        if len(self.encabezados) > 1:
            btn_delete = ctk.CTkButton(menu, text="Eliminar", fg_color="#c0392b", command=lambda: self.eliminar_columna(col_idx, menu))
            btn_delete.pack(pady=5, padx=10, fill="x")
        
        menu.bind("<FocusOut>", lambda e: menu.destroy())
    
    def abrir_configuracion_columna(self, col_idx):
        VentanaConfigurarColumna(self, col_idx, self)
    
    def renombrar_columna(self, col_idx, menu):
        menu.destroy()
        nuevo_nombre = ctk.CTkInputDialog(text=f"Nuevo nombre para '{self.encabezados[col_idx]}':", title="Renombrar").get_input()
        if nuevo_nombre and nuevo_nombre.strip():
            self.encabezados[col_idx] = nuevo_nombre.strip()
            self.dibujar_encabezados()
    
    def insertar_columna(self, col_idx, menu):
        menu.destroy()
        nombre = ctk.CTkInputDialog(text="Nombre de la columna:", title="Insertar").get_input()
        if not nombre:
            nombre = f"Nueva_{len(self.encabezados)+1}"
        
        self.encabezados.insert(col_idx, nombre)
        for fila in self.filas:
            nueva = CeldaInteligente(self.rows_frame, tipo="texto", width=140)
            fila.insert(col_idx, nueva)
        
        self.dibujar_encabezados()
        self.reorganizar_grid()
    
    def eliminar_columna(self, col_idx, menu):
        menu.destroy()
        if messagebox.askyesno("Confirmar", f"¿Eliminar columna '{self.encabezados[col_idx]}'?"):
            self.encabezados.pop(col_idx)
            for fila in self.filas:
                fila[col_idx].destroy()
                fila.pop(col_idx)
            self.dibujar_encabezados()
            self.reorganizar_grid()
    
    def agregar_columna(self, nombre):
        """Agrega una columna nueva al final"""
        self.encabezados.append(nombre)
        for fila in self.filas:
            nueva = CeldaInteligente(self.rows_frame, tipo="texto", width=140)
            fila.append(nueva)
        self.dibujar_encabezados()
        self.reorganizar_grid()
    
    def reorganizar_grid(self):
        for row_idx, fila in enumerate(self.filas):
            for col_idx, celda in enumerate(fila):
                celda.grid(row=row_idx, column=col_idx, padx=1, pady=1)
    
    def añadir_fila(self, datos=None):
        row_idx = len(self.filas)
        fila_widgets = []
        
        for i, col in enumerate(self.encabezados):
            col_lower = col.lower()
            if any(x in col_lower for x in ["debe", "haber", "saldo", "monto"]):
                tipo = "dinero"
            elif "iva" in col_lower:
                tipo = "porcentaje"
            elif "fecha" in col_lower:
                tipo = "fecha"
            else:
                tipo = "texto"
            
            e = CeldaInteligente(self.rows_frame, tipo=tipo, width=140)
            e.grid(row=row_idx, column=i, padx=1, pady=1)
            
            if datos and i < len(datos):
                e.insert(0, str(datos[i]))
            
            letra = chr(65 + i) if i < 26 else chr(65 + (i // 26) - 1) + chr(65 + (i % 26))
            coord = f"{letra}{row_idx + 1}"
            self.coords_map[(row_idx, i)] = coord
            self.reverse_map[coord] = e
            
            e.bind("<KeyRelease>", lambda ev, r=row_idx, c=i: self.recalcular())
            e.bind("<Button-3>", lambda ev, r=row_idx, c=i: self.mostrar_menu_operaciones(ev, r, c))
            fila_widgets.append(e)
        
        self.filas.append(fila_widgets)
        self.recalcular()
    
    def eliminar_ultima_fila(self):
        if self.filas:
            fila = self.filas.pop()
            for celda in fila:
                celda.destroy()
            self.recalcular()
    
    def recalcular(self):
        idx_debe = next((i for i, c in enumerate(self.encabezados) if c.lower() == "debe"), -1)
        idx_haber = next((i for i, c in enumerate(self.encabezados) if c.lower() == "haber"), -1)
        
        total_debe = 0
        total_haber = 0
        
        for fila in self.filas:
            if idx_debe >= 0 and idx_debe < len(fila):
                valor_str = fila[idx_debe].get().replace(',', '').replace('%', '')
                try:
                    total_debe += float(valor_str) if valor_str else 0
                except:
                    pass
            if idx_haber >= 0 and idx_haber < len(fila):
                valor_str = fila[idx_haber].get().replace(',', '').replace('%', '')
                try:
                    total_haber += float(valor_str) if valor_str else 0
                except:
                    pass
        
        self.lbl_total_1.configure(text=f"Total Debe: {total_debe:,.2f}")
        self.lbl_total_2.configure(text=f"Total Haber: {total_haber:,.2f}")
    
    def limpiar_tabla(self):
        for fila in self.filas:
            for celda in fila:
                celda.destroy()
        self.filas = []
        self.coords_map = {}
        self.reverse_map = {}
        self.añadir_fila()
    
    def obtener_datos(self):
        datos = []
        for fila in self.filas:
            fila_datos = []
            for celda in fila:
                valor = celda.get().strip()
                fila_datos.append(valor if valor else "")
            if any(fila_datos):
                datos.append(fila_datos)
        return datos
    
    def obtener_dataframe(self):
        datos = self.obtener_datos()
        if datos:
            df = pd.DataFrame(datos, columns=self.encabezados)
            for col in df.columns:
                try:
                    # Limpiar y convertir a número
                    valores_limpios = df[col].astype(str).str.replace(',', '').str.replace('%', '')
                    df[col] = pd.to_numeric(valores_limpios, errors='ignore')
                except:
                    pass
            return df
        return pd.DataFrame(columns=self.encabezados)
    
    def obtener_valor_celda(self, referencia):
        match = re.match(r'([A-Z]+)(\d+)', referencia.upper())
        if match:
            col_str, row_str = match.groups()
            col_idx = ord(col_str[0]) - 65
            if len(col_str) > 1:
                col_idx = (ord(col_str[0]) - 64) * 26 + (ord(col_str[1]) - 65)
            row_idx = int(row_str) - 1
            
            if 0 <= row_idx < len(self.filas) and 0 <= col_idx < len(self.filas[row_idx]):
                valor_str = self.filas[row_idx][col_idx].get().replace(',', '').replace('%', '')
                try:
                    return float(valor_str) if valor_str else 0
                except:
                    return 0
        return 0
    
    def añadir_fila_con_datos(self, datos):
        self.añadir_fila(datos)
    
    def mostrar_menu_operaciones(self, event, fila_idx, col_idx):
        """Menú contextual para operaciones entre celdas"""
        menu = ctk.CTkToplevel(self)
        menu.wm_overrideredirect(True)
        menu.geometry(f"250x200+{event.x_root}+{event.y_root}")
        menu.attributes("-topmost", True)
        
        ctk.CTkLabel(menu, text="Operaciones", font=("Roboto", 12, "bold")).pack(pady=(10, 5))
        ctk.CTkFrame(menu, height=1, fg_color="gray50").pack(fill="x", padx=10, pady=5)
        
        operaciones = [
            ("➕ Sumar celdas", "suma"),
            ("🔢 Calculadora avanzada", "avanzada"),
            ("📝 Fórmula personalizada", "personalizada")
        ]
        
        for texto, op in operaciones:
            btn = ctk.CTkButton(menu, text=texto, fg_color="transparent", height=35,
                               command=lambda o=op: self.ejecutar_operacion_menu(o, fila_idx, col_idx, menu))
            btn.pack(fill="x", padx=10, pady=2)
        
        menu.bind("<FocusOut>", lambda e: menu.destroy())
    
    def ejecutar_operacion_menu(self, operacion, fila_dest, col_dest, menu):
        menu.destroy()
        
        if operacion == "avanzada":
            self.abrir_calculadora_avanzada()
        elif operacion == "personalizada":
            self.abrir_formula_personalizada(fila_dest, col_dest)
        elif operacion == "suma":
            self.abrir_selector_suma(fila_dest, col_dest)
    
    def abrir_formula_personalizada(self, fila_dest, col_dest):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Fórmula Personalizada")
        dialog.geometry("500x200")
        dialog.attributes("-topmost", True)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Ingrese fórmula (ej: A1 + B2, usa A1, B2, C3...):").pack(pady=10)
        entry_formula = ctk.CTkEntry(dialog, width=450)
        entry_formula.pack(pady=10)
        
        ctk.CTkLabel(dialog, text="Ejemplos: =A1+B2 | =A1*0.19 | =(A1+B2)/2", font=("Roboto", 9), text_color="gray").pack()
        
        def aplicar():
            formula = entry_formula.get()
            if formula.startswith('='):
                formula = formula[1:]
            
            try:
                def reemplazar(match):
                    ref = match.group(0)
                    return str(self.obtener_valor_celda(ref))
                
                formula_procesada = re.sub(r'[A-Z]+\d+', reemplazar, formula)
                resultado = eval(formula_procesada)
                
                destino = self.filas[fila_dest][col_dest]
                destino.delete(0, "end")
                destino.insert(0, f"{resultado:,.2f}")
                messagebox.showinfo("Éxito", f"Resultado: {resultado:,.2f}")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error: {str(e)}")
        
        ctk.CTkButton(dialog, text="Aplicar", command=aplicar, fg_color="#27ae60").pack(pady=15)
    
    def abrir_selector_suma(self, fila_dest, col_dest):
        """Selector de celdas para sumar"""
        self.modo_seleccion = "suma"
        self.celdas_seleccionadas = []
        self.destino = (fila_dest, col_dest)
        
        # Crear ventana de instrucciones
        self.instrucciones = ctk.CTkToplevel(self)
        self.instrucciones.title("Selección de Celdas")
        self.instrucciones.geometry("300x150")
        self.instrucciones.attributes("-topmost", True)
        
        ctk.CTkLabel(self.instrucciones, 
                    text="Selecciona las celdas a sumar\n\nHaz clic en cada celda\n(Presiona ESC para cancelar)", 
                    font=("Roboto", 11)).pack(pady=20)
        
        # Vincular eventos
        self.bind_celdas_seleccion()
        
        def cancelar():
            self.unbind_celdas_seleccion()
            self.instrucciones.destroy()
        
        self.instrucciones.bind("<Escape>", lambda e: cancelar())
        ctk.CTkButton(self.instrucciones, text="Cancelar", command=cancelar, fg_color="red").pack(pady=10)
    
    def bind_celdas_seleccion(self):
        self.seleccion_binds = []
        for r, fila in enumerate(self.filas):
            for c, celda in enumerate(fila):
                celda.bind("<Button-1>", lambda e, rr=r, cc=c: self.seleccionar_celda(rr, cc), add="+")
                self.seleccion_binds.append((celda, r, c))
    
    def unbind_celdas_seleccion(self):
        for celda, r, c in self.seleccion_binds:
            celda.unbind("<Button-1>")
        self.seleccion_binds = []
    
    def seleccionar_celda(self, fila, col):
        celda = self.filas[fila][col]
        original_color = celda.cget("fg_color")
        celda.configure(fg_color="#3498db")
        
        self.celdas_seleccionadas.append((fila, col, celda, original_color))
        celda.after(200, lambda: celda.configure(fg_color=original_color))
        
        if len(self.celdas_seleccionadas) >= 2:
            self.ejecutar_suma_seleccionada()
    
    def ejecutar_suma_seleccionada(self):
        self.unbind_celdas_seleccion()
        if self.instrucciones:
            self.instrucciones.destroy()
        
        try:
            total = 0
            for fila, col, celda, _ in self.celdas_seleccionadas:
                valor_str = celda.get().replace(',', '')
                try:
                    total += float(valor_str) if valor_str else 0
                except:
                    pass
            
            destino = self.filas[self.destino[0]][self.destino[1]]
            destino.delete(0, "end")
            destino.insert(0, f"{total:,.2f}")
            self.recalcular()
            messagebox.showinfo("Éxito", f"Suma total: {total:,.2f}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.celdas_seleccionadas = []