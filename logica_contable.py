# logica_contable_mejorado.py - CON FORMULAENGINE Y FUNCIONES MEJORADAS

import pandas as pd
from tkinter import filedialog, messagebox
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import re

class FormulaEngine:
    """Motor de fórmulas tipo Excel para la tabla contable"""
    
    @staticmethod
    def evaluar_formula(formula, df, fila_actual=None):
        """Evalúa una fórmula estilo Excel con referencias a columnas [NombreColumna]"""
        try:
            formula = str(formula).strip()
            if not formula.startswith('='):
                return None
            
            expr = formula[1:].strip()
            
            def replace_column(match):
                col_name = match.group(1)
                if col_name in df.columns:
                    if fila_actual is not None:
                        return str(df.loc[fila_actual, col_name]) if col_name in df.columns else "0"
                    return f"df['{col_name}']"
                return match.group(0)
            
            expr = re.sub(r'\[([^\]]+)\]', replace_column, expr)
            
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
            
            if fila_actual is not None:
                result = eval(expr, safe_dict)
            else:
                result = eval(expr, safe_dict)
            
            return result
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    @staticmethod
    def aplicar_formula_columna(df, nombre_columna, formula, por_fila=True):
        """Aplica una fórmula a toda una columna y devuelve la serie resultado"""
        try:
            if por_fila:
                resultados = []
                for idx in range(len(df)):
                    resultado = FormulaEngine.evaluar_formula(formula, df, idx)
                    if isinstance(resultado, (int, float)):
                        resultados.append(resultado)
                    else:
                        resultados.append(0)
                return resultados
            else:
                resultado = FormulaEngine.evaluar_formula(formula, df)
                if isinstance(resultado, (int, float)):
                    return [resultado] * len(df)
                return resultado
        except Exception as e:
            print(f"Error en fórmula: {e}")
            return None
    
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


class GestionArchivosMejorado:
    @staticmethod
    def exportar(datos, nombre_cliente, formato):
        if not datos or len(datos) == 0:
            messagebox.showwarning("Aviso", "No hay datos para exportar.")
            return

        extension = ".xlsx" if formato == "Excel" else ".pdf"
        tipo_archivo = [("Excel", "*.xlsx")] if formato == "Excel" else [("PDF", "*.pdf")]

        ruta_guardado = filedialog.asksaveasfilename(
            defaultextension=extension,
            filetypes=tipo_archivo,
            initialfile=f"Reporte_{nombre_cliente}",
            title="Guardar Exportación"
        )
        
        if not ruta_guardado: 
            return

        try:
            if formato == "Excel":
                columnas = [f"Col {i+1}" for i in range(len(datos[0]))]
                df = pd.DataFrame(datos, columns=columnas)
                df.to_excel(ruta_guardado, index=False)
                messagebox.showinfo("Éxito", "Excel guardado correctamente.")

            elif formato == "PDF":
                doc = SimpleDocTemplate(ruta_guardado, pagesize=letter)
                styles = getSampleStyleSheet()
                elementos = []

                titulo = Paragraph(f"<b>ESTADO CONTABLE: {nombre_cliente.upper()}</b>", styles['Title'])
                subtitulo = Paragraph(f"Reporte generado: {pd.Timestamp.now().strftime('%d/%m/%Y')}", styles['Normal'])
                elementos.append(titulo)
                elementos.append(subtitulo)
                elementos.append(Spacer(1, 20))

                tabla_data = datos
                t = Table(tabla_data, repeatRows=1)
                
                estilo = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#34495e")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white])
                ])
                t.setStyle(estilo)
                elementos.append(t)
                doc.build(elementos)
                messagebox.showinfo("Éxito", "PDF guardado correctamente.")

        except Exception as e:
            messagebox.showerror("Error de Exportación", f"Detalle: {str(e)}")
    
    @staticmethod
    def leer_archivo_para_importar():
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo",
            filetypes=[("Archivos Contables", "*.xlsx *.xls *.csv")]
        )
        if not ruta:
            return None, None

        try:
            if ruta.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(ruta)
            else:
                df = pd.read_csv(ruta)
        
            df = df.fillna("") 
            columnas = list(df.columns)
            datos = df.astype(str).values.tolist()
        
            return columnas, datos
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo: {e}")
            return None, None


class Plantillas:
    DIARIO = ["Fecha", "Descripción", "Cuenta", "Debe", "Haber", "IVA %"]
    BALANZA = ["Código", "Cuenta", "Saldo Inicial", "Cargos", "Abonos", "Saldo Final"]
    MAYOR = ["Fecha", "Concepto", "Referencia", "Debe", "Haber", "Saldo"]

    @staticmethod
    def obtener_columnas(tipo):
        if "Balanza" in tipo: 
            return Plantillas.BALANZA
        if "Cuentas T" in tipo or "Mayor" in tipo: 
            return Plantillas.MAYOR
        return Plantillas.DIARIO