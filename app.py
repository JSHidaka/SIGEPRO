from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory, make_response
from werkzeug.utils import secure_filename
from flask_weasyprint import HTML, render_pdf, CSS
import sqlite3
import os
import pandas as pd

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

def get_db_connection():
    conn = sqlite3.connect('sigegprodb.db')
    conn.row_factory = sqlite3.Row
    return conn

# Filtro personalizado para formatear números con símbolo de dólar
@app.template_filter('number_format')
def number_format(value):
    return "${:,.2f}".format(value)

# Filtro personalizado para formatear números sin símbolo de dólar
@app.template_filter('number_format_no_dollar')
def number_format_no_dollar(value):
    return "{:,.2f}".format(value)

@app.route('/')
def inicio():
    return render_template('inicio.html')

@app.route('/proyectos')
def index():
    conn = get_db_connection()
    proyectos = conn.execute('SELECT * FROM Proyectos').fetchall()
    conn.close()
    return render_template('proyectos.html', proyectos=proyectos)

@app.route('/talleres/<contrato>')
def talleres(contrato):
    conn = get_db_connection()
    talleres = conn.execute('SELECT * FROM Talleres WHERE contrato = ?', (contrato,)).fetchall()
    monto_total = conn.execute('SELECT SUM(Montoitem) as monto_total FROM Talleres WHERE contrato = ?', (contrato,)).fetchone()['monto_total']
    cubicaciones = conn.execute('''
        SELECT c.*, t.Lote, t.Item FROM Cubicaciones c
        JOIN Talleres t ON c.ID_Talleres = t.ID_Talleres
        WHERE t.contrato = ?
    ''', (contrato,)).fetchall()
    
    totales = conn.execute('''
        SELECT 
            SUM(c.Aceras) as total_aceras, 
            SUM(c.Contenes) as total_contenes, 
            SUM(c.MontoBruto) as total_monto_bruto 
        FROM Cubicaciones c
        JOIN Talleres t ON c.ID_Talleres = t.ID_Talleres
        WHERE t.contrato = ?
    ''', (contrato,)).fetchone()
    
    conn.close()
    return jsonify({
        'talleres': [dict(taller) for taller in talleres],
        'monto_total': monto_total,
        'cubicaciones': [dict(cubicacion) for cubicacion in cubicaciones],
        'totales': dict(totales) if totales else {'total_aceras': 0, 'total_contenes': 0, 'total_monto_bruto': 0}
    })

@app.route('/talleres_por_contrato/<contrato>')
def talleres_por_contrato(contrato):
    conn = get_db_connection()
    talleres = conn.execute('SELECT * FROM Talleres WHERE contrato = ?', (contrato,)).fetchall()
    conn.close()
    return jsonify([dict(taller) for taller in talleres])

@app.route('/reportes/<int:taller_id>')
def get_reportes(taller_id):
    conn = get_db_connection()
    reportes = conn.execute('SELECT * FROM Reportes WHERE ID_Talleres = ?', (taller_id,)).fetchall()

    # Obtener el contrato del taller
    taller = conn.execute('SELECT contrato FROM Talleres WHERE ID_Talleres = ?', (taller_id,)).fetchone()
    contrato = taller['contrato'] if taller else None

    conn.close()

    reportes_dicts = []
    for reporte in reportes:
        reporte_dict = dict(reporte)
        reporte_id = reporte_dict['ID_Reporte']
        imagenes = []
        for i in range(1, 5):
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], contrato, str(reporte_id), f'{i}.jpg')
            if os.path.exists(image_path):
                imagenes.append(url_for('uploaded_file', filename=os.path.join(contrato, str(reporte_id), f'{i}.jpg')))
        reporte_dict['imagenes'] = imagenes
        reportes_dicts.append(reporte_dict)

    return jsonify(reportes_dicts)

