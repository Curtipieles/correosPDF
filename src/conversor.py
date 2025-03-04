import os
import logging
import shutil
from fpdf import FPDF
from src.config import FONTS_DIR, DEFAULT_FONT

class ConversorPDF:
    @staticmethod
    def copiar_fuente_a_destino():
        """
        Copia la fuente a todos los posibles directorios donde FPDF podría buscarla
        """
        font_name = DEFAULT_FONT['file']
        source_font_path = os.path.join(FONTS_DIR, font_name)
        
        if not os.path.exists(source_font_path):
            logging.error(f"Fuente original no encontrada: {source_font_path}")
            return None
            
        # Obtener el directorio actual del script
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Lista de posibles destinos
        dest_dirs = [
            # Directorio relativo que FPDF está buscando según el error
            os.path.normpath(os.path.join(current_script_dir, '..', 'fonts')),
            # Directorio absoluto que vemos en el error
            r'C:\curti\correos\fonts',
            # Directorio relativo a la ubicación actual
            os.path.join(current_script_dir, 'fonts'),
            # Directorio temporal específico
            os.path.join(current_script_dir, 'temp_fonts')
        ]
        
        # Crear los directorios y copiar la fuente
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
        
        # También intentar copiar al directorio específico del error
        error_path = r'C:\curti\correos\src\..\fonts'
        try:
            os.makedirs(error_path, exist_ok=True)
            error_font_path = os.path.join(error_path, font_name)
            shutil.copy2(source_font_path, error_font_path)
            logging.info(f"Fuente copiada a la ruta del error: {error_font_path}")
            font_paths.append(error_font_path)
        except Exception as e:
            logging.warning(f"No se pudo copiar la fuente a la ruta del error: {e}")
            
        return font_paths[0] if font_paths else None

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

            # Copiar la fuente a todas las posibles ubicaciones
            font_path = ConversorPDF.copiar_fuente_a_destino()
            if not font_path:
                logging.error("No se pudo configurar la fuente")
                return None
                
            logging.info(f"Usando archivo de fuente principal: {font_path}")
            
            # Intentar método alternativo: monkeypatching
            # Guardar el método original
            original_ttfparser = FPDF._ttfparser
            
            # Crear un método de reemplazo que use nuestra ruta específica
            def custom_ttfparser(self, file):
                logging.info(f"Interceptando llamada a _ttfparser con archivo: {file}")
                # Si es nuestra fuente, reemplazar con la ruta absoluta correcta
                if os.path.basename(file) == DEFAULT_FONT['file']:
                    logging.info(f"Reemplazando ruta de fuente con: {font_path}")
                    return original_ttfparser(self, font_path)
                return original_ttfparser(self, file)
                
            # Reemplazar el método
            FPDF._ttfparser = custom_ttfparser

            font_size = 9 if tamano_letra == 'N' else 8
            
            pdf = PDF()
            pdf.logo_path = logo_path
            
            # Usar una fuente incorporada en FPDF como respaldo
            try:
                pdf.add_font('Tipografia', '', font_path, uni=True)
                logging.info("Fuente personalizada agregada correctamente")
            except Exception as e:
                logging.error(f"Error al agregar fuente personalizada: {e}")
                logging.info("Usando fuente incorporada como respaldo")
                pdf.set_font("Courier", size=font_size)
                
            pdf.add_page()
            
            # Intentar establecer la fuente personalizada, o usar la fuente de respaldo
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
            
            # Restaurar el método original antes de finalizar
            FPDF._ttfparser = original_ttfparser
            
            pdf.output(ruta_completa_pdf)
            logging.info(f"PDF generado: {ruta_completa_pdf}")
            return ruta_completa_pdf

        except Exception as e:
            logging.error(f"Error generando PDF: {e}")
            # Asegurarse de restaurar el método original en caso de error
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