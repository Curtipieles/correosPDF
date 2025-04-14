import sys
import os
import logging
import src.config as cfg
from src.conversor import ConversorPDF
from src.enviar_correo import EnviadorCorreo
from src.estado import EstadoCorreo

# Configuración de logging
logging.getLogger('fontTools').setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])

def procesamiento_gmail(path, nit, tamano_letra, correo_origen, app_pw):
    try:
        logging.info(f"Iniciando procesamiento para NIT: {nit}")
        logging.info(f"Usando ruta: {path}")

        os.makedirs(cfg.PDF_DIR, exist_ok=True)
        os.makedirs(cfg.ESTADO_DIR, exist_ok=True)

        pdf_path = None
        estado_correo = "ERROR"
        detalles_error = None
        
        # Convertir a PDF
        pdf_path = ConversorPDF.convertir_a_pdf(path, nit, tamano_letra, cfg.PDF_DIR)
        
        if not pdf_path:
            detalles_error = f"No se pudo generar el PDF para NIT: {nit}"
            logging.error(detalles_error)
            EstadoCorreo.generar_estado(nit, "ERROR", detalles_error, None, correo_origen)
            return False

        logging.info(f"PDF generado exitosamente: {pdf_path}")

        if not os.path.exists(cfg.ARCHIVO_DIRECCIONES) or not os.path.exists(cfg.ARCHIVO_INFO_CORREOS):
            detalles_error = f"Archivo direcciones.txt o info_correo.txt no fue encontrado"
            logging.error(detalles_error)
            EstadoCorreo.generar_estado(nit, "ERROR", detalles_error, pdf_path, correo_origen)
            return False

        smtp_config = cfg.obtener_config_smtp(correo_origen, app_pw)
        enviado = EnviadorCorreo.enviar_correo_gmail(nit, 
                                                   pdf_path, 
                                                   smtp_config,
                                                   cfg.ARCHIVO_DIRECCIONES, 
                                                   cfg.ARCHIVO_INFO_CORREOS)
        
        if enviado:
            estado_correo = "ENVIADO"
            detalles_error = None
        else:
            estado_correo = "ERROR"
            detalles_error = "Error al enviar el correo electrónico"
        
        registro_generado = EstadoCorreo.generar_estado(
            nit, 
            estado_correo, 
            detalles_error, 
            pdf_path, 
            correo_origen
        )
        
        if not registro_generado:
            logging.warning(f"No se pudo generar el registro para el NIT: {nit}")
        
        return enviado

    except Exception as e:
        logging.error(f"Error procesando archivo: {e}")
        EstadoCorreo.generar_estado(nit, "ERROR", str(e), pdf_path if 'pdf_path' in locals() else None, correo_origen)
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
        if not isinstance(sys.argv[3], str):
            logging.error(f"El argumento '{sys.argv[3]}'. Debe ser una letra: 'P' o una 'N'")
            sys.exit(1)
        if not sys.argv[3] == "P":
            if not sys.argv[3] == "N":
                logging.error(f"El argumento '{sys.argv[3]}'. Debe ser una letra: 'P' o una 'N'")
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