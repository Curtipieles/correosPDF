import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def determinar_servidor_smtp(correo):
    try:
        dominio = correo.split('@')[1].lower()
    except (IndexError, AttributeError):
        return {'server': 'smtp.gmail.com', 'port': 587}
    
    # Mapeo de dominios a servidores SMTP
    servidores = {
        # Gmail
        'gmail.com': {'server': 'smtp.gmail.com', 'port': 587},
        # Microsoft (Hotmail, Outlook, Live)
        'hotmail.com': {'server': 'smtp-mail.outlook.com', 'port': 587},
        'outlook.com': {'server': 'smtp-mail.outlook.com', 'port': 587},
        'live.com': {'server': 'smtp-mail.outlook.com', 'port': 587},
        'msn.com': {'server': 'smtp-mail.outlook.com', 'port': 587},
        # Yahoo
        'yahoo.com': {'server': 'smtp.mail.yahoo.com', 'port': 587},
        'yahoo.es': {'server': 'smtp.mail.yahoo.com', 'port': 587},
        # iCloud
        'icloud.com': {'server': 'smtp.mail.me.com', 'port': 587},
        'me.com': {'server': 'smtp.mail.me.com', 'port': 587},
        # AOL
        'aol.com': {'server': 'smtp.aol.com', 'port': 587},
        # Zoho
        'zoho.com': {'server': 'smtp.zoho.com', 'port': 587},
        # GMX
        'gmx.com': {'server': 'mail.gmx.com', 'port': 587},
        'gmx.net': {'server': 'mail.gmx.com', 'port': 587},

        # Servicios de correo empresarial
        'office365.com': {'server': 'smtp.office365.com', 'port': 587},
        'outlook.office365.com': {'server': 'smtp.office365.com', 'port': 587},
        'exchange.com': {'server': 'smtp.exchange.com', 'port': 587},
        'google-mail.com': {'server': 'smtp.gmail.com', 'port': 587},
        'googlemail.com': {'server': 'smtp.gmail.com', 'port': 587},
        'workmail.com': {'server': 'smtp.mail.us-west-2.awsapps.com', 'port': 587}, # AWS WorkMail
        
        # Agregar aquí dominios específicos de tus clientes corporativos conocidos en caso de necesitarse
        # 'empresa1.com': {'server': 'smtp.empresa1.com', 'port': 587},
    }
    
    # Comprobar si el dominio está en nuestra lista
    if dominio in servidores:
        return servidores[dominio]
    
    logging.warning(f"Dominio de correo no reconocido: {dominio}. Usando configuración predeterminada.")
    return {'server': 'smtp.gmail.com', 'port': 587}

def obtener_config_smtp(correo_usuario, app_pw):
    config_servidor = determinar_servidor_smtp(correo_usuario)
    return {
        'server': config_servidor['server'],
        'port': config_servidor['port'],
        'usuario': correo_usuario,
        'app_pw': app_pw
    }

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)

data_path = sys.argv[1] if len(sys.argv) > 1 else ""
if os.path.isabs(data_path):
    DATA_DIR = data_path
else:
    DATA_DIR = os.path.normpath(os.path.join(os.getcwd(), data_path))

# Directorios del proyecto
ENTRADA_DIR = os.path.join(DATA_DIR, 'entrada')
PDF_DIR = os.path.join(DATA_DIR, 'PDF')
ESTADO_DIR = os.path.join(DATA_DIR, 'estado')

FONTS_DIR = os.path.join(BASE_DIR, 'fonts')

DEFAULT_FONT = {
    'family': 'JetBrainsMono',
    'style': '',
    'file': 'JetBrainsMono-SemiBoldItalic.ttf'
}

FONT_FILE_PATH = os.path.join(FONTS_DIR, DEFAULT_FONT['file'])

# Rutas de archivos importantes
ARCHIVO_DIRECCIONES = os.path.join(ENTRADA_DIR, 'direcciones.txt')
LOGO_EMPRESA = os.path.join(BASE_DIR, 'logo_curti.JPG')