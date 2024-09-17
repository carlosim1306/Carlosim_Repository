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
from whoosh.query import Term, Or, DateRange

from datetime import datetime, timedelta
# lineas para evitar error SSL
import os, ssl
from _datetime import date
from enum import unique

from whoosh.qparser.syntax import AndGroup
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

def extraer_noticias():
    
    lista=[]
    
    for p in range(1,3):
        req = urllib.request.Request("https://muzikalia.com/category/noticia/page/"+str(p)+"/", headers={'User-Agent': 'Mozilla/5.0'})
        f = urllib.request.urlopen(req)
        s = BeautifulSoup(f, 'lxml')
        l = s.find_all('div', class_='article-content')

        for i in l:
            titulo = i.find('h2', class_='entry-title').a.string
            enlace = i.find('h2', class_='entry-title').a['href']
            fecha = parseo_fecha(i.find('time').string)
            categoria = ",".join(list(i.find('span',class_='cat-links').stripped_strings))
            descripcion = i.find('div', class_='entry-content').p.string
            autor = i.find('span',class_='author').a.string.strip()
            if i.find('span',class_='tag-links'):
                etiquetas = i.find('span',class_='tag-links').get_text().strip()
            else:
                etiquetas=""
                                          
            lista.append((categoria, fecha, titulo, enlace, descripcion, autor, etiquetas))
   
    return lista

def parseo_fecha(fecha):
    meses = {
    'enero': 1,
    'febrero': 2,
    'marzo': 3,
    'abril': 4,
    'mayo': 5,
    'junio': 6,
    'julio': 7,
    'agosto': 8,
    'septiembre': 9,
    'octubre': 10,
    'noviembre': 11,
    'diciembre': 12
    }

    # Dividir la cadena de fecha en partes
    partes = fecha.split()
        
    # Obtener el día, mes y año
    dia = int(partes[0])
    mes = partes[1].split(',')[0].lower()  # Convertir el nombre del mes a minúsculas para la coincidencia del diccionario
    anio = int(partes[2])
        
    # Obtener el número de mes del diccionario
    mes_numero = meses[mes]
        
    # Crear el objeto datetime
    return datetime(anio, mes_numero, dia)
    
def almacenar_datos():
    schem = Schema(categoria = KEYWORD(stored=True, commas=True, lowercase=True), fecha = DATETIME(stored=True), titulo = TEXT(stored=True,phrase=True),
                   enlace = ID(stored=True, unique=True), descripcion = TEXT(stored=True, phrase= True), autor= TEXT(stored=True,phrase=False), 
                   etiquetas = KEYWORD(stored=True, commas=True, lowercase=True))

    if os.path.exists("Index"):
        shutil.rmtree("Index")
    os.mkdir("Index")
    
    #creamos el índice
    ix = create_in("Index", schema=schem)
    #creamos un writer para poder añadir documentos al indice
    writer = ix.writer()
    i=0
    lista=extraer_noticias()
    for j in lista:
        #aÃ±ade cada juego de la lista al Ã­ndice
        writer.add_document(categoria=str(j[0]), fecha = j[1], titulo=str(j[2]), enlace=str(j[3]), descripcion=str(j[4]), autor=str(j[5]), etiquetas=str(j[6]))    
        i+=1
    writer.commit()
    messagebox.showinfo("Fin de indexado", "Se han indexado "+str(i)+ " noticias")          
   
def cargar():
    respuesta = messagebox.askyesno(title="Confirmar",message="Esta seguro que quiere recargar los datos. \nEsta operaciÃ³n puede ser lenta")
    if respuesta:
        almacenar_datos()

def imprimir_lista(cursor):
        v = Toplevel()
        sc = Scrollbar(v)
        sc.pack(side=RIGHT, fill=Y)
        lb = Listbox(v, width=150, yscrollcommand=sc.set)
        for row in cursor:
            lb.insert(END, row['titulo'])
            lb.insert(END, row['enlace'])
            lb.insert(END, row['fecha'])
            lb.insert(END, row['categoria'])
            lb.insert(END, row['autor'])
            lb.insert(END, "\n\n")
        lb.pack(side=LEFT, fill=BOTH)
        sc.config(command=lb.yview)
        
def listar_14():
    ix = open_dir("Index")

    # Obtenemos la fecha de hace 14 días
    fecha_limite = datetime.now() - timedelta(days=14)

    # Creamos un searcher en el índice
    with ix.searcher() as searcher:
        # Creamos una consulta para buscar noticias publicadas en los últimos 14 días
        query = DateRange("fecha", fecha_limite, datetime.now())
        results = searcher.search(query)
            
        # Creamos la ventana y mostramos los resultados
        v = Toplevel()
        v.title("Noticias de las últimas 2 semanas")
        sc = Scrollbar(v)
        sc.pack(side=RIGHT, fill=Y)
        lb = Listbox(v, width=150, yscrollcommand=sc.set)
        for row in results:
            lb.insert(END, row['titulo'])
            lb.insert(END, row['enlace'])
            lb.insert(END, row['fecha'])
            lb.insert(END, row['categoria'])
            lb.insert(END, row['autor'])
            lb.insert(END, "\n\n")
        lb.pack(side=LEFT, fill=BOTH)
        sc.config(command=lb.yview)


