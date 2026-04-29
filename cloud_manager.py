# cloud_manager.py - COMPLETO con AUTH y DATA API

import requests
import json
from tkinter import messagebox
import hashlib

class CloudManager:
    def __init__(self):
        # ⚠️ REEMPLAZA ESTOS VALORES con los tuyos de MongoDB Atlas
        self.APP_ID = "data-xxxxx"  # Tu App ID de MongoDB Atlas
        self.API_KEY = "tu-api-key-aqui"  # Tu API Key
        self.CLUSTER = "Cluster0"
        self.DATABASE = "contador_pro"
        
        self.url = f"https://data.mongodb-api.com/app/{self.APP_ID}/endpoint/data/v1"
        self.headers = {
            "api-key": self.API_KEY,
            "Content-Type": "application/json"
        }
        
        self.usuario_actual = None
        
    def _request(self, action, collection, **kwargs):
        """Método base para todas las peticiones a MongoDB Data API"""
        payload = {
            "dataSource": self.CLUSTER,
            "database": self.DATABASE,
            "collection": collection
        }
        payload.update(kwargs)
        
        try:
            response = requests.post(
                f"{self.url}/action/{action}",
                json=payload,
                headers=self.headers,
                timeout=15
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    # ========== AUTENTICACIÓN DE USUARIOS ==========
    
    def registrar_usuario(self, email, password, nombre):
        """Registra un nuevo usuario en la nube"""
        # Hash de contraseña (nunca guardes texto plano)
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Verificar si el usuario ya existe
        existe = self._request("findOne", "usuarios", filter={"email": email})
        
        if existe.get("document"):
            return False, "El usuario ya existe"
        
        # Crear nuevo usuario
        nuevo_usuario = {
            "email": email,
            "password": password_hash,
            "nombre": nombre,
            "proyectos": [],  # Lista de IDs de proyectos
            "creado_en": self._fecha_actual()
        }
        
        resultado = self._request("insertOne", "usuarios", document=nuevo_usuario)
        
        if resultado.get("insertedId"):
            return True, "Usuario creado exitosamente"
        return False, "Error al crear usuario"
    
    def login(self, email, password):
        """Autentica un usuario existente"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        resultado = self._request("findOne", "usuarios", filter={
            "email": email,
            "password": password_hash
        })
        
        if resultado.get("document"):
            self.usuario_actual = resultado["document"]
            return True, self.usuario_actual
        return False, "Credenciales incorrectas"
    
    def logout(self):
        """Cierra sesión del usuario actual"""
        self.usuario_actual = None
        return True
    
    # ========== GESTIÓN DE PROYECTOS ==========
    
    def guardar_proyecto(self, nombre, tipo, datos, columnas, callback=None):
        """Guarda un proyecto asociado al usuario actual"""
        if not self.usuario_actual:
            if callback:
                callback(False, "Debes iniciar sesión primero")
            return False
        
        email = self.usuario_actual["email"]
        
        proyecto = {
            "nombre": nombre,
            "tipo": tipo,
            "datos": datos,
            "columnas": columnas,
            "email_usuario": email,
            "ultima_modificacion": self._fecha_actual()
        }
        
        # Buscar si ya existe
        existe = self._request("findOne", "proyectos", filter={
            "nombre": nombre,
            "email_usuario": email
        })
        
        if existe.get("document"):
            # Actualizar
            resultado = self._request("updateOne", "proyectos", 
                                     filter={"nombre": nombre, "email_usuario": email},
                                     update={"$set": proyecto})
            success = "modifiedCount" in str(resultado)
        else:
            # Insertar nuevo
            resultado = self._request("insertOne", "proyectos", document=proyecto)
            success = resultado.get("insertedId") is not None
            
            # Agregar al array de proyectos del usuario
            self._request("updateOne", "usuarios",
                         filter={"email": email},
                         update={"$addToSet": {"proyectos": nombre}})
        
        if callback:
            callback(success, "Guardado" if success else "Error")
        return success
    
    def cargar_proyectos(self, callback=None):
        """Carga todos los proyectos del usuario actual"""
        if not self.usuario_actual:
            if callback:
                callback(False, [])
            return []
        
        email = self.usuario_actual["email"]
        
        resultado = self._request("find", "proyectos", 
                                 filter={"email_usuario": email},
                                 limit=100)
        
        proyectos = resultado.get("documents", [])
        
        if callback:
            callback(True, proyectos)
        return proyectos
    
    def eliminar_proyecto(self, nombre):
        """Elimina un proyecto del usuario actual"""
        if not self.usuario_actual:
            return False
        
        email = self.usuario_actual["email"]
        
        resultado = self._request("deleteOne", "proyectos", 
                                 filter={"nombre": nombre, "email_usuario": email})
        
        # Eliminar del array del usuario
        self._request("updateOne", "usuarios",
                     filter={"email": email},
                     update={"$pull": {"proyectos": nombre}})
        
        return "deletedCount" in str(resultado)
    
    def compartir_proyecto(self, nombre, email_compartir):
        """Comparte un proyecto con otro usuario"""
        resultado = self._request("updateOne", "proyectos",
                                 filter={"nombre": nombre, "email_usuario": self.usuario_actual["email"]},
                                 update={"$addToSet": {"compartido_con": email_compartir}})
        return resultado.get("modifiedCount", 0) > 0
    
    def _fecha_actual(self):
        from datetime import datetime
        return datetime.now().isoformat()