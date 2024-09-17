#encoding:utf-8

from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import sqlite3
import lxml

# lineas para evitar error SSL

import os, ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context
#Estas líneas se ponen siempre

def cargar():
    respuesta = messagebox.askyesno(title="Confirmar",message="Esta seguro que quiere recargar los datos. \nEsta operaciÃ³n puede ser lenta")
    if respuesta:
        almacenar_bd()
#Este código es el mismo siempre(simplemente lanza una pregunta por si queremos recargar los datos)

def extraer_elementos():
    lista=[]
    
    for num_paginas in range(0,3):                                                                 
        #En el documento nos dice que tomemos como mínimo 3 páginas del html
        url = "https://www.vinissimus.com/es/vinos/tinto/index.html?cursor="+str(num_paginas*36)   
        #url + cadena que será el número del for *36(nos dice que cada página aumenta el cursor 36)
        f = urllib.request.urlopen(url)
        #Función para abrir la url(siempre igual)
        s = BeautifulSoup(f, "lxml")
        #Le damos formato lxml
        lista_una_pagina = s.find_all("div", class_="product-list-item")
        #Tomamos todos los valores de los contenedores(div) con clase "product-list-item" (inspeccionando salen
        #como large), para saber que nos tenemos que quedar con este vamos pasando el ratón por las líneas de 
        #inspección hasta que nos quedamos con el contenedor de los vinos y vemos que todos se encuentran bajo
        #el contenedor dicho(Importante que contenga todos los datos)
        lista.extend(lista_una_pagina)
        #Extiende los elementos de la lista(supongo que es como un flatmap de los stream de Java)
   
    return lista


def almacenar_bd():
    conn = sqlite3.connect('vinos.db')
    #Le damos un nombre a la base de datos a la que nos conectaremos
    conn.text_factory = str
    #Formato de texto
    conn.execute("DROP TABLE IF EXISTS VINO")
    #Vaciamos la tabla VINO
    conn.execute("DROP TABLE IF EXISTS TIPOS_UVAS")
    #Vaciamos la tabla TIPOS_UVAS
    conn.execute('''CREATE TABLE VINO
       (NOMBRE            TEXT NOT NULL,
        PRECIO            REAL,
        DENOMINACION      TEXT,
        BODEGA            TEXT,          
        TIPO_UVAS         TEXT);''')
    #Creamos la tabla Vino, con sus claves y tipos
    
    conn.execute('''CREATE TABLE TIPOS_UVAS
       (NOMBRE            TEXT NOT NULL);''')
    #Creamos la tabla TIPOS_UVAS(La usará para ahorrarse pasos en el filtro de después)
    
    lista_vinos = extraer_elementos() 
    #Lista con todos los valores del html
    tipos_uva=set() 
    #Conjunto vacío para añadir todos los tipos de uva
    
    for vino in lista_vinos:
        datos = vino.find("div",class_=["details"])
        #Hacemos un zoom en nuestro div y vamos a details que contiene nombre, bodega, denominación y uvas
        nombre = datos.a.h2.string.strip()
        #El nombre se encuentra bajo un link "a" y bajo un tipo "h2"
        bodega = datos.find("div", class_=["cellar-name"]).string.strip() 
        denominacion  = datos.find("div",class_=["region"]).string.strip()
        #Estas dos se encuentran bajo un div directamente
        uvas = "".join(datos.find("div",class_=["tags"]).stripped_strings)
        #las uvas se encuentran en el div tags y la cadena está separada por "/" en distintos renglones o 
        #span, por lo que primero hay que hacer un join para unirlas todas y después eliminar los "/" y
        #añadirlos al conjunto de uvas
        for uva in uvas.split("/"):
            tipos_uva.add(uva.strip())
        #leemos cada tipo de uva y la añadimos al set
        
        precio = list(vino.find("p",class_=["price"]).stripped_strings)[0]
        #El precio se encuentra en una etiqueta p con clase price (pone price unique small)
        #Almacena el precio como una lista en la que toma el parametro 0, porque aparecen precio+espacio+€
        dto = vino.find("p",class_=["price"]).find_next_sibling("p",class_="dto")
        #Busca el descuento como la siguiente clase p tras encrontrar price con clase dto
        if dto:
            precio = list(dto.stripped_strings)[0]
        #Si existe dto se sustituye por el precio
        
        conn.execute("""INSERT INTO VINO (NOMBRE, PRECIO, DENOMINACION, BODEGA, TIPO_UVAS) VALUES (?,?,?,?,?)""",
                     (nombre, float(precio.replace(',','.')), denominacion, bodega, uvas))
        #Añades a la tabla vino cada valor con su tipo, en el precio hay que cambiar la , por . antes
    conn.commit()
    #Haces un commit
    
    #Insertamos el la tabla TIPOS_UVAS los elemento sdel conjunto tipos_uva
    for u in list(tipos_uva):
        conn.execute("""INSERT INTO TIPOS_UVAS (NOMBRE) VALUES (?)""",
                     (u,))
        #Añades a la tabla tipos_uva cada tipo de uva
    conn.commit()
    #Haces un commit
    
    cursor = conn.execute("SELECT COUNT(*) FROM VINO")
    #Muestras el número de vinos que hay
    cursor1 = conn.execute("SELECT COUNT(*) FROM TIPOS_UVAS")
    #Muestras el número de tipos de uvas que hay
    messagebox.showinfo("Base Datos",
                        "Base de datos creada correctamente \nHay " + str(cursor.fetchone()[0]) + " vinos y "
                        + str(cursor1.fetchone()[0]) + " tipos de uvas")
    #Mensajito
    conn.close()
    #Acaba el almacenaje

