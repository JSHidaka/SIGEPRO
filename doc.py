import sqlite3

conn = sqlite3.connect('sigegprodb.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS Documentos (
    ID_Documento INTEGER PRIMARY KEY AUTOINCREMENT,
    Contrato TEXT,
    AContratoBase TEXT,
    ACertBase TEXT,
    APresBase TEXT,
    AContratoAdenda TEXT,
    ACertAdenda TEXT,
    APresAdenda TEXT,
    FOREIGN KEY (Contrato) REFERENCES Proyectos (Contrato)
)
''')

conn.commit()
conn.close()
