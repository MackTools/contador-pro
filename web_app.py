# ========== FUNCIONES DE REPORTES ==========

def generar_balance_general(edited_df, nombre_proyecto):
    """Genera un Balance General profesional con Activos, Pasivos y Capital"""
    
    # Detectar cuentas según patrones comunes (contabilidad básica)
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
    
    # Determinar qué columna contiene el monto (Debe o Haber según el contexto)
    if "Debe" in edited_df.columns and "Haber" in edited_df.columns:
        # Para balance, usamos saldo = Debe - Haber (para activos y gastos)
        # o Haber - Debe (para pasivos, capital e ingresos)
        
        for idx, row in edited_df.iterrows():
            desc = str(row.get("Descripción", row.get("Cuenta", row.get("Concepto", "")))).lower()
            debe = row.get("Debe", 0) or 0
            haber = row.get("Haber", 0) or 0
            saldo_normal = debe - haber  # Por defecto, activos/gastos
            
            # Clasificación semiautomática
            es_activo = any(p in desc for p in palabras_activo)
            es_pasivo = any(p in desc for p in palabras_pasivo)
            es_capital = any(p in desc for p in palabras_capital)
            
            if es_activo:
                activos += saldo_normal
            elif es_pasivo:
                # Pasivos: saldo acreedor (Haber > Debe)
                pasivos += (haber - debe)
            elif es_capital:
                capital += (haber - debe)
            else:
                # Por defecto, si no se clasifica, intentar inferir por el saldo
                if saldo_normal > 0:
                    activos += saldo_normal
                else:
                    pasivos += abs(saldo_normal)
    
    # Calcular totales
    total_pasivo_capital = pasivos + capital
    
    return {
        "activos": activos,
        "pasivos": pasivos, 
        "capital": capital,
        "total_pasivo_capital": total_pasivo_capital,
        "diferencia": activos - total_pasivo_capital
    }

def generar_estado_resultados(edited_df):
    """Genera Estado de Resultados con Ingresos, Gastos y Utilidad Neta"""
    
    ingresos = 0
    gastos = 0
    
    # Palabras clave por tipo
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
                # Los ingresos se registran en el Haber
                ingresos += haber
            elif es_gasto:
                # Los gastos se registran en el Debe
                gastos += debe
            else:
                # Inferencia por saldo
                if haber > debe:
                    ingresos += haber
                elif debe > haber:
                    gastos += debe
    
    utilidad_neta = ingresos - gastos
    
    return {
        "ingresos": ingresos,
        "gastos": gastos,
        "utilidad_neta": utilidad_neta,
        "tipo": "Ganancia" if utilidad_neta > 0 else "Pérdida" if utilidad_neta < 0 else "Equilibrio"
    }

