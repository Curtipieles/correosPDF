import os
import logging
from fpdf import FPDF
from src.config import PDF_DIR, BASE_DIR, EMPRESAS_CONFIG, obtener_info_empresa

def obtener_info_empresa_completa(tipo_empresa):
        try:  
            if tipo_empresa in EMPRESAS_CONFIG:
                return EMPRESAS_CONFIG[tipo_empresa]
            else:
                # Retorna información genérica si no encuentra la empresa
                return {
                    'nombre_completo': f'EMPRESA',
                    'logo_file': None,
                    'nit': 'N/A'
                }
        except Exception as e:
            logging.error(f"Error al obtener la informacion de la empresa: {str(e)}")

class ConversorPDF:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_dir = os.path.dirname(self.base_dir)
        self.fonts_dir = os.path.join(self.project_dir, 'fonts')
        self.default_font = {
            'family': 'JetBrainsMono',
            'style': '',
            'file': 'JetBrainsMono-SemiBoldItalic.ttf'
        }

    def validar_archivo(self, ruta_usuario, nombre_archivo):
        ruta_archivo = os.path.normpath(os.path.join(ruta_usuario, 'entrada', f'{nombre_archivo}.txt'))
        if not os.path.exists(ruta_archivo):
            error_msg = f"Archivo de entrada no encontrado: {ruta_archivo}"
            logging.error(error_msg)
            return False, error_msg
        if not os.access(ruta_archivo, os.R_OK):
            error_msg = f"Sin permisos de lectura sobre archivo de entrada: {ruta_archivo}"
            logging.error(error_msg)
            return False, error_msg
        return True, None

    def convertir_a_pdf(self, ruta_usuario, nombre_archivo, tamano_letra):
        try:
            # Validar archivo de entrada
            archivo_valido, error_validacion = self.validar_archivo(ruta_usuario, nombre_archivo)
            if not archivo_valido:
                return None, error_validacion

            # Obtener información de empresa
            info_empresa = obtener_info_empresa()
            if not info_empresa:
                error_msg = "No se pudo obtener información de la empresa desde configuración"
                logging.error(error_msg)
                return None, error_msg

            # Crear directorio de PDFs
            try:
                os.makedirs(PDF_DIR, exist_ok=True)
            except Exception as e:
                error_msg = f"No se pudo crear directorio de PDFs: {str(e)}"
                logging.error(error_msg)
                return None, error_msg
            
            font_size = 9 if tamano_letra == 'N' else 8
            
            try:
                pdf = PDF(info_empresa)
            except Exception as e:
                error_msg = f"Error al inicializar objeto PDF: {str(e)}"
                logging.error(error_msg)
                return None, error_msg
                
            source_pro_path = os.path.normpath(os.path.join(self.fonts_dir, self.default_font['file']))

            # Configurar fuente
            fuente_personalizada = False
            if not os.path.exists(source_pro_path):
                logging.warning(f"Archivo de fuente no encontrado: {source_pro_path}")
                logging.warning("Usando fuente por defecto del sistema")
            else:
                try:
                    pdf.add_font(self.default_font['family'], '', source_pro_path, uni=True)
                    pdf.set_font(self.default_font['family'], size=font_size)
                    fuente_personalizada = True
                except Exception as e:
                    error_msg = f"Error al cargar fuente personalizada: {str(e)}"
                    logging.warning(error_msg)
                    logging.warning("Continuando con fuente por defecto")
            
            # Configurar márgenes automáticamente según membrete
            pdf.set_auto_page_break(True, margin=pdf.margen_inferior)
            
            try:
                pdf.add_page()
            except Exception as e:
                error_msg = f"Error al agregar página inicial: {str(e)}"
                logging.error(error_msg)
                return None, error_msg
            
            # Si no se pudo añadir la fuente personalizada, usar fuente por defecto
            if not fuente_personalizada:
                try:
                    pdf.set_font("Arial", size=font_size)
                except Exception as e:
                    error_msg = f"Error al configurar fuente por defecto: {str(e)}"
                    logging.error(error_msg)
                    return None, error_msg
            
            margin_left = 14
            margin_right = 195
            pdf.set_left_margin(margin_left)
            pdf.set_right_margin(pdf.w - margin_right)
            # Posición inicial automática según membrete
            pdf.set_y(pdf.posicion_inicial_y)
            
            try:
                char_width = pdf.get_string_width("0")
                max_chars = int((margin_right - margin_left) / char_width)
            except Exception as e:
                error_msg = f"Error al calcular ancho de caracteres: {str(e)}"
                logging.error(error_msg)
                return None, error_msg
            
            # Leer y procesar archivo de texto
            ruta_archivo_txt = os.path.normpath(os.path.join(ruta_usuario, 'entrada', f'{nombre_archivo}.txt'))
            try:
                with open(ruta_archivo_txt, 'r', encoding='utf-8') as file:
                    lineas = file.readlines()
            except UnicodeDecodeError as e:
                error_msg = f"Error de codificación al leer archivo de texto: {str(e)}"
                logging.error(error_msg)
                return None, error_msg
            except Exception as e:
                error_msg = f"Error al leer archivo de texto: {str(e)}"
                logging.error(error_msg)
                return None, error_msg
                
            altura_linea = 5
            
            try:
                for i, linea in enumerate(lineas):
                    # Verificar espacio disponible con margen automático
                    if pdf.get_y() > (pdf.h - pdf.margen_inferior):
                        pdf.add_page()
                        pdf.set_y(pdf.posicion_inicial_y)
                    # Procesar la línea
                    linea_cortada = linea.rstrip('\n')[:max_chars]
                    pdf.write(altura_linea, linea_cortada)
                    pdf.ln()
            except Exception as e:
                error_msg = f"Error al escribir contenido en PDF (línea {i+1}): {str(e)}"
                logging.error(error_msg)
                return None, error_msg
            
            # Generar archivo PDF
            nombre_pdf = f'{nombre_archivo}.pdf'
            ruta_completa_pdf = os.path.normpath(os.path.join(PDF_DIR, nombre_pdf))
            
            try:
                pdf.output(ruta_completa_pdf)
            except Exception as e:
                error_msg = f"Error al generar archivo PDF: {str(e)}"
                logging.error(error_msg)
                return None, error_msg
                
            # Verificar que el archivo se creó correctamente
            if not os.path.exists(ruta_completa_pdf):
                error_msg = f"El archivo PDF no se generó correctamente: {ruta_completa_pdf}"
                logging.error(error_msg)
                return None, error_msg
                
            if os.path.getsize(ruta_completa_pdf) == 0:
                error_msg = f"El archivo PDF generado está vacío: {ruta_completa_pdf}"
                logging.error(error_msg)
                return None, error_msg
                
            logging.info(f"PDF generado exitosamente: {ruta_completa_pdf}")
            return ruta_completa_pdf, None

        except Exception as e:
            error_msg = f"Error inesperado generando PDF: {str(e)}"
            logging.error(error_msg)
            return None, error_msg

