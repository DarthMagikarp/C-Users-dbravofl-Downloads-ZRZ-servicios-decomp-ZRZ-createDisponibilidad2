# chat conversation
import json
import pymysql
import requests
import http.client
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin

from datetime import datetime, timedelta
import calendar

from itertools import cycle

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_DDBB = os.getenv("DB_DDBB")
#try:
connection = pymysql.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASS,
    database=DB_DDBB)
cursor = connection.cursor()

@app.route("/", methods=["POST"])
@cross_origin()
def function(self):
    print("REQUEST: "+str(request.json))
    
    #try:
    
    fecha_inicio = str(request.json['fechaInicio'])
    fecha_fin = str(request.json['fechaFin'])
    
    frecuencia = str(request.json['frecuencia'])
    if 'recurrencia' in request.json:
        recurrencia = int(request.json['recurrencia'])
    else:
        recurrencia = ''
    dias = request.json['dias']
    orden = str(request.json['orden'])
    #diaNumero = int(request.json['diaNumero'])
    #print("diaNumero: "+str(diaNumero))

    # Generar las fechas de las citas
    #repeticiones = calcular_fechas(fecha_inicio, fecha_fin, frecuencia, recurrencia, dias, orden, diaNumero)

    #print("dia numero: "+str(request.json['diaNumero']))
    #print('diaNumero' in request.json)
    #print(request.json['diaNumero'] != '')

    if frecuencia == 'diaria' or frecuencia == 'semanal':
        if 'diaNumero' in request.json and request.json['diaNumero'] != '':
            diaNumero = int(request.json['diaNumero'])
            repeticiones = calcular_fechas(fecha_inicio, fecha_fin, frecuencia, recurrencia, dias, orden, diaNumero)
        else:
            repeticiones = calcular_fechas_sindia(fecha_inicio, fecha_fin, frecuencia, recurrencia, dias, orden)
    else:
        repeticiones = calcular_fechas_mensual(dias, fecha_inicio, fecha_fin, frecuencia, orden)


    #print("Ejemplo 2:", repeticiones)
    print("repeticiones: "+str(repeticiones))

    # Insertar las fechas en la tabla MySQL
    insertar_fechas(repeticiones, frecuencia, orden)

    retorno = {
            "estado":True,
            "detalle":"success!!"
        }

    #except Exception as e:
    #    print('Error: '+ str(e))
    #    retorno = {
    #        "estado":False,
    #        "detalle":"fail!!"
    #    }
    return retorno

