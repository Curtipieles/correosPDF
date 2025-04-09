import sys
import os
import logging
import src.config as cfg
from src.conversor import ConversorPDF
from src.enviar_correo import EnviadorCorreo

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

def procesamiento_gmail(path, nit, tamano_letra, correo_origen, app_pw):
    try:
        logging.info(f"Iniciando procesamiento para NIT: {nit}")
        logging.info(f"Usando ruta: {path}")

        os.makedirs(cfg.PDF_DIR, exist_ok=True)
        os.makedirs(cfg.ESTADO_DIR, exist_ok=True)

        pdf_path = ConversorPDF.convertir_a_pdf(path, nit, tamano_letra, cfg.PDF_DIR)
        
        if not pdf_path:
            logging.error(f"No se pudo generar el PDF para NIT: {nit}")
            return False

        logging.info(f"PDF generado exitosamente: {pdf_path}")

        if not os.path.exists(cfg.ARCHIVO_DIRECCIONES) and os.path.exists(cfg.ARCHIVO_INFO_CORREOS):
            logging.error(f"Archivo direcciones.txt o info_correo.txt no fue encontrado")
            return False

        smtp_config = cfg.obtener_config_smtp(correo_origen, app_pw)
        enviado = EnviadorCorreo.enviar_correo_gmail(nit, 
                                                     pdf_path, 
                                                     smtp_config, 
                                                     cfg.ARCHIVO_DIRECCIONES, 
                                                     cfg.ARCHIVO_INFO_CORREOS)
        
        estado = 'ENVIADO' if enviado else 'ERROR'
        estado_path = os.path.join(cfg.ESTADO_DIR, f'{nit}_estado.txt')
        with open(estado_path, 'w') as f:
            f.write(estado)
        
        logging.info(f"Estado de envío: {estado}")
        return enviado

    except Exception as e:
        logging.error(f"Error procesando archivo: {e}")
        return False
    
def main():
    try:
        if len(sys.argv) < 5:
            logging.error("Argumentos insuficientes.")
            sys.exit(1)
        if not os.path.exists(sys.argv[1]):
            logging.error(f"La ruta '{sys.argv[1]}' no existe.")
            sys.exit(1)
        if not sys.argv[2].isdigit():
            logging.error(f"NIT inválido: '{sys.argv[2]}'. Debe ser un valor numérico.")
            sys.exit(1)
        if not sys.argv[3].isinstance() or not sys.argv[3] == 'P' or not sys.argv[3] == 'N':
            logging.error(f'Tamaño de letra inválido: "{sys.argv[3]}". Debe ser una letra "P" o "N"')
            sys.exit(1)
        if not '@' in sys.argv[4] or not '.' in sys.argv[4]:
            logging.error(f"Correo origen inválido: '{sys.argv[4]}'")
            sys.exit(1)
        path = sys.argv[1]
        nit = sys.argv[2]
        tamano_letra = sys.argv[3]
        correo_origen = sys.argv[4]        
        app_pw = None
        if len(sys.argv) > 5 and sys.argv[5] and sys.argv[5] != "":
            app_pw = sys.argv[5]
            resultado = procesamiento_gmail(path, nit, tamano_letra, correo_origen, app_pw)
        else:
            logging.warning("No se proporcionó contraseña de aplicación. Algunas funciones pueden no estar disponibles.")
            resultado = None

        sys.exit(0 if resultado else 1)

    except Exception as e:
        logging.error(f"Error en ejecución principal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()