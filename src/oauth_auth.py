import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta
import msal

class OAuthHandler:
    def __init__(self, credenciales_path, tokens_path):
        self.credenciales_path = credenciales_path
        self.tokens_path = tokens_path
        self.credenciales = self._cargar_json(credenciales_path)
        self.tokens = self._cargar_json(tokens_path)
     
    def _cargar_json(self, ruta):
        try:
            if os.path.exists(ruta):
                with open(ruta, 'r') as f:
                    return json.load(f)
            else:
                # Si el archivo de tokens no existe, crear estructura inicial
                if ruta == self.tokens_path:
                    datos_iniciales = {"correos": []}
                    self._guardar_json(ruta, datos_iniciales)
                    return datos_iniciales
                logging.error(f"Archivo no encontrado: {ruta}")
                return {}
        except Exception as e:
            logging.error(f"Error cargando JSON {ruta}: {e}")
            return {}
    
    def _guardar_json(self, ruta, datos):
        try:
            with open(ruta, 'w') as f:
                json.dump(datos, f, indent=4)
            return True
        except Exception as e:
            logging.error(f"Error guardando JSON {ruta}: {e}")
            return False
    
    def _obtener_info_correo(self, email):
        """Busca la información de tokens para un email específico"""
        for cuenta in self.tokens.get("correos", []):
            if cuenta.get("email") == email:
                return cuenta
        return None
    
    def _actualizar_info_correo(self, email, access_token, refresh_token, expires_in):
        """Actualiza o agrega información de tokens para un email"""
        info_correo = self._obtener_info_correo(email)
        expires_at = int(time.time()) + expires_in
        
        if info_correo:
            # Actualizar información existente
            info_correo["access_token"] = access_token
            info_correo["refresh_token"] = refresh_token
            info_correo["expires_at"] = expires_at
        else:
            # Agregar nueva entrada
            nueva_info = {
                "email": email,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at
            }
            self.tokens["correos"].append(nueva_info)
        
        # Guardar cambios
        return self._guardar_json(self.tokens_path, self.tokens)
    
    def _token_expirado(self, info_correo):
        """Verifica si el token ha expirado"""
        if not info_correo or "expires_at" not in info_correo:
            return True
        
        # Agregar un margen de 5 minutos para evitar problemas de timing
        return time.time() > (info_correo["expires_at"] - 300)
    
    def obtener_token_valido(self, email):
        """Obtiene un token válido para el email especificado"""
        info_correo = self._obtener_info_correo(email)
        
        # Si no hay información o el token ha expirado, obtener uno nuevo
        if not info_correo or self._token_expirado(info_correo):
            if info_correo and "refresh_token" in info_correo:
                # Intentar renovar usando refresh token
                return self._renovar_token(email, info_correo["refresh_token"])
            else:
                # No hay refresh token, se necesita autenticación completa
                logging.warning(f"Se requiere autenticación manual para {email}")
                return self._autenticar_usuario(email)
        
        # El token actual es válido
        return info_correo["access_token"]
    
    def _renovar_token(self, email, refresh_token):
        """Renueva el token de acceso usando un refresh token"""
        try:
            app = msal.ConfidentialClientApplication(
                self.credenciales["client_id"],
                authority=f"https://login.microsoftonline.com/{self.credenciales.get('tenant_id', 'common')}",
                client_credential=self.credenciales["client_secret"]
            )
            
            resultado = app.acquire_token_by_refresh_token(
                refresh_token,
                scopes=self.credenciales["scope"].split()
            )
            
            if "access_token" in resultado:
                # Actualizar tokens en almacenamiento
                self._actualizar_info_correo(
                    email,
                    resultado["access_token"],
                    resultado.get("refresh_token", refresh_token),  # Usar el anterior si no viene uno nuevo
                    resultado.get("expires_in", 3600)
                )
                logging.info(f"Token renovado exitosamente para {email}")
                return resultado["access_token"]
            else:
                logging.error(f"Error renovando token: {resultado.get('error_description', 'Sin descripción')}")
                # Si falla la renovación, intentar autenticación completa
                return self._autenticar_usuario(email)
                
        except Exception as e:
            logging.error(f"Error en renovación de token: {e}")
            return None
    
    def _autenticar_usuario(self, email):
        """Realiza el flujo de autenticación completo"""
        try:
            app = msal.PublicClientApplication(
                self.credenciales["client_id"],
                authority=f"https://login.microsoftonline.com/{self.credenciales.get('tenant_id', 'common')}"
            )
            
            # Para aplicaciones de línea de comandos, lo mejor es usar el flujo de código de dispositivo
            flow = app.initiate_device_flow(scopes=self.credenciales["scope"].split())
            
            if "user_code" not in flow:
                logging.error(f"Error iniciando flujo de autenticación: {flow.get('error_description')}")
                return None
            
            # Mostrar instrucciones al usuario
            print(flow["message"])
            
            # Esperar a que el usuario complete la autenticación
            resultado = app.acquire_token_by_device_flow(flow)
            
            if "access_token" in resultado:
                # Guardar tokens
                self._actualizar_info_correo(
                    email,
                    resultado["access_token"],
                    resultado.get("refresh_token", ""),
                    resultado.get("expires_in", 3600)
                )
                logging.info(f"Autenticación exitosa para {email}")
                return resultado["access_token"]
            else:
                logging.error(f"Error en autenticación: {resultado.get('error_description', 'Sin descripción')}")
                return None
                
        except Exception as e:
            logging.error(f"Error en autenticación: {e}")
            return None