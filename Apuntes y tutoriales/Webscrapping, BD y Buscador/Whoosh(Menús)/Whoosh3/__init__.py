#encoding:utf-8

from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import sqlite3
import lxml
import re, shutil
from whoosh import qparser, query
from whoosh.index import create_in,open_dir
from whoosh.fields import Schema, TEXT, NUMERIC, KEYWORD, ID, DATETIME
from whoosh.qparser import QueryParser, OrGroup, MultifieldParser
from whoosh.query import Term, Or

from datetime import datetime
# lineas para evitar error SSL
import os, ssl
from _datetime import date
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context
    
PAGINAS = 2  #número de páginas

def extraer_peliculas():
    
    lista=[]
    
    for i in range(1,PAGINAS):
        f = urllib.request.urlopen("https://www.elseptimoarte.net/estrenos/"+str(i)+"/")
        s = BeautifulSoup(f, "lxml")
        lista_link_peliculas = s.find("ul", class_="elements").find_all("li")
        
        for link_pelicula in lista_link_peliculas:
            url_peli = "https://www.elseptimoarte.net/"+link_pelicula.a['href']
            f = urllib.request.urlopen("https://www.elseptimoarte.net/"+link_pelicula.a['href'])
            s = BeautifulSoup(f, "lxml")
            #Le damos el formato al beautifulsoup
            datos = s.find("main", class_="informativo").find("section",class_="highlight").div.dl
            titulo_original = datos.find("dt",string="Título original").find_next_sibling("dd").string.strip()
            #si no tiene título se pone el título original
            if (datos.find("dt",string="Título")):
                titulo = datos.find("dt",string="Título").find_next_sibling("dd").string.strip()
            else:
                titulo = titulo_original      
            pais = "".join(datos.find("dt",string="País").find_next_sibling("dd").stripped_strings)
            fecha = datetime.strptime(datos.find("dt",string="Estreno en España").find_next_sibling("dd").string.strip(), '%d/%m/%Y')
    
            generos_director = s.find("div",id="datos_pelicula")
            #Nos movemos al contenedor datos_pelicula para sacar más data
            generos = "".join(generos_director.find("p",class_="categorias").stripped_strings)
            director = "".join(generos_director.find("p",class_="director").stripped_strings)
            sinopsis = s.find("div", class_="info").get_text
            
            lista.append((titulo,titulo_original, fecha, pais, generos, director, sinopsis, url_peli))
    
    return lista

def almacenar_datos():
    #define el esquema de la informaciÃ³n
    schem = Schema(titulo=TEXT(stored=True,phrase=False),titulo_original=TEXT(stored=True,phrase=False), fecha= DATETIME(stored=True),
                   pais=KEYWORD(stored=True,commas=True,lowercase=True), generos=KEYWORD(stored=True,commas=True), director=KEYWORD(stored=True,commas=True), sinopsis=TEXT(stored=True,phrase=False), url_peli=ID(stored=True, unique=True))
    
    #Para hacer modificaciones tipo update o delete el atributo debe ser de tipo ID
    #Se pone el stored=True si vamos a mostrar el valor en algún momento
    #Se utiliza Keyword para guardar las las palabras o conjunto de palabras separados por comas
    
    #eliminamos el directorio del Añdice, si existe
    if os.path.exists("Index"):
        shutil.rmtree("Index")
    os.mkdir("Index")
    
    #creamos el índice
    ix = create_in("Index", schema=schem)
    #creamos un writer para poder añadir documentos al indice
    writer = ix.writer()
    i=0
    lista=extraer_peliculas()
    for j in lista:
        #aÃ±ade cada juego de la lista al Ã­ndice
        writer.add_document(titulo=str(j[0]),titulo_original=str(j[1]), fecha=j[2], pais=str(j[3]), generos=str(j[4]), director=str(j[5]), sinopsis=str(j[6]), url_peli=str(j[7]))    
        i+=1
    writer.commit()
    messagebox.showinfo("Fin de indexado", "Se han indexado "+str(i)+ " películas")          
   
def cargar():
    respuesta = messagebox.askyesno(title="Confirmar",message="Esta seguro que quiere recargar los datos. \nEsta operaciÃ³n puede ser lenta")
    if respuesta:
        almacenar_datos()
         
