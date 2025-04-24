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
        """Verifica el estado de la red y devuelve información de diagnóstico"""
        info_red = {}
        
        # Comprobar si hay conexión a internet
        try:
            # Intenta hacer ping a Google DNS
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            info_red["conexion_internet"] = True
        except (socket.error, socket.timeout):
            info_red["conexion_internet"] = False
        
        # Información de interfaces de red
        if_addrs = psutil.net_if_addrs()
        interfaces_activas = []
        
        for interface_name, interface_addresses in if_addrs.items():
            for addr in interface_addresses:
                if addr.family == socket.AF_INET:  # IPv4
                    interfaces_activas.append({
                        "nombre": interface_name,
                        "direccion": addr.address,
                    })
        
        info_red["interfaces"] = interfaces_activas
        
        # Estadísticas de red
        try:
            net_io = psutil.net_io_counters()
            info_red["bytes_enviados"] = net_io.bytes_sent
            info_red["bytes_recibidos"] = net_io.bytes_recv
        except:
            pass
            
        return info_red

    @staticmethod
    def generar_diagnostico(detalles_error):
        """Genera un diagnóstico basado en el tipo de error"""
        if not detalles_error:
            return "No se detectaron errores"
        
        diagnostico = "Error desconocido"
        detalles_lower = detalles_error.lower()
        
        # Detectar tipos específicos de error
        if any(palabra in detalles_lower for palabra in ["timeout", "tiempo", "agotado"]):
            diagnostico = "Tiempo de espera agotado. Posible conexión lenta o inestable."
        elif any(palabra in detalles_lower for palabra in ["connection", "conexión", "socket", "network", "red"]):
            diagnostico = "Problema de conexión a internet o red inestable."
        elif any(palabra in detalles_lower for palabra in ["refused", "rechazado", "unreachable"]):
            diagnostico = "Conexión rechazada. Posible bloqueo por firewall o servidor caído."
        elif any(palabra in detalles_lower for palabra in ["autenticación", "authentication", "login", "password"]):
            diagnostico = "Error de autenticación. Revisar credenciales de correo."
        elif any(palabra in detalles_lower for palabra in ["smtp"]):
            diagnostico = "Error en el servidor SMTP de correo."
        elif any(palabra in detalles_lower for palabra in ["archivo", "file", "no encontrado", "not found"]):
            diagnostico = "Error con el archivo o su ubicación."
        
        return diagnostico

    @staticmethod
    def generar_estado(codigo_archivo, estado="ERROR", detalles_error=None, pdf_path=None, correo_origen=None):
        """Genera archivos de estado para el procesamiento de correos."""
        try:
            print(f"CODIGO ARCHIVO: {codigo_archivo}, ESTADO: {estado}, DETALLES: {detalles_error}, PDF: {pdf_path}, CORREO ORIGEN: {correo_origen}")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            enviador = EnviadorCorreo()
            correo_destino = enviador.obtener_correo_por_codigo(codigo_archivo)
            id_transaccion = str(uuid.uuid4())[:8]  # ID único para seguimiento
            
            # Generar diagnóstico detallado
            diagnostico = EstadoCorreo.generar_diagnostico(detalles_error)
            
            # Obtener información de red si hay error
            info_red = {}
            if estado == "ERROR":
                info_red = EstadoCorreo.verificar_estado_red()
                estado_conexion = "CONECTADO" if info_red.get("conexion_internet", False) else "DESCONECTADO"
            else:
                estado_conexion = "N/A"
            
            # Tamaño del archivo PDF en KB si existe
            tamano_pdf = "N/A"
            if pdf_path and os.path.exists(pdf_path):
                tamano_pdf = f"{os.path.getsize(pdf_path) / 1024:.2f} KB"
            
            # Crear directorio de estados si no existe
            os.makedirs(ESTADO_DIR, exist_ok=True)
            
            # 1. Generar archivo individual para este correo específico
            archivo_individual = os.path.join(ESTADO_DIR, f"registro_{codigo_archivo}.txt")
            
            # Información del sistema
            hostname = platform.node()
            sistema_operativo = f"{platform.system()} {platform.version()}"
            
            # Formato del registro detallado individual
            registro_detallado = (
                f"Archivo: {codigo_archivo}\n"
                f"Fecha De Envio: {timestamp}\n"
                f"Estado: {estado}\n"
                f"Correo destino: {correo_destino if correo_destino else 'No encontrado'}\n"
                f"Detalles error: {detalles_error if detalles_error else 'No hay detalles de error'}\n"
                f"Diagnóstico: {diagnostico}\n"
                f"Estado conexión: {estado_conexion}\n"
            )
            
            # Añadir información de red si hay error
            if estado == "ERROR" and info_red:
                interfaces = "\n  ".join([f"{i['nombre']}: {i['direccion']}" for i in info_red.get("interfaces", [])])
                registro_detallado += (
                    f"Información de red:\n"
                    f"  Conexión a internet: {'Disponible' if info_red.get('conexion_internet', False) else 'No disponible'}\n"
                    f"  Interfaces de red:\n  {interfaces if interfaces else 'No hay interfaces con IPv4 disponibles'}\n"
                )
            
            # Continuar con el resto de la información
            registro_detallado += (
                f"Ruta PDF: {pdf_path if pdf_path else 'No se encontró la ruta del PDF'}\n"
                f"Correo origen: {correo_origen if correo_origen else 'N/A'}\n"
                f"Tamaño PDF: {tamano_pdf}\n"
                f"ID transacción: {id_transaccion}\n"
                f"Sistema: {hostname} - {sistema_operativo}\n"
            )
            
            # Guardar el registro individual
            with open(archivo_individual, 'w', encoding='utf-8') as file:
                file.write(registro_detallado)
            
            # 2. Actualizar archivo general de estado_correos.txt
            estado_correos_path = os.path.join(ESTADO_DIR, "estado_correos.txt")

            encabezado = " ARCHIVO    || FECHA ENVÍO         || ESTADO  || DIAGNÓSTICO\n"
            separador = "=" * 100 + "\n"
            
            # Formato resumido para el archivo general
            nuevo_registro = f"{codigo_archivo} || {timestamp} || {estado} || {diagnostico}\n"
            
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