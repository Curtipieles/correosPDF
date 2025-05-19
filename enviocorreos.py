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
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

class ProcesadorCorreos:
    def __init__(self, ruta_usuario, tamano_letra, estado_proceso):
        self.ruta_usuario = ruta_usuario
        self.tamano_letra = tamano_letra
        self.estado_proceso = estado_proceso
        self.entrada_dir = cfg.ENTRADA_DIR
        self.info_empresa = self._obtener_info_empresa()
        self.archivos_pendientes = self._obtener_archivos_pendientes() if estado_proceso == '1' else []

    def _obtener_info_empresa(self):
        info_empresa = cfg.obtener_info_empresa()
        if not info_empresa:
            logging.error("No se pudo obtener información de empresa.txt")
            return None
        return info_empresa
    
    def actualizar_estado_envio(self, codigo_archivo):
        try:
            if not os.path.exists(cfg.ARCHIVO_DIRECCIONES):
                logging.error(f"El archivo de direcciones no existe: {cfg.ARCHIVO_DIRECCIONES}")
                return False
                
            with open(cfg.ARCHIVO_DIRECCIONES, 'r') as file:
                lineas = file.readlines()
            
            actualizado = False
            with open(cfg.ARCHIVO_DIRECCIONES, 'w') as file:
                for linea in lineas:
                    datos = linea.strip().split(',')
                    if len(datos) >= 3 and datos[1] == codigo_archivo:
                        # Actualizar estado a 0 (enviado)
                        file.write(f"0,{datos[1]},{datos[2]}\n")
                        logging.info(f"Estado de envío actualizado a 0 para {codigo_archivo}")
                        actualizado = True
                    else:
                        file.write(linea)
            
            return actualizado
        except Exception as e:
            logging.error(f"Error actualizando estado de envío para {codigo_archivo}: {e}")
            return False
            
    def _obtener_archivos_pendientes(self):
        try:
            archivos_pendientes = []
            
            if not os.path.exists(cfg.ARCHIVO_DIRECCIONES):
                logging.warning("No existe el archivo de direcciones. No se pueden determinar archivos pendientes.")
                return []
                
            with open(cfg.ARCHIVO_DIRECCIONES, 'r', encoding='utf-8') as f:
                for linea in f:
                    linea = linea.strip()
                    if not linea:
                        continue
                        
                    # El formato es "ESTADO,CODIGO,CORREO"
                    partes = linea.split(',')
                    if len(partes) >= 3:
                        estado = partes[0].strip()
                        codigo = partes[1].strip()
                        
                        # Solo agregar a la lista si está pendiente (estado = 1)
                        if estado == "1":
                            archivos_pendientes.append(codigo)
            
            logging.info(f"Se encontraron {len(archivos_pendientes)} archivos pendientes por enviar")
            return archivos_pendientes
                
        except Exception as e:
            logging.error(f"Error al obtener archivos pendientes: {e}")
            return []
    
    def procesar_archivo(self, nombre_archivo):
        try:
            if not self.info_empresa:
                logging.error("No se pudieron obtener la información de la empresa")
                EstadoCorreo.generar_estado(
                    os.path.splitext(nombre_archivo)[0], 
                    "ERROR", 
                    "No se pudo obtener información de la empresa", 
                    None, 
                    None
                )
                return False
                
            nombre_base = os.path.splitext(nombre_archivo)[0]  # Obtiene el nombre sin extensión
            
            # Verificar si este archivo NO está en la lista de pendientes (solo en modo reenvío)
            if self.estado_proceso == '1' and nombre_base not in self.archivos_pendientes:
                logging.info(f"Omitiendo archivo que no está pendiente: {nombre_archivo}")
                # Generar un registro para este archivo omitido
                EstadoCorreo.generar_estado(
                    nombre_base, 
                    "OMITIDO", 
                    "Archivo no está en la lista de pendientes", 
                    None, 
                    self.info_empresa['correo_origen']
                )
                return True  # Considerar como éxito ya que no está en la lista de pendientes
                
            logging.info(f"Procesando archivo: {nombre_archivo}")
            
            # Verificación previa de archivos críticos
            if not os.path.exists(cfg.ARCHIVO_DIRECCIONES) or not os.path.exists(cfg.ARCHIVO_INFO_CORREOS):
                detalles_error = f"Archivo direcciones.txt o info_correo.txt no fue encontrado"
                logging.error(detalles_error)
                EstadoCorreo.generar_estado(
                    nombre_base, 
                    "ERROR", 
                    detalles_error,
                    None, 
                    self.info_empresa['correo_origen']
                )
                return False
            
            pdf_path = None
            estado_correo = "ERROR"
            detalles_error = None
            
            # Convertir a PDF
            try:
                conversor = ConversorPDF()
                pdf_path = conversor.convertir_a_pdf(self.ruta_usuario, nombre_base, self.tamano_letra)
                
                if not pdf_path:
                    detalles_error = f"No se pudo generar el PDF para archivo: {nombre_archivo}"
                    logging.error(detalles_error)
                    EstadoCorreo.generar_estado(
                        nombre_base, 
                        "ERROR", 
                        detalles_error, 
                        None, 
                        self.info_empresa['correo_origen']
                    )
                    return False
                
                logging.info(f"PDF generado exitosamente: {pdf_path}")
            except Exception as e:
                detalles_error = f"Error al generar PDF: {str(e)}"
                logging.error(detalles_error)
                EstadoCorreo.generar_estado(
                    nombre_base, 
                    "ERROR", 
                    detalles_error, 
                    None, 
                    self.info_empresa['correo_origen']
                )
                return False

            # Enviar correo
            try:
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
                    
                    # Actualizamos el estado en la libreta de direcciones solo si fue enviado con éxito
                    estado_archivo = self.actualizar_estado_envio(nombre_base)
                    if estado_archivo:
                        logging.info(f"Se cambió el estado a '0' en la libreta de direcciones para: {nombre_base}")
                    else:
                        logging.warning(f"No se pudo cambiar el estado a '0' en la libreta de direcciones para: {nombre_base}")
                else:
                    estado_correo = "ERROR"
                    detalles_error = detalle
            except Exception as e:
                estado_correo = "ERROR"
                detalles_error = f"Error durante el envío: {str(e)}"
                logging.error(detalles_error)
            
            # Generar registro del estado final
            registro_generado = EstadoCorreo.generar_estado(
                nombre_base, 
                estado_correo, 
                detalles_error, 
                pdf_path, 
                self.info_empresa['correo_origen']
            )
            
            if not registro_generado:
                logging.warning(f"No se pudo generar el registro para: {nombre_base}")
            
            return exito if 'exito' in locals() else False

        except Exception as e:
            logging.error(f"Error procesando archivo {nombre_archivo}: {e}")
            # Asegurar que se genere un registro incluso en caso de excepción general
            try:
                nombre_base = os.path.splitext(nombre_archivo)[0]
                EstadoCorreo.generar_estado(
                    nombre_base, 
                    "ERROR", 
                    f"Error general: {str(e)}", 
                    pdf_path if 'pdf_path' in locals() else None, 
                    self.info_empresa['correo_origen'] if self.info_empresa else None
                )
            except:
                logging.critical(f"Error fatal al generar registro para {nombre_archivo}")
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
                cfg.actualizar_estado_proceso('0')
                logging.info("Proceso completado. Estado actualizado a 0.")
                return True
                
            total_archivos = len(archivos)
            logging.info(f"Se encontraron {total_archivos} archivos para procesar")
            
            # Si estamos en modo reenvío, filtrar solo los archivos pendientes
            if self.estado_proceso == '1':
                # Filtrar archivos y registrar los omitidos
                archivos_originales = archivos.copy()
                archivos_a_procesar = []
                for archivo in archivos_originales:
                    nombre_base = os.path.splitext(archivo)[0]
                    if nombre_base in self.archivos_pendientes:
                        archivos_a_procesar.append(archivo)
                
                # Registrar los archivos que se omitieron en el filtrado inicial
                omitidos = set(archivo for archivo in archivos_originales) - set(archivo for archivo in archivos_a_procesar)
                for archivo_omitido in omitidos:
                    nombre_base = os.path.splitext(archivo_omitido)[0]
                    logging.info(f"Archivo omitido en el filtrado inicial: {archivo_omitido}")
                    if self.info_empresa:
                        EstadoCorreo.generar_estado(
                            nombre_base, 
                            "OMITIDO", 
                            "Archivo no está en la lista de pendientes (filtrado inicial)", 
                            None, 
                            self.info_empresa['correo_origen']
                        )
                
                archivos = archivos_a_procesar
                logging.info(f"Después de filtrar, hay {len(archivos)} archivos pendientes por procesar")
                
                if not archivos:
                    logging.info("No hay archivos pendientes para procesar")
                    cfg.actualizar_estado_proceso('0')
                    logging.info("Proceso completado. Estado actualizado a 0.")
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
            
            cfg.actualizar_estado_proceso('0')
            logging.info("Proceso completado. Estado actualizado a 0.")
                    
            return True
            
        except Exception as e:
            logging.error(f"Error al procesar archivos: {e}")
            # Intentar registrar este error general
            if self.info_empresa:
                EstadoCorreo.generar_estado(
                    "proceso_general", 
                    "ERROR", 
                    f"Error general en procesar_todos: {str(e)}", 
                    None, 
                    self.info_empresa['correo_origen']
                )
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