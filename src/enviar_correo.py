from collections import namedtuple
from email.utils import formataddr, formatdate, make_msgid
import smtplib
import logging
from src.config import LOGO_EMPRESA
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
import time
import re

info_correo = namedtuple('info_correo', ['asunto', 'cuerpo'])

class EnviadorCorreo:
    @staticmethod
    def obtener_correo_por_nit(nit, archivo_direcciones):
        try:
            with open(archivo_direcciones, 'r') as file:
                for linea in file:
                    datos = linea.strip().split(',')
                    if datos[0] == nit:
                        return datos[1]
            logging.warning(f"NIT {nit} no encontrado")
            return None
        except FileNotFoundError:
            logging.error(f"Archivo de direcciones no encontrado: {archivo_direcciones}")
        except Exception as e:
            logging.error(f"Error buscando correo: {e}")
        return None
    
    @staticmethod
    def obtener_info_correo(archivo_info_correos):
        try:
            with open(archivo_info_correos, 'r', encoding='utf-8') as file:
                lineas = file.readlines()
                asunto = lineas[0].strip()
                cuerpo = ''.join(lineas[1:]).strip()
            if asunto and cuerpo:
                return info_correo(asunto, cuerpo)
            logging.warning(f"Asunto: {asunto} Cuerpo: {cuerpo}")
            return None
        except FileNotFoundError:
            logging.error(f"Archivo info_correo no encontrado: {archivo_info_correos}")
        except Exception as e:
            logging.error(f"Error buscando informacion del correo: {e}")
        return None

    @staticmethod
    def _limpiar_texto_html(texto):
        # Elimina etiquetas HTML para obtener el texto plano para conteo de palabras
        return re.sub(r'<[^>]*>', '', texto)
    
    @staticmethod
    def _asegurar_longitud_minima(cuerpo):
        """Asegura que el cuerpo del correo tenga suficiente texto (al menos 300 palabras)"""
        texto_plano = EnviadorCorreo._limpiar_texto_html(cuerpo)
        palabras = texto_plano.split()
        
        # Si el texto tiene menos de 300 palabras, añadir contenido adicional
        if len(palabras) < 300:
            contenido_adicional = """
            <div style="color: #333333; font-size: 14px; margin-top: 30px; padding: 15px; border-top: 1px solid #e0e0e0;">
                <h3>Información sobre nuestros productos</h3>
                <p>En Curtipieles S.A.S nos especializamos en la producción y distribución de cueros de alta calidad para diversas aplicaciones industriales y artesanales. Todos nuestros productos pasan por rigurosos controles de calidad que aseguran su durabilidad y resistencia.</p>
                
                <h4>Beneficios de trabajar con Curtipieles S.A.S:</h4>
                <ul>
                    <li>Atención personalizada y asesoría técnica</li>
                    <li>Entregas puntuales y garantía en todos nuestros productos</li>
                    <li>Variedad de acabados y texturas para diferentes necesidades</li>
                </ul>
                
                <p>Agradecemos su confianza en nuestros productos y servicios. Estamos comprometidos con la excelencia y la mejora continua para ofrecerle siempre la mejor calidad en cada pieza de cuero que producimos.</p> 
                <p>Si necesita más información sobre nuestros productos o servicios, no dude en contactar con nuestro equipo de atención al cliente, quienes estarán encantados de resolver cualquier duda que pueda tener.</p>
            </div>
            """
            return cuerpo + contenido_adicional
        return cuerpo

    @staticmethod
    def enviar_correo_gmail(nit, pdf_path, config_correo, archivo_direcciones, archivo_info_correos):
        try:
            correo = EnviadorCorreo.obtener_correo_por_nit(nit, archivo_direcciones)
            info = EnviadorCorreo.obtener_info_correo(archivo_info_correos)
            asunto, cuerpo_original = (info.asunto, info.cuerpo) if info else ("", "") 
            if not correo:
                return False
            # Asegurar que el correo tiene suficiente texto para mejorar ratio imagen/texto
            cuerpo = EnviadorCorreo._asegurar_longitud_minima(cuerpo_original)
            
            msg = MIMEMultipart('alternative')
            msg['From'] = formataddr(('Curtipieles', config_correo['usuario']))
            msg['To'] = correo
            msg['Subject'] = asunto
            
            # Usar un Message-ID conforme a RFC 5322 con el dominio real del remitente
            domain = config_correo['usuario'].split('@')[1]
            msg['Message-ID'] = make_msgid(domain=domain)
            msg['X-Authentication-Warning'] = f"{domain} sender verified"
            
            # Otros encabezados importantes
            msg['Date'] = formatdate(localtime=True)
            msg['Reply-To'] = 'no-reply+unsubscribe@' + config_correo['usuario'].split('@')[1]
            
            msg['Precedence'] = 'list'
            msg['X-Mailer'] = f"Curtipieles Sistema CorreosPDF."
            msg['X-Priority'] = '3'  # Prioridad (1=alta, 3=normal, 5=baja)
            msg['X-MSMail-Priority'] = 'Normal'

            # Configuración de desuscripción según RFC 8058
            unsubscribe_email = 'unsubscribe@' + config_correo['usuario'].split('@')[1]
            msg['List-Unsubscribe'] = f"<mailto:{unsubscribe_email}?subject=unsubscribe-{nit}>"
            msg['List-Unsubscribe-Post'] = "List-Unsubscribe=One-Click"
            msg['Feedback-ID'] = f"crtp:{nit}:{time.strftime('%Y%m')}"  # Para feedback loops

            msg['X-Spam-Status'] = 'No'
            msg['X-Spam-Score'] = '0.0'
            msg['X-Spam-Level'] = ''
            msg['X-Spam-Flag'] = 'NO'
            
            # Cargar la imagen desde un archivo local
            logo_cid = "cid:logo"
            try:
                with open(LOGO_EMPRESA, 'rb') as img_file:
                    img_data = img_file.read()
                    image = MIMEImage(img_data)
                    image.add_header('Content-ID', '<logo>')
                    image.add_header('Content-Disposition', 'inline')
                    msg.attach(image)
            except Exception as e:
                logging.error(f"No se pudo cargar la imagen del logo: {e}")
                logo_cid = ""
            
            # Convertir HTML a texto plano de manera más sofisticada
            texto_plano = EnviadorCorreo._limpiar_texto_html(cuerpo)
            texto_plano += "\n\n---\nCURTIPIELES S.A.S agradece su confianza.\nPara darte de baja, responde a este correo con el asunto 'unsubscribe'"
            part_text = MIMEText(texto_plano, 'plain', 'utf-8')
            
            # Preparar la sección del encabezado dependiendo de si tenemos logo o no
            encabezado_html = ""
            if logo_cid:
                encabezado_html = f"""
                <div style="background-color: #4a2511; padding: 20px; text-align: center;">
                    <img src="{logo_cid}" alt="Logo Curtipieles" style="max-height: 60px;">
                    <h1 style="color: #ffffff; margin: 10px 0 0 0; font-size: 22px;">Curtipieles S.A.S</h1>
                </div>
                """
            else:
                encabezado_html = f"""
                <div style="background-color: #4a2511; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 24px;">Curtipieles S.A.S</h1>
                </div>
                """
            
            # Versión HTML con mejor estructura y cumpliendo estándares
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
                    
                    <div style="background-color: #f5f0e8; padding: 20px; border-top: 1px solid #e0d5c5; border-bottom: 1px solid #e0d5c5;">
                        <p style="font-style: italic; text-align: center; color: #5d4b35; margin: 0;">
                            <strong>Curtipieles S.A.S</strong> agradece su confianza.<br>
                            Nuestra misión es ofrecerle los mejores productos en cuero con compromiso y calidad.
                        </p>
                    </div>
                    
                    <div style="padding: 20px 25px; background-color: #f9f9f9;">
                        <div>
                            <div style="font-size: 12px; color: #777;">
                                <p style="margin-top: 0;">
                                    © 2025 Curtipieles S.A.S. Todos los derechos reservados.<br>
                                    Dirección: Cl. 8 #20-15, El Cerrito, Valle del Cauca, Colombia<br>
                                    Teléfono: +57 3173711707
                                </p>
                            </div>
                        </div>
                        <div style="font-size:10px; color:#999; text-align:center; margin-top:20px; border-top:1px solid #eee; padding-top:15px;">
                            Este mensaje se envía a su dirección de correo electrónico porque es cliente de Curtipieles S.A.S.
                            <br>Si no desea recibir más comunicaciones, por favor 
                            <a href="mailto:{unsubscribe_email}?subject=UNSUBSCRIBE-{nit}" style="color:#999; text-decoration:underline;">haga clic aquí</a>.
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
            nombre_pdf = f"Doc_Oficial_{nit}.pdf"
            with open(pdf_path, 'rb') as pdf_file:
                part = MIMEApplication(
                    pdf_file.read(),
                    Name=nombre_pdf,
                    _subtype="pdf"
                )
                part.add_header('Content-Disposition', 'attachment', filename=nombre_pdf)
                part.add_header('Content-Type', 'application/pdf')
                part.add_header('Content-Description', f'Documento oficial Curtipieles para cliente {nit}')
                part.add_header('Content-Transfer-Encoding', 'base64')
                part.add_header('X-Attachment-Id', f'doc_{time.strftime("%Y%m%d%H%M%S")}')
                msg.attach(part)

            # Enviar el correo con más tiempo de espera y mejor manejo de errores
            try:
                with smtplib.SMTP(config_correo['server'], config_correo['port'], timeout=20) as server:
                    server.starttls()
                    server.login(config_correo['usuario'], config_correo['app_pw'])
                    server.send_message(msg)
                    logging.info(f"Correo enviado a {correo} para NIT {nit}")
                    return True
            except smtplib.SMTPSenderRefused as e:
                logging.error(f"Remitente rechazado: {e}")
            except smtplib.SMTPRecipientsRefused as e:
                logging.error(f"Destinatario rechazado: {e}")
            except smtplib.SMTPDataError as e:
                logging.error(f"Error de datos SMTP: {e}")
            except smtplib.SMTPConnectError as e:
                logging.error(f"Error de conexión SMTP: {e}")
            except smtplib.SMTPServerDisconnected as e:
                logging.error(f"Servidor SMTP desconectado: {e}")
            except smtplib.SMTPResponseException as e:
                logging.error(f"Error de respuesta SMTP ({e.smtp_code}): {e.smtp_error}")
            except smtplib.SMTPAuthenticationError as e:
                logging.error(f"Error de autenticación SMTP: {e}")
            except smtplib.SMTPException as e:
                logging.error(f"Error SMTP general: {e}")

        except Exception as e:
            logging.error(f"Error inesperado enviando correo: {e}")
        return False