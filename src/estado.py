import logging
import os
import datetime
import uuid
from src.config import ESTADO_DIR
from src.enviar_correo import EnviadorCorreo

class EstadoCorreo:
    @staticmethod
    def generar_estado(codigo_archivo, estado="ERROR", detalles_error=None, pdf_path=None, correo_origen=None):
        """Genera archivos de estado para el procesamiento de correos."""
        try:
            print(f"CODIGO ARCHIVO: {codigo_archivo}, ESTADO: {estado}, DETALLES: {detalles_error}, PDF: {pdf_path}, CORREO ORIGEN: {correo_origen}")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            enviador = EnviadorCorreo()
            correo_destino = enviador.obtener_correo_por_codigo(codigo_archivo)
            id_transaccion = str(uuid.uuid4())[:8]  # ID único para seguimiento
            
            # Tamaño del archivo PDF en KB si existe
            tamano_pdf = "N/A"
            if pdf_path and os.path.exists(pdf_path):
                tamano_pdf = f"{os.path.getsize(pdf_path) / 1024:.2f} KB"
            
            # Crear directorio de estados si no existe
            os.makedirs(ESTADO_DIR, exist_ok=True)
            
            # 1. Generar archivo individual para este correo específico
            archivo_individual = os.path.join(ESTADO_DIR, f"registro_{codigo_archivo}.txt")
            
            # Formato del registro detallado individual
            registro_detallado = (
                f"Archivo: {codigo_archivo}\n"
                f"Fecha De Envio: {timestamp}\n"
                f"Estado: {estado}\n"
                f"Correo destino: {correo_destino if correo_destino else 'No encontrado'}\n"
                f"Detalles error: {detalles_error if detalles_error else 'No hay detalles de error'}\n"
                f"Ruta PDF: {pdf_path if pdf_path else 'No se encontró la ruta del PDF'}\n"
                f"Correo origen: {correo_origen if correo_origen else 'N/A'}\n"
                f"Tamaño PDF: {tamano_pdf}\n"
                f"ID transacción: {id_transaccion}\n"
            )
            
            # Guardar el registro individual
            with open(archivo_individual, 'w', encoding='utf-8') as file:
                file.write(registro_detallado)
            
            # 2. Actualizar archivo general de estado_correos.txt
            estado_correos_path = os.path.join(ESTADO_DIR, "estado_correos.txt")

            encabezado = " ARCHIVO      || FECHA ENVÍO         || ESTADO\n"
            separador = "=" * 65 + "\n"
            
            # Formato resumido para el archivo general
            nuevo_registro = f"{codigo_archivo} || {timestamp} || {estado}\n"
            
            registros_acumulados = []
            
            # Verificar si el archivo existe para extraer registros previos
            if os.path.exists(estado_correos_path):
                try:
                    with open(estado_correos_path, 'r', encoding='utf-8') as file:
                        lineas = file.readlines()
                        
                        # Si hay al menos un encabezado y un separador (mínimo 2 líneas)
                        if len(lineas) > 2:
                            # Extraer todos los registros existentes (desde la línea 3 en adelante)
                            registros_acumulados = lineas[2:]
                except Exception as e:
                    logging.warning(f"Error leyendo registros previos: {e}")
            
            # Añadir el nuevo registro al principio de la lista
            registros_acumulados.insert(0, nuevo_registro)
            
            with open(estado_correos_path, 'w', encoding='utf-8') as file:
                file.write(encabezado)
                file.write(separador)
                file.writelines(registros_acumulados)

            logging.info(f"Registro de envío guardado para NIT: {codigo_archivo}, ID: {id_transaccion}")
            return True

        except Exception as e:
            logging.error(f"Error al generar registro de estado: {e}")
            return False
