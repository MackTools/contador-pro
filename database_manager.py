import os
import sqlite3
import ast

class DBManager:
    @staticmethod
    def conectar():
        # Obtiene la ruta de la carpeta donde está este archivo .py
        ruta_base = os.path.dirname(os.path.abspath(__file__))
        ruta_db = os.path.join(ruta_base, 'contabilidad_pro.db')
        return sqlite3.connect(ruta_db)

    @staticmethod
    def inicializar():
        with DBManager.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS proyectos (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                nombre TEXT UNIQUE,
                                datos TEXT,
                                tipo TEXT)''')
            # Lógica de emergencia: Intenta agregar la columna si no existe
            try:
                cursor.execute("ALTER TABLE proyectos ADD COLUMN tipo TEXT")
            except:
                pass # Si ya existe, no hace nada
            conn.commit()

    @staticmethod
    def guardar_proyecto(nombre, filas, tipo_tabla):
        with DBManager.conectar() as conn:
            cursor = conn.cursor()
            # Convertimos la lista de listas a un texto (string) para guardarlo fácil
            datos_str = str(filas)
            cursor.execute('''INSERT OR REPLACE INTO proyectos (nombre, datos, tipo) 
                              VALUES (?, ?, ?)''', (nombre, datos_str, tipo_tabla))
            conn.commit()

    @staticmethod
    def obtener_todos_los_proyectos():
        with DBManager.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT nombre, tipo FROM proyectos")
            return cursor.fetchall()

    @staticmethod
    def obtener_datos_proyecto(nombre):
        with DBManager.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT datos FROM proyectos WHERE nombre = ?", (nombre,))
            res = cursor.fetchone()
            if res and res[0]:
                # Convertimos el texto de vuelta a una lista de Python
                return ast.literal_eval(res[0])
            return []

    @staticmethod
    def eliminar_proyecto(nombre):
        with DBManager.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM proyectos WHERE nombre = ?", (nombre,))
            conn.commit()