def listar_todos():
    conn = sqlite3.connect('vinos.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT NOMBRE, PRECIO, BODEGA, DENOMINACION FROM VINO")
    conn.close
    listar_vinos(cursor)


def buscar_por_denominacion():  
    def listar(event):
            conn = sqlite3.connect('vinos.db')
            conn.text_factory = str
            cursor = conn.execute("SELECT NOMBRE, PRECIO, BODEGA, DENOMINACION FROM VINO WHERE DENOMINACION LIKE '%" + str(entry.get()) + "%'")
            conn.close
            listar_vinos(cursor)   
    
    conn = sqlite3.connect('vinos.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT DISTINCT DENOMINACION FROM VINO")
    denominaciones = [d[0] for d in cursor]

    
    ventana = Toplevel()
    label = Label(ventana,text="Seleccione una denominaciÃ³n de origen: ")
    label.pack(side=LEFT)
    entry = Spinbox(ventana, width= 30, values=denominaciones)
    entry.bind("<Return>", listar)
    entry.pack(side=LEFT)
    
    conn.close
    

def buscar_por_precio():
    def listar(event):
            conn = sqlite3.connect('vinos.db')
            conn.text_factory = str
            cursor = conn.execute("SELECT NOMBRE, PRECIO, BODEGA, DENOMINACION FROM VINO WHERE PRECIO <= ? ORDER BY PRECIO", (str(entry.get()),))
            conn.close
            listar_vinos(cursor)
    ventana = Toplevel()
    label = Label(ventana, text="Indique el precio mÃ¡ximo: ")
    label.pack(side=LEFT)
    entry = Entry(ventana)
    entry.bind("<Return>", listar)
    entry.pack(side=LEFT)



def buscar_por_uvas():
    def listar(event):
            conn = sqlite3.connect('vinos.db')
            conn.text_factory = str
            cursor = conn.execute("SELECT NOMBRE, TIPO_UVAS FROM VINO where TIPO_UVAS LIKE '%" + str(tipo_uva.get()) + "%'")
            conn.close
            listar_por_uvas(cursor)
    
    conn = sqlite3.connect('vinos.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT NOMBRE FROM TIPOS_UVAS")
    
    tipos_uva=[u[0] for u in cursor]

    v = Toplevel()
    label = Label(v,text="Seleccione el tipo de uva: ")
    label.pack(side=LEFT)
    tipo_uva = Spinbox(v, width= 30, values=tipos_uva)
    tipo_uva.bind("<Return>", listar)
    tipo_uva.pack(side=LEFT)
    
    conn.close()



def listar_por_uvas(cursor):
    v = Toplevel()
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width=150, yscrollcommand=sc.set)
    for row in cursor:
        s = 'VINO: ' + row[0]
        lb.insert(END, s)
        lb.insert(END, "-----------------------------------------------------")
        s = "     TIPOS DE UVA: " + row[1]
        lb.insert(END, s)
        lb.insert(END, "\n\n")
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)

    
    
def listar_vinos(cursor):      
    v = Toplevel()
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width=150, yscrollcommand=sc.set)
    for row in cursor:
        s = 'VINO: ' + row[0]
        lb.insert(END, s)
        lb.insert(END, "------------------------------------------------------------------------")
        s = "     PRECIO: " + str(row[1]) + ' | BODEGA: ' + row[2]+ ' | DENOMINACION: ' + row[3]
        lb.insert(END, s)
        lb.insert(END,"\n\n")
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)



def ventana_principal():
    raiz = Tk()

    menu = Menu(raiz)

    #DATOS
    menudatos = Menu(menu, tearoff=0)
    menudatos.add_command(label="Cargar", command=cargar)
    menudatos.add_command(label="Listar", command=listar_todos)
    menudatos.add_command(label="Salir", command=raiz.quit)
    menu.add_cascade(label="Datos", menu=menudatos)

    #BUSCAR
    menubuscar = Menu(menu, tearoff=0)
    menubuscar.add_command(label="DenominaciÃ³n", command=buscar_por_denominacion)
    menubuscar.add_command(label="Precio", command=buscar_por_precio)
    menubuscar.add_command(label="Uvas", command=buscar_por_uvas)
    menu.add_cascade(label="Buscar", menu=menubuscar)

    raiz.config(menu=menu)

    raiz.mainloop()



if __name__ == "__main__":
    ventana_principal()