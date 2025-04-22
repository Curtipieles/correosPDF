import sys
import os
import logging
import time
from src.conversor import ConversorPDF
from src.enviar_correo import EnviadorCorreo
from src.estado import EstadoCorreo
import src.config as cfg

# Configuración de logging
logging.getLogger('fontTools').setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])

class ProcesadorCorreos:
    def __init__(self, ruta_usuario, tamano_letra):
        self.ruta_usuario = ruta_usuario
        self.tamano_letra = tamano_letra
        self.entrada_dir = os.path.join(ruta_usuario, 'entrada')
        self.credenciales = self._obtener_credenciales()
        
    def _obtener_credenciales(self):
        """Obtiene correo origen y contraseña del archivo correo_origen.txt"""
        try:
            with open(cfg.ARCHIVO_CORREO_ORIGEN, 'r') as f:
                linea = f.readline().strip()
                partes = linea.split(',')
                if len(partes) >= 2:
                    return {
                        'correo': partes[0].strip(),
                        'app_pw': partes[1].strip()
                    }
                else:
                    logging.error("Formato incorrecto en archivo de credenciales")
                    return None
        except Exception as e:
            logging.error(f"Error al leer credenciales: {e}")
            return None
            
    def procesar_archivo(self, nombre_archivo):
        """Procesa un solo archivo de entrada"""
        try:
            if not self.credenciales:
                logging.error("No se pudieron obtener las credenciales")
                return False
                
            nombre_base = os.path.splitext(nombre_archivo)[0]  # Obtiene el nombre sin extensión
            logging.info(f"Procesando archivo: {nombre_archivo}")
            
            pdf_path = None
            estado_correo = "ERROR"
            detalles_error = None
            
            # Convertir a PDF
            conversor = ConversorPDF()
            pdf_path = conversor.convertir_a_pdf(self.ruta_usuario, nombre_base, self.tamano_letra)
            
            if not pdf_path:
                detalles_error = f"No se pudo generar el PDF para archivo: {nombre_archivo}"
                logging.error(detalles_error)
                EstadoCorreo.generar_estado(nombre_base, "ERROR", detalles_error, None, self.credenciales['correo'])
                return False

            logging.info(f"PDF generado exitosamente: {pdf_path}")

            if not os.path.exists(cfg.ARCHIVO_DIRECCIONES) or not os.path.exists(cfg.ARCHIVO_INFO_CORREOS):
                detalles_error = f"Archivo direcciones.txt o info_correo.txt no fue encontrado"
                logging.error(detalles_error)
                EstadoCorreo.generar_estado(nombre_base, "ERROR", detalles_error, pdf_path, self.credenciales['correo'])
                return False

            smtp_config = cfg.obtener_config_smtp(self.credenciales['correo'], self.credenciales['app_pw'])
            enviador = EnviadorCorreo()
            enviado = enviador.enviar_correo_gmail(
                nombre_base, 
                pdf_path, 
                smtp_config
            )
            
            if enviado:
                estado_correo = "ENVIADO"
                detalles_error = None
            else:
                estado_correo = "ERROR"
                detalles_error = "Error al enviar el correo electrónico"
            
            registro_generado = EstadoCorreo.generar_estado(
                nombre_base, 
                estado_correo, 
                detalles_error, 
                pdf_path, 
                self.credenciales['correo']
            )
            
            if not registro_generado:
                logging.warning(f"No se pudo generar el registro para: {nombre_base}")
            
            return enviado

        except Exception as e:
            logging.error(f"Error procesando archivo {nombre_archivo}: {e}")
            EstadoCorreo.generar_estado(nombre_base, "ERROR", str(e), pdf_path if 'pdf_path' in locals() else None, 
                                       self.credenciales['correo'] if self.credenciales else None)
            return False
    
    def procesar_todos(self, intervalo=60):
        """Procesa todos los archivos en la carpeta de entrada con un intervalo de tiempo"""
        try:
            if not os.path.exists(self.entrada_dir):
                logging.error(f"El directorio de entrada no existe: {self.entrada_dir}")
                return False
                
            archivos = [f for f in os.listdir(self.entrada_dir) if f.endswith('.txt')]
            
            if not archivos:
                logging.info("No hay archivos para procesar")
                return True
                
            logging.info(f"Se encontraron {len(archivos)} archivos para procesar")
            
            for i, archivo in enumerate(archivos):
                logging.info(f"Procesando {i+1}/{len(archivos)}: {archivo}")
                self.procesar_archivo(archivo)
                
                # Si no es el último archivo, esperar el intervalo
                if i < len(archivos) - 1:
                    logging.info(f"Esperando {intervalo} segundos antes del siguiente envío...")
                    time.sleep(intervalo)
                    
            return True
            
        except Exception as e:
            logging.error(f"Error al procesar archivos: {e}")
            return False

def main():
    try:
        if len(sys.argv) < 3:
            logging.error("Argumentos insuficientes. Uso: python main.py <ruta_usuario> <tamano_letra>")
            sys.exit(1)
            
        ruta_usuario = sys.argv[1]
        tamano_letra = sys.argv[2]
        
        if not os.path.exists(ruta_usuario):
            logging.error(f"La ruta '{ruta_usuario}' no existe.")
            sys.exit(1)
            
        if tamano_letra not in ['P', 'N']:
            logging.error(f"El tamaño de letra '{tamano_letra}' es inválido. Debe ser 'P' o 'N'.")
            sys.exit(1)
            
        procesador = ProcesadorCorreos(ruta_usuario, tamano_letra)
        resultado = procesador.procesar_todos()
        
        sys.exit(0 if resultado else 1)

    except Exception as e:
        logging.error(f"Error en ejecución principal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()