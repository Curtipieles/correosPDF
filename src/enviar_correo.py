from collections import namedtuple
from email.utils import formataddr, formatdate, make_msgid
import smtplib
import logging
import time
import re
import socket
import requests
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from src.config import ARCHIVO_DIRECCIONES, ARCHIVO_INFO_CORREOS, obtener_info_empresa, obtener_logo_por_empresa

info_correo = namedtuple('info_correo', ['asunto', 'cuerpo'])

class EnviadorCorreo:
    def __init__(self):
        # Configurar parámetros de reintento
        self.max_intentos = 5
        self.tiempo_espera_base = 30  # segundos
        self.internet_disponible = True
        self.info_empresa = obtener_info_empresa()
        self.tipo_empresa = self.info_empresa['tipo_empresa']
        self.logo_empresa = obtener_logo_por_empresa(self.tipo_empresa)
        
        # Configuración específica para cada tipo de empresa
        self.config_empresa = {
            'CUR': {
                'color_encabezado': '#4a2511',  # Marrón para Curtipieles
                'nombre_empresa': 'Curtipieles S.A.S',
                'descripcion': 'Especialistas en comercialización de cueros de alta calidad',
                'color_banner': '#f5f0e8',
                'color_borde': '#e0d5c5',
                'color_texto': '#5d4b35',
                'productos': [
                    'Cueros tratados para diferentes usos',
                    'Pieles de diversos acabados',
                    'Materiales para marroquinería'
                ],
                'beneficios': [
                    'Atención personalizada y asesoría técnica',
                    'Entregas puntuales y garantía en todos nuestros productos',
                    'Variedad de acabados y texturas para diferentes necesidades'
                ]
            },
            'COM': {
                'color_encabezado': '#083D77',  # Azul para Comercueros
                'nombre_empresa': 'Comercializadora Calle & CÍA. S. En C.S.',
                'descripcion': 'Comercio al por mayor de materias primas agropecuarias y animales vivos',
                'color_banner': '#e6f0f7',
                'color_borde': '#c0d5e5',
                'color_texto': '#355d7d',
                'productos': [
                    'Insumos agropecuarios de primera calidad',
                    'Materias primas para diversos sectores',
                    'Servicios especializados para el sector agropecuario'
                ],
                'beneficios': [
                    'Gran variedad de productos nacionales e importados',
                    'Asesoría profesional para la elección de materiales',
                    'Precios competitivos y descuentos por volumen'
                ]
            },
            'LBC': {
                'color_encabezado': '#1E5631',  # Verde para La Bodega
                'nombre_empresa': 'Luis Bernardo Calle Pareja',
                'descripcion': 'Servicios especializados en cría de cerdos y relacionados',
                'color_banner': '#e8f5ed',
                'color_borde': '#c5e0d0',
                'color_texto': '#355d42',
                'productos': [
                    'Productos para cría y cuidado de cerdos',
                    'Insumos para producción porcícola',
                    'Asesoría en manejo de granjas porcinas'
                ],
                'beneficios': [
                    'Amplio stock disponible para entrega inmediata',
                    'Productos seleccionados de los mejores proveedores',
                    'Excelente relación calidad-precio'
                ]
            }
        }
        
        # Valores por defecto en caso de no encontrar el tipo de empresa
        config_default = {
            'color_encabezado': '#333333',
            'nombre_empresa': 'Empresa S.A.S',
            'descripcion': 'Productos y servicios de calidad',
            'color_banner': '#f5f5f5',
            'color_borde': '#e0e0e0',
            'color_texto': '#555555',
            'productos': [
                'Productos de alta calidad',
                'Servicios especializados',
                'Soluciones a medida'
            ],
            'beneficios': [
                'Atención personalizada',
                'Garantía en todos nuestros productos',
                'Excelente relación calidad-precio'
            ]
        }
        
        # Obtener la configuración para la empresa actual o usar valores por defecto
        self.config_actual = self.config_empresa.get(self.tipo_empresa, config_default)
        
        # Asignar valores desde la configuración
        self.color_encabezado = self.config_actual['color_encabezado']
        self.nombre_empresa = self.config_actual['nombre_empresa']
        self.color_banner = self.config_actual['color_banner']
        self.color_borde = self.config_actual['color_borde']
        self.color_texto = self.config_actual['color_texto']
        
        # Obtener dirección y teléfono de la empresa
        self.direccion = self.info_empresa.get('direccion', 'Cl. 8 #20-15, El Cerrito, Valle del Cauca, Colombia')
        self.telefono = self.info_empresa.get('telefono', '+57 3173711707')

    def _get_contenido_adicional(self):
        """Genera contenido adicional según el tipo de empresa."""
        productos_html = ''.join([f'<li>{producto}</li>' for producto in self.config_actual['productos']])
        beneficios_html = ''.join([f'<li>{beneficio}</li>' for beneficio in self.config_actual['beneficios']])
        
        return f"""
        <div style="color: #333333; font-size: 14px; margin-top: 30px; padding: 15px; border-top: 1px solid #e0e0e0;">
            <h3>Información sobre nuestros productos y servicios</h3>
            <p>En {self.nombre_empresa} nos especializamos en {self.config_actual['descripcion']}. 
               Todos nuestros productos y servicios cumplen con altos estándares de calidad para satisfacer 
               las necesidades de nuestros clientes más exigentes.</p>
            
            <h4>Nuestros principales productos:</h4>
            <ul>
                {productos_html}
            </ul>
            
            <h4>Beneficios de trabajar con {self.nombre_empresa}:</h4>
            <ul>
                {beneficios_html}
            </ul>
            
            <p>Agradecemos su confianza en nuestros productos y servicios. Estamos comprometidos con la 
               excelencia y la mejora continua para ofrecerle siempre la mejor calidad.</p> 
            <p>Si necesita más información, no dude en contactar con nuestro equipo de atención al cliente, 
               quienes estarán encantados de resolver cualquier duda que pueda tener.</p>
        </div>
        """

    def comprobar_conexion(self):
        """Comprueba si hay conexión a internet"""
        try:
            # Intenta conectarse a Google DNS para verificar conexión
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            # Intenta hacer una petición HTTP a Google como segunda verificación
            requests.get("https://www.google.com", timeout=3)
            self.internet_disponible = True
            return True
        except (socket.error, requests.RequestException):
            self.internet_disponible = False
            return False

    def iniciar_monitor_conexion(self):
        """Inicia un hilo para monitorear la conexión a internet"""
        def monitor():
            while True:
                self.comprobar_conexion()
                time.sleep(60)  # Comprobar cada minuto
        
        # Iniciar hilo en modo daemon para que termine cuando termine el programa principal
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    @staticmethod
    def obtener_correo_por_codigo(codigo_archivo):
        """Obtiene el correo destino según el código de archivo."""
        try:
            with open(ARCHIVO_DIRECCIONES, 'r') as file:
                for linea in file:
                    datos = linea.strip().split(',')
                    # Nueva estructura: estado,codigo,correo
                    if len(datos) >= 3 and datos[1] == codigo_archivo:
                        return datos[2]
            logging.warning(f"Código {codigo_archivo} no encontrado en direcciones")
            return None
        except FileNotFoundError:
            logging.error(f"Archivo de direcciones no encontrado: {ARCHIVO_DIRECCIONES}")
        except Exception as e:
            logging.error(f"Error buscando correo: {e}")
        return None
    
    def obtener_info_correo(self):
        """Obtiene la información de asunto y cuerpo del correo."""
        try:
            with open(ARCHIVO_INFO_CORREOS, 'r', encoding='utf-8') as file:
                lineas = file.readlines()
                asunto = lineas[0].strip()
                cuerpo = ''.join(lineas[1:]).strip()
            if asunto and cuerpo:
                return info_correo(asunto, cuerpo)
            logging.warning(f"Asunto o cuerpo vacío en archivo info_correo")
            return None
        except FileNotFoundError:
            logging.error(f"Archivo info_correo no encontrado: {ARCHIVO_INFO_CORREOS}")
        except Exception as e:
            logging.error(f"Error leyendo información del correo: {e}")
        return None

    def _limpiar_texto_html(self, texto):
        """Elimina etiquetas HTML para obtener texto plano."""
        return re.sub(r'<[^>]*>', '', texto)
    
    def _asegurar_longitud_minima(self, cuerpo):
        """Asegura que el cuerpo del correo tenga suficiente texto (al menos 300 palabras)."""
        texto_plano = self._limpiar_texto_html(cuerpo)
        palabras = texto_plano.split()
        
        # Si el texto tiene menos de 300 palabras, añadir contenido adicional
        if len(palabras) < 300:
            return cuerpo + self._get_contenido_adicional()
        return cuerpo

    def esperar_por_conexion(self, intento):
        """Espera un tiempo antes de reintentar, usando backoff exponencial"""
        tiempo_espera = self.tiempo_espera_base * (2 ** (intento - 1))  # Backoff exponencial
        tiempo_espera = min(tiempo_espera, 300)  # Máximo 5 minutos
        
        logging.info(f"Esperando {tiempo_espera} segundos antes de reintentar (intento {intento}/{self.max_intentos})...")
        
        # Esperar con comprobaciones periódicas
        tiempo_inicio = time.time()
        while time.time() - tiempo_inicio < tiempo_espera:
            if self.comprobar_conexion():
                logging.info("¡Conexión a internet recuperada!")
                return True
            time.sleep(5)  # Comprobar cada 5 segundos
        
        return self.comprobar_conexion()  # Comprobar una vez más antes de continuar

    def enviar_correo_gmail(self, codigo_archivo, pdf_path, config_correo):
        """Envía un correo con el PDF adjunto usando Gmail."""
        detalles_error = None
        intento = 0
        
        # Iniciar monitor de conexión en segundo plano
        self.iniciar_monitor_conexion()
        
        while intento < self.max_intentos:
            intento += 1
            try:
                if not self.internet_disponible and not self.comprobar_conexion():
                    detalles_error = "Sin conexión a internet"
                    logging.warning(f"Sin conexión a internet. Reintentando... (intento {intento}/{self.max_intentos})")
                    if not self.esperar_por_conexion(intento):
                        continue  # Sigue esperando si no hay conexión
                
                correo_destino = self.obtener_correo_por_codigo(codigo_archivo)
                info = self.obtener_info_correo()
                
                if not correo_destino:
                    detalles_error = f"No se encontró correo destino para {codigo_archivo}"
                    logging.error(detalles_error)
                    return False, detalles_error
                    
                if not info:
                    detalles_error = "No se pudo obtener información del correo"
                    logging.error(detalles_error)
                    return False, detalles_error
                    
                asunto, cuerpo_original = info.asunto, info.cuerpo
                
                # Asegurar que el correo tiene suficiente texto para mejorar ratio imagen/texto
                cuerpo = self._asegurar_longitud_minima(cuerpo_original)
                
                msg = MIMEMultipart('alternative')
                msg['From'] = formataddr((self.nombre_empresa, config_correo['usuario']))
                msg['To'] = correo_destino
                msg['Subject'] = asunto
                
                # Usar un Message-ID conforme a RFC 5322 con el dominio real del remitente
                domain = config_correo['usuario'].split('@')[1]
                msg['Message-ID'] = make_msgid(domain=domain)
                msg['X-Authentication-Warning'] = f"{domain} sender verified"
                
                # Fecha correo
                msg['Date'] = formatdate(localtime=True)
                tiempo_colombia = time.time() - (5 * 3600) # Restamos 5 horas en segundos
                msg['Date'] = formatdate(tiempo_colombia, localtime=False)
                msg['Reply-To'] = 'no-reply+unsubscribe@' + domain
                
                msg['Precedence'] = 'list'
                msg['X-Mailer'] = f"{self.nombre_empresa} Sistema CorreosPDF"
                msg['X-Priority'] = '3'  # Prioridad normal
                msg['X-MSMail-Priority'] = 'Normal'

                # Configuración de desuscripción según RFC 8058
                unsubscribe_email = 'unsubscribe@' + domain
                msg['List-Unsubscribe'] = f"<mailto:{unsubscribe_email}?subject=unsubscribe-{codigo_archivo}>"
                msg['List-Unsubscribe-Post'] = "List-Unsubscribe=One-Click"
                
                # Generar Feedback-ID basado en el tipo de empresa
                empresa_codigo = self.tipo_empresa.lower()
                msg['Feedback-ID'] = f"{empresa_codigo}:{codigo_archivo}:{time.strftime('%Y%m')}"
                
                msg['X-Spam-Status'] = 'No'
                msg['X-Spam-Score'] = '0.0'
                msg['X-Spam-Level'] = ''
                msg['X-Spam-Flag'] = 'NO'
                
                # Cargar la imagen desde un archivo local
                logo_cid = "cid:logo"
                try:
                    with open(self.logo_empresa, 'rb') as img_file:
                        img_data = img_file.read()
                        image = MIMEImage(img_data)
                        image.add_header('Content-ID', '<logo>')
                        image.add_header('Content-Disposition', 'inline')
                        msg.attach(image)
                except Exception as e:
                    logging.error(f"No se pudo cargar la imagen del logo: {e}")
                    logo_cid = ""
                
                # Convertir HTML a texto plano
                texto_plano = self._limpiar_texto_html(cuerpo)
                texto_plano += f"\n\n---\n{self.nombre_empresa} agradece su confianza.\nPara darte de baja, responde a este correo con el asunto 'unsubscribe'"
                part_text = MIMEText(texto_plano, 'plain', 'utf-8')
                
                # Preparar la sección del encabezado dependiendo de si tenemos logo o no
                encabezado_html = f"""
                <div style="background-color: {self.color_encabezado}; padding: 20px; text-align: center;">
                    {"<img src='"+logo_cid+"' alt='Logo "+self.nombre_empresa+"' style='max-height: 60px;'>" if logo_cid else ""}
                    <h1 style="color: #ffffff; margin: {"10px 0 0 0" if logo_cid else "0"}; font-size: {"22px" if logo_cid else "24px"};">{self.nombre_empresa}</h1>
                    <p style="color: #ffffff; margin: 5px 0 0 0; font-size: 16px;">{self.config_actual['descripcion']}</p>
                </div>
                """
                
                # Versión HTML con mejor estructura
                html_cuerpo = f"""
                <!DOCTYPE html>
                <html lang="es">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>{asunto}</title>
                </head>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f9f9f9; margin: 0; padding: 0;">
                    <div style="max-width: 650px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); overflow: hidden;">
                        <!-- Encabezado -->
                        {encabezado_html}
                        
                        <!-- Contenido principal -->
                        <div style="padding: 30px 25px;">
                            {cuerpo.replace('\n', '<br>')}
                        </div>
                        
                        <div style="background-color: {self.color_banner}; padding: 20px; border-top: 1px solid {self.color_borde}; border-bottom: 1px solid {self.color_borde};">
                            <p style="font-style: italic; text-align: center; color: {self.color_texto}; margin: 0;">
                                <strong>{self.nombre_empresa}</strong> agradece su confianza.<br>
                                Nuestra misión es ofrecerle los mejores productos y servicios con compromiso y calidad.
                            </p>
                        </div>
                        
                        <div style="padding: 20px 25px; background-color: #f9f9f9;">
                            <div>
                                <div style="font-size: 12px; color: #777;">
                                    <p style="margin-top: 0;">
                                        © {time.strftime('%Y')} {self.nombre_empresa}. Todos los derechos reservados.<br>
                                        Dirección: {self.direccion}<br>
                                        Teléfono: {self.telefono}
                                    </p>
                                </div>
                            </div>
                            <div style="font-size:10px; color:#999; text-align:center; margin-top:20px; border-top:1px solid #eee; padding-top:15px;">
                                Este mensaje se envía a su dirección de correo electrónico porque es cliente de {self.nombre_empresa}.
                                <br>Si no desea recibir más comunicaciones, por favor 
                                <a href="mailto:{unsubscribe_email}?subject=UNSUBSCRIBE-{codigo_archivo}" style="color:#999; text-decoration:underline;">haga clic aquí</a>.
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                """
                part_html = MIMEText(html_cuerpo, 'html', 'utf-8')
                
                # Añadir las partes en el orden correcto (primero texto, luego HTML)
                msg.attach(part_text)
                msg.attach(part_html)

                # Adjuntar el PDF con un nombre más específico y profesional
                nombre_pdf = f"Doc_Oficial_{codigo_archivo}.pdf"
                with open(pdf_path, 'rb') as pdf_file:
                    part = MIMEApplication(
                        pdf_file.read(),
                        Name=nombre_pdf,
                        _subtype="pdf"
                    )
                    part.add_header('Content-Disposition', 'attachment', filename=nombre_pdf)
                    part.add_header('Content-Type', 'application/pdf')
                    part.add_header('Content-Description', f'Documento oficial {self.nombre_empresa} para cliente {codigo_archivo}')
                    part.add_header('Content-Transfer-Encoding', 'base64')
                    part.add_header('X-Attachment-Id', f'doc_{time.strftime("%Y%m%d%H%M%S")}')
                    msg.attach(part)

                # Enviar el correo con mejor manejo de errores
                try:
                    with smtplib.SMTP(config_correo['server'], config_correo['port'], timeout=20) as server:
                        server.starttls()
                        server.login(config_correo['usuario'], config_correo['app_pw'])
                        server.send_message(msg)
                        logging.info(f"Correo enviado a {correo_destino} para código {codigo_archivo}")
                        return True, None
                except smtplib.SMTPSenderRefused as e:
                    detalles_error = f"Remitente rechazado: {e}"
                    logging.error(detalles_error)
                except smtplib.SMTPRecipientsRefused as e:
                    detalles_error = f"Destinatario rechazado: {e}"
                    logging.error(detalles_error)
                except smtplib.SMTPDataError as e:
                    detalles_error = f"Error de datos SMTP: {e}"
                    logging.error(detalles_error)
                except smtplib.SMTPConnectError as e:
                    detalles_error = f"Error de conexión con servidor SMTP: {e}"
                    logging.error(detalles_error)
                    # En caso de error de conexión con servidor, esperamos antes de reintentar
                    if not self.esperar_por_conexion(intento):
                        continue
                except smtplib.SMTPServerDisconnected as e:
                    detalles_error = f"Servidor SMTP desconectado: {e}"
                    logging.error(detalles_error)
                    # En caso de desconexión, esperamos antes de reintentar
                    if not self.esperar_por_conexion(intento):
                        continue
                except smtplib.SMTPResponseException as e:
                    detalles_error = f"Error de respuesta SMTP ({e.smtp_code}): {e.smtp_error}"
                    logging.error(detalles_error)
                except smtplib.SMTPAuthenticationError as e:
                    detalles_error = f"Error de autenticación SMTP: {e}"
                    logging.error(detalles_error)
                    # Error de autenticación no debería reintentar, probablemente credenciales incorrectas
                    return False, detalles_error
                except smtplib.SMTPException as e:
                    detalles_error = f"Error SMTP general: {e}"
                    logging.error(detalles_error)
                except socket.timeout as e:
                    detalles_error = f"Tiempo de espera agotado en la conexión: {e}"
                    logging.error(detalles_error)
                    # En caso de timeout, esperamos antes de reintentar
                    if not self.esperar_por_conexion(intento):
                        continue
                except socket.error as e:
                    detalles_error = f"Error de socket/conexión: {e}"
                    logging.error(detalles_error)
                    # En caso de error de socket, esperamos antes de reintentar
                    if not self.esperar_por_conexion(intento):
                        continue

            except Exception as e:
                detalles_error = f"Error inesperado enviando correo: {e}"
                logging.error(f"{detalles_error}. Posible error de conexión")
                
                # Comprobar si el error parece relacionado con problemas de conexión
                if any(texto in str(e).lower() for texto in ["timeout", "connection", "network", "socket", "unreachable", "route"]):
                    if not self.esperar_por_conexion(intento):
                        continue
            
            # Si llegamos aquí y no es el último intento, reintentamos
            if intento < self.max_intentos:
                logging.info(f"Reintentando envío para {codigo_archivo} (intento {intento+1}/{self.max_intentos})...")
            else:
                mensaje_final = f"Se agotaron los {self.max_intentos} intentos de envío para {codigo_archivo}. Último error: {detalles_error}"
                logging.error(mensaje_final)
                return False, detalles_error

        return False, detalles_error