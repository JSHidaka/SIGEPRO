import pandas as pd
import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect('sigegprodb.db')
c = conn.cursor()

# Leer el archivo Excel
excel_file = 'estructura.xlsx'

# Verificar las hojas disponibles
xls = pd.ExcelFile(excel_file)
print("Hojas disponibles:", xls.sheet_names)

# Exportar datos de la hoja 'Proyectos' a la tabla Proyectos
try:
    df_proyectos = pd.read_excel(excel_file, sheet_name='Proyectos')
    df_proyectos.to_sql('Proyectos', conn, if_exists='append', index=False)
except ValueError as e:
    print(f"Error al leer la hoja 'Proyectos': {e}")

# Exportar datos de la hoja 'Talleres' a la tabla Talleres
try:
    df_talleres = pd.read_excel(excel_file, sheet_name='Talleres')
    df_talleres.to_sql('Talleres', conn, if_exists='append', index=False)
except ValueError as e:
    print(f"Error al leer la hoja 'Talleres': {e}")

# Exportar datos de la hoja 'Reportes' a la tabla Reportes
try:
    df_reportes = pd.read_excel(excel_file, sheet_name='Reportes')
    df_reportes.to_sql('Reportes', conn, if_exists='append', index=False)
except ValueError as e:
    print(f"Error al leer la hoja 'Reportes': {e}")

# Exportar datos de la hoja 'Cubicaciones' a la tabla Cubicaciones
try:
    df_cubicaciones = pd.read_excel(excel_file, sheet_name='Cubicaciones')
    df_cubicaciones.to_sql('Cubicaciones', conn, if_exists='append', index=False)
except ValueError as e:
    print(f"Error al leer la hoja 'Cubicaciones': {e}")

# Cerrar la conexión
conn.close()