def imprimir_lista(cursor):
    v = Toplevel()
    v.title("Películas el séptimo arte")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END,row['titulo'])
        lb.insert(END,row['titulo_original'])
        lb.insert(END,row['fecha'])
        lb.insert(END,row['pais'])
        lb.insert(END,row['generos'])
        lb.insert(END,row['director'])
        lb.insert(END,row['sinopsis'])
        lb.insert(END,row['url_peli'])
        lb.insert(END,"\n\n")
    lb.pack(side=LEFT,fill=BOTH)
    sc.config(command = lb.yview)

# permite buscar palabras en el "titulo" o en la "sinopsis" de las peliculas 
def buscar_titulo_sinopsis():
    def mostrar_lista(event):
        #abrimos el Ã­ndice
        ix=open_dir("Index")
        #creamos un searcher en el Ã­ndice    
        with ix.searcher() as searcher:
            #se crea la consulta: buscamos en los campos "titulo" o "sinopsis" alguna de las palabras que hay en el Entry "en"
            #se usa la opciÃ³n OrGroup para que use el operador OR por defecto entre palabras, en lugar de AND
            query = MultifieldParser(["titulo","sinopsis"], ix.schema, group=OrGroup).parse(str(en.get()))
            #llamamos a la funciÃ³n search del searcher, pasÃ¡ndole como parÃ¡metro la consulta creada
            results = searcher.search(query) #sÃ³lo devuelve los 10 primeros
            #recorremos los resultados obtenidos(es una lista de diccionarios) y mostramos lo solicitado
            v = Toplevel()
            v.title("Listado de Peliculas")
            v.geometry('800x150')
            sc = Scrollbar(v)
            sc.pack(side=RIGHT, fill=Y)
            lb = Listbox(v, yscrollcommand=sc.set)
            lb.pack(side=BOTTOM, fill = BOTH)
            sc.config(command = lb.yview)
            #Importante: el diccionario solo contiene los campos que han sido almacenados(stored=True) en el Schema
            for r in results: 
                lb.insert(END,r['titulo'])
                lb.insert(END,r['titulo_original'])
                lb.insert(END,r['director'])
                lb.insert(END,'')
    
    v = Toplevel()
    v.title("Busqueda por TÃ­tulo o Sinopsis")
    l = Label(v, text="Introduzca las palabras a buscar:")
    l.pack(side=LEFT)
    en = Entry(v)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)
        


# permite buscar las pelÃ­culas de un "gÃ©nero"
def buscar_generos():
    def mostrar_lista(event):
        ix=open_dir("Index")      
        with ix.searcher() as searcher:
            #lista de todos los gÃ©neros disponibles en el campo de gÃ©neros
            lista_generos = [i.decode('utf-8') for i in searcher.lexicon('generos')]
            # en la entrada ponemos todo en minÃºsculas
            entrada = str(en.get().lower())
            #si la entrada no estÃ¡ en la lista de gÃ©neros disponibles, da un error e informa de los gÃ©neros disponibles     
            if entrada not in lista_generos:
                messagebox.showinfo("Error", "El criterio de bÃºsqueda no es un gÃ©nero existente\nLos gÃ©neros existentes son: " + ",".join(lista_generos))
                return
            
            query = QueryParser("generos", ix.schema).parse('"'+entrada+'"')
            results = searcher.search(query, limit=20) #sÃ³lo devuelve los 20 primeros
            v = Toplevel()
            v.title("Listado de PelÃ­culas")
            v.geometry('800x150')
            sc = Scrollbar(v)
            sc.pack(side=RIGHT, fill=Y)
            lb = Listbox(v, yscrollcommand=sc.set)
            lb.pack(side=BOTTOM, fill = BOTH)
            sc.config(command = lb.yview)
            for r in results:
                lb.insert(END,r['titulo'])
                lb.insert(END,r['titulo_original'])
                lb.insert(END,r['pais'])
                lb.insert(END,'')
    
    v = Toplevel()
    v.title("Busqueda por GÃ©nero")
    l = Label(v, text="Introduzca gÃ©nero a buscar:")
    l.pack(side=LEFT)
    en = Entry(v)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)

