import sys
import os
import logging
import time
import re
from src.conversor import ConversorPDF
from src.enviar_correo import EnviadorCorreo
from src.estado import EstadoCorreo
import src.config as cfg

# Configuración de logging
logging.getLogger('fontTools').setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])

class ProcesadorCorreos:
    def __init__(self, ruta_usuario, tamano_letra, estado_proceso):
        self.ruta_usuario = ruta_usuario
        self.tamano_letra = tamano_letra
        self.estado_proceso = estado_proceso
        self.entrada_dir = cfg.ENTRADA_DIR
        self.info_empresa = self._obtener_info_empresa()
        print(self.info_empresa)
        self.archivos_ya_enviados = self._obtener_archivos_ya_enviados() if estado_proceso == '1' else []

    def _obtener_info_empresa(self):
        """Obtiene información de la empresa del archivo empresa.txt"""
        info_empresa = cfg.obtener_info_empresa()
        if not info_empresa:
            logging.error("No se pudo obtener información de empresa.txt")
            return None
        return info_empresa
            
    def _obtener_archivos_ya_enviados(self):
        try:
            archivos_enviados = []
            if not os.path.exists(cfg.ARCHIVO_ESTADO):
                logging.warning("No existe archivo de estado previo. Se procesarán todos los archivos.")
                return []
                
            with open(cfg.ARCHIVO_ESTADO, 'r', encoding='utf-8') as f:
                lineas = f.readlines()
                # Saltar las dos primeras líneas (encabezado y separador)
                for i in range(2, len(lineas)):
                    linea = lineas[i].strip()
                    if not linea:
                        continue
                        
                    # El formato es "ARCHIVO || FECHA ENVÍO || ESTADO || DIAGNÓSTICO"
                    partes = linea.split('||')
                    if len(partes) >= 3:
                        archivo = partes[0].strip()
                        estado = partes[2].strip()
                        
                        # Solo agregar a la lista si fue enviado exitosamente
                        if estado == "ENVIADO":
                            archivos_enviados.append(archivo)
            
            logging.info(f"Se encontraron {len(archivos_enviados)} archivos ya enviados previamente")
            return archivos_enviados
            
        except Exception as e:
            logging.error(f"Error al obtener archivos ya enviados: {e}")
            return []
            
    def procesar_archivo(self, nombre_archivo):
        try:
            if not self.info_empresa:
                logging.error("No se pudieron obtener la información de la empresa")
                return False
                
            nombre_base = os.path.splitext(nombre_archivo)[0]  # Obtiene el nombre sin extensión
            
            # Verificar si este archivo ya fue enviado (solo en modo reenvío)
            if self.estado_proceso == '1' and nombre_base in self.archivos_ya_enviados:
                logging.info(f"Omitiendo archivo ya enviado: {nombre_archivo}")
                return True  # Considerar como éxito ya que fue procesado anteriormente
                
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
                EstadoCorreo.generar_estado(nombre_base, "ERROR", detalles_error, None, self.info_empresa['correo_origen'])
                return False

            logging.info(f"PDF generado exitosamente: {pdf_path}")

            if not os.path.exists(cfg.ARCHIVO_DIRECCIONES) or not os.path.exists(cfg.ARCHIVO_INFO_CORREOS):
                detalles_error = f"Archivo direcciones.txt o info_correo.txt no fue encontrado"
                logging.error(detalles_error)
                EstadoCorreo.generar_estado(nombre_base, "ERROR", detalles_error, pdf_path, self.info_empresa['correo_origen'])
                return False

            smtp_config = cfg.obtener_config_smtp(self.info_empresa['correo_origen'], self.info_empresa['app_pw'])
            enviador = EnviadorCorreo()
            enviado = enviador.enviar_correo_gmail(
                nombre_base, 
                pdf_path, 
                smtp_config
            )
            exito, detalle = enviado # Desempaquetamos la tupla
            if exito:
                estado_correo = "ENVIADO"
                detalles_error = detalle
            else:
                estado_correo = "ERROR"
                detalles_error = detalle
            
            registro_generado = EstadoCorreo.generar_estado(
                nombre_base, 
                estado_correo, 
                detalles_error, 
                pdf_path, 
                self.info_empresa['correo_origen']
            )
            
            if not registro_generado:
                logging.warning(f"No se pudo generar el registro para: {nombre_base}")
            
            return enviado

        except Exception as e:
            logging.error(f"Error procesando archivo {nombre_archivo}: {e}")
            EstadoCorreo.generar_estado(nombre_base, "ERROR", str(e), pdf_path if 'pdf_path' in locals() else None, 
                                       self.info_empresa['correo_origen'] if self.info_empresa else None)
            return False
    
    def procesar_todos(self, intervalo_min=30, intervalo_max=60):
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
            
            # Si estamos en modo reenvío, filtrar los archivos que ya fueron enviados
            if self.estado_proceso == '1' and self.archivos_ya_enviados:
                archivos_a_procesar = []
                for archivo in archivos:
                    nombre_base = os.path.splitext(archivo)[0]
                    if nombre_base not in self.archivos_ya_enviados:
                        archivos_a_procesar.append(archivo)
                        
                archivos = archivos_a_procesar
                logging.info(f"Después de filtrar archivos ya enviados, quedan {len(archivos)} por procesar")
                
                if not archivos:
                    logging.info("Todos los archivos ya fueron enviados previamente")
                    return True
            
            CORREOS_ANTES_DESCANSO = 30
            TIEMPO_DESCANSO = 150  # 2.5 minutos en segundos
            
            for i, archivo in enumerate(archivos):
                logging.info(f"Procesando {i+1}/{len(archivos)}: {archivo}")
                self.procesar_archivo(archivo)
                
                # Verificar si toca hacer un descanso (cada 30 correos)
                if (i + 1) % CORREOS_ANTES_DESCANSO == 0 and i < len(archivos) - 1:
                    logging.info(f"Se han procesado {i+1} correos. Haciendo una pausa de {TIEMPO_DESCANSO/60} minutos...")
                    time.sleep(TIEMPO_DESCANSO)
                # Si no es el último archivo y no toca descanso, esperar un intervalo aleatorio
                elif i < len(archivos) - 1:
                    intervalo_aleatorio = random.randint(intervalo_min, intervalo_max)
                    logging.info(f"Esperando {intervalo_aleatorio} segundos antes del siguiente envío...")
                    time.sleep(intervalo_aleatorio)
            
            # Al finalizar todos los envíos, actualizar el estado del proceso a 0
            cfg.actualizar_estado_proceso('0')
            logging.info("Proceso completado. Estado actualizado a 0.")
                    
            return True
            
        except Exception as e:
            logging.error(f"Error al procesar archivos: {e}")
            return False

def main():
    try:
        if len(sys.argv) != 4:
            logging.error("Argumentos incorrectos. Uso: python main.py <ruta_usuario> <tamano_letra> <estado_proceso>")
            sys.exit(1)

        if not os.path.exists(sys.argv[1]):
            logging.error(f"La ruta '{sys.argv[1]}' no existe.")
            sys.exit(1)
            
        if sys.argv[2] not in ['P', 'N']:
            logging.error(f"El tamaño de letra '{sys.argv[2]}' es inválido. Debe ser 'P' o 'N'.")
            sys.exit(1)

        if sys.argv[3] not in ['0', '1']:
            logging.error(f"Estado del proceso inválido. Debe ser '0' (nuevo proceso) o '1' (reenvío).")
            sys.exit(1)
            
        ruta_usuario = sys.argv[1]
        tamano_letra = sys.argv[2]
        estado_proceso = sys.argv[3]

        procesador = ProcesadorCorreos(ruta_usuario, tamano_letra, estado_proceso)
        resultado = procesador.procesar_todos()
        
        sys.exit(0 if resultado else 1)

    except Exception as e:
        logging.error(f"Error en ejecución principal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()