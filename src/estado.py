import logging
import os
import datetime
import uuid
import socket
import platform
import psutil
from src.config import ESTADO_DIR
from src.enviar_correo import EnviadorCorreo

class EstadoCorreo:
    @staticmethod
    def verificar_estado_red():
        """Verifica el estado de la conexión de red de forma simplificada"""
        info_red = {}
        
        # Verificar conexión a internet
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            info_red["conexion_internet"] = True
        except (socket.error, socket.timeout):
            info_red["conexion_internet"] = False
        
        # Obtener IP local principal
        try:
            if_addrs = psutil.net_if_addrs()
            ip_local = "No disponible"
            
            for interface_name, interface_addresses in if_addrs.items():
                # Buscar interfaz principal (no loopback)
                if interface_name.lower() not in ['lo', 'loopback']:
                    for addr in interface_addresses:
                        if addr.family == socket.AF_INET and not addr.address.startswith('127.'):
                            ip_local = addr.address
                            break
                    if ip_local != "No disponible":
                        break
            
            info_red["ip_local"] = ip_local
        except Exception:
            info_red["ip_local"] = "No disponible"
            
        return info_red

    @staticmethod
    def generar_diagnostico(detalles_error, correo_destino=None):
        """Generar diagnóstico que incluye validación de dominios"""
        # Si no hay errores Y hay correo destino, validar dominio
        if correo_destino and (not detalles_error or detalles_error == "No hay detalles de error"):
            es_sospechoso, mensaje_dominio = EstadoCorreo.validar_dominio_correo(correo_destino)
            if es_sospechoso:
                return mensaje_dominio
        
        # Si no hay errores y el dominio está bien
        if not detalles_error:
            return "No se detectaron errores"
        
        # Diagnosticar errores comunes
        detalles_lower = detalles_error.lower()
        
        diagnosticos = {
            "timeout|tiempo|agotado": "Tiempo de espera agotado. Posible conexión lenta o inestable.",
            "connection|conexión|socket|network|red": "Problema de conexión a internet o red inestable.",
            "refused|rechazado|unreachable": "Conexión rechazada. Posible bloqueo por firewall o servidor caído.",
            "autenticación|authentication|login|password": "Error de autenticación. Revisar credenciales de correo.",
            "smtp": "Error en el servidor SMTP de correo.",
            "archivo|file|no encontrado|not found": "Error con el archivo o su ubicación.",
            "omitido": "Archivo omitido del procesamiento según criterios de filtrado."
        }
        
        for palabras_clave, diagnostico in diagnosticos.items():
            if any(palabra in detalles_lower for palabra in palabras_clave.split('|')):
                return diagnostico
        
        return "Error desconocido"
    
    @staticmethod
    def validar_dominio_correo(correo_destino):
        """Valida si el dominio del correo tiene errores tipográficos comunes"""
        if not correo_destino or '@' not in correo_destino:
            return False, None
        
        dominio = correo_destino.split('@')[1].lower()
        
        # Dominios populares y sus variantes tipográficas comunes
        dominios_populares = {
            'gmail.com': ['gmai.com', 'gmial.com', 'gmail.co', 'gmal.com', 'gmil.com', 'gmail.con'],
            'hotmail.com': ['hotmai.com', 'hotmial.com', 'hotmal.com', 'hotmil.com', 'hotmail.co'],
            'outlook.com': ['outlok.com', 'outloo.com', 'outlook.co', 'outluk.com'],
            'yahoo.com': ['yaho.com', 'yahoo.co', 'yhoo.com', 'yahu.com'],
            'icloud.com': ['iclod.com', 'icloud.co', 'icoud.com'],
            'live.com': ['liv.com', 'live.co', 'liev.com']
        }
        
        for dominio_correcto, variantes in dominios_populares.items():
            if dominio in variantes:
                return True, f"Posible error tipográfico en dominio. ¿Quiso decir '{dominio_correcto}'?"
        
        return False, None

    @staticmethod
    def generar_estado(codigo_archivo, estado="ERROR", detalles_error=None, pdf_path=None, correo_origen=None):
        try:
            if not codigo_archivo:
                logging.error("No se proporcionó un código de archivo válido")
                return False
                
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            enviador = EnviadorCorreo()
            correo_destino = enviador.obtener_correo_por_codigo(codigo_archivo)
            id_transaccion = str(uuid.uuid4())[:8]
            
            diagnostico = EstadoCorreo.generar_diagnostico(detalles_error, correo_destino)
            
            # Obtener información de red solo si hay error
            info_red = {}
            if estado == "ERROR":
                info_red = EstadoCorreo.verificar_estado_red()
                estado_conexion = "CONECTADO" if info_red.get("conexion_internet", False) else "DESCONECTADO"
            else:
                estado_conexion = "N/A"
            
            # Tamaño del archivo PDF
            tamano_pdf = "N/A"
            if pdf_path and os.path.exists(pdf_path):
                tamano_pdf = f"{os.path.getsize(pdf_path) / 1024:.2f} KB"
            
            # Crear directorio de estados si no existe
            os.makedirs(ESTADO_DIR, exist_ok=True)
            
            # Generar registro detallado
            archivo_individual = os.path.join(ESTADO_DIR, f"registro_{codigo_archivo}.txt")
            hostname = platform.node()
            sistema_operativo = f"{platform.system()} {platform.version()}"
            
            registro_detallado = (
                f"Archivo: {codigo_archivo}\n"
                f"Fecha De Envio: {timestamp}\n"
                f"Estado: {estado}\n"
                f"Correo destino: {correo_destino if correo_destino else 'No encontrado'}\n"
                f"Detalles error: {detalles_error if detalles_error else 'No hay detalles de error'}\n"
                f"Diagnóstico: {diagnostico}\n"
                f"Estado conexión: {estado_conexion}\n"
            )
            
            # Información de red simplificada para errores
            if estado == "ERROR" and info_red:
                registro_detallado += (
                    f"Información de red:\n"
                    f"  Internet: {'Disponible' if info_red.get('conexion_internet', False) else 'No disponible'}\n"
                    f"  IP Local: {info_red.get('ip_local', 'No disponible')}\n"
                )
            
            registro_detallado += (
                f"Ruta PDF: {pdf_path if pdf_path else 'No se encontró la ruta del PDF'}\n"
                f"Correo origen: {correo_origen if correo_origen else 'N/A'}\n"
                f"Tamaño PDF: {tamano_pdf}\n"
                f"ID transacción: {id_transaccion}\n"
                f"Sistema: {hostname} - {sistema_operativo}\n"
            )
            
            # Guardar registro individual
            with open(archivo_individual, 'w', encoding='utf-8') as file:
                file.write(registro_detallado)
            
            # Actualizar registro general
            estado_correos_path = os.path.join(ESTADO_DIR, "estado_correos.txt")
            encabezado = " ARCHIVO    || FECHA ENVÍO         || ESTADO  || DIAGNÓSTICO\n"
            separador = "=" * 100 + "\n"
            nuevo_registro = f"{codigo_archivo.ljust(10)} || {timestamp} || {estado.ljust(8)} || {diagnostico}\n"
            
            registros_acumulados = []
            
            # Leer registros existentes
            if os.path.exists(estado_correos_path):
                try:
                    with open(estado_correos_path, 'r', encoding='utf-8') as file:
                        lineas = file.readlines()
                        if len(lineas) > 2:
                            registros_acumulados = lineas[2:]
                except Exception as e:
                    logging.warning(f"Error leyendo registros previos: {e}")
            
            registros_acumulados.insert(0, nuevo_registro)
            
            # Escribir registro actualizado
            with open(estado_correos_path, 'w', encoding='utf-8') as file:
                file.write(encabezado)
                file.write(separador)
                file.writelines(registros_acumulados)

            logging.info(f"Registro guardado para {codigo_archivo}, ID: {id_transaccion}")
            return True

        except Exception as e:
            logging.error(f"Error al generar registro de estado: {e}")
            # Registro de emergencia
            try:
                os.makedirs(ESTADO_DIR, exist_ok=True)
                error_log_path = os.path.join(ESTADO_DIR, "errores_registro.log")
                with open(error_log_path, 'a', encoding='utf-8') as error_file:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    error_file.write(f"{timestamp} - Error al registrar '{codigo_archivo}': {e}\n")
            except Exception:
                pass
            return False