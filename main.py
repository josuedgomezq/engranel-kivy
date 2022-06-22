from ast import Global, Pass
from re import A
import kivy
import os
import sqlite3

from kivy.config import Config

from kivy.uix.widget import Widget

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label 
from kivy.uix.screenmanager import ScreenManager, Screen 
from kivy.uix.screenmanager import FadeTransition
from kivy.properties import StringProperty
from kivy.properties import ObjectProperty

import sqlite3
import socket
import time
ESP_IP='192.168.4.1'
ESP_PORT=9999
a=0

lista=[]
def connect_to_database(path):
    try:
        con = sqlite3.connect(path)
        cursor = con.cursor()
        create_table_productos(cursor)
        con.commit()
        con.close()
    except Exception as e:
        print(e)

def create_table_productos(cursor):
    cursor.execute(
        '''
        CREATE TABLE Productos(
            ID INT PRIMARY KEY  NOT NULL,
            Nombre TEXT NOT NULL,
            Codigo TEXT NOT NULL,
            Acumulado FLOAT NOT NULL,
            Puntos INT NOT NULL,
            REUTILIZACION INT NOT NULL
        )'''
    )


class MainWid(ScreenManager):
    def __init__(self):
        super(MainWid,self).__init__()
        self.App_PATH=os.getcwd() # se crea una variable que es directorio donde estara nuestro archivo principal
        self.DB_PATH=self.App_PATH+"/my_database.db"
        self.StartWid = StartWid(self) # recibe un parametro entonces se pone el self,  ya puede acceder a la informacion del mainwid            
        self.InsertDataWid=BoxLayout()  #se crea instanacia databasewid y se pasa el self    
        self.Popup = MessagePopup()
        self.MyGridLayout=MyGridLayout(self)
        self.Productos=Productos(self)
        self.d1=''
        self.ban=0
        
        
        wid = Screen(name='productos')
        wid.add_widget(self.Productos)
        self.add_widget(wid)
        
        wid = Screen(name='camaras')
        wid.add_widget(self.MyGridLayout)
        self.add_widget(wid)

        wid=Screen(name='start')
        wid.add_widget(self.StartWid)
        self.add_widget(wid)
        
        wid = Screen(name='insertdata')
        wid.add_widget(self.InsertDataWid)
        self.add_widget(wid)
        
        self.goto_start()
        
    def goto_productos(self,cliente):
        self.Productos.recibe(cliente)
        self.current = 'productos'
        
    def scan_qr(self):
        self.MyGridLayout.ids.zbar.remove_widget(self.MyGridLayout.ids.registrar)
        self.current='camaras'
        
             

    def goto_cameraz(self,d1,d2):
        self.MyGridLayout.recibir(d1,d2)
        self.current = 'camaras'

        return a
    
    
    def goto_insertdata(self):
        
        self.InsertDataWid.clear_widgets()
        wid = InsertDataWid(self)
        self.InsertDataWid.add_widget(wid)
        self.current = 'insertdata'
        
    def goto_guardar(self,d1,d2,d3):
        
        self.InsertDataWid.clear_widgets()
        wid = InsertDataWid(self)
        wid.insert_data(d1,d2,d3)
        self.InsertDataWid.add_widget(wid)
        self.current = 'insertdata'
    
    def goto_start_completar(self):
    
        self.MyGridLayout.ids.zbar.add_widget(self.MyGridLayout.ids.registrar)
        self.current='start'
        
    def goto_start(self):
        
        self.current='start'
        """_summary_

        Returns:
            _type_: _description_
        """        

class StartWid(BoxLayout):
    def __init__(self,mainwid, **kwargs):#recibe el screenmanager para acceder al path la base 
            super(StartWid,self).__init__()#passamos el startwid
            self.mainwid=mainwid #el mainwid se almacena en esta variable
            

    # funcion para conectar con la base de datos cuando se presione el boton
    def create_database(self):
        #invocamos la funcion y le pasamaos el path:
        connect_to_database(self.mainwid.DB_PATH)
        print("mainwid",self.mainwid)
        self.mainwid.goto_insertdata()
    
        
    def qr_cliente(self):
        self.mainwid.scan_qr()


class Productos(BoxLayout):
    def __init__(self,mainwid,**kwargs):
        super(Productos,self).__init__()
        self.mainwid = mainwid
        self.ban=0   
        cloro_jabonoso= ObjectProperty(None)
 
        
    def recibe(self,cliente):
        self.cliente=cliente
        print("self.client",self.cliente)
        
    
    def completar(self):
        
        Codigo=self.cliente[2]
        print(Codigo)
        con = sqlite3.connect(self.mainwid.DB_PATH)
        acum=self.cliente[3]+int(self.ids.cloro_jabonoso.text)     
                
        sql = 'UPDATE Productos SET Acumulado = ?, Puntos = ?, Reutilizacion = ? WHERE Codigo = ?;'
        cursor = con.cursor()
        
        cursor.execute(sql,(acum,1,4,Codigo))
        con.commit()
        
        
        message = self.mainwid.Popup.ids.message
        self.mainwid.Popup.open()
        self.mainwid.Popup.title = "Compra"
        
        message.text = 'Compra exitosa'
        if con:
            con.close()
        self.ban=1
        self.ids.cloro_jabonoso.text=''

        self.mainwid.goto_start_completar()
    
    def bandera(self):
        ban=self.ban
        return ban