@app.route('/ultimo_reporte/<int:taller_id>')
def ultimo_reporte(taller_id):
    conn = get_db_connection()
    reporte = conn.execute('''
        SELECT * FROM Reportes 
        WHERE ID_Talleres = ? 
        ORDER BY Fecha_Reporte DESC 
        LIMIT 1
    ''', (taller_id,)).fetchone()
    
    # Obtener el contrato del taller
    taller = conn.execute('SELECT contrato FROM Talleres WHERE ID_Talleres = ?', (taller_id,)).fetchone()
    contrato = taller['contrato'] if taller else None
    
    conn.close()

    if not reporte:
        return jsonify([])

    reporte_dict = dict(reporte)
    reporte_id = reporte_dict['ID_Reporte']
    imagenes = []
    for i in range(1, 5):
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], contrato, str(reporte_id), f'{i}.jpg')
        if os.path.exists(image_path):
            imagenes.append(url_for('uploaded_file', filename=os.path.join(contrato, str(reporte_id), f'{i}.jpg')))
    reporte_dict['imagenes'] = imagenes

    return jsonify(reporte_dict)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/crear_reporte', methods=['GET', 'POST'])
def crear_reporte():
    if request.method == 'POST':
        contrato = request.form['contrato']
        id_taller = int(request.form['id_taller'])
        fecha_reporte = request.form['fecha_reporte']
        descripcion = request.form['descripcion']
        estatus = request.form['estatus']
        porciento_eje = request.form['porciento_eje']
        
        # Guardar el reporte en la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Reportes (ID_Talleres, Fecha_Reporte, Descripción, Estatus, PorcientoEje)
            VALUES (?, ?, ?, ?, ?)
        ''', (id_taller, fecha_reporte, descripcion, estatus, porciento_eje))
        conn.commit()
        reporte_id = cursor.lastrowid
        conn.close()

        # Crear las carpetas y guardar las imágenes
        reporte_path = os.path.join(app.config['UPLOAD_FOLDER'], contrato, str(reporte_id))
        os.makedirs(reporte_path, exist_ok=True)

        for i in range(1, 5):
            image = request.files[f'imagen_{i}']
            if image:
                image.save(os.path.join(reporte_path, f'{i}.jpg'))

        return redirect(url_for('index'))
    
    conn = get_db_connection()
    proyectos = conn.execute('SELECT * FROM Proyectos').fetchall()
    conn.close()
    return render_template('crear_reporte.html', proyectos=proyectos)

@app.route('/cubicaciones')
def cubicaciones():
    conn = get_db_connection()
    cubicaciones = conn.execute('SELECT * FROM Cubicaciones').fetchall()
    conn.close()
    return render_template('cubicaciones.html', cubicaciones=cubicaciones)

@app.route('/agregar_cubicacion', methods=['GET', 'POST'])
def agregar_cubicacion():
    if request.method == 'POST':
        id_proyecto = int(request.form['id_proyecto'])
        fecha_cubicacion = request.form['fecha_cubicacion']
        fecha_firma = request.form['fecha_firma']
        
        conn = get_db_connection()
        cursor = conn.cursor()

        for key in request.form.keys():
            if key.startswith('aceras_'):
                id_taller = int(key.split('_')[1])
                aceras = float(request.form[f'aceras_{id_taller}'])
                contenes = float(request.form[f'contenes_{id_taller}'])
                monto_bruto = float(request.form[f'monto_bruto_{id_taller}'])

                cursor.execute('''
                    INSERT INTO Cubicaciones (ID_Talleres, ID_Proyecto, Fecha_Cubicacion, Fecha_Firma, Aceras, Contenes, MontoBruto)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (id_taller, id_proyecto, fecha_cubicacion, fecha_firma, aceras, contenes, monto_bruto))

        conn.commit()
        conn.close()

        return redirect(url_for('cubicaciones'))
    
    conn = get_db_connection()
    proyectos = conn.execute('SELECT * FROM Proyectos').fetchall()
    conn.close()
    return render_template('agregar_cubicacion.html', proyectos=proyectos)

@app.route('/talleres_por_proyecto/<int:proyecto_id>')
def talleres_por_proyecto(proyecto_id):
    conn = get_db_connection()
    proyecto = conn.execute('SELECT Contrato FROM Proyectos WHERE ID_Proyecto = ?', (proyecto_id,)).fetchone()
    contrato = proyecto['Contrato'] if proyecto else None
    talleres = conn.execute('SELECT * FROM Talleres WHERE contrato = ?', (contrato,)).fetchall()
    conn.close()
    return jsonify([dict(taller) for taller in talleres])

