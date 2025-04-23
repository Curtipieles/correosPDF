import os
import sys
import logging
import smtplib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def validar_servidor_smtp(servidor, puerto, timeout=5):
    try:
        with smtplib.SMTP(servidor, puerto, timeout=timeout) as smtp:
            smtp.ehlo()
            return True
    except Exception as e:
        logging.warning(f"Servidor {servidor} no responde: {str(e)}")
        return False

def determinar_servidor_smtp(correo):
    try:
        dominio = correo.split('@')[1].lower()
    except (IndexError, AttributeError):
        return {'server': 'smtp.gmail.com', 'port': 587}
    
    if dominio == 'gmail.com':
        servidores_posibles = [
            {'server': 'smtp.gmail.com', 'port': 587},
            {'server': 'smtp-relay.gmail.com', 'port': 587},
            {'server': 'smtp-mail.gmail.com', 'port': 587},
            {'server': 'aspmx.l.google.com', 'port': 587},
        ]        
        for config in servidores_posibles:
            if validar_servidor_smtp(config['server'], config['port']):
                logging.info(f"Servidor válido encontrado: {config['server']}")
                return config
    return {'server': 'smtp.gmail.com', 'port': 587}

def obtener_config_smtp(correo_usuario, app_pw):
    servidor_default = {'server': 'smtp.gmail.com', 'port': 587}    
    if validar_servidor_smtp(servidor_default['server'], servidor_default['port']):
        return {
            'server': servidor_default['server'],
            'port': servidor_default['port'],
            'usuario': correo_usuario,
            'app_pw': app_pw
        }
    logging.warning(f"Servidor predeterminado no responde. Buscando alternativas...")
    config_servidor = determinar_servidor_smtp(correo_usuario)
    return {
        'server': config_servidor['server'],
        'port': config_servidor['port'],
        'usuario': correo_usuario,
        'app_pw': app_pw
    }

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)

# Normalizacion de la ruta para ser utilizada
data_path = sys.argv[1] if len(sys.argv) > 1 else ""
if os.path.isabs(data_path):
    DATA_DIR = data_path
else:
    DATA_DIR = os.path.normpath(os.path.join(os.getcwd(), data_path))

ENTRADA_DIR = os.path.join(DATA_DIR, 'entrada')
PDF_DIR = os.path.join(DATA_DIR, 'pdf')
ESTADO_DIR = os.path.join(DATA_DIR, 'estado')
ORIGEN_DIR = os.path.join(DATA_DIR, 'origen')

FONTS_DIR = os.path.join(BASE_DIR, 'fonts')
DEFAULT_FONT = {
    'family': 'JetBrainsMono',
    'style': '',
    'file': 'JetBrainsMono-SemiBoldItalic.ttf'
}
FONT_FILE_PATH = os.path.join(FONTS_DIR, DEFAULT_FONT['file'])

# Rutas de archivos importantes
ARCHIVO_CORREO_ORIGEN = os.path.join(ORIGEN_DIR, 'correo_origen.txt')
ARCHIVO_DIRECCIONES = os.path.join(ORIGEN_DIR, 'direcciones.txt')
ARCHIVO_INFO_CORREOS = os.path.join(ORIGEN_DIR, 'info_correo.txt')
LOGO_EMPRESA = os.path.join(BASE_DIR, 'logo_curti.JPG')