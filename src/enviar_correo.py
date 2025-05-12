from collections import namedtuple
from email.utils import formataddr, formatdate, make_msgid
import smtplib
import logging
import time
import re
import socket
import requests
import threading
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from src.config import ARCHIVO_DIRECCIONES, ARCHIVO_INFO_CORREOS, obtener_info_empresa

info_correo = namedtuple('info_correo', ['asunto', 'cuerpo'])

class EnviadorCorreo:
    def __init__(self):
        self.max_intentos = 5
        self.tiempo_espera_base = 30  # segundos
        self.internet_disponible = True
        self.info_empresa = obtener_info_empresa()
        self.tipo_empresa = self.info_empresa['tipo_empresa']
        self.config_empresa = {
            'CUR': {
                'color_encabezado': '#4a2511',  # Marrón para Curtipieles
                'nombre_empresa': 'Curtipieles S.A.S',
                'color_banner': '#f5f0e8',
                'color_borde': '#e0d5c5',
                'color_texto': '#5d4b35'
            },
            'COM': {
                'color_encabezado': '#083D77',
                'nombre_empresa': 'Comercializadora Calle & CÍA. S. En C.S.',
                'color_banner': '#639DAE',
                'color_borde': '#E8E2D6',
                'color_texto': '#355d7d'
            },
            'LBC': {
                'color_encabezado': '#1E5631',
                'nombre_empresa': 'Luis Bernardo Calle Pareja',
                'color_banner': '#537D5D',
                'color_borde': '#D2D0A0',
                'color_texto': '#355d42'
            }
        }
        config_default = {
            'color_encabezado': '#333333',
            'nombre_empresa': 'Empresa S.A.S',
            'descripcion': 'Productos y servicios de calidad',
            'color_banner': '#f5f5f5',
            'color_borde': '#e0e0e0',
            'color_texto': '#555555'
        }
        self.config_actual = self.config_empresa.get(self.tipo_empresa, config_default)
        self.color_encabezado = self.config_actual['color_encabezado']
        self.nombre_empresa = self.config_actual['nombre_empresa']
        self.color_banner = self.config_actual['color_banner']
        self.color_borde = self.config_actual['color_borde']
        self.color_texto = self.config_actual['color_texto']
        self.direccion = self.info_empresa.get('pie_pagina1', 'Cl. 8 #20-15, El Cerrito, Valle del Cauca, Colombia')
        self.telefono = self.info_empresa.get('pie_pagina2', '+57 3173711707')
        self.correo = self.info_empresa.get('pie_pagina3', 'No es posible acceder al servicio de correo en este instante. ' \
        'Le invitamos a intentarlo más tarde o utilizar canales alternativos de contacto.')
        self.frases_cierre = [
            "Gracias por su confianza.",
            "Estamos aquí para resolver cualquier consulta adicional.",
            "Valoramos su confianza.",
            "Estamos encantados de poder ayudarle.",
            "Nuestro objetivo es ofrecerle el mejor servicio.",
            "Trabajamos para mejorar constantemente.",
            "Su satisfacción es importante para nosotros.",
            "Gracias por confiar en nosotros.",
            "Todo nuestro equipo agradece su preferencia.",
            "Continuamos a su disposición para cualquier consulta.",
            "Gracias por la oportunidad de servirle.",
            "Estamos comprometidos con su satisfacción.",
            "La calidad es nuestra prioridad diaria.",
            "Apreciamos su confianza.",
            "Gracias por ser parte de nuestra clientela.",
            "Estamos a su servicio.",
            "Cada cliente es importante para nosotros.",
            "Su confianza nos motiva a mejorar.",
            "Gracias por su tiempo.",
            "Agradecemos su preferencia.",
            "Gracias por elegirnos.",
            "Siempre a su disposición."
        ]

    def comprobar_conexion(self):
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
        def monitor():
            while True:
                self.comprobar_conexion()
                time.sleep(60)  # Comprobar cada minuto
        
        # Iniciar hilo en modo daemon para que termine cuando termine el programa principal
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    @staticmethod
    def obtener_correo_por_codigo(codigo_archivo):
        try:
            with open(ARCHIVO_DIRECCIONES, 'r') as file:
                for linea in file:
                    datos = linea.strip().split(',')
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
    
    def _obtener_frase_aleatoria(self):
        return random.choice(self.frases_cierre)

    def esperar_por_conexion(self, intento):
        tiempo_espera = self.tiempo_espera_base * (2 ** (intento - 1))  # Backoff exponencial
        tiempo_espera = min(tiempo_espera, 300)  # Máximo 5 minutos
        
        logging.info(f"Esperando {tiempo_espera} segundos antes de reintentar (intento {intento}/{self.max_intentos})...")
        
        tiempo_inicio = time.time()
        while time.time() - tiempo_inicio < tiempo_espera:
            if self.comprobar_conexion():
                logging.info("¡Conexión a internet recuperada!")
                return True
            time.sleep(5)  # Comprobar cada 5 segundos
        
        return self.comprobar_conexion()  # Comprobar una vez más antes de continuar

    def enviar_correo_gmail(self, codigo_archivo, pdf_path, config_correo):
        detalles_error = None
        intento = 0
        
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
                    
                asunto, cuerpo = info.asunto, info.cuerpo
                frase_aleatoria = self._obtener_frase_aleatoria()
                
                msg = MIMEMultipart('alternative')
                msg['From'] = formataddr((self.nombre_empresa, config_correo['usuario']))
                msg['To'] = correo_destino
                msg['Subject'] = asunto
                
                # Usar un Message-ID conforme a RFC 5322 con el dominio real del remitente
                domain = config_correo['usuario'].split('@')[1]
                msg['Message-ID'] = make_msgid(domain=domain)
                
                # Cabeceras Anti-Spam añadidas del segundo código
                msg['X-Authentication-Warning'] = f"{domain} sender verified"
                msg['Precedence'] = 'list'
                msg['X-Mailer'] = f"{self.nombre_empresa} Sistema CorreosPDF"
                msg['X-Priority'] = '3'  # Prioridad normal
                msg['X-MSMail-Priority'] = 'Normal'
                msg['X-Spam-Status'] = 'No'
                msg['X-Spam-Score'] = '0.0'
                msg['X-Spam-Level'] = ''
                msg['X-Spam-Flag'] = 'NO'
                
                msg['Date'] = formatdate(localtime=False)
                
                msg['Reply-To'] = correo_destino
                
                # Configuración de desuscripción según RFC 8058
                unsubscribe_email = 'unsubscribe@' + domain
                msg['List-Unsubscribe'] = f"<mailto:{unsubscribe_email}?subject=unsubscribe-{codigo_archivo}>"
                msg['List-Unsubscribe-Post'] = "List-Unsubscribe=One-Click"
                
                # Generar Feedback-ID basado en el tipo de empresa
                empresa_codigo = self.tipo_empresa.lower()
                msg['Feedback-ID'] = f"{empresa_codigo}:{codigo_archivo}:{time.strftime('%Y%m')}"
                
                # Preparar la sección del encabezado sin logo
                encabezado_html = f"""
                <div style="background-color: {self.color_encabezado}; padding: 15px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 22px;">{self.nombre_empresa}</h1>
                </div>
                """
                
                # Convertir HTML a texto plano con la frase aleatoria
                texto_plano = self._limpiar_texto_html(cuerpo)
                texto_plano += f"\n\n{frase_aleatoria}\n\n---\n{self.nombre_empresa}\nDirección: {self.direccion}\nTeléfono: {self.telefono}\n\nPara darse de baja, responda a este correo con el asunto 'unsubscribe'"
                part_text = MIMEText(texto_plano, 'plain', 'utf-8')
                
                # Versión HTML simplificada pero manteniendo el estilo consistente
                html_cuerpo = f"""
                <!DOCTYPE html>
                <html lang="es">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>{asunto}</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333333; margin: 0; padding: 0; }}
                        .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; }}
                        .header {{ background-color: {self.color_encabezado}; padding: 15px; text-align: center; }}
                        .content {{ padding: 20px 15px; }}
                        .signature {{ font-style: italic; margin-top: 15px; color: #666666; }}
                        .footer {{ padding: 15px; background-color: {self.color_banner}; border-top: 1px solid {self.color_borde}; }}
                        .contact {{ font-size: 13px; color: {self.color_texto}; margin-top: 10px; }}
                        .unsubscribe {{ font-size: 11px; color: #777777; margin-top: 10px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1 style="color: #ffffff; margin: 0; font-size: 22px;">{self.nombre_empresa}</h1>
                        </div>
                        
                        <div class="content">
                            {cuerpo.replace('\n', '<br>')}
                            <p class="signature">{frase_aleatoria}</p>
                        </div>
                        
                        <div class="footer">
                            <p style="margin: 0; color: {self.color_texto};">
                                <strong>{self.nombre_empresa}</strong>
                            </p>
                            <div class="contact">
                                <p style="margin: 5px 0;">
                                    Dirección: {self.direccion}<br>
                                    Teléfono: {self.telefono}
                                </p>
                            </div>
                            <div class="unsubscribe" style="font-size: 11px; color: #777777; margin-top: 10px;">
                                <p>Si no desea recibir más comunicaciones, puede 
                                <a href="mailto:{unsubscribe_email}?subject=unsubscribe-{codigo_archivo}" style="color:#555555;">
                                darse de baja aquí</a>.</p>
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                """
                part_html = MIMEText(html_cuerpo, 'html', 'utf-8')
                
                msg.attach(part_text)
                msg.attach(part_html)

                nombre_pdf = f"Doc_{codigo_archivo}.pdf"
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
            
            if intento < self.max_intentos:
                logging.info(f"Reintentando envío para {codigo_archivo} (intento {intento+1}/{self.max_intentos})...")
            else:
                mensaje_final = f"Se agotaron los {self.max_intentos} intentos de envío para {codigo_archivo}. Último error: {detalles_error}"
                logging.error(mensaje_final)
                return False, detalles_error

        return False, detalles_error