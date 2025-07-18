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
        
        # Inicializar variables de correos
        self.correo_cliente = None
        self.correo_usuario = None
        
        self.config_empresa = self._obtener_config_empresa()
        self.color_encabezado = self.config_empresa['color_encabezado']
        self.nombre_empresa = self.config_empresa['nombre_empresa']
        self.color_banner = self.config_empresa['color_banner']
        self.color_borde = self.config_empresa['color_borde']
        self.color_texto = self.config_empresa['color_texto']
        self.direccion = self.info_empresa.get('pie_pagina1', 'Cl. 8 #20-15, El Cerrito, Valle del Cauca, Colombia')
        self.telefono = self.info_empresa.get('pie_pagina2', 'No es posible acceder al servicio de telefono en este instante.')
        self.correo = self.info_empresa.get('pie_pagina3', 'No es posible acceder al servicio de correo en este instante.')
        
        # Frases de cierre simplificadas
        self.frases_cierre = [
            "Gracias por su confianza.",
            "Estamos aquí para resolver cualquier consulta adicional.",
            "Valoramos su confianza.",
            "Nuestro objetivo es ofrecerle el mejor servicio.",
            "Trabajamos para mejorar constantemente.",
            "Gracias por confiar en nosotros.",
            "Estamos comprometidos con su satisfacción.",
            "Apreciamos su confianza.",
            "Siempre a su disposición."
        ]

    def _obtener_config_empresa(self):
        """Retorna el estilo de la empresa según el tipo"""
        configs = {
            'CUR': {
                'color_encabezado': '#4a2511',
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
        
        return configs.get(self.tipo_empresa, {
            'color_encabezado': "#5C9DF1",
            'nombre_empresa': 'Empresa',
            'color_banner': '#f5f5f5',
            'color_borde': '#e0e0e0',
            'color_texto': '#555555'
        })

    def comprobar_conexion(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
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
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    @staticmethod
    def obtener_correo_por_codigo(codigo_archivo):
        try:
            try:
                with open(ARCHIVO_DIRECCIONES, 'r', encoding='utf-8') as file:
                    lineas = file.readlines()
            except UnicodeDecodeError:
                with open(ARCHIVO_DIRECCIONES, 'r', encoding='iso-8859-1') as file:
                    lineas = file.readlines()
            
            for linea in lineas:
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
    
    @staticmethod
    def es_email_valido(email_a, email_b):
        # Patrón regex para validar email
        patron_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        # Verificar que ambos emails existan y sean strings
        if not email_a or not email_b or not isinstance(email_a, str) or not isinstance(email_b, str):
            return None, None
        
        # Limpiar espacios
        email_a = email_a.strip()
        email_b = email_b.strip()
        # Validar ambos emails con regex
        email_a_valido = re.match(patron_email, email_a) is not None
        email_b_valido = re.match(patron_email, email_b) is not None
        # Retornar emails válidos o None si no son válidos
        return (email_a if email_a_valido else None, 
                email_b if email_b_valido else None)
    
    def obtener_info_correo(self):
        try:
            try:
                with open(ARCHIVO_INFO_CORREOS, 'r', encoding='utf-8') as file:
                    lineas = file.readlines()
            except UnicodeDecodeError:
                with open(ARCHIVO_INFO_CORREOS, 'r', encoding='iso-8859-1') as file:
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
        tiempo_espera = min(self.tiempo_espera_base * (2 ** (intento - 1)), 300)  # Máximo 5 minutos
        
        logging.info(f"Esperando {tiempo_espera} segundos antes de reintentar (intento {intento}/{self.max_intentos})...")
        
        tiempo_inicio = time.time()
        while time.time() - tiempo_inicio < tiempo_espera:
            if self.comprobar_conexion():
                logging.info("¡Conexión a internet recuperada!")
                return True
            time.sleep(5)
        
        return self.comprobar_conexion()

    def enviar_correo_gmail(self, codigo_archivo, pdf_path, config_correo):
        detalles_error = None
        
        # Inicializar correos
        self.correo_cliente = self.obtener_correo_por_codigo(codigo_archivo)
        self.correo_usuario = config_correo['usuario']
        
        correo_destino, correo_usuario_valido = self.es_email_valido(self.correo_cliente, self.correo_usuario)
        
        if not correo_destino:
            detalles_error = f"Correo de cliente inválido o no encontrado para {codigo_archivo}. El correo no está en la libreta de direcciones generada por MAX. Consulte direcciones.txt en el directorio origen de su usuario."
            logging.error(detalles_error)
            return False, detalles_error
            
        if not correo_usuario_valido:
            detalles_error = f"Correo de usuario inválido en la configuración. Por favor, revise el archivo empresa.txt ubicado en la carpeta origen dentro de su directorio de usuario para verificar y corregir la dirección de correo electrónico."
            logging.error(detalles_error)
            return False, detalles_error
        
        intento = 0
        self.iniciar_monitor_conexion()
        
        while intento < self.max_intentos:
            intento += 1
            try:
                if not self.internet_disponible and not self.comprobar_conexion():
                    detalles_error = "Sin conexión a internet"
                    logging.warning(f"Sin conexión a internet. Reintentando... (intento {intento}/{self.max_intentos})")
                    if not self.esperar_por_conexion(intento):
                        continue
                
                info = self.obtener_info_correo()
                
                if not info:
                    detalles_error = "No se pudo obtener información del correo"
                    logging.error(detalles_error)
                    return False, detalles_error
                    
                asunto, cuerpo = info.asunto, info.cuerpo
                frase_aleatoria = self._obtener_frase_aleatoria()

                msg = MIMEMultipart('alternative')
                msg['From'] = formataddr((self.correo, correo_usuario_valido))
                msg['To'] = correo_destino
                msg['Subject'] = asunto
                
                domain = correo_usuario_valido.split('@')[1]
                msg['Message-ID'] = make_msgid(domain=domain)
                
                # Cabeceras Anti-Spam
                msg['X-Authentication-Warning'] = f"{domain} sender verified"
                msg['Precedence'] = 'list'
                msg['X-Mailer'] = f"{self.nombre_empresa} Sistema CorreosPDF"
                msg['X-Priority'] = '3'
                msg['X-MSMail-Priority'] = 'Normal'
                msg['X-Spam-Status'] = 'No'
                msg['X-Spam-Score'] = '0.0'
                msg['X-Spam-Level'] = ''
                msg['X-Spam-Flag'] = 'NO'
                msg['Date'] = formatdate(localtime=False)
                msg['Reply-To'] = correo_destino
                
                # Configuración de desuscripción
                unsubscribe_email = 'unsubscribe@' + domain
                msg['List-Unsubscribe'] = f"<mailto:{unsubscribe_email}?subject=unsubscribe-{codigo_archivo}>"
                msg['List-Unsubscribe-Post'] = "List-Unsubscribe=One-Click"
                empresa_codigo = self.tipo_empresa.lower()
                msg['Feedback-ID'] = f"{empresa_codigo}:{codigo_archivo}:{time.strftime('%Y%m')}"

                # Texto plano
                texto_plano = self._limpiar_texto_html(cuerpo)
                texto_plano += f"\n\n{frase_aleatoria}\n\n---\n{self.nombre_empresa}\nDirección: {self.direccion}\nTeléfono: {self.telefono}\n\nPara darse de baja, responda a este correo con el asunto 'unsubscribe'"
                part_text = MIMEText(texto_plano, 'plain', 'utf-8')
                
                # HTML
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

                # Adjunto PDF
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
                        
                except (smtplib.SMTPSenderRefused, smtplib.SMTPRecipientsRefused, 
                        smtplib.SMTPDataError) as e:
                    detalles_error = f"Error SMTP específico: {e}"
                    logging.error(detalles_error)
                    
                except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected,
                        socket.timeout, socket.error) as e:
                    detalles_error = f"Error de conexión: {e}"
                    logging.error(detalles_error)
                    if not self.esperar_por_conexion(intento):
                        continue
                        
                except smtplib.SMTPAuthenticationError as e:
                    detalles_error = f"Error de autenticación SMTP: {e}"
                    logging.error(detalles_error)
                    return False, detalles_error  # No reintentar errores de autenticación
                    
                except smtplib.SMTPException as e:
                    detalles_error = f"Error SMTP general: {e}"
                    logging.error(detalles_error)

            except Exception as e:
                detalles_error = f"Error inesperado enviando correo: {e}"
                logging.error(detalles_error)
                
                if any(texto in str(e).lower() for texto in ["timeout", "connection", "network", "socket"]):
                    if not self.esperar_por_conexion(intento):
                        continue
            
            if intento < self.max_intentos:
                logging.info(f"Reintentando envío para {codigo_archivo} (intento {intento+1}/{self.max_intentos})...")
            else:
                mensaje_final = f"Se agotaron los {self.max_intentos} intentos de envío para {codigo_archivo}. Último error: {detalles_error}"
                logging.error(mensaje_final)
                return False, detalles_error
        return False, detalles_error