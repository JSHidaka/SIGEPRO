import sqlite3

# Conectar a la base de datos (o crearla si no existe)
conn = sqlite3.connect('sigegprodb.db')
c = conn.cursor()

# Crear la tabla Proyectos
c.execute('''
    CREATE TABLE Proyectos (
        ID_Proyecto INTEGER PRIMARY KEY AUTOINCREMENT,
        Oferente TEXT,
        Contrato TEXT UNIQUE
    )
''')

# Crear la tabla Talleres
c.execute('''
    CREATE TABLE Talleres (
        ID_Talleres INTEGER PRIMARY KEY AUTOINCREMENT,
        Contrato TEXT,
        Zonagpro TEXT,
        Lote TEXT,
        Item TEXT,
        Provincia TEXT,
        Municipio TEXT,
        Sectores TEXT,
        Ejecucion TEXT,
        Porcientoeje REAL,
        Comentarios TEXT,
        Montoitem REAL,
        Longitud REAL,
        Latitud REAL,
        FOREIGN KEY (Contrato) REFERENCES Proyectos (Contrato)
    )
''')

# Crear la tabla Reportes
c.execute('''
    CREATE TABLE Reportes (
        ID_Reporte INTEGER PRIMARY KEY AUTOINCREMENT,
        ID_Talleres INTEGER,
        ID_Proyecto INTEGER,
        Fecha_Reporte TEXT,
        Descripción TEXT,
        Imagen_1 BLOB,
        Imagen_2 BLOB,
        Imagen_3 BLOB,
        Imagen_4 BLOB,
        FOREIGN KEY (ID_Talleres) REFERENCES Talleres (ID_Talleres),
        FOREIGN KEY (ID_Proyecto) REFERENCES Proyectos (ID_Proyecto)
    )
''')

# Crear la tabla Cubicaciones
c.execute('''
    CREATE TABLE Cubicaciones (
        ID_Cubicacion INTEGER PRIMARY KEY AUTOINCREMENT,
        ID_Talleres INTEGER,
        ID_Proyecto INTEGER,
        Fecha_Cubicacion TEXT,
        Fecha_Firma TEXT,
        Aceras REAL,
        Contenes REAL,
        MontoBruto REAL,
        FOREIGN KEY (ID_Talleres) REFERENCES Talleres (ID_Talleres),
        FOREIGN KEY (ID_Proyecto) REFERENCES Proyectos (ID_Proyecto)
    )
''')

# Guardar los cambios y cerrar la conexión
conn.commit()
conn.close()