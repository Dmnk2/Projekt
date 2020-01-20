"""
import RPi.GPIO as GPIO
import board
import time
import busio
import adafruit_bmp280
import adafruit_htu21d
from adafruit_htu21d import HTU21D
"""
import sqlite3
from datetime import datetime

import kivy
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy_garden.graph import Graph, MeshLinePlot

sm = ScreenManager()
kivy.require('1.0.7')

mainScreen = Screen(name='main')
graphScreen = Screen(name='graphs')
sm.add_widget(mainScreen)
sm.add_widget(graphScreen)

sm.current = 'main'
graph_data = '0'
Cas_zapisu = 0

class MyGrid(GridLayout):
    def __init__(self, **kwargs):
        super(MyGrid, self).__init__(**kwargs)
        self.cols = 1

        self.temButton = Button(text="25 °C")
        self.temButton.bind(on_press=self.temButtonPressed)

        self.humButton = Button(text="22 %")
        self.humButton.bind(on_press=self.humButtonPressed)

        self.preButton = Button(text="995 hPa")
        self.preButton.bind(on_press=self.preButtonPressed)

        self.mainLayout = GridLayout(cols=2)
        self.mainLayout.add_widget(Label(text="Teplota: "))
        self.mainLayout.add_widget(self.temButton)

        self.mainLayout.add_widget(Label(text="Vlhkost: "))
        self.mainLayout.add_widget(self.humButton)

        self.mainLayout.add_widget(Label(text="Tlak: "))
        self.mainLayout.add_widget(self.preButton)

        self.add_widget(self.mainLayout)

    def temButtonPressed(self, *args):
        global graph_data
        graph_data = "tem"
        sm.current = "graphs"

    def humButtonPressed(self, *args):
        global graph_data 
        graph_data = "hum"
        sm.current = "graphs"
        

    def preButtonPressed(self, *args):
        global graph_data
        graph_data = "pre"
        sm.current = "graphs"
        

    def update(self, dt):
        data = dataSQL()
        now = datetime.now()
        cas = now.strftime("%H:%M")
        global Cas_zapisu
        """
        self.temButton.text = str(round(MyApp.bme280.temperature,1))+"C"
        self.humButton.text = str(round(MyApp.htu21d.relative_humidity,1))+"%"
        self.preButton.text = str(round(MyApp.bme280.pressure,1))+"hPa"
        """
        if Cas_zapisu == 360:
            data.zapis(cas, round(MyApp.bme280.temperature,1), round(MyApp.htu21d.relative_humidity,1), round(MyApp.bme280.pressure,1))
            Cas_zapisu = 0
        else:
            Cas_zapisu += 1 

class MyGraphs(GridLayout):
    def __init__(self, **kwargs):
        super(MyGraphs, self).__init__(**kwargs)
        self.cols = 1

        # Graphs init
        self.graph = graph = Graph(xlabel='t', ylabel='C', x_ticks_minor=1,
        x_ticks_major=5, y_ticks_major=10,
        y_grid_label=True, x_grid_label=True, padding=5,
        x_grid=True, y_grid=True, xmin=-0, xmax=10, ymin=-1, ymax=1)


        self.backButton = Button(text="Back", size_hint=(1,.1))
        self.backButton.bind(on_press=self.backButtonPressed)

        self.mainLayout = GridLayout(rows=2)
        self.mainLayout.add_widget(graph)
        self.mainLayout.add_widget(self.backButton)
        self.add_widget(self.mainLayout)

    def setPoints(self, points, maxY, label):
        self.graph.ylabel = label
        self.graph.ymax = maxY
        self.graph.xmax = points[len(points)-1][0]
        self.graph.xmin = points[0][0]

        # Nastaveni skaly osy X
        self.graph.x_ticks_major = round((self.graph.xmax-self.graph.xmin)/10)

        plot = MeshLinePlot(color=[0, 1, 0, 1])

        plot.points = points
        self.graph.add_plot(plot)

        # Nula
        plot = MeshLinePlot(color=[1, 0, 0, 1])

        plot.points = [(points[0][0], 0),(points[len(points)-1][0], 0)]
        self.graph.add_plot(plot)

    def backButtonPressed(self, *args):
        sm.current = "main"

class dataSQL():
    def zapis(self, cas, teplota, vlhkost, tlak):
        conn = sqlite3.connect('my.db')
        c = conn.cursor()
        sqlite_insert_with_param = """INSERT INTO data (cas,teplota,vlhkost,tlak)
                    VALUES(?,?,?,?);"""
        data_tuple = (cas, teplota, vlhkost, tlak)
        c.execute(sqlite_insert_with_param,data_tuple)
        conn.commit()
        conn.close()

    def cteni(self):
        conn = sqlite3.connect('my.db')
        c = conn.cursor()
        c.execute("SELECT * FROM data ORDER BY id DESC LIMIT 10")
        kam = c.fetchall()
        conn.commit()
        conn.close()
        return kam




class MyApp(App):
    """
    bme28_i2c = busio.I2C(3,2)
    bme280 = adafruit_bmp280.Adafruit_BMP280_I2C(bme28_i2c,0x76)
    htu21d_i2c = busio.I2C(1,0)
    htu21d = HTU21D(htu21d_i2c)
    teplota = bme280.temperature
    vlhkost = htu21d.relative_humidity
    tlak = bme280.pressure
    """
    def build(self):

        # Graphs screen
        self.graphs = MyGraphs()
        graphScreen.add_widget(self.graphs)
        graphScreen.bind(on_pre_enter=self.on_graph_enter)

        # Main screen
        grid = MyGrid()
        mainScreen.add_widget(grid)
        Clock.schedule_interval(grid.update,5)

        return sm

    def on_graph_enter(self, *args):
        h_tem = []
        h_hum = []
        h_pre = []
        temp = []
        hodnoty = []
        casy = []
        sql = dataSQL()
        data = sql.cteni()
        global graph_data
        for object in data:
            casy.append(object[1])
            h_tem.append(object[2])
            h_hum.append(object[3])
            h_pre.append(object[4])
        # Posleni do graphs set Values
        if graph_data == "tem":
            for i, object in enumerate(h_tem):
                temp.append(object)
                temp.append(i)
                hodnoty.append(temp)
                temp = []
        elif graph_data == "hum":
            for i, object in enumerate(h_hum):
                temp.append(object)
                temp.append(i)
                hodnoty.append(temp)
                temp = []
        elif graph_data == "pre":
            for i, object in enumerate(h_pre):
                temp.append(object)
                temp.append(i)
                hodnoty.append(temp)
                temp = []
        
        print(data)
        print(hodnoty)
        #self.graphs.setPoints(hodnoty, 50, "C")



if __name__ == '__main__':
    MyApp().run()

        
        