class PDF(FPDF):
    def __init__(self, info_empresa, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.info_empresa = info_empresa
        self.tipo_empresa = info_empresa['tipo_empresa']

        # Obtener información completa de la empresa
        self.empresa_info = obtener_info_empresa_completa(self.tipo_empresa)

        self.pie_pagina1 = info_empresa['pie_pagina1']
        self.pie_pagina2 = info_empresa['pie_pagina2']
        self.pie_pagina3 = info_empresa['pie_pagina3']
        
        # Configuración automática de espacios según membrete
        self.mostrar_membrete = info_empresa['membrete'].upper() in ['S']
        
        if self.mostrar_membrete:
            # Con membrete: espacios normales
            self.posicion_inicial_y = 34
            self.margen_inferior = 25
        else:
            # Sin membrete: aprovecha todo el espacio
            self.posicion_inicial_y = 1
            self.margen_inferior = 0
        
    def header(self):
        if not self.mostrar_membrete:
            return
            
        try:
            logo_path = None
            if self.empresa_info['logo_file']:
                logo_path = os.path.join(BASE_DIR, 'img', self.empresa_info['logo_file'])
                if not os.path.exists(logo_path):
                    logo_path = None

            if logo_path:
                # Si hay logo, mostrarlo
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
                
                self.image(logo_path, x=x_pos, y=y_pos, w=ancho, h=alto)
                self.set_y(y_pos + alto + 2)
            else:
                # Si no hay logo, mostrar información textual de la empresa
                self.set_font('Arial', 'B', 14)
                self.cell(0, 8, self.empresa_info['nombre_completo'], ln=True, align='C')
                
                # Mostrar NIT si está disponible
                if self.empresa_info['nit'] != 'N/A':
                    self.set_font('Arial', '', 10)
                    self.cell(0, 6, f"NIT: {self.empresa_info['nit']}", ln=True, align='C')
                
                self.ln(5)
                # Línea separadora
                margen = 15
                self.line(margen, self.get_y(), self.w - margen, self.get_y())
                self.ln(8)  

        except Exception as e:
            logging.error(f"Error en el encabezado del PDF: {str(e)}")

    def footer(self):
        if not self.mostrar_membrete:
            return
            
        try:
            self.set_y(-21)
            self.set_font("Helvetica", '', 10)
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
        except Exception as e:
            logging.error(f"Error en footer del PDF: {str(e)}")