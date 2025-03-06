import os
import sys
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Obtener la ruta absoluta del directorio actual
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)

# Obtener la ruta proporcionada como argumento
data_path = sys.argv[1] if len(sys.argv) > 1 else ""
if os.path.isabs(data_path):
    DATA_DIR = data_path
else:
    DATA_DIR = os.path.normpath(os.path.join(os.getcwd(), data_path))

# Directorios del proyecto
ENTRADA_DIR = os.path.join(DATA_DIR, 'entrada')
PDF_DIR = os.path.join(DATA_DIR, 'PDF')
ESTADO_DIR = os.path.join(DATA_DIR, 'estado')

# Configuraciones de correo
SMTP_CONFIG = {
    'server': 'smtp.gmail.com',
    'port': 587,
    'usuario': 'samueluwu88@gmail.com',
    'clave': 'GRISLYsan112006++'
}

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