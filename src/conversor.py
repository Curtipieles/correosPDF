import os
import logging
import shutil
from fpdf import FPDF
from src.config import FONTS_DIR, BASE_DIR, CURRENT_DIR, DEFAULT_FONT, LOGO_EMPRESA

class ConversorPDF:
    @staticmethod
    def copiar_fuente_a_destino():
        font_name = DEFAULT_FONT['file']
        source_font_path = os.path.join(FONTS_DIR, font_name)
        
        if not os.path.exists(source_font_path):
            logging.error(f"Fuente original no encontrada: {source_font_path}")
            return None
        
        dest_dirs = [
            os.path.normpath(os.path.join(CURRENT_DIR, 'fonts')),
            os.path.normpath(os.path.join(BASE_DIR, 'fonts')),
            os.path.normpath(os.path.join(BASE_DIR, 'src', 'fonts'))
        ]
        
        font_paths = []
        for dest_dir in dest_dirs:
            try:
                os.makedirs(dest_dir, exist_ok=True)
                dest_path = os.path.join(dest_dir, font_name)
                shutil.copy2(source_font_path, dest_path)
                logging.info(f"Fuente copiada a: {dest_path}")
                font_paths.append(dest_path)
            except Exception as e:
                logging.warning(f"No se pudo copiar la fuente a {dest_dir}: {e}")
        
        return font_paths[0] if font_paths else None

    @staticmethod
    def validar_archivo(ruta_usuario, nit):
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

            pdf_dir = os.path.normpath(ruta_pdf)
            os.makedirs(pdf_dir, exist_ok=True)

            # Copiar fuente
            font_path = ConversorPDF.copiar_fuente_a_destino()
            if not font_path:
                logging.error("No se pudo configurar la fuente")
                return None
            
            logging.info(f"Usando archivo de fuente: {font_path}")

            # Método personalizado para búsqueda de fuentes
            def custom_ttfparser(self, ttf_filename):
                logging.info(f"Buscando fuente: {ttf_filename}")
                
                # Si es nuestra fuente específica, usar la ruta correcta
                if os.path.basename(ttf_filename) == DEFAULT_FONT['file']:
                    font_path = os.path.join(FONTS_DIR, DEFAULT_FONT['file'])
                    logging.info(f"Usando fuente personalizada: {font_path}")
                    return original_ttfparser(self, font_path)
                
                # Para otras fuentes, usar el comportamiento original
                return original_ttfparser(self, ttf_filename)

            # Guardar método original
            original_ttfparser = FPDF._ttfparser
            
            # Reemplazar método
            FPDF._ttfparser = custom_ttfparser

            font_size = 9 if tamano_letra == 'N' else 8
            
            pdf = PDF()
            pdf.logo_path = logo_path
            
            # Intentar agregar fuente personalizada
            try:
                pdf.add_font('Tipografia', '', font_path, uni=True)
                logging.info("Fuente personalizada agregada correctamente")
            except Exception as e:
                logging.error(f"Error al agregar fuente personalizada: {e}")
                pdf.set_font("Courier", size=font_size)
                
            pdf.add_page()
            
            # Intentar establecer fuente personalizada
            try:
                pdf.set_font("Tipografia", size=font_size)
            except Exception as e:
                logging.error(f"Error al establecer fuente tipográfica: {e}")
                pdf.set_font("Courier", size=font_size)
            
            margin_left = 14
            margin_right = 195
            pdf.set_left_margin(margin_left)
            pdf.set_right_margin(pdf.w - margin_right)
            pdf.set_y(34)
            
            char_width = pdf.get_string_width("0")
            max_chars = int((margin_right - margin_left) / char_width)
            
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
            
            # Restaurar método original
            FPDF._ttfparser = original_ttfparser
            
            pdf.output(ruta_completa_pdf)
            logging.info(f"PDF generado: {ruta_completa_pdf}")
            return ruta_completa_pdf

        except Exception as e:
            logging.error(f"Error generando PDF: {e}")
            # Asegurarse de restaurar el método original
            try:
                FPDF._ttfparser = original_ttfparser
            except:
                pass
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
    
    def _putfonts(self):
        try:
            super()._putfonts()
        except Exception as e:
            logging.error(f"Error en _putfonts: {e}")