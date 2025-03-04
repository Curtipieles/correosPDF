import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, 'data')
ENTRADA_DIR = os.path.join(DATA_DIR, 'entrada')
PDF_DIR = os.path.join(DATA_DIR, 'PDF')
ESTADO_DIR = os.path.join(DATA_DIR, 'estado')

SMTP_CONFIG = {
    'server': 'smtp.gmail.com',
    'port': 587,
    'usuario': 'samueluwu88@gmail.com',
    'clave': 'GRISLYsan112006++'
}

FONTS_DIR = os.path.join(BASE_DIR, 'fonts')
DEFAULT_FONT = {
    'family': 'Tipografia',
    'style': '',
    'file': 'JetBrainsMono-SemiBoldItalic.ttf'
}

ARCHIVO_DIRECCIONES = os.path.join(ENTRADA_DIR, 'direcciones.txt')
LOGO_EMPRESA = os.path.join(BASE_DIR, 'logo_curti.JPG')