@app.route('/eliminar_cubicacion/<int:cubicacion_id>', methods=['POST'])
def eliminar_cubicacion(cubicacion_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM Cubicaciones WHERE ID_Cubicacion = ?', (cubicacion_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('cubicaciones'))

@app.route('/seleccionar_taller')
def seleccionar_taller():
    conn = get_db_connection()
    proyectos = conn.execute('SELECT * FROM Proyectos').fetchall()
    conn.close()
    return render_template('seleccionar_taller.html', proyectos=proyectos)

@app.route('/talleres_por_proyecto_seleccion/<int:proyecto_id>')
def talleres_por_proyecto_seleccion(proyecto_id):
    conn = get_db_connection()
    proyecto = conn.execute('SELECT Contrato FROM Proyectos WHERE ID_Proyecto = ?', (proyecto_id,)).fetchone()
    contrato = proyecto['Contrato'] if proyecto else None
    talleres = conn.execute('SELECT * FROM Talleres WHERE contrato = ?', (contrato,)).fetchall()
    conn.close()
    return jsonify([dict(taller) for taller in talleres])

@app.route('/generar_ficha')
def generar_ficha():
    taller_id = request.args.get('taller')
    if not taller_id:
        return redirect(url_for('seleccionar_taller'))
    
    conn = get_db_connection()
    taller = conn.execute('SELECT * FROM Talleres WHERE ID_Talleres = ?', (taller_id,)).fetchone()
    proyecto = conn.execute('SELECT * FROM Proyectos WHERE Contrato = ?', (taller['Contrato'],)).fetchone()
    reporte = conn.execute('''
        SELECT Estatus, ID_Reporte, Descripción, PorcientoEje FROM Reportes 
        WHERE ID_Talleres = ? 
        ORDER BY Fecha_Reporte DESC 
        LIMIT 1
    ''', (taller_id,)).fetchone()
    
    cubicaciones = conn.execute('''
        SELECT SUM(MontoBruto) as total_cubicacion, SUM(Aceras) as total_aceras, SUM(Contenes) as total_contenes
        FROM Cubicaciones 
        WHERE ID_Talleres = ?
    ''', (taller_id,)).fetchone()
    
    conn.close()
    
    estatus = reporte['Estatus'] if reporte else 'N/A'
    porciento_eje = reporte['PorcientoEje'] if reporte else 0
    total_cubicacion = cubicaciones['total_cubicacion'] if cubicaciones['total_cubicacion'] else 0.0
    total_aceras = cubicaciones['total_aceras'] if cubicaciones['total_aceras'] else 0.0
    total_contenes = cubicaciones['total_contenes'] if cubicaciones['total_contenes'] else 0.0
    observaciones = reporte['Descripción'] if reporte else 'N/A'

    imagenes = []
    if reporte:
        contrato = taller['Contrato']
        reporte_id = reporte['ID_Reporte']
        for i in range(1, 5):
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], contrato, str(reporte_id), f'{i}.jpg')
            if os.path.exists(image_path):
                imagenes.append(url_for('uploaded_file', filename=os.path.join(contrato, str(reporte_id), f'{i}.jpg')))
            else:
                imagenes.append(url_for('uploaded_file', filename='placeholder.jpg'))  # Placeholder image path

    return render_template('ficha_taller.html', taller=taller, proyecto=proyecto, estatus=estatus, porciento_eje=porciento_eje, total_cubicacion=total_cubicacion, total_aceras=total_aceras, total_contenes=total_contenes, imagenes=imagenes, observaciones=observaciones)