def autores_etiquetas():
    def mostrar_lista(event):    
        with ix.searcher() as searcher:
            entrada = str(en.get().lower())
            query = QueryParser("etiquetas", ix.schema).parse('"'+entrada+'"')
            results = searcher.search(query,limit=None)
            imprimir_lista(results)
    
    
    v = Toplevel()
    v.title("Búsqueda por etiquetas")
    l = Label(v, text="Seleccione temÃ¡tica a buscar:")
    l.pack(side=LEFT)
    
    ix=open_dir("Index")      
    with ix.searcher() as searcher:
        lista_etiquetas = [i.decode('utf-8') for i in searcher.lexicon('etiquetas')]
    
    en = Spinbox(v, values=lista_etiquetas, state="readonly")
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)

def resumen_titulo():
    def mostrar_lista(event):
        ix=open_dir("Index")   
        with ix.searcher() as searcher:
            query = MultifieldParser(["titulo","descripcion"], ix.schema, group=AndGroup).parse('"'+ str(en.get()) + '"')
            results = searcher.search(query,limit=None)
            imprimir_lista(results)
    
    v = Toplevel()
    v.title("Bússqueda por Título y descripción")
        
    l1 = Label(v, text="Escriba frase del título o descripción:")
    l1.pack(side=LEFT)
    en = Entry(v, width=75)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)

def titulo_fecha():

    def mostrar_lista():
        fecha_ingresada = en_fecha.get()
        palabras_ingresadas = en_palabras.get()
        try:
            fecha_obj = datetime.strptime(fecha_ingresada, '%d-%m-%Y')
        except ValueError:
            messagebox.showerror("Error", "Formato de fecha incorrecto. Introduzca la fecha en formato dd-mm-aaaa")
            return

        fecha_maxima = fecha_obj + timedelta(days=1)

        ix = open_dir("Index")

        with ix.searcher() as searcher:
            query = MultifieldParser(["titulo"], ix.schema).parse('fecha:[' + fecha_ingresada + ' TO ' + fecha_maxima + '] AND titulo:(' + palabras_ingresadas + ')')
            results = searcher.search(query)
            imprimir_lista(results)

    v = Toplevel()
    v.title("Modificar Fecha Estreno")
    l = Label(v, text="Introduzca Fecha DD-MM-AAAA:")
    l.pack(side=LEFT)
    en_fecha = Entry(v)
    en_fecha.pack(side=LEFT)
    l1 = Label(v, text="Introduzca el Título:")
    l1.pack(side=LEFT)
    en_palabras = Entry(v)
    en_palabras.pack(side=LEFT)
    bt = Button(v, text='Buscar', command=mostrar_lista)
    bt.pack(side=LEFT)
    
def eliminar_categoria():
    def eliminar():
        ix=open_dir("Index")
        lista=[]
        with ix.searcher() as searcher:
            query = QueryParser("categoria", ix.schema).parse(str(en.get()))
            results = searcher.search(query, limit=None) 
            v = Toplevel()
            v.title("Listado de noticias a Eliminar")
            v.geometry('800x150')
            sc = Scrollbar(v)
            sc.pack(side=RIGHT, fill=Y)
            lb = Listbox(v, yscrollcommand=sc.set)
            lb.pack(side=BOTTOM, fill = BOTH)
            sc.config(command = lb.yview)
            for r in results:
                lb.insert(END,r['titulo'])
                lb.insert(END,r['enlace'])
                lb.insert(END,r['fecha'])
                lb.insert(END,r['categoria'])
                lb.insert(END,r['autor'])
                lb.insert(END,'')
                lista.append(r)
        respuesta = messagebox.askyesno(title="Confirmar",message="Esta seguro que quiere eliminar la categorias de estas noticias?")
        if respuesta:
            writer = ix.writer()
            for r in lista:
                writer.delete_by_term("enlace", r['enlace'])
            writer.commit()
    
    ix=open_dir("Index")      
    with ix.searcher() as searcher:
        lista_categoria = [i.decode('utf-8') for i in searcher.lexicon('categoria')]
    
    v = Toplevel()
    v.title("Eliminar ")
    l = Label(v, text="Introduzca una Categoria:")
    l.pack(side=LEFT)
    en = Spinbox(v, values=lista_categoria, state="readonly")
    en.pack(side=LEFT)
    bt = Button(v, text='Eliminar', command=eliminar)
    bt.pack(side=LEFT)

    
def ventana_principal():
    raiz = Tk()
    menu = Menu(raiz)

    #DATOS
    menudatos = Menu(menu, tearoff=0)
    menudatos.add_command(label="Cargar", command=cargar)
    menudatos.add_command(label="Listar ultimos 14 dias", command=listar_14)
    menudatos.add_command(label="Salir", command=raiz.quit)
    menu.add_cascade(label="Datos", menu=menudatos)

    #BUSCAR
    menubuscar = Menu(menu, tearoff=0)
    menubuscar.add_command(label="Autores por etiquetas", command=autores_etiquetas)
    menubuscar.add_command(label="Resumen y Titulo", command=resumen_titulo)
    menubuscar.add_command(label="Titulo y Fecha", command=titulo_fecha)
    menubuscar.add_command(label="Elimina Categoria", command=eliminar_categoria)
    menu.add_cascade(label="Buscar y Modificar", menu=menubuscar)

    raiz.config(menu=menu)

    raiz.mainloop()


if __name__ == "__main__":
    ventana_principal()