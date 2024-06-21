import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect('sigegprodb.db')
cursor = conn.cursor()

# Obtener la lista de tablas en la base de datos
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# Obtener el esquema de la tabla 'Reportes' si existe
schema_reportes = None
if ('Reportes',) in tables:
    cursor.execute("PRAGMA table_info(Reportes)")
    schema_reportes = cursor.fetchall()

# Cerrar la conexión
conn.close()

tables, schema_reportes