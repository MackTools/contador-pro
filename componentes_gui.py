import customtkinter as ctk
from tkcalendar import DateEntry
from tkinter import simpledialog, messagebox, Toplevel
from datetime import datetime
import re

class CeldaInteligente(ctk.CTkEntry):
    def __init__(self, master, tipo="texto", **kwargs):
        super().__init__(master, **kwargs)
        self.tipo = tipo
        self.configure(height=30, width=140)
        
        if self.tipo == "dinero":
            self.configure(placeholder_text="0.00")
            self.bind("<FocusOut>", self.formatear_moneda)
            # Validación de números
            vcmd = (self.register(self.validar_numero), '%P')
            self.configure(validate="key", validatecommand=vcmd)
        elif self.tipo == "fecha":
            self.configure(placeholder_text="DD-MM-AAAA")
            self.bind("<FocusOut>", self.validar_fecha)
            self.bind("<Button-1>", self.abrir_calendario)
        else:
            self.bind("<KeyRelease>", self.verificar_formula)

    def verificar_formula(self, event):
        """Detecta si se ingresó una fórmula que comienza con ="""
        texto = self.get()
        if texto.startswith('='):
            self.evaluar_formula_celda(texto[1:])

    def evaluar_formula_celda(self, formula):
        """Evalúa una fórmula tipo Excel"""
        try:
            # Buscar referencias a celdas (A1, B2, etc)
            def reemplazar_celda(match):
                ref = match.group(0)
                # Buscar en el toplevel la tabla
                root = self.winfo_toplevel()
                for widget in root.winfo_children():
                    if isinstance(widget, TablaContable):
                        return str(widget.obtener_valor_celda(ref))
                return "0"
            
            # Reemplazar referencias de celdas
            formula_procesada = re.sub(r'[A-Z]+\d+', reemplazar_celda, formula)
            
            # Reemplazar operadores y evaluar
            formula_procesada = formula_procesada.replace(',', '.')
            resultado = eval(formula_procesada)
            
            # Formatear según tipo
            if self.tipo == "dinero":
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
                else:
                    self.configure(text_color=("black", "white"))
        except ValueError:
            pass
    
    def validar_numero(self, value):
        if value == "" or value == "-":
            return True
        # Permitir un solo signo negativo
        if value == "-":
            return True
        # Permitir números, punto decimal y un signo negativo al inicio
        patron = r'^-?\d*\.?\d*$'
        if re.match(patron, value):
            return True
        return False
    
    def abrir_calendario(self, event):
        top = ctk.CTkToplevel(self)
        top.title("Seleccionar Fecha")
        top.geometry("250x250")
        top.attributes("-topmost", True)
        top.grab_set()
        
        # Usar tkcalendar
        cal = DateEntry(top, width=12, background='darkblue', 
                       foreground='white', borderwidth=2, 
                       date_pattern='dd/mm/yyyy')
        cal.pack(padx=10, pady=20)
        
        def set_date():
            self.delete(0, "end")
            self.insert(0, cal.get())
            top.destroy()
            
        ctk.CTkButton(top, text="Confirmar", command=set_date, 
                     fg_color="#27ae60").pack(pady=10)
    
    def validar_fecha(self, event):
        """Valida y corrige formato de fecha"""
        texto = self.get()
        if len(texto) == 10 and '/' in texto:
            try:
                datetime.strptime(texto, '%d/%m/%Y')
                self.configure(text_color="#27ae60")
            except:
                self.configure(text_color="#e74c3c")
                self.after(2000, lambda: self.configure(text_color=("black", "white")))


