import os
import sys
import logging
import smtplib

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
IMAGENES = os.path.join(DATA_DIR, 'img')

# Rutas de archivos importantes
ARCHIVO_EMPRESA = os.path.join(ORIGEN_DIR, 'empresa.txt') # Nuevo archivo de configuración
ARCHIVO_DIRECCIONES = os.path.join(ORIGEN_DIR, 'direcciones.txt')
ARCHIVO_INFO_CORREOS = os.path.join(ORIGEN_DIR, 'info_correo.txt')
ARCHIVO_ESTADO = os.path.join(ESTADO_DIR, 'estado_correos.txt') # Para verificar los correos ya enviados

# Logos de empresas
LOGO_EMPRESA_CURTI = os.path.join(BASE_DIR, 'img', 'logo_curti.JPG')
LOGO_EMPRESA_LBC = os.path.join(BASE_DIR, 'img', 'logo_lbc.JPG')
LOGO_EMPRESA_COMER = os.path.join(BASE_DIR, 'img', 'logo_comer.JPG')

def obtener_info_empresa():
    try:
        with open(ARCHIVO_EMPRESA, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
            
        if len(lineas) < 7:
            logging.error("El archivo empresa.txt no tiene suficientes líneas de configuración")
            return None
            
        return {
            'correo_origen': lineas[0].strip(),
            'app_pw': lineas[1].strip(),
            'tipo_empresa': lineas[2].strip().upper(),
            'pie_pagina1': lineas[3].strip(), # Direccion
            'pie_pagina2': lineas[4].strip(), # Telefono
            'pie_pagina3': lineas[5].strip(), # Email
            'estado_proceso': lineas[6].strip()
        }
    except Exception as e:
        logging.error(f"Error al leer archivo empresa.txt: {e}")
        return None

def actualizar_estado_proceso(nuevo_estado='0'):
    try:
        info_empresa = obtener_info_empresa()
        if not info_empresa:
            return False
            
        with open(ARCHIVO_EMPRESA, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
            
        # Actualizar la línea 7 (índice 6)
        if len(lineas) >= 7:
            lineas[6] = f"{nuevo_estado}\n"
        else:
            # Si no hay suficientes líneas, agregar la que falta
            while len(lineas) < 6:
                lineas.append("\n")
            lineas.append(f"{nuevo_estado}\n")
            
        # Escribir todas las líneas de vuelta al archivo
        with open(ARCHIVO_EMPRESA, 'w', encoding='utf-8') as f:
            f.writelines(lineas)
            
        return True
    except Exception as e:
        logging.error(f"Error al actualizar estado en empresa.txt: {e}")
        return False

def obtener_logo_por_empresa(tipo_empresa):
    if tipo_empresa == 'CUR':
        return LOGO_EMPRESA_CURTI
    elif tipo_empresa == 'LBC':
        return LOGO_EMPRESA_LBC
    elif tipo_empresa == 'COM':
        return LOGO_EMPRESA_COMER
    else:
        logging.warning(f"Tipo de empresa desconocido: {tipo_empresa}, usando logo CURTI por defecto")
        return LOGO_EMPRESA_CURTI