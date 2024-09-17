#encoding:latin-1
import os
from datetime import datetime
from whoosh.index import create_in,open_dir
from whoosh.fields import Schema, TEXT, KEYWORD, DATETIME, ID
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh import qparser, query
from tkinter import *
from tkinter import messagebox

agenda={}
#En un inicio estar� vac�a y la generaremos con los correos
dirdocs="Docs\Correos"
#Directorio para los correos, cuelga del index que se llamar� Docs
dirindex="Index"
#Directorio para el index, se generar� aparte del Docs\
dirage="Docs\Agenda"
#Directorio para la agenda, cuelga del index que se llamar� Docs

#Crea un indice desde los documentos contenidos en dirdocs
#El indice lo crea en el directorio dirindex 
def crea_index():
    def carga():
        sch = Schema(remitente=TEXT(stored=True), destinatarios=KEYWORD(stored=True),
                     #KEYWORD almacena palabras separadas por comas o espacios
                     fecha=DATETIME(stored=True), asunto=TEXT(stored=True), 
                     contenido=TEXT(stored=True,phrase=False), nombrefichero=ID(stored=True))
                    #El par�metro pharase=False indica que la coincidencia puede hacerse de manera indivi_
                    #dual por palabras sin tener que coincidir el texto completo al hacer una consulta
        #Aqu� indicamos todos los atributos y sus tipos posibles
        
        ix = create_in(dirindex, schema=sch)
        #Indicamos que el �ndice comienza en dirindex
        writer = ix.writer()
        #Damos permiso de escritura sobre el �ndice
        for docname in os.listdir(dirdocs):
            #leemos todos los txt bajo el directorio Docs\Correos
            if not os.path.isdir(dirdocs+docname):
                #Si la ruta Docs\Correos\nombre_fichero no existe, la a�ade
                add_doc(writer, dirdocs, docname)  
                #add_doc es una funci�n definida m�s abajo no es cosa de python
                #aqu� entran los parseos l�nea a l�nea
                                
        writer.commit()
        messagebox.showinfo("INDICE CREADO", "Se han cargado " + str(ix.reader().doc_count()) + " documentos")
        #Crea el �ndice y cuenta los documentos cargados
        
    if not os.path.exists(dirdocs):
        #Si no existe el directorio Docs\Correos, da un error
        messagebox.showerror("ERROR", "No existe el directorio de documentos " + dirdocs)
    else:
        #Si existe el directorio Docs\Correos y no se ha creado el index a�n se crea el directorio index
        if not os.path.exists(dirindex):
            os.mkdir(dirindex)
            
    if not len(os.listdir(dirindex))==0:
        #Comprueba si ya hay datos en el index por si queremos volver a cargarlo, si est� vac�o lo carga
        #directamente
        respuesta = messagebox.askyesno("Confirmar","Indice no vac�o. Desea reindexar?") 
        if respuesta:
            carga()           
    else:
        carga()
        
     
def crea_agenda():
    try:
        fileobj=open(dirage+'\\'+"agenda.txt", "r")
        #abre el archivo con ruta Docs\Agenda\agenda.txt
        email=fileobj.readline()
        #lee la primera l�nea, en este caso es un email, la siguiente l�nea siempre ser� el nombre
        while email:
            nombre=fileobj.readline()
            #Carga el nombre que sigue al email
            agenda[email.strip()]=nombre.strip()
            #Crea en el diccionario agenda(est� al inicio) una entrada cuya clave es email y valor nombre
            email=fileobj.readline()
            #Carga la siguiente l�nea que es un email o vac�o
    except:
        #Si no existe la ruta Docs\Agenda\agenda.txt, se muestra un error
        messagebox.showerror("ERROR", "No se ha podido crear la agenda. Compruebe que existe el fichero "+dirage+'\\'+"agenda.txt")
  
def add_doc(writer, path, docname):
    try:
        fileobj=open(path+'\\'+docname, "r")
        #Abrimos el fichero del directorio Docs\Correos\nombre_fichero y vamos leyendo l�nea a l�nea
        #parseando los datos que van apareciendo
        rte=fileobj.readline().strip()
        dtos=fileobj.readline().strip()
        f=fileobj.readline().strip()
        dat=datetime.strptime(f,'%Y%m%d')
        ast=fileobj.readline().strip()
        ctdo=fileobj.read()
        #En este caso cono el asunto puede ocupar m�s de una l�nea lee todo con read()
        fileobj.close()           
        
        writer.add_document(remitente=rte, destinatarios=dtos, fecha=dat, asunto=ast, contenido=ctdo, nombrefichero=docname)
        #Tras esto se rellenan todos los datos que definimos en Schema, al inicio
    
    except:
        messagebox.showerror("ERROR", "Error: No se ha podido a�adir el documento "+path+'\\'+docname) 
   