@app.route('/generar_ficha_pdf')
def generar_ficha_pdf():
    taller_id = request.args.get('taller')
    if not taller_id:
        return redirect(url_for('seleccionar_taller'))
    
    conn = get_db_connection()
    taller = conn.execute('SELECT * FROM Talleres WHERE ID_Talleres = ?', (taller_id,)).fetchone()
    proyecto = conn.execute('SELECT * FROM Proyectos WHERE Contrato = ?', (taller['Contrato'],)).fetchone()
    reporte = conn.execute('''
        SELECT Estatus, ID_Reporte, Descripción, PorcientoEje FROM Reportes 
        WHERE ID_Talleres = ? 
        ORDER BY Fecha_Reporte DESC 
        LIMIT 1
    ''', (taller_id,)).fetchone()
    
    cubicaciones = conn.execute('''
        SELECT SUM(MontoBruto) as total_cubicacion, SUM(Aceras) as total_aceras, SUM(Contenes) as total_contenes
        FROM Cubicaciones 
        WHERE ID_Talleres = ?
    ''', (taller_id,)).fetchone()
    
    conn.close()
    
    estatus = reporte['Estatus'] if reporte else 'N/A'
    porciento_eje = reporte['PorcientoEje'] if reporte else 0
    total_cubicacion = cubicaciones['total_cubicacion'] if cubicaciones['total_cubicacion'] else 0.0
    total_aceras = cubicaciones['total_aceras'] if cubicaciones['total_aceras'] else 0.0
    total_contenes = cubicaciones['total_contenes'] if cubicaciones['total_contenes'] else 0.0
    observaciones = reporte['Descripción'] if reporte else 'N/A'

    imagenes = []
    if reporte:
        contrato = taller['Contrato']
        reporte_id = reporte['ID_Reporte']
        for i in range(1, 5):
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], contrato, str(reporte_id), f'{i}.jpg')
            if os.path.exists(image_path):
                imagenes.append(url_for('uploaded_file', filename=os.path.join(contrato, str(reporte_id), f'{i}.jpg')))
            else:
                imagenes.append(url_for('uploaded_file', filename='placeholder.jpg'))  # Placeholder image path

    rendered = render_template('ficha_taller.html', taller=taller, proyecto=proyecto, estatus=estatus, porciento_eje=porciento_eje, total_cubicacion=total_cubicacion, total_aceras=total_aceras, total_contenes=total_contenes, imagenes=imagenes, observaciones=observaciones)
    pdf = render_pdf(HTML(string=rendered), stylesheets=[CSS(string='@page { size: A3 landscape; margin: 0; }')])
    return pdf

# Nuevas rutas para manejar los documentos

@app.route('/documentos_por_contrato/<contrato>')
def documentos_por_contrato(contrato):
    conn = get_db_connection()
    documentos = conn.execute('SELECT * FROM Documentos WHERE Contrato = ?', (contrato,)).fetchone()
    conn.close()
    return jsonify(dict(documentos) if documentos else {})

@app.route('/subir_documentos', methods=['GET', 'POST'])
def subir_documentos():
    if request.method == 'POST':
        contrato = request.form['contrato']
        archivos = {
            'AContratoBase': request.files.get('AContratoBase'),
            'ACertBase': request.files.get('ACertBase'),
            'APresBase': request.files.get('APresBase'),
            'AContratoAdenda': request.files.get('AContratoAdenda'),
            'ACertAdenda': request.files.get('ACertAdenda'),
            'APresAdenda': request.files.get('APresAdenda')
        }
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si ya existen documentos para este contrato
        documentos_existentes = cursor.execute('SELECT * FROM Documentos WHERE Contrato = ?', (contrato,)).fetchone()
        
        if documentos_existentes:
            # Actualizar documentos existentes
            for key, archivo in archivos.items():
                if archivo:
                    filename = secure_filename(f"{contrato}_{key}.pdf")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], contrato, 'docs')
                    os.makedirs(filepath, exist_ok=True)
                    archivo.save(os.path.join(filepath, filename))
                    cursor.execute(f'''
                        UPDATE Documentos
                        SET {key} = ?
                        WHERE Contrato = ?
                    ''', (filename, contrato))
        else:
            # Insertar nuevos documentos
            data = {}
            for key, archivo in archivos.items():
                if archivo:
                    filename = secure_filename(f"{contrato}_{key}.pdf")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], contrato, 'docs')
                    os.makedirs(filepath, exist_ok=True)
                    archivo.save(os.path.join(filepath, filename))
                    data[key] = filename
                else:
                    data[key] = None

            cursor.execute('''
                INSERT INTO Documentos (Contrato, AContratoBase, ACertBase, APresBase, AContratoAdenda, ACertAdenda, APresAdenda)
                VALUES (:Contrato, :AContratoBase, :ACertBase, :APresBase, :AContratoAdenda, :ACertAdenda, :APresAdenda)
            ''', {**data, 'Contrato': contrato})
        
        conn.commit()
        conn.close()

        return redirect(url_for('subir_documentos'))

    conn = get_db_connection()
    proyectos = conn.execute('SELECT * FROM Proyectos').fetchall()
    conn.close()
    return render_template('subir_documentos.html', proyectos=proyectos)

