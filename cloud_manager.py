# cloud_manager.py - Versión con PyMongo (RECOMENDADA)

import pymongo
import hashlib
from datetime import datetime
import threading

class CloudManager:
    def __init__(self):
        # ⚠️ REEMPLAZA ESTA CADENA con la que copiaste de MongoDB Atlas
        # Formato: mongodb+srv://USUARIO:CONTRASEÑA@cluster0.xxxxx.mongodb.net/
        self.MONGO_URI = "mongodb+srv://contador_user:<db_password>@cluster0.fhvaqrj.mongodb.net/?appName=Cluster0"
        
        self.DB_NAME = "contador_pro"
        self.usuario_actual = None
        self.client = None
        
        self._conectar()
    
    def _conectar(self):
        """Conecta a MongoDB Atlas"""
        try:
            self.client = pymongo.MongoClient(self.MONGO_URI)
            # Probar conexión
            self.client.admin.command('ping')
            print("✓ Conectado a MongoDB Atlas")
            return True
        except Exception as e:
            print(f"✗ Error de conexión: {e}")
            return False
    
    def _get_db(self):
        """Obtiene la base de datos"""
        if self.client is None:
            self._conectar()
        return self.client[self.DB_NAME]
    
    # ========== AUTENTICACIÓN ==========
    
    def registrar_usuario(self, email, password, nombre):
        """Registra un nuevo usuario"""
        db = self._get_db()
        usuarios = db.usuarios
        
        # Verificar si ya existe
        if usuarios.find_one({"email": email}):
            return False, "El usuario ya existe"
        
        # Hash de contraseña
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Crear usuario
        nuevo_usuario = {
            "email": email,
            "password": password_hash,
            "nombre": nombre,
            "proyectos": [],
            "creado_en": datetime.now()
        }
        
        try:
            usuarios.insert_one(nuevo_usuario)
            return True, "Usuario creado exitosamente"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def login(self, email, password):
        """Inicia sesión"""
        db = self._get_db()
        usuarios = db.usuarios
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        usuario = usuarios.find_one({
            "email": email,
            "password": password_hash
        })
        
        if usuario:
            # Convertir ObjectId a string para serialización
            usuario["_id"] = str(usuario["_id"])
            self.usuario_actual = usuario
            return True, usuario
        return False, "Credenciales incorrectas"
    
    def logout(self):
        """Cierra sesión"""
        self.usuario_actual = None
        return True
    
    # ========== GESTIÓN DE PROYECTOS ==========
    
    def guardar_proyecto(self, nombre, tipo, datos, columnas, callback=None):
        """Guarda un proyecto en la nube"""
        if not self.usuario_actual:
            if callback:
                callback(False, "Debes iniciar sesión primero")
            return False
        
        db = self._get_db()
        proyectos = db.proyectos
        
        proyecto = {
            "nombre": nombre,
            "tipo": tipo,
            "datos": datos,
            "columnas": columnas,
            "email_usuario": self.usuario_actual["email"],
            "ultima_modificacion": datetime.now()
        }
        
        try:
            # Buscar si ya existe
            existe = proyectos.find_one({
                "nombre": nombre,
                "email_usuario": self.usuario_actual["email"]
            })
            
            if existe:
                # Actualizar
                proyectos.update_one(
                    {"_id": existe["_id"]},
                    {"$set": proyecto}
                )
            else:
                # Insertar nuevo
                proyectos.insert_one(proyecto)
                # Actualizar lista de proyectos del usuario
                db.usuarios.update_one(
                    {"email": self.usuario_actual["email"]},
                    {"$addToSet": {"proyectos": nombre}}
                )
            
            if callback:
                callback(True, "Guardado en la nube")
            return True
            
        except Exception as e:
            if callback:
                callback(False, str(e))
            return False
    
    def cargar_proyectos(self, callback=None):
        """Carga todos los proyectos del usuario actual"""
        if not self.usuario_actual:
            if callback:
                callback(False, [])
            return []
        
        db = self._get_db()
        proyectos = db.proyectos
        
        try:
            resultados = proyectos.find({
                "email_usuario": self.usuario_actual["email"]
            })
            
            proyectos_lista = []
            for proy in resultados:
                proy["_id"] = str(proy["_id"])
                proyectos_lista.append(proy)
            
            if callback:
                callback(True, proyectos_lista)
            return proyectos_lista
            
        except Exception as e:
            if callback:
                callback(False, [])
            return []
    
    def eliminar_proyecto(self, nombre):
        """Elimina un proyecto"""
        if not self.usuario_actual:
            return False
        
        db = self._get_db()
        
        try:
            db.proyectos.delete_one({
                "nombre": nombre,
                "email_usuario": self.usuario_actual["email"]
            })
            
            # Eliminar de la lista del usuario
            db.usuarios.update_one(
                {"email": self.usuario_actual["email"]},
                {"$pull": {"proyectos": nombre}}
            )
            
            return True
        except Exception as e:
            print(f"Error al eliminar: {e}")
            return False
    
    def crear_sesion(self):
        """Método para compatibilidad con código existente"""
        return self._conectar()