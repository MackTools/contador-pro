# cloud_manager.py - Módulo de sincronización con la nube

import requests
import json
from datetime import datetime
import hashlib

class CloudManager:
    def __init__(self):
        self.api_base = "https://api.contaduria.com/v1"  # URL de tu API (puedes cambiarla)
        self.token = None
        self.usuario_actual = None
        self.modo_offline = False
    
    def crear_sesion(self):
        """Inicializa la sesión (modo offline por defecto)"""
        self.token = None
        self.usuario_actual = None
        self.modo_offline = True
    
    def login(self, email, password):
        """Inicia sesión en la nube"""
        try:
            # Para desarrollo/testing, aceptamos cualquier credencial
            # En producción, conectar con MongoDB Atlas real
            if email and password:
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                # Simulación de login exitoso
                self.token = "demo_token_12345"
                self.usuario_actual = {"email": email, "nombre": email.split('@')[0]}
                self.modo_offline = False
                return True, self.usuario_actual
            else:
                return False, "Credenciales inválidas"
        except Exception as e:
            return False, str(e)
    
    def registrar_usuario(self, email, password, nombre):
        """Registra un nuevo usuario"""
        try:
            if email and password and nombre:
                if len(password) >= 6:
                    # Simulación de registro exitoso
                    return True, "Usuario registrado exitosamente"
                else:
                    return False, "La contraseña debe tener al menos 6 caracteres"
            else:
                return False, "Complete todos los campos"
        except Exception as e:
            return False, str(e)
    
    def guardar_proyecto(self, nombre, tipo, datos, columnas, callback=None):
        """Guarda un proyecto en la nube"""
        if self.modo_offline or not self.token:
            if callback:
                callback(False, "Modo offline - no se sincronizó")
            return False
        
        try:
            # Simulación de guardado exitoso
            if callback:
                callback(True, "Proyecto sincronizado")
            return True
        except Exception as e:
            if callback:
                callback(False, str(e))
            return False
    
    def eliminar_proyecto(self, nombre):
        """Elimina un proyecto de la nube"""
        if self.modo_offline or not self.token:
            return False
        try:
            # Simulación de eliminación exitosa
            return True
        except:
            return False
    
    def obtener_proyectos(self):
        """Obtiene todos los proyectos del usuario"""
        if self.modo_offline or not self.token:
            return []
        try:
            # Retornar lista vacía en modo demo
            return []
        except:
            return []