class TablaContable(ctk.CTkFrame):
    
    def __init__(self, master, columnas=None, tipo="Libro Diario", **kwargs):
        super().__init__(master, **kwargs)
        self.encabezados = columnas if columnas else ["Fecha", "Descripcion", "Cuenta", "Debe", "Haber", "IVA %"]
        self.tipo_actual = tipo
        self.filas = []
        self.coords_map = {}  # Mapeo (fila, col) -> coordenada (A1, B2)
        self.reverse_map = {}  # Mapeo coordenada -> widget
        
        # Configurar grid principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Frame para encabezados
        self.header_frame = ctk.CTkFrame(self, fg_color=("gray85", "gray18"), height=45)
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 2))
        self.header_frame.grid_columnconfigure(0, weight=1)
        
        # Scrollable frame para el cuerpo
        self.body_canvas = ctk.CTkScrollableFrame(self, orientation="vertical")
        self.body_canvas.grid(row=1, column=0, sticky="nsew")
        
        self.rows_frame = ctk.CTkFrame(self.body_canvas, fg_color="transparent")
        self.rows_frame.pack(fill="x")
        
        # Footer
        self.footer_frame = ctk.CTkFrame(self, height=45, fg_color=("gray85", "gray18"))
        self.footer_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        
        self.lbl_total_1 = ctk.CTkLabel(self.footer_frame, text="Total Debe: 0.00", 
                                        font=("Roboto", 12, "bold"))
        self.lbl_total_1.pack(side="left", padx=20)
        
        self.lbl_total_2 = ctk.CTkLabel(self.footer_frame, text="Total Haber: 0.00", 
                                        font=("Roboto", 12, "bold"))
        self.lbl_total_2.pack(side="left", padx=20)
        
        self.lbl_naturaleza = ctk.CTkLabel(self.footer_frame, text="", 
                                          font=("Roboto", 11, "bold"))
        self.lbl_naturaleza.pack(side="right", padx=20)
        
        self.dibujar_encabezados()
        self.añadir_fila()

    def dibujar_encabezados(self):
        # Limpiar header existente
        for widget in self.header_frame.winfo_children():
            widget.destroy()
        
        # Frame interno para scroll horizontal si es necesario
        header_inner = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        header_inner.pack(fill="x")
        
        for i, col in enumerate(self.encabezados):
            lbl = ctk.CTkLabel(header_inner, text=col, font=("Roboto", 12, "bold"), 
                              anchor="center", width=140, height=35)
            lbl.grid(row=0, column=i, padx=1, pady=2)
            lbl.bind("<Button-3>", lambda e, idx=i: self.menu_columnas(e, idx))
    
    def menu_columnas(self, event, col_idx):
        menu = ctk.CTkToplevel(self)
        menu.wm_overrideredirect(True)
        menu.geometry(f"200x250+{event.x_root}+{event.y_root}")
        menu.attributes("-topmost", True)
        
        titulo = ctk.CTkLabel(menu, text=self.encabezados[col_idx], font=("Roboto", 10, "bold"))
        titulo.pack(pady=(10, 5))
        
        ctk.CTkFrame(menu, height=1, fg_color="gray50").pack(fill="x", padx=10, pady=5)
        
        btn_rename = ctk.CTkButton(menu, text="Renombrar", 
                                   command=lambda: self.renombrar_columna(col_idx, menu))
        btn_rename.pack(pady=5, padx=10, fill="x")
        
        btn_tipo = ctk.CTkButton(menu, text="Cambiar Tipo",
                                 command=lambda: self.cambiar_tipo_columna(col_idx, menu))
        btn_tipo.pack(pady=5, padx=10, fill="x")
        
        btn_insert = ctk.CTkButton(menu, text="Insertar Columna (Izq)", 
                                   command=lambda: self.insertar_columna(col_idx, menu))
        btn_insert.pack(pady=5, padx=10, fill="x")
        
        if len(self.encabezados) > 1:
            btn_delete = ctk.CTkButton(menu, text="Eliminar Columna", 
                                       fg_color="#c0392b",
                                       command=lambda: self.eliminar_columna(col_idx, menu))
            btn_delete.pack(pady=5, padx=10, fill="x")
        
        menu.bind("<FocusOut>", lambda e: menu.destroy())
    
    def renombrar_columna(self, col_idx, menu):
        menu.destroy()
        nuevo_nombre = ctk.CTkInputDialog(
            text=f"Nuevo nombre para '{self.encabezados[col_idx]}':",
            title="Renombrar"
        ).get_input()
        if nuevo_nombre and nuevo_nombre.strip():
            self.encabezados[col_idx] = nuevo_nombre.strip()
            self.dibujar_encabezados()
    
    def cambiar_tipo_columna(self, col_idx, menu):
        menu.destroy()
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Tipo de Columna")
        dialog.geometry("250x150")
        dialog.attributes("-topmost", True)
        dialog.grab_set()
        
        tipo_var = ctk.StringVar(value="texto")
        
        for t in ["texto", "dinero", "fecha"]:
            rb = ctk.CTkRadioButton(dialog, text=t.capitalize(), variable=tipo_var, value=t)
            rb.pack(pady=5)
        
        def aplicar():
            nuevo_tipo = tipo_var.get()
            for fila in self.filas:
                if col_idx < len(fila):
                    valor = fila[col_idx].get()
                    fila[col_idx].destroy()
                    nueva = CeldaInteligente(self.rows_frame, tipo=nuevo_tipo, width=140)
                    nueva.insert(0, valor)
                    fila[col_idx] = nueva
                    nueva.grid(row=self.filas.index(fila), column=col_idx, padx=1, pady=1)
            dialog.destroy()
        
        ctk.CTkButton(dialog, text="Aplicar", command=aplicar, fg_color="#27ae60").pack(pady=15)
    
    def insertar_columna(self, col_idx, menu):
        menu.destroy()
        nombre = ctk.CTkInputDialog(text="Nombre de la columna:", title="Insertar").get_input()
        if not nombre:
            nombre = f"Nueva {len(self.encabezados)+1}"
        
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
    
    def reorganizar_grid(self):
        for row_idx, fila in enumerate(self.filas):
            for col_idx, celda in enumerate(fila):
                celda.grid(row=row_idx, column=col_idx, padx=1, pady=1)
    
    def mostrar_menu_operaciones(self, event, fila_idx, col_idx):
        """Menú contextual para operaciones entre celdas"""
        menu = ctk.CTkToplevel(self)
        menu.wm_overrideredirect(True)
        menu.geometry(f"250x350+{event.x_root}+{event.y_root}")
        menu.attributes("-topmost", True)
        
        ctk.CTkLabel(menu, text="Operaciones Matemáticas", font=("Roboto", 12, "bold")).pack(pady=(10, 5))
        ctk.CTkFrame(menu, height=1, fg_color="gray50").pack(fill="x", padx=10, pady=5)
        
        # Botones de operaciones básicas
        operaciones = [
            ("➕ Sumar", "suma"),
            ("➖ Restar", "resta"),
            ("✖️ Multiplicar", "multiplicacion"),
            ("➗ Dividir", "division"),
            ("⚡ Potencia", "potencia"),
            ("📊 Promedio", "promedio"),
            ("🔢 Porcentaje", "porcentaje"),
            ("📝 Fórmula Personalizada", "personalizada")
        ]
        
        for texto, op in operaciones:
            btn = ctk.CTkButton(menu, text=texto, fg_color="transparent", height=35,
                               command=lambda o=op: self.seleccionar_operacion(o, fila_idx, col_idx, menu))
            btn.pack(fill="x", padx=10, pady=2)
        
        menu.bind("<FocusOut>", lambda e: menu.destroy())
    
    def seleccionar_operacion(self, operacion, fila_dest, col_dest, menu):
        menu.destroy()
        
        if operacion == "personalizada":
            # Ventana para fórmula personalizada
            dialog = ctk.CTkToplevel(self)
            dialog.title("Fórmula Personalizada")
            dialog.geometry("500x200")
            dialog.attributes("-topmost", True)
            dialog.grab_set()
            
            ctk.CTkLabel(dialog, text="Ingresa tu fórmula (ej: A1 + B2 * 100, usa A1, B2, C3...):").pack(pady=10)
            entry_formula = ctk.CTkEntry(dialog, width=450)
            entry_formula.pack(pady=10)
            
            ctk.CTkLabel(dialog, text="Ejemplos: =A1+B2 | =A1*0.19 | =(A1+B2)/2 | =PROMEDIO(A1:A5)", 
                        font=("Roboto", 9), text_color="gray").pack()
            
            def aplicar_formula():
                formula = entry_formula.get()
                if formula.startswith('='):
                    formula = formula[1:]
                self.aplicar_formula_personalizada(formula, fila_dest, col_dest)
                dialog.destroy()
            
            ctk.CTkButton(dialog, text="Aplicar", command=aplicar_formula, fg_color="#27ae60").pack(pady=15)
            
        else:
            # Para operaciones con selección de celdas
            self.modo_seleccion = operacion
            self.celdas_seleccionadas = []
            self.destino = (fila_dest, col_dest)
            
            # Crear ventana de instrucciones
            self.instrucciones = ctk.CTkToplevel(self)
            self.instrucciones.title("Selección de Celdas")
            self.instrucciones.geometry("300x150")
            self.instrucciones.attributes("-topmost", True)
            
            ctk.CTkLabel(self.instrucciones, 
                        text=f"Operación: {operacion.upper()}\n\nHaz clic en las celdas que deseas usar\n(Presiona ESC para cancelar)", 
                        font=("Roboto", 11)).pack(pady=20)
            
            # Vincular eventos de clic
            self.bind_celdas_seleccion()
            
            def cancelar():
                self.unbind_celdas_seleccion()
                self.instrucciones.destroy()
            
            self.instrucciones.bind("<Escape>", lambda e: cancelar())
            ctk.CTkButton(self.instrucciones, text="Cancelar", command=cancelar, fg_color="red").pack(pady=10)
    
    def bind_celdas_seleccion(self):
        """Vincula eventos de clic para seleccionar celdas"""
        self.seleccion_binds = []
        for r, fila in enumerate(self.filas):
            for c, celda in enumerate(fila):
                celda.bind("<Button-1>", lambda e, rr=r, cc=c: self.seleccionar_celda(rr, cc), add="+")
                self.seleccion_binds.append((celda, r, c))
    
    def unbind_celdas_seleccion(self):
        """Desvincula eventos de selección"""
        for celda, r, c in self.seleccion_binds:
            celda.unbind("<Button-1>")
        self.seleccion_binds = []
    
    def seleccionar_celda(self, fila, col):
        """Selecciona una celda para la operación"""
        celda = self.filas[fila][col]
        # Resaltar celda seleccionada
        original_color = celda.cget("fg_color")
        celda.configure(fg_color="#3498db")
        
        self.celdas_seleccionadas.append((fila, col, celda, original_color))
        
        # Destacar visualmente
        celda.after(200, lambda: celda.configure(fg_color=original_color))
        
        if len(self.celdas_seleccionadas) >= 2:
            self.ejecutar_operacion_seleccionada()
    
    def ejecutar_operacion_seleccionada(self):
        """Ejecuta la operación con las celdas seleccionadas"""
        self.unbind_celdas_seleccion()
        if self.instrucciones:
            self.instrucciones.destroy()
        
        try:
            valores = []
            for fila, col, celda, _ in self.celdas_seleccionadas:
                valor_str = celda.get().replace(',', '')
                try:
                    valor = float(valor_str) if valor_str else 0
                    valores.append(valor)
                except:
                    messagebox.showerror("Error", f"Celda inválida: {celda.get()}")
                    return
            
            if self.modo_seleccion == "suma":
                resultado = sum(valores)
            elif self.modo_seleccion == "resta":
                resultado = valores[0] - sum(valores[1:]) if valores else 0
            elif self.modo_seleccion == "multiplicacion":
                resultado = 1
                for v in valores:
                    resultado *= v
            elif self.modo_seleccion == "division":
                resultado = valores[0]
                for v in valores[1:]:
                    if v != 0:
                        resultado /= v
                    else:
                        messagebox.showerror("Error", "División por cero")
                        return
            elif self.modo_seleccion == "potencia":
                resultado = valores[0] ** valores[1] if len(valores) >= 2 else 0
            elif self.modo_seleccion == "promedio":
                resultado = sum(valores) / len(valores) if valores else 0
            elif self.modo_seleccion == "porcentaje":
                resultado = (valores[0] * valores[1]) / 100 if len(valores) >= 2 else 0
            
            # Aplicar resultado a la celda destino
            destino = self.filas[self.destino[0]][self.destino[1]]
            destino.delete(0, "end")
            destino.insert(0, f"{resultado:,.2f}")
            if resultado < 0:
                destino.configure(text_color="#e74c3c")
            else:
                destino.configure(text_color="#27ae60")
            
            self.recalcular()
            messagebox.showinfo("Éxito", f"Resultado: {resultado:,.2f}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error en operación: {str(e)}")
        finally:
            self.celdas_seleccionadas = []
    
    def aplicar_formula_personalizada(self, formula, fila_dest, col_dest):
        """Aplica una fórmula personalizada"""
        try:
            # Función para reemplazar referencias de celdas
            def reemplazar_referencia(match):
                ref = match.group(0)
                valor = self.obtener_valor_celda(ref)
                return str(valor)
            
            # Reemplazar rangos (ej: A1:A5)
            def procesar_rango(match):
                rango = match.group(0)
                if ':' in rango:
                    inicio, fin = rango.split(':')
                    valores = self.obtener_rango_valores(inicio, fin)
                    return str(valores)
                return rango
            
            # Procesar rangos primero
            formula_procesada = re.sub(r'[A-Z]+\d+:[A-Z]+\d+', procesar_rango, formula)
            # Procesar referencias individuales
            formula_procesada = re.sub(r'[A-Z]+\d+', reemplazar_referencia, formula_procesada)
            
            # Reemplazar funciones simples
            formula_procesada = formula_procesada.replace('SUMA', 'sum')
            formula_procesada = formula_procesada.replace('PROMEDIO', 'sum')
            
            # Evaluar
            resultado = eval(formula_procesada)
            
            # Aplicar resultado
            destino = self.filas[fila_dest][col_dest]
            destino.delete(0, "end")
            if isinstance(resultado, (int, float)):
                destino.insert(0, f"{resultado:,.2f}")
                if resultado < 0:
                    destino.configure(text_color="#e74c3c")
                else:
                    destino.configure(text_color="#27ae60")
            else:
                destino.insert(0, str(resultado))
            
            self.recalcular()
            messagebox.showinfo("Éxito", f"Fórmula aplicada: {resultado}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error en fórmula: {str(e)}\nVerifica la sintaxis")
    
    def obtener_valor_celda(self, referencia):
        """Obtiene el valor numérico de una celda por su referencia (A1, B2, etc)"""
        # Convertir referencia a índices (A1 -> fila 0, col 0)
        import re
        match = re.match(r'([A-Z]+)(\d+)', referencia.upper())
        if match:
            col_str, row_str = match.groups()
            col_idx = sum((ord(c) - 65 + 1) * (26 ** i) for i, c in enumerate(reversed(col_str))) - 1
            row_idx = int(row_str) - 1
            
            if 0 <= row_idx < len(self.filas) and 0 <= col_idx < len(self.filas[row_idx]):
                valor_str = self.filas[row_idx][col_idx].get().replace(',', '')
                try:
                    return float(valor_str) if valor_str else 0
                except:
                    return 0
        return 0
    
    def obtener_rango_valores(self, inicio, fin):
        """Obtiene lista de valores de un rango (A1:A5)"""
        valores = []
        # Implementación simplificada
        # Puedes expandirla según necesidad
        return valores
    
    def añadir_fila(self, datos=None):
        row_idx = len(self.filas)
        fila_widgets = []
        
        for i, col in enumerate(self.encabezados):
            # Determinar tipo automáticamente
            col_lower = col.lower()
            if any(x in col_lower for x in ["debe", "haber", "saldo", "iva", "importe", "monto"]):
                tipo = "dinero"
            elif "fecha" in col_lower:
                tipo = "fecha"
            else:
                tipo = "texto"
            
            e = CeldaInteligente(self.rows_frame, tipo=tipo, width=140)
            e.grid(row=row_idx, column=i, padx=1, pady=1)
            
            if datos and i < len(datos):
                e.insert(0, str(datos[i]))
            
            # Registrar coordenadas
            letra = ''.join(chr(65 + (i // 26) - 1) + chr(65 + (i % 26)) if i >= 26 else chr(65 + i))
            letra = chr(65 + i) if i < 26 else chr(65 + (i // 26) - 1) + chr(65 + (i % 26))
            coord = f"{letra}{row_idx + 1}"
            self.coords_map[(row_idx, i)] = coord
            self.reverse_map[coord] = e
            
            e.bind("<KeyRelease>", lambda ev, r=row_idx, c=i: [self.recalcular(), self.marcar_cambio()])
            e.bind("<Button-3>", lambda ev, r=row_idx, c=i: self.mostrar_menu_operaciones(ev, r, c))
            fila_widgets.append(e)
        
        self.filas.append(fila_widgets)
        self.recalcular()
    
    def marcar_cambio(self):
        try:
            self.winfo_toplevel().cambios_pendientes = True
        except:
            pass
    
    def recalcular(self):
        idx_debe = next((i for i, c in enumerate(self.encabezados) if c.lower() == "debe"), -1)
        idx_haber = next((i for i, c in enumerate(self.encabezados) if c.lower() == "haber"), -1)
        
        total_debe = 0
        total_haber = 0
        
        for fila in self.filas:
            try:
                if idx_debe >= 0 and idx_debe < len(fila):
                    valor_str = fila[idx_debe].get().replace(',', '')
                    total_debe += float(valor_str) if valor_str else 0
                if idx_haber >= 0 and idx_haber < len(fila):
                    valor_str = fila[idx_haber].get().replace(',', '')
                    total_haber += float(valor_str) if valor_str else 0
            except (ValueError, IndexError):
                pass
        
        self.lbl_total_1.configure(text=f"Total Debe: {total_debe:,.2f}")
        self.lbl_total_2.configure(text=f"Total Haber: {total_haber:,.2f}")
        
        diff = total_debe - total_haber
        if abs(diff) < 0.01:
            self.lbl_naturaleza.configure(text="✓ Cuadrado", text_color="#27ae60")
        else:
            self.lbl_naturaleza.configure(text=f"Diferencia: {diff:,.2f}", text_color="#e74c3c")
    
    def limpiar_tabla(self):
        for fila in self.filas:
            for celda in fila:
                celda.destroy()
        self.filas = []
        self.coords_map = {}
        self.reverse_map = {}
        self.añadir_fila()
    
    def obtener_datos(self):
        return [[c.get().strip() for c in f] for f in self.filas if any(c.get().strip() for c in f)]
    
    def añadir_fila_con_datos(self, datos):
        self.añadir_fila(datos)