def exportar_pdf_reporte(tipo, datos, nombre_proyecto):
    """Exporta reporte a PDF usando ReportLab"""
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from io import BytesIO
    
    buffer = BytesIO()
    
    if tipo == "balance":
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Estilo personalizado
        titulo_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=16,
            textColor=colors.HexColor('#1a1e2e'),
            alignment=1,
            spaceAfter=30
        )
        
        elementos = []
        
        # Título
        elementos.append(Paragraph(f"<b>BALANCE GENERAL</b>", titulo_style))
        elementos.append(Paragraph(f"{nombre_proyecto}", styles['Normal']))
        elementos.append(Spacer(1, 0.2*inch))
        
        # Datos del balance
        data = [
            ['', 'Monto (USD)'],
            ['<b>ACTIVOS</b>', f'<b>${datos["activos"]:,.2f}</b>'],
            ['', ''],
            ['<b>PASIVOS</b>', f'<b>${datos["pasivos"]:,.2f}</b>'],
            ['<b>CAPITAL</b>', f'<b>${datos["capital"]:,.2f}</b>'],
            ['', ''],
            ['<b>TOTAL PASIVO + CAPITAL</b>', f'<b>${datos["total_pasivo_capital"]:,.2f}</b>'],
            ['', ''],
            ['<b>DIFERENCIA (Activo - Pasivo+Capital)</b>', f'<b>${datos["diferencia"]:,.2f}</b>']
        ]
        
        tabla = Table(data, colWidths=[4*inch, 2*inch])
        tabla.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#2d3748')),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (0, 3), colors.HexColor('#e8f0fe')),
            ('BACKGROUND', (0, 4), (0, 6), colors.HexColor('#fef9e8')),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
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
        elementos.append(Spacer(1, 0.2*inch))
        
        # Calcular indicadores
        margen_bruto = (datos["ingresos"] - datos["gastos"]) / datos["ingresos"] * 100 if datos["ingresos"] > 0 else 0
        
        data = [
            ['', 'Monto (USD)', 'Indicador'],
            ['<b>INGRESOS</b>', f'<b>${datos["ingresos"]:,.2f}</b>', '<b>100%</b>'],
            ['<b>GASTOS</b>', f'<b>${datos["gastos"]:,.2f}</b>', f'<b>{((datos["gastos"]/datos["ingresos"])*100) if datos["ingresos"] > 0 else 0:.1f}%</b>'],
            ['', '', ''],
            ['<b>UTILIDAD NETA</b>', f'<b>${datos["utilidad_neta"]:,.2f}</b>', f'<b>{margen_bruto:.1f}%</b>'],
            ['', '', ''],
            ['<b>RESULTADO</b>', f'<b>{datos["tipo"]}</b>', '']
        ]
        
        # Color según resultado
        if datos["utilidad_neta"] > 0:
            data.append(['', '', ''])
            data.append(['', '<b>✓ Utilidad del período</b>', ''])
        elif datos["utilidad_neta"] < 0:
            data.append(['', '', ''])
            data.append(['', '<b>⚠ Pérdida del período</b>', ''])
        
        tabla = Table(data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        
        color_fila_ingreso = colors.HexColor('#e8f8f5') if datos["utilidad_neta"] > 0 else colors.HexColor('#fef9e8')
        
        tabla.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.white),
            ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#3498db') if datos["utilidad_neta"] > 0 else colors.HexColor('#e67e22')),
            ('TEXTCOLOR', (0, 4), (-1, 4), colors.white),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        elementos.append(tabla)
        
        # Nota explicativa
        elementos.append(Spacer(1, 0.3*inch))
        nota = Paragraph(
            "<i>Nota: Los valores se basan en la clasificación automática de cuentas. "
            "Para mayor precisión, revise la categorización de cada partida.</i>",
            styles['Italic']
        )
        elementos.append(nota)
        
        doc.build(elementos)
    
    buffer.seek(0)
    return buffer

# ========== INTEGRAR REPORTES EN LA INTERFAZ ==========
# Agregar esta sección después de las métricas y antes de las gráficas
# Busca donde dice "# Botones de acción" y agrega un cuarto botón para reportes

# Reemplazar la sección de botones de acción con esta versión actualizada:

# Botones de acción (actualizado con Reportes)
col_accion1, col_accion2, col_accion3, col_accion4, col_accion5 = st.columns([1, 1, 1, 1, 2])

with col_accion1:
    if st.button("Guardar", use_container_width=True):
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

with col_accion2:
    if st.button("Exportar Excel", use_container_width=True):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            edited_df.to_excel(writer, sheet_name=proyecto["nombre"], index=False)
        st.download_button(
            label="Descargar archivo",
            data=output.getvalue(),
            file_name=f"{proyecto['nombre']}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="download_excel"
        )

with col_accion3:
    if st.button("Balance General", use_container_width=True):
        if len(edited_df) > 0:
            balance = generar_balance_general(edited_df, proyecto["nombre"])
            pdf_buffer = exportar_pdf_reporte("balance", balance, proyecto["nombre"])
            st.download_button(
                label="Descargar Balance PDF",
                data=pdf_buffer,
                file_name=f"Balance_{proyecto['nombre']}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="download_balance"
            )
        else:
            st.warning("No hay datos para generar el Balance General")

with col_accion4:
    if st.button("Estado Resultados", use_container_width=True):
        if len(edited_df) > 0:
            resultados = generar_estado_resultados(edited_df)
            pdf_buffer = exportar_pdf_reporte("resultados", resultados, proyecto["nombre"])
            st.download_button(
                label="Descargar Resultados PDF",
                data=pdf_buffer,
                file_name=f"Resultados_{proyecto['nombre']}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="download_resultados"
            )
        else:
            st.warning("No hay datos para generar el Estado de Resultados")

with col_accion5:
    if st.button("Eliminar proyecto", use_container_width=True):
        st.session_state.confirmar_eliminar = True
