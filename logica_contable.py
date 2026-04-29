import pandas as pd
from tkinter import filedialog, messagebox
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

class GestionArchivos:
    @staticmethod
    def exportar(datos, nombre_cliente, formato):
        if not datos or len(datos) == 0:
            messagebox.showwarning("Aviso", "No hay datos para exportar.")
            return

        # CORRECCIÓN: Filtros de archivo para que no salga vacío
        extension = ".xlsx" if formato == "Excel" else ".pdf"
        tipo_archivo = [("Excel", "*.xlsx")] if formato == "Excel" else [("PDF", "*.pdf")]

        ruta_guardado = filedialog.asksaveasfilename(
            defaultextension=extension,
            filetypes=tipo_archivo,
            initialfile=f"Reporte_{nombre_cliente}",
            title="Guardar Exportación"
        )
        
        if not ruta_guardado: return

        try:
            if formato == "Excel":
                # Detectamos cuántas columnas hay para poner encabezados genéricos si varía
                columnas = [f"Col {i+1}" for i in range(len(datos[0]))]
                df = pd.DataFrame(datos, columns=columnas)
                df.to_excel(ruta_guardado, index=False)
                messagebox.showinfo("Éxito", "Excel guardado correctamente.")

            elif formato == "PDF":
                doc = SimpleDocTemplate(ruta_guardado, pagesize=letter)
                styles = getSampleStyleSheet()
                elementos = []

                # Encabezado profesional
                titulo = Paragraph(f"<b>ESTADO CONTABLE: {nombre_cliente.upper()}</b>", styles['Title'])
                subtitulo = Paragraph(f"Reporte generado: 2026", styles['Normal'])
                elementos.append(titulo)
                elementos.append(subtitulo)
                elementos.append(Spacer(1, 20))

                # Datos de la tabla
                tabla_data = datos
                t = Table(tabla_data, repeatRows=1)
                
                # Estilo tipo Despacho
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
        
        # Convertimos todo a string para los CTkEntry y evitamos valores NaN
            df = df.fillna("") 
            columnas = list(df.columns)
            datos = df.astype(str).values.tolist()
        
            return columnas, datos
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo: {e}")
            return None, None

class Plantillas:
    DIARIO = ["Fecha", "Descripción", "Cuenta", "Debe", "Haber", "IVA %"]
    BALANZA = ["Código", "Cuenta", "S. Inicial", "Cargos", "Abonos", "Saldo Final"]
    MAYOR = ["Fecha", "Concepto", "Referencia", "Debe", "Haber", "Saldo"]

    @staticmethod
    def obtener_columnas(tipo):
        if "Balanza" in tipo: return Plantillas.BALANZA
        if "Cuentas T" in tipo or "Mayor" in tipo: return Plantillas.MAYOR
        return Plantillas.DIARIO