@app.route('/download/<contrato>/<filename>')
def download_file(contrato, filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], contrato, 'docs'), filename)

@app.route('/exportar_excel')
def exportar_excel():
    conn = get_db_connection()
    
    # Obtener información de proyectos
    proyectos_query = '''
    SELECT p.ID_Proyecto, p.Contrato as Proyecto_Contrato, p.Oferente,
           t.ID_Talleres, t.Contrato as Taller_Contrato, t.Zonagpro, t.Lote, t.Item, t.Provincia, t.Municipio, t.Sectores, 
           t.Ejecucion, t.Porcientoeje as Taller_PorcientoEje, t.Comentarios, t.Montoitem, t.Longitud, t.Latitud, t.Coordinador, t.Supervisor,
           r.ID_Reporte, r.ID_Talleres as Reporte_Talleres, r.ID_Proyecto as Reporte_Proyecto, r.Fecha_Reporte, r.Descripción, r.Imagen_1, r.Imagen_2, 
           r.Imagen_3, r.Imagen_4, r.Estatus as Reporte_Estatus, r.PorcientoEje as Reporte_PorcientoEje,
           c.total_monto_bruto, c.total_aceras, c.total_contenes
    FROM Proyectos p
    LEFT JOIN Talleres t ON p.Contrato = t.Contrato
    LEFT JOIN (
        SELECT r1.*
        FROM Reportes r1
        JOIN (
            SELECT ID_Talleres, MAX(Fecha_Reporte) as max_fecha
            FROM Reportes
            GROUP BY ID_Talleres
        ) r2 ON r1.ID_Talleres = r2.ID_Talleres AND r1.Fecha_Reporte = r2.max_fecha
    ) r ON t.ID_Talleres = r.ID_Talleres
    LEFT JOIN (
        SELECT ID_Talleres, SUM(MontoBruto) as total_monto_bruto, SUM(Aceras) as total_aceras, SUM(Contenes) as total_contenes
        FROM Cubicaciones
        GROUP BY ID_Talleres
    ) c ON t.ID_Talleres = c.ID_Talleres
    '''
    
    proyectos = conn.execute(proyectos_query).fetchall()
    conn.close()
    
    # Convertir los datos a un DataFrame de pandas
    df = pd.DataFrame(proyectos)
    
    # Definir los nombres de las columnas
    column_names = [
        'ID Proyecto', 'Contrato Proyecto', 'Oferente',
        'ID Taller', 'Contrato Taller', 'Zona Gpro', 'Lote', 'Item', 'Provincia', 'Municipio', 'Sectores', 
        'Ejecución', 'Porciento Ejecución Taller', 'Comentarios', 'Monto Item', 'Longitud', 'Latitud', 
        'Coordinador', 'Supervisor',
        'ID Reporte', 'ID Taller Reporte', 'ID Proyecto Reporte', 'Fecha Reporte', 'Descripción', 'Imagen 1', 'Imagen 2', 
        'Imagen 3', 'Imagen 4', 'Estatus Reporte', 'Porciento Ejecución Reporte',
        'Total Monto Bruto', 'Total Aceras', 'Total Contenes'
    ]
    
    # Asignar los nombres a las columnas del DataFrame
    df.columns = column_names
    
    # Crear un archivo Excel con los datos
    output_file = 'proyectos_talleres_reportes_cubicaciones.xlsx'
    df.to_excel(output_file, index=False)
    
    return send_from_directory(directory='.', path=output_file, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
