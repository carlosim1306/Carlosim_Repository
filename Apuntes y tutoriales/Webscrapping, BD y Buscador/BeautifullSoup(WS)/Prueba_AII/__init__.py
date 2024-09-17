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

def extraer_eventos():
    lista=[]
    
    for num_paginas in range(1,5):                                                                 
        req = urllib.request.Request("https://sevilla.cosasdecome.es/eventos/filtrar?pg="+str(num_paginas), headers={'User-Agent': 'Mozilla/5.0'})   
        f = urllib.request.urlopen(req)
        s = BeautifulSoup(f, "lxml")
        lista_eventos = s.find_all("article", class_="post-summary")
        
        for evento in lista_eventos:
            
            link = evento.find("h2", class_="post-title")
            f = urllib.request.urlopen(link.a['href'])
            s1 = BeautifulSoup(f, "lxml")
            
            titulo = s1.find("div", class_="post-title").string.strip()
            if s1.find("div", class_="lugar"):
                lugar = s1.find("div", class_="lugar").find("div", class_="value").p.string.strip()
            else:
                lugar = NULL
            if s1.find("div", class_="direccion"):
                direccion = s1.find("div", class_="direccion").find("div", class_="value").string.strip()
            else:
                direccion = NULL
            poblacion = s1.find("div", class_="poblacion").find("div", class_="value").a.string.strip()
            fechas =  s1.find("div", class_="block-elto fechas").find("div", class_="post-date")
            for c in fechas.children:
                if c.name != "i":
                    fechas = c.strip()
            fecha_inicio= parse_fechas(fechas)[0].date()
            fecha_fin = parse_fechas(fechas)[1].date()
            if s1.find("div", class_="hora"):
                
                hora = s1.find("div", class_="hora").find("div", class_="value")
                for c in hora.children:
                    if c.name != "i":
                        horario = c.strip()
                horario = parse_horario(horario)
            else:
                horario = NULL
            categorias = s1.find("div", class_="categoria").find("div", class_="value").a.string.strip()
            
            
            lista.append((titulo,lugar,direccion,poblacion,fecha_inicio, fecha_fin,horario,categorias))
       
    return lista

def parse_horario(horario):
    if 'cena' in horario:
        horario = time(hour=20, minute=0)
    elif len(horario.split(" "))>1:
        horario = horario.split(" ")[-1].strip()
        horas = horario[0].split(":")[0].strip()
        minutos = horario[1].split(":")[0].strip()
        horario = time(hour=int(horas), minute=int(minutos))
    else:
        horas = horario[0].split(":")[0].strip()
        minutos = horario[1].split(":")[0].strip()
        horario = time(hour=int(horas), minute=int(minutos)) 
    return horario.strftime("%I:%M %p") 
    
def parse_fechas(fecha):
    res = []
    if "al" in fecha:
        fechas = fecha.split("al")
        fecha_inicio = datetime.strptime(fechas[0].strip(), '%d/%m/%Y')
        fecha_fin = datetime.strptime(fechas[1].strip(), '%d/%m/%Y')
        res.append(fecha_inicio)
        res.append(fecha_fin)
        
    else:
        fecha = datetime.strptime(fecha.strip(), '%d/%m/%Y')
        res.append(fecha)
        res.append(fecha)
    
    return res

def almacenar_bd():
    conn = sqlite3.connect('eventos.db')
    conn.text_factory = str  # para evitar problemas con el conjunto de caracteres que maneja la BD
    conn.execute("DROP TABLE IF EXISTS EVENTOS") 
    conn.execute('''CREATE TABLE EVENTOS
       (TITULO        TEXT    NOT NULL,
       LUGAR          TEXT    ,
       DIRECCION         TEXT    ,
       POBLACION        TEXT    ,
       FECHA_INICIO        DATE    ,
       FECHA_FIN            DATE    ,
       HORARIO              TIME    ,
       CATEGORIA           TEXT);''')

    for i in extraer_eventos():              
        conn.execute("""INSERT INTO EVENTOS VALUES (?,?,?,?,?,?,?,?)""",i)
    conn.commit()
    cursor = conn.execute("SELECT COUNT(*) FROM EVENTOS")
    messagebox.showinfo( "Base Datos", "Base de datos creada correctamente \nHay " + str(cursor.fetchone()[0]) + " registros")
    conn.close()
