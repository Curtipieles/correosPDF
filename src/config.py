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

# Mostrar información de rutas para depuración
logging.info(f"CURRENT_DIR: {CURRENT_DIR}")
logging.info(f"BASE_DIR: {BASE_DIR}")

# Obtener la ruta proporcionada como argumento
# Si sys.argv[1] es una ruta absoluta, se usará tal cual
# Si es una ruta relativa, se resolverá relativa al directorio actual
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

# Asegurarse de que la ruta de las fuentes sea absoluta
FONTS_DIR = os.path.abspath(os.path.join(BASE_DIR, 'fonts'))
logging.info(f"FONTS_DIR: {FONTS_DIR}")

# Crear directorio de fuentes si no existe
try:
    os.makedirs(FONTS_DIR, exist_ok=True)
    logging.info(f"Directorio de fuentes asegurado: {FONTS_DIR}")
except Exception as e:
    logging.error(f"Error al crear directorio de fuentes: {e}")

# directorio específico que aparece en el error
error_fonts_dir = r'{sys.argv[1]}\fonts'
try:
    os.makedirs(error_fonts_dir, exist_ok=True)
    logging.info(f"Directorio de fuentes del error creado: {error_fonts_dir}")
except Exception as e:
    logging.warning(f"No se pudo crear el directorio de fuentes del error: {e}")

# También crear directorio relativo que aparece en el error
rel_fonts_dir = os.path.join(CURRENT_DIR, '..', 'fonts')
try:
    os.makedirs(rel_fonts_dir, exist_ok=True)
    logging.info(f"Directorio de fuentes relativo creado: {rel_fonts_dir}")
except Exception as e:
    logging.warning(f"No se pudo crear el directorio de fuentes relativo: {e}")

DEFAULT_FONT = {
    'family': 'Tipografia',
    'style': '',
    'file': 'JetBrainsMono-SemiBoldItalic.ttf'
}

FONT_FILE_PATH = os.path.join(FONTS_DIR, DEFAULT_FONT['file'])
logging.info(f"FONT_FILE_PATH: {FONT_FILE_PATH}")

if not os.path.exists(FONT_FILE_PATH):
    logging.warning(f"Archivo de fuente no encontrado en: {FONT_FILE_PATH}")
    
    alt_locations = [
        os.path.join(os.getcwd(), 'fonts', DEFAULT_FONT['file']),
        os.path.join(BASE_DIR, 'src', 'fonts', DEFAULT_FONT['file']),
        os.path.join(CURRENT_DIR, 'fonts', DEFAULT_FONT['file']),
    ]
    
    for loc in alt_locations:
        if os.path.exists(loc):
            try:
                import shutil
                shutil.copy2(loc, FONT_FILE_PATH)
                logging.info(f"Fuente copiada desde {loc} a {FONT_FILE_PATH}")
                break
            except Exception as e:
                logging.warning(f"Error al copiar fuente: {e}")

ARCHIVO_DIRECCIONES = os.path.join(ENTRADA_DIR, 'direcciones.txt')
LOGO_EMPRESA = os.path.join(BASE_DIR, 'logo_curti.JPG')