import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

import requests

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
    def enviar_correo_gmail(nit, pdf_path, config_correo, archivo_direcciones):
        try:
            correo = EnviadorCorreo.obtener_correo_por_nit(nit, archivo_direcciones)
            print(correo)
            if not correo:
                return False

            msg = MIMEMultipart()
            msg['From'] = config_correo['usuario']
            msg['To'] = correo
            msg['Subject'] = 'Estado de Cuenta Curtipieles'

            body = 'Adjunto encontrará su estado de cuenta.'
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

    @staticmethod
    def enviar_correo_make(nit, pdf_path, correo_origen, archivo_direcciones):
        try:
            correo = EnviadorCorreo.obtener_correo_por_nit(nit, archivo_direcciones)
            if not correo:
                return False
            
            # Leer el PDF como base64
            import base64
            with open(pdf_path, 'rb') as pdf_file:
                pdf_base64 = base64.b64encode(pdf_file.read()).decode('utf-8')

            # Estructura que espera Make (Microsoft 365)
            make_config = {
                "toRecipients": [{"email": correo}],
                "from": {"email": correo_origen},
                "subject": "Estado de Cuenta Curtipíeles",
                "body": {
                    "content": "Adjunto encontrará su estado de cuenta.",
                    "contentType": "text"
                },
                "attachments": [
                    {
                        "contentBytes": pdf_base64,
                        "name": os.path.splitext(os.path.basename(pdf_path))[0]
                    }
                ]
            }

            webhook_url = "https://hook.us2.make.com/r42elu8lgoha8u2v596he5qkgsgk47kq"

            # Enviar la solicitud
            response = requests.post(
                webhook_url,
                headers={"Content-Type": "application/json"},
                json=make_config
            )
            import json
            print("Payload enviado a Make:")
            print(json.dumps(make_config, indent=2))
            print(f"Respuesta: {response.status_code} - {response.text}")

            if response.status_code == 200:
                logging.info(f"Datos enviados exitosamente a Make para NIT: {nit}")
                return True
            else:
                logging.error(f"Error al enviar datos a Make: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logging.error(f"Error preparando envío por Make: {e}")
            return False