def imprimir_lista(cursor):
    v = Toplevel()
    v.title("LISTADO DE EVENTOS")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END,row[0])
        lb.insert(END,"    Lugar: "+ str(row[1] if row[1]== NULL else "desconocido"))
        lb.insert(END,"    Direccion: "+ str(row[2] if row[2]==NULL else "desconocido"))
        lb.insert(END,"    Poblacion: "+ row[3])
        lb.insert(END,"    Fecha Inicial: "+ row[4])
        lb.insert(END,"    Fecha Final: "+ row[5])
        lb.insert(END,"    Horario: "+ str(row[6] if row[6]==NULL else "desconocido"))
        lb.insert(END,"    Categoria/s: "+ row[7])
        lb.insert(END,"\n\n")
    lb.pack(side=LEFT,fill=BOTH)
    sc.config(command = lb.yview)


def listar_eventos():
    conn = sqlite3.connect('eventos.db')
    conn.text_factory = str  
    cursor = conn.execute("SELECT * FROM EVENTOS")
    imprimir_lista(cursor)
    conn.close()

def listar_eventos_noche():
    conn = sqlite3.connect('eventos.db')
    conn.text_factory = str  
    cursor = conn.execute("SELECT * FROM EVENTOS WHERE HORARIO > 19:00:00")
    imprimir_lista(cursor)
    conn.close()

def buscar_por_fechas():
    def listar(event):
            conn = sqlite3.connect('eventos.db')
            conn.text_factory = str
            fec = re.match(r"\d\d de \d\d de \d{4}",entry.get().strip())
            if fec:
                fecha = datetime.strptime(entry.get().strip(),"%d/%m/%Y")
                cursor = conn.execute("SELECT * FROM EVENTOS WHERE FECHA_INICIO => ? OR FECHA_FIN =< ?", (fecha,fecha,))
                conn.close
                imprimir_lista(cursor, entry.get().strip() )
            else:
                messagebox.showerror("Error", "Formato de fecha incorrecto")
    
    
    v = Toplevel()
    label = Label(v,text="Escriba la fecha (dia de mes de año): ")
    label.pack(side=LEFT)
    entry = Entry(v)
    entry.bind("<Return>", listar)
    entry.pack(side=LEFT)   
    
def buscar_por_categoria_poblacion():
    def mostrar_categoria():
        conn = sqlite3.connect('eventos.db')
        conn.text_factory = str
        cursor = conn.execute("SELECT DISTINCT CATEGORIA FROM EVENTOS")
        categoria.config([d[0] for d in cursor])
        conn.close()


    def mostrar_poblacion():
        conn = sqlite3.connect('eventos.db')
        conn.text_factory = str
        cursor = conn.execute("SELECT DISTINCT POBLACION FROM EVENTOS")
        poblacion.config([d[0] for d in cursor])
        conn.close()

    def listar1(event):
        conn = sqlite3.connect('eventos.db')
        conn.text_factory = str
        cursor = conn.execute("SELECT * FROM EVENTOS WHERE CATEGORIA LIKE '%" + str(entry.get()) + "%'")
        conn.close
        imprimir_lista(cursor)
    def listar2(event):
        conn = sqlite3.connect('eventos.db')
        conn.text_factory = str
        cursor = conn.execute("SELECT * FROM EVENTOS WHERE POBLACION LIKE '%" + str(entry.get()) + "%'")
        conn.close
        imprimir_lista(cursor)

    ventana = Toplevel()
    opcion = IntVar() # Como StrinVar pero en entero

    Radiobutton(ventana, text="Categoria", variable=opcion, value=1, command=mostrar_categoria).pack()
    Radiobutton(ventana, text="Poblacion", variable=opcion, value=2, command=mostrar_poblacion).pack()

    if opcion==1:
        categoria = Label(ventana,text="Seleccione una Categoria: ")
        categoria.pack(side=LEFT)
        entry = Spinbox(ventana, width= 30, values=categoria)
        entry.bind("<Return>", listar1)
        entry.pack(side=LEFT)
    if opcion==2:
        poblacion = Label(ventana,text="Seleccione una poblacion: ")
        poblacion.pack(side=LEFT)
        entry = Spinbox(ventana, width= 30, values=poblacion)
        entry.bind("<Return>", listar2)
        entry.pack(side=LEFT)
   
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
    buscarmenu.add_command(label="Eventos", command=listar_eventos)
    buscarmenu.add_command(label="Eventos por la noche", command=listar_eventos_noche)
    
    menubar.add_cascade(label="Listar", menu=buscarmenu)
    
    buscarmenu = Menu(menubar, tearoff=0)
    buscarmenu.add_command(label="Eventos por fecha de celebración", command=buscar_por_fechas)
    buscarmenu.add_command(label="Eventos por categoria o poblacion", command=buscar_por_categoria_poblacion)
    
    menubar.add_cascade(label="Buscar", menu=buscarmenu)
        
    root.config(menu=menubar)
    root.mainloop()

if __name__ == "__main__":
    ventana_principal()