# permite buscar una pelÃ­cula por su tÃ­tulo y modificar su fecha de estreno
def modificar_fecha():
    def modificar():
        #comprobamos el formato de la entrada
        if(not re.match("\d{8}",en1.get())):
            messagebox.showinfo("Error", "Formato del rango de fecha incorrecto")
            return
        ix=open_dir("Index")
        lista=[]    # lista de las pelÃ­culas a modificar, usamos el campo url (unique) para updates 
        with ix.searcher() as searcher:
            query = QueryParser("titulo", ix.schema).parse(str(en.get()))
            results = searcher.search(query, limit=None) 
            v = Toplevel()
            v.title("Listado de PelÃ­culas a Modificar")
            v.geometry('800x150')
            sc = Scrollbar(v)
            sc.pack(side=RIGHT, fill=Y)
            lb = Listbox(v, yscrollcommand=sc.set)
            lb.pack(side=BOTTOM, fill = BOTH)
            sc.config(command = lb.yview)
            for r in results:
                lb.insert(END,r['titulo'])
                lb.insert(END,r['fecha'])
                lb.insert(END,'')
                lista.append(r) #cargamos la lista con los resultados de la bÃºsqueda
        # actualizamos con la nueva fecha de estreno todas las pelÃ­culas de la lista
        respuesta = messagebox.askyesno(title="Confirmar",message="Esta seguro que quiere modificar las fechas de estrenos de estas peliculas?")
        if respuesta:
            writer = ix.writer()
            for r in lista:
                writer.update_document(url=r['url'], fecha=datetime.strptime(str(en1.get()),'%Y%m%d'), titulo=r['titulo'], titulo_original=r['titulo_original'], pais=r['pais'], director=r['director'], generos=r['generos'], sinopsis=r['sinopsis'])
            writer.commit()
    
    v = Toplevel()
    v.title("Modificar Fecha Estreno")
    l = Label(v, text="Introduzca TÃ­tulo PelÃ­cula:")
    l.pack(side=LEFT)
    en = Entry(v)
    en.pack(side=LEFT)
    l1 = Label(v, text="Introduzca Fecha Estreno AAAAMMDD:")
    l1.pack(side=LEFT)
    en1 = Entry(v)
    en1.pack(side=LEFT)
    bt = Button(v, text='Modificar', command=modificar)
    bt.pack(side=LEFT)

def buscar_fecha():
    def mostrar_lista(event):
        #comprobamos el formato de la entrada
        if(not re.match("\d{8}\s+\d{8}",en.get())):
            messagebox.showinfo("Error", "Formato del rango de fecha incorrecto")
            return
        ix=open_dir("Index")      
        with ix.searcher() as searcher:
            
            aux = en.get().split()
            rango_fecha = '['+ aux[0] + ' TO ' + aux[1] +']'
            query = QueryParser("fecha", ix.schema).parse(rango_fecha)
            results = searcher.search(query,limit=None) #devuelve todos los resultados
            v = Toplevel()
            v.title("Listado de PelÃ­culas")
            v.geometry('800x150')
            sc = Scrollbar(v)
            sc.pack(side=RIGHT, fill=Y)
            lb = Listbox(v, yscrollcommand=sc.set)
            lb.pack(side=BOTTOM, fill = BOTH)
            sc.config(command = lb.yview)
            for r in results:
                lb.insert(END,r['titulo'])
                lb.insert(END,r['fecha'])
                lb.insert(END,'')
    
    v = Toplevel()
    v.title("Busqueda por Fecha")
    l = Label(v, text="Introduzca rango de fechas AAAAMMDD AAAAMMDD:")
    l.pack(side=LEFT)
    en = Entry(v)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)


def ventana_principal():
        
    root = Tk()
    menubar = Menu(root)
    
    datosmenu = Menu(menubar, tearoff=0)
    datosmenu.add_command(label="Cargar", command=cargar)
    datosmenu.add_separator()   
    datosmenu.add_command(label="Salir", command=root.quit)
    
    menubar.add_cascade(label="Datos", menu=datosmenu)
    
    buscarmenu = Menu(menubar, tearoff=0)
    buscarmenu.add_command(label="TÃ­tulo o Sinopsis", command=buscar_titulo_sinopsis)
    buscarmenu.add_command(label="GÃ©neros", command=buscar_generos)
    buscarmenu.add_command(label="Fecha", command=buscar_fecha)
    buscarmenu.add_command(label="Modificar Fecha", command=modificar_fecha)
    
    menubar.add_cascade(label="Buscar", menu=buscarmenu)
        
    root.config(menu=menubar)
    root.mainloop()


if __name__ == "__main__":
    ventana_principal()