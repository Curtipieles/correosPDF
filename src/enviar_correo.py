from collections import namedtuple
from email.utils import formatdate
import os
import random
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from src.config import LOGO_EMPRESA
import time

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
    def enviar_correo_gmail(nit, pdf_path, config_correo, archivo_direcciones, archivo_info_correos):
        try:
            correo = EnviadorCorreo.obtener_correo_por_nit(nit, archivo_direcciones)
            info = EnviadorCorreo.obtener_info_correo(archivo_info_correos)
            asunto, cuerpo = (info.asunto, info.cuerpo) if info else ("", "")
            if not correo:
                return False
            print(correo)
            msg = MIMEMultipart()
            msg['From'] = config_correo['usuario']
            msg['To'] = correo
            msg['Subject'] = asunto
            
            msg['Reply-To'] = config_correo['usuario']
            msg['Message-ID'] = f"<{time.time()}.{random.randint(1,99999)}@{config_correo['usuario'].split('@')[1]}>"
            msg['Date'] = formatdate(localtime=True)
            
            # Header List-Unsubscribe (esencial para pasar filtros)
            msg['List-Unsubscribe'] = f"<mailto:{config_correo['usuario']}?subject=unsubscribe>"
            msg['List-Unsubscribe-Post'] = "List-Unsubscribe=One-Click"
            
            # Versión texto plano con instrucciones de desuscripción
            texto_plano = cuerpo + "\n\n---\nPara darte de baja, responde a este correo con el asunto 'unsubscribe'"
            part_text = MIMEText(texto_plano, 'plain')
            
            # Versión HTML con mejor estructura y cumpliendo estándares
            html_cuerpo = f"""
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f9f9f9; margin: 0; padding: 0;">
                <div style="max-width: 650px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); overflow: hidden;">
                    <!-- Encabezado -->
                    <div style="background-color: #4a2511; padding: 20px; text-align: center;">
                        <img src="https://curtipieles.github.io/logoCurti/logoCur.jpg" alt="Logo Curtipieles" style="max-height: 60px;">
                    </div>
                    
                    <!-- Contenido principal -->
                    <div style="padding: 30px 25px;">
                        {cuerpo.replace('\n', '<br>')}
                    </div>
                    
                    <div style="background-color: #f5f0e8; padding: 20px; border-top: 1px solid #e0d5c5; border-bottom: 1px solid #e0d5c5;">
                        <p style="font-style: italic; text-align: center; color: #5d4b35; margin: 0;">
                            <strong>CURTIPIELES SAS</strong> agradece su confianza.<br>
                            Nuestra misión es ofrecerle los mejores productos en cuero con compromiso y calidad.
                        </p>
                    </div>
                    
                    <div style="padding: 20px 25px; background-color: #f9f9f9;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="font-size: 12px; color: #777;">
                                <p style="margin-top: 0;">
                                    © 2025 Curtipieles S.A.S. Todos los derechos reservados.<br>
                                    Para darte de baja, responde a este correo con asunto "unsubscribe".
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            part_html = MIMEText(html_cuerpo, 'html')
            
            # Añadir las partes en el orden correcto (primero texto, luego HTML)
            msg.attach(part_text)
            msg.attach(part_html)

            # Adjuntar el PDF
            with open(pdf_path, 'rb') as pdf_file:
                part = MIMEApplication(pdf_file.read(), Name=os.path.basename(pdf_path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(pdf_path)}"'
                msg.attach(part)

            # Enviar el correo
            with smtplib.SMTP(config_correo['server'], config_correo['port']) as server:
                server.starttls()
                server.login(config_correo['usuario'], config_correo['app_pw'])
                server.send_message(msg)
                logging.info(f"Correo enviado a {correo} para NIT {nit}")
                return True

        except smtplib.SMTPException as e:
            logging.error(f"Error SMTP enviando correo: {e}")
        except Exception as e:
            logging.error(f"Error inesperado enviando correo: {e}")
        return False
