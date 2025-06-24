import sys
import os
import logging
import time
import random
from src.conversor import ConversorPDF
from src.enviar_correo import EnviadorCorreo
from src.estado import EstadoCorreo
import src.config as cfg

# Configuración de logging unificada
logging.getLogger('fontTools').setLevel(logging.WARNING)
logging.basicConfig(level=logging.CRITICAL, format='%(asctime)s - %(levelname)s - %(message)s')

class ProcesadorCorreos:
    def __init__(self, ruta_usuario, tamano_letra, estado_proceso):
        self.ruta_usuario = ruta_usuario
        self.tamano_letra = tamano_letra
        self.estado_proceso = estado_proceso
        self.entrada_dir = cfg.ENTRADA_DIR
        self.info_empresa = self._obtener_info_empresa()
        self.archivos_pendientes = self._obtener_archivos_pendientes() if estado_proceso == '1' else []

    def _obtener_info_empresa(self):
        """Obtiene información de la empresa desde configuración"""
        info_empresa = cfg.obtener_info_empresa()
        if not info_empresa:
            logging.critical("No se pudo obtener información de empresa.txt")
            return None
        return info_empresa
    
    def _validar_archivos_criticos(self):
        """Valida la existencia de archivos críticos para el proceso"""
        archivos_criticos = [cfg.ARCHIVO_DIRECCIONES, cfg.ARCHIVO_INFO_CORREOS]
        for archivo in archivos_criticos:
            if not os.path.exists(archivo):
                return False, f"Archivo crítico no encontrado: {archivo}"
        return True, None
    
    def _actualizar_estado_archivo(self, codigo_archivo):
        """Actualiza el estado del archivo a enviado en el archivo de direcciones"""
        try:
            if not os.path.exists(cfg.ARCHIVO_DIRECCIONES):
                logging.critical(f"El archivo de direcciones no existe: {cfg.ARCHIVO_DIRECCIONES}")
                return False
                
            with open(cfg.ARCHIVO_DIRECCIONES, 'r') as file:
                lineas = file.readlines()
            
            actualizado = False
            with open(cfg.ARCHIVO_DIRECCIONES, 'w') as file:
                for linea in lineas:
                    datos = linea.strip().split(',')
                    if len(datos) >= 3 and datos[1] == codigo_archivo:
                        file.write(f"0,{datos[1]},{datos[2]}\n")
                        logging.info(f"Estado actualizado a enviado para {codigo_archivo}")
                        actualizado = True
                    else:
                        file.write(linea)
            
            return actualizado
        except Exception as e:
            logging.error(f"Error actualizando estado para {codigo_archivo}: {e}")
            return False
            
    def _obtener_archivos_pendientes(self):
        """Obtiene lista de archivos pendientes por enviar"""
        try:
            archivos_pendientes = []
            
            if not os.path.exists(cfg.ARCHIVO_DIRECCIONES):
                logging.critical("No existe el archivo de direcciones")
                return []
                
            with open(cfg.ARCHIVO_DIRECCIONES, 'r', encoding='utf-8') as f:
                for linea in f:
                    linea = linea.strip()
                    if not linea:
                        continue
                        
                    partes = linea.split(',')
                    if len(partes) >= 3:
                        estado = partes[0].strip()
                        codigo = partes[1].strip()
                        
                        if estado == "1":  # Pendiente
                            archivos_pendientes.append(codigo)
            
            logging.info(f"Archivos pendientes encontrados: {len(archivos_pendientes)}")
            return archivos_pendientes
                
        except Exception as e:
            logging.critical(f"Error al obtener archivos pendientes: {e}")
            return []
    
    def _generar_estado_error(self, nombre_base, mensaje_error, pdf_path=None):
        """Genera un estado de error de forma centralizada"""
        EstadoCorreo.generar_estado(
            nombre_base, 
            "ERROR", 
            mensaje_error, 
            pdf_path, 
        )
    
    def procesar_archivo(self, nombre_archivo):
        """Procesa un archivo individual: convierte a PDF y envía por correo"""
        nombre_base = os.path.splitext(nombre_archivo)[0]
        pdf_path = None
        
        try:
            # Validar información de empresa
            if not self.info_empresa:
                self._generar_estado_error(nombre_base, "No se pudo obtener información de la empresa")
                return False
                
            # Verificar si el archivo debe ser procesado
            if self.estado_proceso == '1' and nombre_base not in self.archivos_pendientes:
                logging.info(f"Omitiendo archivo no pendiente: {nombre_archivo}")
                EstadoCorreo.generar_estado(
                    nombre_base, 
                    "OMITIDO", 
                    "Archivo no está en la lista de pendientes", 
                    None, 
                )
                return True
                
            logging.info(f"Procesando archivo: {nombre_archivo}")
            
            # Validar archivos críticos
            archivos_validos, error_validacion = self._validar_archivos_criticos()
            if not archivos_validos:
                self._generar_estado_error(nombre_base, error_validacion)
                return False
            
            # Convertir a PDF
            try:
                conversor = ConversorPDF()
                pdf_path, detalle = conversor.convertir_a_pdf(self.ruta_usuario, nombre_base, self.tamano_letra)
                
                if not pdf_path:
                    mensaje_error = detalle if detalle else f"No se pudo generar el PDF para {nombre_archivo}"
                    self._generar_estado_error(nombre_base, mensaje_error)
                    return False
                
                logging.info(f"PDF generado: {pdf_path}")
            except Exception as e:
                self._generar_estado_error(nombre_base, f"Error al generar PDF: {str(e)}")
                return False
            
            # Enviar correo
            try:
                smtp_config = cfg.obtener_config_smtp(self.info_empresa['correo_origen'], self.info_empresa['app_pw'])
                enviador = EnviadorCorreo()
                exito, detalle = enviador.enviar_correo_gmail(nombre_base, pdf_path, smtp_config)
                
                if exito:
                    estado_correo = "ENVIADO"
                    self._actualizar_estado_archivo(nombre_base)
                else:
                    estado_correo = "ERROR"
                
                EstadoCorreo.generar_estado(
                    nombre_base, 
                    estado_correo, 
                    detalle, 
                    pdf_path, 
                )
                
                return exito
                
            except Exception as e:
                self._generar_estado_error(nombre_base, f"Error durante el envío: {str(e)}", pdf_path)
                return False

        except Exception as e:
            logging.error(f"Error procesando archivo {nombre_archivo}: {e}")
            self._generar_estado_error(nombre_base, f"Error general: {str(e)}", pdf_path)
            return False
    
    def procesar_todos(self):
        """Procesa todos los archivos en el directorio de entrada"""
        try:
            # Validar directorio de entrada
            if not os.path.exists(self.entrada_dir):
                logging.critical(f"El directorio de entrada no existe: {self.entrada_dir}")
                return False
                
            archivos = [f for f in os.listdir(self.entrada_dir) if f.endswith('.txt')]
            
            if not archivos:
                logging.info("No hay archivos para procesar")
                cfg.actualizar_estado_proceso('0')
                return True
                
            logging.info(f"Archivos encontrados: {len(archivos)}")
            
            # Filtrar archivos si es un reenvío
            if self.estado_proceso == '1':
                archivos_originales = archivos.copy()
                archivos = [f for f in archivos if os.path.splitext(f)[0] in self.archivos_pendientes]
                
                # Registrar archivos omitidos en el filtrado
                omitidos = set(archivos_originales) - set(archivos)
                for archivo_omitido in omitidos:
                    nombre_base = os.path.splitext(archivo_omitido)[0]
                    if self.info_empresa:
                        EstadoCorreo.generar_estado(
                            nombre_base, 
                            "OMITIDO", 
                            "Archivo no está en la lista de pendientes (filtrado inicial)", 
                            None, 
                        )
                
                logging.info(f"Archivos pendientes a procesar: {len(archivos)}")
                
                if not archivos:
                    cfg.actualizar_estado_proceso('0')
                    return True
            
            # Procesar archivos con pausas programadas
            CORREOS_ANTES_DESCANSO = 30
            TIEMPO_DESCANSO = 150
            
            for i, archivo in enumerate(archivos):
                logging.info(f"Procesando {i+1}/{len(archivos)}: {archivo}")
                self.procesar_archivo(archivo)
                
                # Gestión de pausas
                if (i + 1) % CORREOS_ANTES_DESCANSO == 0 and i < len(archivos) - 1:
                    logging.info(f"Pausa programada después de {i+1} correos ({TIEMPO_DESCANSO/60} minutos)")
                    time.sleep(TIEMPO_DESCANSO)
                elif i < len(archivos) - 1:
                    intervalo = random.randint(30, 60)
                    logging.info(f"Pausa aleatoria: {intervalo} segundos")
                    time.sleep(intervalo)
            
            cfg.actualizar_estado_proceso('0')
            logging.info("Proceso completado")
            return True
            
        except Exception as e:
            logging.critical(f"Error al procesar archivos: {e}")
            if self.info_empresa:
                EstadoCorreo.generar_estado(
                    "proceso_general", 
                    "ERROR", 
                    f"Error general en procesar_todos: {str(e)}", 
                    None,
                )
            return False

def main():
    """Función principal del programa"""
    try:
        # Validar argumentos
        if len(sys.argv) != 4:
            logging.critical("Argumentos incorrectos. Uso: python main.py <ruta_usuario> <tamano_letra> <estado_proceso>")
            sys.exit(1)
            
        ruta_usuario, tamano_letra, estado_proceso = sys.argv[1], sys.argv[2], sys.argv[3]
        
        # Validaciones de entrada
        if not os.path.exists(ruta_usuario):
            logging.critical(f"La ruta '{ruta_usuario}' no existe")
            sys.exit(1)
            
        if tamano_letra not in ['P', 'N']:
            logging.critical(f"Tamaño de letra inválido: '{tamano_letra}'. Debe ser 'P' o 'N'")
            sys.exit(1)

        if estado_proceso not in ['0', '1']:
            logging.critical(f"Estado del proceso inválido: '{estado_proceso}'. Debe ser '0' o '1'")
            sys.exit(1)

        # Ejecutar procesamiento
        procesador = ProcesadorCorreos(ruta_usuario, tamano_letra, estado_proceso)
        resultado = procesador.procesar_todos()
        
        sys.exit(0 if resultado else 1)

    except Exception as e:
        logging.critical(f"Error en ejecución principal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()