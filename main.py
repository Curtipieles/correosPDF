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
        self.entrada_dir = cfg.ENTRADA_DIR
        self.credenciales = self._obtener_credenciales()

    @staticmethod
    def mostrar_barra_progreso(progreso, total, longitud=50, prefijo='Progreso:', sufijo='Completado', relleno='█', vacio='░'):
        """
        Args:
            progreso (int): Cantidad de elementos procesados
            total (int): Total de elementos a procesar
            longitud (int): Longitud de la barra de progreso en caracteres
            prefijo (str): Texto que precede a la barra
            sufijo (str): Texto que sigue a la barra
            relleno (str): Carácter para la parte completada de la barra
            vacio (str): Carácter para la parte no completada de la barra
        """
        porcentaje = progreso / total
        completado = int(longitud * porcentaje)
        barra = relleno * completado + vacio * (longitud - completado)
        porcentaje_texto = f"{100 * porcentaje:.1f}%"
        
        # Sobrescribe la línea actual con la barra de progreso
        print(f'\r{prefijo} |{barra}| {progreso}/{total} {porcentaje_texto} {sufijo}', end='', flush=True)
        
        # Agregar salto de línea cuando se completa
        if progreso == total:
            print()

    @staticmethod        
    def _obtener_credenciales():
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
    
    def procesar_todos(self, intervalo_min=30, intervalo_max=60):
        """Procesa todos los archivos en la carpeta de entrada con intervalos aleatorios
        y descansos programados cada cierto número de envíos, mostrando una barra de progreso"""
        try:
            import random
            
            if not os.path.exists(self.entrada_dir):
                logging.error(f"El directorio de entrada no existe: {self.entrada_dir}")
                return False
                
            archivos = [f for f in os.listdir(self.entrada_dir) if f.endswith('.txt')]
            
            if not archivos:
                logging.info("No hay archivos para procesar")
                return True
                
            total_archivos = len(archivos)
            logging.info(f"Se encontraron {total_archivos} archivos para procesar")
            
            CORREOS_ANTES_DESCANSO = 30
            TIEMPO_DESCANSO = 150  # 2.5 minutos en segundos
            
            # Mostrar barra inicial
            ProcesadorCorreos.mostrar_barra_progreso(0, total_archivos, prefijo='Envío de correos:')
            
            for i, archivo in enumerate(archivos):
                logging.info(f"Procesando {i+1}/{total_archivos}: {archivo}")
                self.procesar_archivo(archivo)
                
                # Actualizar barra de progreso
                ProcesadorCorreos.mostrar_barra_progreso(i+1, total_archivos, prefijo='Envío de correos:')
                
                # Verificar si toca hacer un descanso (cada 30 correos)
                if (i + 1) % CORREOS_ANTES_DESCANSO == 0 and i < total_archivos - 1:
                    logging.info(f"Se han procesado {i+1} correos. Haciendo una pausa de {TIEMPO_DESCANSO/60} minutos...")
                    time.sleep(TIEMPO_DESCANSO)
                # Si no es el último archivo y no toca descanso, esperar un intervalo aleatorio
                elif i < total_archivos - 1:
                    intervalo_aleatorio = random.randint(intervalo_min, intervalo_max)
                    logging.info(f"Esperando {intervalo_aleatorio} segundos antes del siguiente envío...")
                    time.sleep(intervalo_aleatorio)
                    
            return True
            
        except Exception as e:
            logging.error(f"Error al procesar archivos: {e}")
            return False

def main():
    try:
        if not len(sys.argv) < 3 and not len(sys.argv) > 3:
            logging.error("Argumentos incorrectos. Uso: python main.py <ruta_usuario> <tamano_letra>")
            sys.exit(1)

        if not os.path.exists(sys.argv[1]):
            logging.error(f"La ruta '{sys.argv[1]}' no existe.")
            sys.exit(1)
            
        if sys.argv[2] not in ['P', 'N']:
            logging.error(f"El tamaño de letra '{sys.argv[2]}' es inválido. Debe ser 'P' o 'N'.")
            sys.exit(1)
            
        ruta_usuario = sys.argv[1]
        tamano_letra = sys.argv[2]

        procesador = ProcesadorCorreos(ruta_usuario, tamano_letra)
        resultado = procesador.procesar_todos()
        
        sys.exit(0 if resultado else 1)

    except Exception as e:
        logging.error(f"Error en ejecución principal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()