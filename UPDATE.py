import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect('sigegprodb.db')
cursor = conn.cursor()

# Definir los coordinadores y supervisores por zona
zonas = {
    'Zona I': ('WIILDER GUANTE REINOSO', 'WIILDER GUANTE REINOSO'),
    'Zona II': ('VICTOR JAQUEZ', 'VICTOR JAQUEZ'),
    'Zona III': ('ANGEL OGANDO', 'ANGEL OGANDO'),
    'Zona IV': ('JACINTO DIAZ', 'JACINTO DIAZ'),
    'Zona V': ('WALDY CAMACHO', 'WALDY CAMACHO'),
    'Zona VI': ('ILONCA JUSTO', 'ILONCA JUSTO')
}

# Obtener los registros con campos vacíos de coordinador o supervisor
cursor.execute("""
    SELECT ID_Talleres, Zonagpro 
    FROM Talleres 
    WHERE Coordinador IS NULL OR Supervisor IS NULL
""")
talleres = cursor.fetchall()

# Actualizar los registros
for taller in talleres:
    id_talleres, zonagpro = taller
    if zonagpro in zonas:
        coordinador, supervisor = zonas[zonagpro]
        cursor.execute("""
            UPDATE Talleres
            SET Coordinador = ?, Supervisor = ?
            WHERE ID_Talleres = ?
        """, (coordinador, supervisor, id_talleres))

# Confirmar los cambios
conn.commit()

# Cerrar la conexión
conn.close()

print("Los campos vacíos de coordinador y supervisor han sido actualizados correctamente.")
