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

def extraer_partidos():
    lista=[]
    
    url =  'https://resultados.as.com/resultados/futbol/primera/2021_2022/calendario/'
    f = urllib.request.urlopen(url)
    s = BeautifulSoup(f,"lxml")      
    contenedor_jornadas = s.find_all("div", class_="col-md-6 col-sm-6 col-xs-12")
    
    for jornada in contenedor_jornadas:
         
        n_jornada = jornada.find("h2", class_='tit-modulo').a.string.strip()
        
        contenedor_partidos = jornada.find("table", class_="tabla-datos")
        partidos = contenedor_partidos.tbody.findAll("tr")
        
        for partido in partidos:
            
            equipo_local = partido.find("td",class_="col-equipo-local").find("span",class_="nombre-equipo").string.strip()
            equipo_visitante = partido.find("td",class_="col-equipo-visitante").find("span",class_="nombre-equipo").string.strip()
            resultado = partido.find("td",class_="col-resultado").a.string.strip()
            goles_local = goles(resultado)[0]
            goles_visitante = goles(resultado)[1]
            
            
            lista.append((n_jornada,equipo_local,equipo_visitante,goles_local,goles_visitante))
    
    return lista

def goles(resultado):
    goles = resultado.split("-")
    gl = int(goles[0].strip())
    gv = int(goles[1].strip())
    return list((gl,gv))

def almacenar_bd():
    conn = sqlite3.connect('partidos.db')
    conn.text_factory = str  # para evitar problemas con el conjunto de caracteres que maneja la BD
    conn.execute("DROP TABLE IF EXISTS PARTIDOS") 
    conn.execute('''CREATE TABLE PARTIDOS
       (JORNADA        INT    NOT NULL,
       EQUIPO_LOCAL          TEXT    ,
       EQUIPO_VISITANTE         TEXT    ,
       GOLES_LOCAL        TIME    ,
       GOLES_VISITANTE        TEXT);''')

    for i in extraer_partidos():              
        conn.execute("""INSERT INTO PARTIDOS VALUES (?,?,?,?,?)""",i)
    conn.commit()
    cursor = conn.execute("SELECT COUNT(*) FROM PARTIDOS")
    messagebox.showinfo( "Base Datos", "Base de datos creada correctamente \nHay " + str(cursor.fetchone()[0]) + " registros")
    conn.close()
    
def cargar_datos():
    try:
        almacenar_bd()
        messagebox.showinfo("Éxito", "Datos cargados correctamente")
    except Exception as e:
        messagebox.showerror("Error", f"Error al cargar datos: {str(e)}")

def listar_partidos():
    try:
        conn = sqlite3.connect('partidos.db')
        cursor = conn.execute("SELECT * FROM PARTIDOS")
        imprimir_lista(cursor)
        conn.close()
    except Exception as e:
        messagebox.showerror("Error", f"Error al listar partidos: {str(e)}")

def listar_por_equipo():
    def buscar(event):
        try:
            conn = sqlite3.connect('partidos.db')
            equipo = equipo_entry.get().strip()
            cursor = conn.execute(f"SELECT * FROM PARTIDOS WHERE EQUIPO_LOCAL LIKE '%{equipo}%' OR EQUIPO_VISITANTE LIKE '%{equipo}%'")
            imprimir_lista(cursor)
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al buscar por equipo: {str(e)}")

    buscar_equipo_window = Toplevel()
    buscar_equipo_window.title("Buscar por Equipo")
    
    label = Label(buscar_equipo_window, text="Ingrese el nombre del equipo:")
    label.pack(side=LEFT)
    
    equipo_entry = Entry(buscar_equipo_window, width=30)
    equipo_entry.bind("<Return>", buscar)
    equipo_entry.pack(side=LEFT)


def imprimir_lista(cursor):
    lista_window = Toplevel()
    lista_window.title("Lista de Partidos")
    
    lista_text = Text(lista_window, wrap=WORD)
    lista_text.pack(expand=YES, fill=BOTH)
    
    for row in cursor:
        lista_text.insert(END, row)
        lista_text.insert(END, "\n")


def ventana_principal():       
    root = Tk()
    root.geometry("300x100")

    menubar = Menu(root)
    
    datos_menu = Menu(menubar, tearoff=0)
    datos_menu.add_command(label="Cargar Datos", command=cargar_datos)
    datos_menu.add_separator()   
    datos_menu.add_command(label="Salir", command=root.quit)
    
    menubar.add_cascade(label="Datos", menu=datos_menu)
    
    listar_menu = Menu(menubar, tearoff=0)
    listar_menu.add_command(label="Listar Partidos", command=listar_partidos)
    listar_menu.add_command(label="Listar por Equipo", command=listar_por_equipo)
    
    menubar.add_cascade(label="Listar", menu=listar_menu)
    

        
    root.config(menu=menubar)
    root.mainloop()

if __name__ == "__main__":
    ventana_principal()