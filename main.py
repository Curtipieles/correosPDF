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

        # Usar la ruta tal como está (ya está normalizada en config.py)
        logging.info(f"Usando ruta: {path}")

        # Crear carpetas si no existen
        os.makedirs(cfg.PDF_DIR, exist_ok=True)
        os.makedirs(cfg.ESTADO_DIR, exist_ok=True)

        # Convertir a PDF
        pdf_path = ConversorPDF.convertir_a_pdf(path, nit, tamano_letra, cfg.PDF_DIR)
        
        if not pdf_path:
            logging.error(f"No se pudo generar el PDF para NIT: {nit}")
            return False

        logging.info(f"PDF generado exitosamente: {pdf_path}")

        # Verificar archivo de direcciones
        if not os.path.exists(cfg.ARCHIVO_DIRECCIONES):
            logging.error(f"No se encontró el archivo de direcciones: {cfg.ARCHIVO_DIRECCIONES}")
            return False

        # Enviar correo
        smtp_config = cfg.obtener_config_smtp(correo_origen, app_pw)
        enviado = EnviadorCorreo.enviar_correo(nit, pdf_path, smtp_config, cfg.ARCHIVO_DIRECCIONES)
        
        # Registrar estado de envío
        estado = 'ENVIADO' if enviado else 'ERROR'
        estado_path = os.path.join(cfg.ESTADO_DIR, f'{nit}_estado.txt')
        with open(estado_path, 'w') as f:
            f.write(estado)
        
        logging.info(f"Estado de envío: {estado}")
        return enviado

    except Exception as e:
        logging.error(f"Error procesando archivo: {e}")
        return False
    
def procesamiento_microsoft(path, nit, tamano_letra):
    print("todo meloo")
    pass

def main(*args):
    print(f"Total de argumentos: {len(sys.argv)}")
    try:
        if len(sys.argv) >= 4:
            path = sys.argv[1]
            nit = sys.argv[2]
            tamano_letra = sys.argv[3]
            correo_origen = sys.argv[4]
            if len(sys.argv) == 6:
                if sys.argv[5] != None and sys.argv[5] != "":
                    app_pw = sys.argv[5]
                    logging.info(f"pw app: {app_pw}")
                    resultado = procesamiento_gmail(path, nit, tamano_letra, correo_origen, app_pw)
            else:
                resultado = procesamiento_microsoft(path, nit, tamano_letra)
                

            logging.info(f"Ruta proporcionada: {path}")
            logging.info(f"NIT proporcionado: {nit}")
            logging.info(f"Tamaño de letra: {tamano_letra}")

            sys.exit(0 if resultado else 1)

    except Exception as e:
        logging.error(f"Error en ejecución principal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()