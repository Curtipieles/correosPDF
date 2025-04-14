from collections import namedtuple
import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

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
            body = cuerpo
            msg.attach(MIMEText(body, 'plain'))

            with open(pdf_path, 'rb') as pdf_file:
                part = MIMEApplication(pdf_file.read(), Name=os.path.basename(pdf_path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(pdf_path)}"'
                msg.attach(part)

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