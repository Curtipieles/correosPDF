import sys
import os
import logging
from src.config import PDF_DIR, ESTADO_DIR, SMTP_CONFIG, ARCHIVO_DIRECCIONES, LOGO_EMPRESA
from src.conversor import ConversorPDF
from src.enviar_correo import EnviadorCorreo

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

def procesar_archivo(path, nit, tamano_letra):
    try:
        logging.info(f"Iniciando procesamiento para NIT: {nit}")

        # Usar la ruta tal como está (ya está normalizada en config.py)
        logging.info(f"Usando ruta: {path}")

        # Crear carpetas si no existen
        os.makedirs(PDF_DIR, exist_ok=True)
        os.makedirs(ESTADO_DIR, exist_ok=True)

        # Convertir a PDF
        pdf_path = ConversorPDF.convertir_a_pdf(path, nit, tamano_letra, PDF_DIR)
        
        if not pdf_path:
            logging.error(f"No se pudo generar el PDF para NIT: {nit}")
            return False

        logging.info(f"PDF generado exitosamente: {pdf_path}")

        # Verificar archivo de direcciones
        if not os.path.exists(ARCHIVO_DIRECCIONES):
            logging.error(f"No se encontró el archivo de direcciones: {ARCHIVO_DIRECCIONES}")
            return False

        # Enviar correo
        enviado = EnviadorCorreo.enviar_correo(nit, pdf_path, SMTP_CONFIG, ARCHIVO_DIRECCIONES)
        
        # Registrar estado de envío
        estado = 'ENVIADO' if enviado else 'ERROR'
        estado_path = os.path.join(ESTADO_DIR, f'{nit}_estado.txt')
        with open(estado_path, 'w') as f:
            f.write(estado)
        
        logging.info(f"Estado de envío: {estado}")
        return enviado

    except Exception as e:
        logging.error(f"Error procesando archivo: {e}")
        return False

def main():
    try:
        # Validar argumentos
        if len(sys.argv) < 5 and len(sys.argv) > 5:
            logging.error("Uso: python main.py <ruta> <nit> <tamano_letra> <correo_origen")
            sys.exit(1)
        
        # Estos valores se usan en config.py para configurar las rutas
        path = sys.argv[1]
        nit = sys.argv[2]
        tamano_letra = sys.argv[3]
        correo_origen = sys.argv[4]
        app_pw = sys.argv[5]

        logging.info(f"Ruta proporcionada: {path}")
        logging.info(f"NIT proporcionado: {nit}")
        logging.info(f"Tamaño de letra: {tamano_letra}")

        # Procesar archivo con la ruta proporcionada
        resultado = procesar_archivo(path, nit, tamano_letra)
        
        sys.exit(0 if resultado else 1)

    except Exception as e:
        logging.error(f"Error en ejecución principal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()