class MyGridLayout(Widget):
    def __init__(self,mainwid,**kwargs):
        super(MyGridLayout,self).__init__()
        self.mainwid = mainwid
        self.InsertDataWid=InsertDataWid(self)
    
    def qr_cliente(self):
        self.ids.zbar.remove_widget(self.ids.registrar)

    def escanear(self):
        
        Codigo=', '.join([str(symbol.data) for symbol in self.ids.zbarcam.symbols]) 
        
        print(str(Codigo))        
        
        if(Codigo==''):
            print("ingrese qr")
        else:
            con = sqlite3.connect(self.mainwid.DB_PATH)
            sql = "SELECT * FROM Productos WHERE Codigo = ?;"
            cursor = con.cursor()
            cursor.execute(sql, (Codigo,))
            registros = cursor.fetchall()

            for r in registros:
                print(r)
            
            sql = "SELECT * FROM Productos"
            cursor = con.cursor()
            cursor.execute(sql)

            clientes=cursor.fetchall()
             #inicializo variables
            clientes_registrados=0
            envases_reutilizados=0
            litros_vendidos=0
            
            for x in clientes:
                clientes_registrados=clientes_registrados+1
            envases_reutilizados=envases_reutilizados+int(x[5])
            print(envases_reutilizados)
            litros_vendidos=litros_vendidos+float(x[3])/1000
            
            acum_litros=0

            acum_litros=float(r[3])/1000 
            
            print(str(r[1]),str(acum_litros) ) 
            
            self.mainwid.goto_productos(r)     


    def recibir(self,d1,d2):
        self.ids.zbar.remove_widget(self.ids.scanqr)
        self.d1=d1
        self.d2=d2
        print("leer",d1,d2)
    
    
    def leer(self):
        connect_to_database(self.mainwid.DB_PATH)
        print(self.d1,self.d2)
        self.d3=', '.join([str(symbol.data) for symbol in self.ids.zbarcam.symbols]) 
        if(self.d3==''):
            print("ingrese qr")
        else:
            self.ids.zbar.add_widget(self.ids.scanqr)
            self.mainwid.goto_guardar(self.d1,self.d2,self.d3)
        
    def off(self):
        self.ids.zbarcam.stop()
    
    def on(self):
        self.ids.zbarcam.start()
        
    def back_to_dbw(self):
        self.mainwid.goto_insertdata()
        

    
class InsertDataWid(BoxLayout):
    def __init__(self,mainwid,**kwargs):
        super(InsertDataWid,self).__init__()
        self.mainwid = mainwid
        

    def datos(self):
        
        d1=self.ids.ti_id.text
        d2 = self.ids.ti_nombre.text
        
        if ''in d1 or d2:
            print("datos vacios")
        if d1!='' and d2!='':
            self.mainwid.goto_cameraz(d1,d2)
                
            
    def insert_data(self,d1,d2,d3):
        Acumulado=0
        Puntos=0
        Reutilizacion=0
        con = sqlite3.connect(self.mainwid.DB_PATH)
        cursor = con.cursor()
        a1 = (d1,d2,d3,Acumulado,Puntos,Reutilizacion)
        s1 = 'INSERT INTO Productos(ID, Nombre, Codigo, Acumulado, Puntos, Reutilizacion)'
        s2 = 'VALUES(%s,"%s","%s",%s,"%s","%s")' % a1
        try:
            cursor.execute(s1+' '+s2)
            con.commit()
            con.close()
            
        except Exception as e:
            message = self.mainwid.Popup.ids.message
            self.mainwid.Popup.open()
            self.mainwid.Popup.title = "Data base error"
            if (d1=='' or d2=='' or d3=='') :
                message.text = 'Uno o más campos están vacíos'
           
            else: 
                message.text = str(e)
            con.close()

        
    def leer(self):
        
        a=self.mainwid.goto_cameraz()
    
    def back_to_dbw(self):
        self.mainwid.goto_start()

            
class Registro(Button):
    def __init__(self,mainwid,**kwargs):#recibe el screenmanager para acceder al path la base
        super(Registro,self).__init__()# superherencia que hereda de databasewid
        self.mainwid = mainwid#el mainwid se almacena en esta variable

    def create_new_producto(self):
        print("hola")


class MessagePopup(Popup):
    pass        

class MainApp(App):
    title='Engranel'
    def build(self):
        return MainWid()
    
if __name__=='__main__':
    MainApp().run()
        