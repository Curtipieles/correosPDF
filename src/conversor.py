import os
import logging
from fpdf import FPDF
from src.config import FONTS_DIR, DEFAULT_FONT

class ConversorPDF:
    @staticmethod
    def validar_archivo(ruta_usuario, nit):
        # Convertir la ruta a relativa al directorio base
        ruta_archivo = os.path.normpath(os.path.join(ruta_usuario, 'entrada', f'{nit}.txt'))
        logging.info(f"Validando archivo en: {ruta_archivo}")
        if not os.path.exists(ruta_archivo):
            logging.error(f"Archivo no encontrado: {ruta_archivo}")
            return False
        if not os.access(ruta_archivo, os.R_OK):
            logging.error(f"Sin permisos de lectura: {ruta_archivo}")
            return False
        return True

    @staticmethod
    def convertir_a_pdf(ruta_usuario, nit, logo_path, tamano_letra, ruta_pdf):
        try:
            if not ConversorPDF.validar_archivo(ruta_usuario, nit):
                return None

            # Convertir la ruta del PDF a relativa al directorio base
            pdf_dir = os.path.normpath(ruta_pdf)
            os.makedirs(pdf_dir, exist_ok=True)

            font_size = 9 if tamano_letra == 'N' else 8
            
            pdf = PDF()
            pdf.logo_path = logo_path
            
            source_pro_path = os.path.normpath(os.path.join(FONTS_DIR, DEFAULT_FONT['file']))
            logging.info(f"Buscando fuente en: {source_pro_path}")

            if not os.path.exists(source_pro_path):
                logging.error(f"Archivo de fuente no encontrado: {source_pro_path}")
                return None
                
            pdf.add_font('Tipografia', '', source_pro_path, uni=True)
            
            pdf.add_page()
            
            pdf.set_font("Tipografia", size=font_size)
            
            margin_left = 14
            margin_right = 195
            pdf.set_left_margin(margin_left)
            pdf.set_right_margin(pdf.w - margin_right)
            pdf.set_y(34)
            
            char_width = pdf.get_string_width("0")
            max_chars = int((margin_right - margin_left) / char_width)
            
            # Convertir la ruta del archivo de entrada a relativa al directorio base
            ruta_archivo_txt = os.path.normpath(os.path.join(ruta_usuario, 'entrada', f'{nit}.txt'))
            with open(ruta_archivo_txt, 'r', encoding='utf-8') as file:
                for linea in file:
                    if pdf.get_y() > pdf.get_effective_height():
                        pdf.add_page()
                    
                    linea_cortada = linea.rstrip('\n')[:max_chars]
                    pdf.write(5, linea_cortada)
                    pdf.ln()
            
            nombre_pdf = f'{nit}.pdf'
            ruta_completa_pdf = os.path.normpath(os.path.join(pdf_dir, nombre_pdf))
            
            pdf.output(ruta_completa_pdf)
            logging.info(f"PDF generado: {ruta_completa_pdf}")
            return ruta_completa_pdf

        except Exception as e:
            logging.error(f"Error generando PDF: {e}")
            return None

class PDF(FPDF):
    def header(self):
        if os.path.exists(self.logo_path):
            self.image(self.logo_path, x=14, y=8, w=32)
        
        self.set_font("Arial", size=10)
        self.set_xy(19, 27)
        self.cell(0, 5, f"NIT: 800.085.026-8", ln=True, align='L')
        self.ln(1)

    def footer(self):
        self.set_y(-21)  
        self.set_font("Arial", 'BI', 10)
        self.cell(0, 4, "LA NUEVA GENERACIÓN DE CUERO", ln=True, align='C')
        margen = 15
        posicion_inicial = margen
        posicion_final = self.w - margen
        self.line(posicion_inicial, self.get_y() + 2, posicion_final, self.get_y() + 2)
        self.ln(4)
        self.set_font("Arial", "", 9)
        self.multi_cell(0, 6, f"Calle 8 No. 20-15 El Cerrito (valle, Col) - PBX: (092) 2565774 Fax: (092) 2565389 Tels: 2564859 - 2564860 e-mail: contabilidadcurti@gmail.com", align='C')

    def get_effective_height(self):
        return self.h - 1 - 4