def asunto_o_cuerpo():
    def listar_asunto_o_cuerpo(event):
            ix=open_dir(dirindex)   
            with ix.searcher() as searcher:
                myquery = MultifieldParser(["asunto","contenido"], ix.schema).parse(str(entry.get()))
                results = searcher.search(myquery)
                listar(results)
            
    v = Toplevel()
    label = Label(v, text="Introduzca consulta sobre asunto o contenido: ")
    label.pack(side=LEFT)
    entry = Entry(v)
    entry.bind("<Return>", listar_asunto_o_cuerpo)
    entry.pack(side=LEFT)
    
        
def posteriores_a_fecha():  
    def listar_fecha(event):
            myquery='{'+ str(entry.get()) + ' TO]'
            ix=open_dir(dirindex)   
            try:
                with ix.searcher() as searcher:
                    query = QueryParser("fecha", ix.schema).parse(myquery)
                    results = searcher.search(query)
                    listar(results)
            except:
                messagebox.showerror("ERROR", "Formato de fecha incorrecto")
            
    v = Toplevel()
    label = Label(v, text="Introduzca la fecha (AAAAMMDD): ")
    label.pack(side=LEFT)
    entry = Entry(v)
    entry.bind("<Return>", listar_fecha)
    entry.pack(side=LEFT)
              

def spam():
    def listar_spam(event):
        ix=open_dir(dirindex)   
        with ix.searcher() as searcher:
            query = QueryParser("asunto", ix.schema,group=qparser.OrGroup).parse(str(entry.get()))
            results = searcher.search(query)
            
            v1 = Toplevel()
            sc = Scrollbar(v1)
            sc.pack(side=RIGHT, fill=Y)
            lb = Listbox(v1, width=100, yscrollcommand=sc.set)
            for row in results:
                s = 'FICHERO: ' + row['nombrefichero']
                lb.insert(END, s)
                s = 'REMITENTE: ' + agenda[row['remitente']]
                lb.insert(END, s)
                lb.insert(END, "-------------------------------")       
            lb.pack(side=LEFT, fill=BOTH)
            sc.config(command=lb.yview)        
    v = Toplevel()
    label = Label(v, text="Introduzca palabras spam: ")
    label.pack(side=LEFT)
    entry = Entry(v)
    entry.bind("<Return>", listar_spam)
    entry.pack(side=LEFT)                   

def cargar():
    crea_index()
    crea_agenda()
    
def listar(results):      
    v = Toplevel()
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width=150, yscrollcommand=sc.set)
    for row in results:
        s = 'REMITENTE: ' + row['remitente']
        lb.insert(END, s)       
        s = "DESTINATARIOS: " + row['destinatarios']
        lb.insert(END, s)
        s = "FECHA: " + row['fecha'].strftime('%d-%m-%Y')
        lb.insert(END, s)
        s = "ASUNTO: " + row['asunto']
        lb.insert(END, s)
        s = "CUERPO: " + row['contenido']
        lb.insert(END, s)
        lb.insert(END,"------------------------------------------------------------------------\n")
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)


def ventana_principal():
    def listar_todo():
        ix=open_dir(dirindex)
        with ix.searcher() as searcher:
            results = searcher.search(query.Every(),limit=None)
            listar(results) 
    
    raiz = Tk()

    menu = Menu(raiz)

    #DATOS
    menudatos = Menu(menu, tearoff=0)
    menudatos.add_command(label="Cargar", command=cargar)
    menudatos.add_command(label="Listar", command=listar_todo)
    menudatos.add_command(label="Salir", command=raiz.quit)
    menu.add_cascade(label="Datos", menu=menudatos)

    #BUSCAR
    menubuscar = Menu(menu, tearoff=0)
    menubuscar.add_command(label="Asunto o Cuerpo", command=asunto_o_cuerpo)
    menubuscar.add_command(label="Posteriores a una Fecha", command=posteriores_a_fecha)
    menubuscar.add_command(label="Spam", command=spam)
    menu.add_cascade(label="Buscar", menu=menubuscar)

    raiz.config(menu=menu)

    raiz.mainloop()


if __name__ == "__main__":
    ventana_principal()