def calcular_fechas_mensual(dias, fechaInicio, fechaFin, frecuencia, orden):
    # Convertir las fechas de cadena a objetos datetime
    fecha_inicio = datetime.strptime(fechaInicio, "%Y-%m-%d")
    fecha_fin = datetime.strptime(fechaFin, "%Y-%m-%d")
    
    # Diccionario para mapear nombres de días a números de la semana
    dias_semana = {"lunes": 0, "martes": 1, "miércoles": 2, "jueves": 3, "viernes": 4, "sábado": 5, "domingo": 6}
    
    # Obtener el número de día correspondiente al día especificado
    dia_semana = dias_semana[dias[0]]
    
    # Lista para almacenar las fechas que cumplen con las restricciones
    fechas_cumplen = []
    
    # Inicializar fecha actual como fecha de inicio
    fecha_actual = fecha_inicio
    
    # Iterar sobre todos los días entre fechaInicio y fechaFin
    while fecha_actual <= fecha_fin:
        # Verificar si el día es el día de la semana deseado
        if fecha_actual.weekday() == dia_semana:
            # Agregar la fecha a la lista
            fechas_cumplen.append(fecha_actual.strftime("%Y-%m-%d"))
        
        # Avanzar al siguiente día
        fecha_actual += timedelta(days=1)
    
    # Filtrar las fechas de acuerdo al orden especificado
    if orden == "segundo":
        fechas_cumplen = [fecha for fecha in fechas_cumplen if (datetime.strptime(fecha, "%Y-%m-%d").day - 1) // 7 == 1]
    elif orden == "tercero":
        fechas_cumplen = [fecha for fecha in fechas_cumplen if (datetime.strptime(fecha, "%Y-%m-%d").day - 1) // 7 == 2]
    elif orden == "cuarto":
        fechas_cumplen = [fecha for fecha in fechas_cumplen if (datetime.strptime(fecha, "%Y-%m-%d").day - 1) // 7 == 3]
    elif orden == "último":
        fechas_cumplen = [fechas_cumplen[-1]] if fechas_cumplen else []
    
    return fechas_cumplen



def traduceDia(dia):
    if dia == "monday":
        return "lunes"
    elif dia == "tuesday":
        return "martes"
    elif dia == "wednesday":
        return "miércoles"
    elif dia == "thursday":
        return "jueves"
    elif dia == "friday":
        return "viernes"
    elif dia == "saturday":
        return "sábado"
    elif dia == "sunday":
        return "domingo"
        

def calcular_fechas_sindia(fecha_inicio, fecha_fin, frecuencia, recurrencia, dias, orden):
    print("SIN DÍA")
    fechas_encontradas = []
    
    # Convertir las fechas de inicio y fin a objetos datetime si es necesario
    if isinstance(fecha_inicio, str):
        fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    if isinstance(fecha_fin, str):
        fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
    
    # Iterar sobre las fechas entre fechaInicio y fechaFin
    current_date = fecha_inicio
    while current_date <= fecha_fin:
        # Verificar si el día de la semana está en la lista de días
        diaEsp = traduceDia(current_date.strftime("%A").lower())
        if diaEsp in dias:
            fechas_encontradas.append(current_date.strftime("%Y-%m-%d"))
        
        # Avanzar al siguiente día
        current_date += timedelta(days=1)
    
    return fechas_encontradas


def calcular_fechas(fecha_inicio, fecha_fin, frecuencia, recurrencia, arrayDias, orden, diaNumero):
    # Convertir las fechas de inicio y fin a objetos datetime
    fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
    
    # Crear una lista para almacenar las fechas de las repeticiones
    fechas_repeticiones = []
    
    # Iterar sobre todas las fechas entre fecha_inicio y fecha_fin
    current_date = fecha_inicio
    while current_date <= fecha_fin:
        # Verificar si el día de la semana está en el arreglo de días
        dia_semana = current_date.strftime('%A').lower()
        #print(dia_semana)
        if traduceDia(dia_semana) in arrayDias:
            fechas_repeticiones.append(current_date.strftime('%Y-%m-%d'))
        
        # Avanzar al siguiente día
        current_date += timedelta(days=1)
    
    return fechas_repeticiones


def ajustar_fecha_al_orden(fecha, orden, dia_dia, diaNumero):
    # Encontrar el día de la semana del primer día del mes
    primer_dia_mes = fecha.replace(day=1)
    while primer_dia_mes.weekday() != dia_dia:
        primer_dia_mes += timedelta(days=1)
    
    if orden == 'quinto' and diaNumero == 5:
        # Encontrar el quinto día de la semana correspondiente al día especificado
        primer_dia_semana = primer_dia_mes + timedelta(days=(dia_dia - primer_dia_mes.weekday()) % 7)
        # Mover al quinto día del mes
        primer_dia_semana += timedelta(days=(5 - primer_dia_semana.day) % 7)
        return primer_dia_semana
    else:
        # Ajustar la fecha al orden especificado
        if orden == 'primero':
            return primer_dia_semana
        elif orden == 'segundo':
            return primer_dia_semana + timedelta(weeks=1)
        elif orden == 'tercero':
            return primer_dia_semana + timedelta(weeks=2)
        elif orden == 'cuarto':
            return primer_dia_semana + timedelta(weeks=3)
        else:
            raise ValueError("El orden especificado no es válido.")


def dia_de_la_semana(fecha_dt):
    # Convertir la fecha a un objeto de datetime
    #fecha_dt = datetime.datetime.strptime(fecha, '%Y-%m-%d')
    
    # Obtener el nombre del día de la semana en español
    dias_semana = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
    dia_semana = dias_semana[fecha_dt.weekday()]
    
    return dia_semana

def dia_to_weekday(dia):
    dias_semana = {'lunes': 0, 'martes': 1, 'miércoles': 2, 'jueves': 3, 'viernes': 4, 'sábado': 5, 'domingo': 6}
    return dias_semana[dia]

# Conexión a MySQL y función para insertar fechas en la tabla
def insertar_fechas(fechas, frecuencia, orden_dia_semana):
    
    tipoServicio = str(request.json['tipo_cita'])
    
    horaIni = str(request.json['horaIni'])
    horaFin = str(request.json['horaFin'])
    modalidad = str(request.json['modalidad'])
    id_user = str(request.json['id_user'])
    if 'detalleServicio' in request.json:
        detalleServicio = str(request.json['detalleServicio'])
    else:
        detalleServicio=''
    duracionServicio = str(request.json['duracionServicio'])
    tipo = 'profesional'
    id_bloque = 1
    repeticiones = 0

    #insertar_fechas(fechas_citas, frecuencia, recurrencia, orden_dia_semana, orden_numero)

    print("fechas, frecuencia, orden_dia_semana, horaIni,horaIni,horaFin,modalidad,id_user,detalleServicio,duracionServicio,tipo,id_bloque,repeticiones, tipoServicio")
    print(fechas, frecuencia, orden_dia_semana, horaIni,horaIni,horaFin,modalidad,id_user,detalleServicio,duracionServicio,tipo,id_bloque,repeticiones, tipoServicio)

    try:
        for fecha in fechas:
            sql_insertar = 'INSERT INTO '+DB_DDBB+'.disponibilidades'+'''
                (id_bloque, id_user, tipo, día, fechaInicio, fechaFin, repeticiones, horaIni, horaFin, modalidad, frecuencia, detalleServicio, duracionServicio, tipoServicio)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                '''
            #print('INSERT:'+sql_insertar)
            #print(str(id_bloque)+", "+str(id_user)+", "+str(tipo)+", "+str(dia)+", "+str(fechaInicio)+", "+str(fechaFin)+", "+str(repeticiones)+", "+str(horaIni)+", "+str(horaFin)+", "+str(modalidad)+", "+str(frecuencia))
            cursor.execute(sql_insertar,(id_bloque, id_user, tipo, orden_dia_semana, fecha, fecha, repeticiones, horaIni, horaFin, modalidad, frecuencia, detalleServicio, duracionServicio, tipoServicio))

            #cursor.execute("INSERT INTO citas (fecha) VALUES (%s)", (fecha,))
        connection.commit()
        print(f"Se han insertado {len(fechas)} fechas.")
    except Error as e:
        print("Error al conectar con MySQL:", e)

if __name__ == "__main__":
    app.run(debug=True, port=8002, ssl_context='adhoc')
