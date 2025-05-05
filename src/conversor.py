import os
import logging
from fpdf import FPDF
from src.config import FONTS_DIR, DEFAULT_FONT, PDF_DIR, obtener_info_empresa, obtener_logo_por_empresa

class ConversorPDF:
    def validar_archivo(self, ruta_usuario, nombre_archivo):
        ruta_archivo = os.path.normpath(os.path.join(ruta_usuario, 'entrada', f'{nombre_archivo}.txt'))
        if not os.path.exists(ruta_archivo):
            logging.error(f"Archivo no encontrado: {ruta_archivo}")
            return False
        if not os.access(ruta_archivo, os.R_OK):
            logging.error(f"Sin permisos de lectura: {ruta_archivo}")
            return False
        return True

    def convertir_a_pdf(self, ruta_usuario, nombre_archivo, tamano_letra):
        try:
            if not self.validar_archivo(ruta_usuario, nombre_archivo):
                return None

            info_empresa = obtener_info_empresa()
            if not info_empresa:
                logging.error("No se pudo obtener información de la empresa")
                return None

            os.makedirs(PDF_DIR, exist_ok=True)
            font_size = 9 if tamano_letra == 'N' else 8
            pdf = PDF(info_empresa)
            source_pro_path = os.path.normpath(os.path.join(FONTS_DIR, DEFAULT_FONT['file']))

            if not os.path.exists(source_pro_path):
                logging.error(f"Archivo de fuente no encontrado: {source_pro_path}")
                return None
            
            pdf.add_font(DEFAULT_FONT['family'], '', source_pro_path, uni=True)
            pdf.set_auto_page_break(True, margin=25)  # Activamos el salto automático con margen adecuado
            pdf.add_page()
            pdf.set_font(DEFAULT_FONT['family'], size=font_size)
            
            margin_left = 14
            margin_right = 195
            pdf.set_left_margin(margin_left)
            pdf.set_right_margin(pdf.w - margin_right)
            
            pdf.set_y(34) # Posicionar correctamente después del encabezado - ajustar este valor si es necesario
            
            char_width = pdf.get_string_width("0")
            max_chars = int((margin_right - margin_left) / char_width)
            
            ruta_archivo_txt = os.path.normpath(os.path.join(ruta_usuario, 'entrada', f'{nombre_archivo}.txt'))
            with open(ruta_archivo_txt, 'r', encoding='utf-8') as file:
                lineas = file.readlines()
                
                # Calculamos el espacio disponible en la página
                espacio_disponible = pdf.h - pdf.get_y() - 25  # Altura página - posición actual - margen pie
                altura_linea = 5  # Altura de cada línea en mm
                lineas_por_pagina = int(espacio_disponible / altura_linea)
                
                for i, linea in enumerate(lineas):
                    # Verificar si queda suficiente espacio en la página actual
                    if pdf.get_y() > (pdf.h - 25):  # Si estamos cerca del pie de página
                        pdf.add_page()
                        pdf.set_y(34)  # Reiniciar posición en Y para la nueva página
                    
                    # Procesar la línea
                    linea_cortada = linea.rstrip('\n')[:max_chars]
                    pdf.write(altura_linea, linea_cortada)
                    pdf.ln()
            
            nombre_pdf = f'{nombre_archivo}.pdf'
            ruta_completa_pdf = os.path.normpath(os.path.join(PDF_DIR, nombre_pdf))
            pdf.output(ruta_completa_pdf)
            logging.info(f"PDF generado: {ruta_completa_pdf}")
            return ruta_completa_pdf

        except Exception as e:
            logging.error(f"Error generando PDF: {e}")
            return None

class PDF(FPDF):
    def __init__(self, info_empresa, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.info_empresa = info_empresa
        self.tipo_empresa = info_empresa['tipo_empresa']
        self.pie_pagina1 = info_empresa['pie_pagina1']
        self.pie_pagina2 = info_empresa['pie_pagina2']
        self.pie_pagina3 = info_empresa['pie_pagina3']
        
    def header(self):
        logo_path = obtener_logo_por_empresa(self.tipo_empresa)
        y_pos, alto = 8, 20
        
        if self.tipo_empresa == 'COM':
            ancho = 208
            alto = 26
            y_pos = 8
            x_pos = (self.w - ancho) / 2
        elif self.tipo_empresa == 'CUR':
            ancho = 130
            alto = 26
            y_pos = 8
            x_pos = 14
        elif self.tipo_empresa == 'LBC':
            ancho = 160
            alto = 26
            y_pos = 10
            x_pos = (self.w - ancho) / 2
        else:
            ancho = 120
            x_pos = (self.w - ancho) / 2
        
        if os.path.exists(logo_path):
            logging.info(f"Insertando logo {logo_path} en posición: x={x_pos}, y={y_pos}")
            self.image(logo_path, x=x_pos, y=y_pos, w=ancho, h=alto)
        else:
            logging.warning(f"Logo no encontrado: {logo_path}")
        
        self.set_y(y_pos + alto + 2) # Establece la posición Y después del logo

    def footer(self):
        self.set_y(-21)
        self.set_font("Helvetica", 'BI', 10)
        self.cell(0, 4, "Excelencia desde el origen hasta el producto final", ln=True, align='C')
        margen = 15
        posicion_inicial = margen
        posicion_final = self.w - margen
        self.line(posicion_inicial, self.get_y() + 2, posicion_final, self.get_y() + 2)
        self.ln(4)
        self.set_font("Helvetica", "", 8)
        texto_pie = f"{self.pie_pagina1} | {self.pie_pagina2} | {self.pie_pagina3}"
        self.set_x(margen)
        self.multi_cell(self.w - 2*margen, 4, texto_pie, align='C')
    
    def get_effective_height(self):
        # Altura efectiva para el contenido (descontando encabezado y pie de página)
        return self.h - 34 - 21  # Altura total - encabezado - pie de página