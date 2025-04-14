import logging
import os
import datetime
import uuid
import src.config as cfg
from src.enviar_correo import EnviadorCorreo

class EstadoCorreo:
    @staticmethod
    def generar_estado(nit, estado="ERROR", detalles_error=None, pdf_path=None, correo_origen=None):
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            correo_destino = EnviadorCorreo.obtener_correo_por_nit(nit, cfg.ARCHIVO_DIRECCIONES)
            id_transaccion = str(uuid.uuid4())[:8]  # Generamos un ID único para seguimiento
            
            # Tamaño del archivo PDF en KB si existe
            tamano_pdf = "N/A"
            if pdf_path and os.path.exists(pdf_path):
                tamano_pdf = f"{os.path.getsize(pdf_path) / 1024:.2f} KB"
            
            # Crear directorio de estados si no existe
            os.makedirs(cfg.ESTADO_DIR, exist_ok=True)
            
            # 1. Generar archivo individual para este correo específico
            archivo_individual = os.path.join(cfg.ESTADO_DIR, f"registro_{nit}.txt")
            
            # Formato del registro detallado individual
            registro_detallado = (
                f"NIT: {nit}\n"
                f"Fecha De Envio: {timestamp}\n"
                f"Estado: {estado}\n"
                f"Correo destino: {correo_destino if correo_destino else 'No encontrado'}\n"
                f"Detalles error: {detalles_error if detalles_error else 'No hay detalles de error'}\n"
                f"Ruta PDF: {pdf_path if pdf_path else 'No se encontro la ruta del PDF'}\n"
                f"Correo origen: {correo_origen if correo_origen else 'N/A'}\n"
                f"Tamaño PDF: {tamano_pdf}\n"
                f"ID transacción: {id_transaccion}\n"
            )
            
            # Guardar el registro individual
            with open(archivo_individual, 'w', encoding='utf-8') as file:
                file.write(registro_detallado)
            
            # 2. Actualizar archivo general de estado_correos.txt (sobreescribir)
            estado_correos_path = os.path.join(cfg.ESTADO_DIR, "estado_correos.txt")

            encabezado = " NIT      || FECHA ENVÍO         || ESTADO\n"
            separador = "=" * 55 + "\n"
            
            # Formato resumido para el archivo general
            nuevo_registro = f"{nit} || {timestamp} || {estado}\n"
            
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
            
            # Añadir el nuevo registro al principio de la lista (para que sea el más reciente)
            registros_acumulados.insert(0, nuevo_registro)
            
            with open(estado_correos_path, 'w', encoding='utf-8') as file:
                file.write(encabezado)
                file.write(separador)
                file.writelines(registros_acumulados)
            
            logging.info(f"Registro de envío guardado para NIT: {nit}, ID: {id_transaccion}")
            return True
            
        except Exception as e:
            logging.error(f"Error al generar registro de estado: {e}")
            return False