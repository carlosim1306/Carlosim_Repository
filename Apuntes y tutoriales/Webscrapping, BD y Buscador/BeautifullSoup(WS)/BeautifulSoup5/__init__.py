#encoding:utf-8

from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import sqlite3
import re
from datetime import datetime, time

# lineas para evitar error SSL
import os, ssl
from _overlapped import NULL
from scipy.constants._constants import hour
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

def extraer_recetas():
    lista=[]
    
    url =  'https://www.recetasgratis.net/Recetas-de-Aperitivos-tapas-listado_receta-1_1.html'
    #Añadimos la página a la url
    f = urllib.request.urlopen(url)
    #Abrimos la url
    s = BeautifulSoup(f,"lxml")      
    #Le damos el formato al BeautifulSoup
    lista_link_recetas = s.find_all("div", class_="resultado link")
    #cogemos todos los contenedores de las carteleras <li>
    
    for link_receta in lista_link_recetas:
         
        f = urllib.request.urlopen(link_receta.a['href'])
        s = BeautifulSoup(f, "lxml")
                
        nombre_receta = s.find("h1", class_="titulo--articulo").string.strip()
        autor = s.find("div", class_="nombre_autor").a.string.strip()
        fecha = parse_fecha(s.find("div", class_="nombre_autor").span.string.strip())
        comensales =int(re.compile('\d+').search(s.find("div", class_="properties").find("span", class_="property comensales").string.strip()).group())
        duracion = s.find("div", class_="properties").find("span", class_="property duracion").string.strip()
        duracion = parse_duracion(duracion)
        dificultad = s.find("div", class_="properties").find("span", class_="property dificultad").string.strip()
        
        lista.append((nombre_receta,dificultad,comensales,duracion,autor, fecha))
    return lista
        
def almacenar_bd():
    conn = sqlite3.connect('recetas.db')
    conn.text_factory = str  # para evitar problemas con el conjunto de caracteres que maneja la BD
    conn.execute("DROP TABLE IF EXISTS RECETAS") 
    conn.execute('''CREATE TABLE RECETAS
       (NOMBRE        TEXT    NOT NULL,
       DIFICULTAD          TEXT    ,
       COMENSALES         INT    ,
       DURACION        TIME    ,
       AUTOR        TEXT    ,
       FECHA      TIME);''')

    for i in extraer_recetas():              
        conn.execute("""INSERT INTO RECETAS VALUES (?,?,?,?,?,?)""",i)
    conn.commit()
    cursor = conn.execute("SELECT COUNT(*) FROM RECETAS")
    messagebox.showinfo( "Base Datos", "Base de datos creada correctamente \nHay " + str(cursor.fetchone()[0]) + " registros")
    conn.close()
      
def parse_fecha(fecha):
    
    meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
    
    if fecha.split(" ") == 3:
        dia, mes, anyo = fecha.split(" ")
        mes = meses.index(mes) + 1
        fecha_datetime = datetime(int(anyo), mes, int(dia))
        return fecha_datetime.date()
    else:
        return NULL

def parse_duracion(duracion):
    
    duracion = duracion.split(" ")
    if len(duracion) > 1:
        horas = duracion[0].split("h")[0].strip()
        minutos = duracion[1].split("m")[0].strip()
        duracion = time(hour=int(horas), minute=int(minutos))
    elif "m" in duracion[0]:
        duracion = time(minute=int(duracion[0].split("m")[0].strip()))
    elif "24h" in duracion[0]:
        return NULL
    else:
        duracion = time(hour=int(duracion[0].split("h")[0].strip()))
        
    return duracion.strftime("%I:%M %p")

def imprimir_lista(cursor):
    v = Toplevel()
    v.title("Recetitas potente")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END,row[0])
        lb.insert(END,row[1])
        lb.insert(END,row[2])
        lb.insert(END,row[3])
        lb.insert(END,row[4])
        lb.insert(END,row[5])
        lb.insert(END,"\n\n")
    lb.pack(side=LEFT,fill=BOTH)
    sc.config(command = lb.yview)
    
def listar_recetas():
    conn = sqlite3.connect('recetas.db')
    conn.text_factory = str  
    cursor = conn.execute("SELECT * FROM RECETAS")
    imprimir_lista(cursor)
    conn.close()
    
def ventana_principal():       
    root = Tk()
    root.geometry("150x100")

    menubar = Menu(root)
    
    datosmenu = Menu(menubar, tearoff=0)
    datosmenu.add_command(label="Cargar", command=almacenar_bd)
    datosmenu.add_separator()   
    datosmenu.add_command(label="Salir", command=root.quit)
    
    menubar.add_cascade(label="Datos", menu=datosmenu)
    
    buscarmenu = Menu(menubar, tearoff=0)
    buscarmenu.add_command(label="Recetas", command=listar_recetas())
    
    menubar.add_cascade(label="Listar", menu=buscarmenu)
    

    
    menubar.add_cascade(label="Buscar", menu=buscarmenu)
        
    root.config(menu=menubar)
    root.mainloop()
    
if __name__ == "__main__":
    ventana_principal()