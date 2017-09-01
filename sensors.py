#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

"""
"Wireless pH sensor"
"based on PyQt5, Matplotlib, Arduino, and Sensors"

author: Hao Jin
last edited: Sept. 1, 2017
"""

# === system modules ===
import sys
import os
import time
import random
import json

import matplotlib
matplotlib.use('Qt5Agg') # Make sure that we are using QT5
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from numpy import sin, pi
import numpy as np

from PyQt5.QtWidgets import (QApplication, QMainWindow, QMenu, QGridLayout,
     QSizePolicy, QMessageBox, QWidget, QPushButton, QAction, QHBoxLayout,
     QVBoxLayout, QLCDNumber, QSlider, QLabel, QComboBox)
from PyQt5.QtGui import (QIcon, QColor, QFont)
from PyQt5.QtCore import (QCoreApplication, Qt, QTimer)

# === custom module ===
import serial_comm as comm

# === define classes ===
# basic canvas for matplotlib figure
class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        fig.subplots_adjust(bottom=0.15) # set the botoom space to show the x-axis label
        self.axes = fig.add_subplot(111)

        self.compute_initial_figure()

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass

# static figure
class MyStaticMplCanvas(MyMplCanvas):
    """Simple canvas with a sine plot."""

    def compute_initial_figure(self):
        t = np.arange(0.0, 3.0, 0.01)
        s = sin(2*pi*t)
        self.axes.plot(t, s)

# dynamic figure
class MyDynamicMplCanvas(MyMplCanvas):
    """A canvas that updates itself every second with a new plot."""

    def __init__(self, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)
        timer = QTimer(self)
        timer.timeout.connect(self.update_figure)
        timer.start(1000)

    def compute_initial_figure(self):
        self.axes.plot([0, 1, 2, 3], [1, 2, 0, 4], 'r')

    def update_figure(self):
        # Build a list of 4 random integers between 0 and 10 (both inclusive)
        l = [random.randint(0, 10) for i in range(4)]
        self.axes.cla()
        self.axes.plot([0, 1, 2, 3], l, 'r')
        self.draw()

# dynamic figure for pH plot
class PHMplCanvas(MyMplCanvas):
    """A canvas that updates itself every second with a new plot."""

    def __init__(self, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)

    def compute_initial_figure(self):
        self.x = np.arange(10)
        self.y = np.zeros(10)
        self.li, = self.axes.plot(self.x, self.y, 'r')
        self.axes.set_title("Potentiometric pH sensor", fontweight='bold')
        self.axes.set_xlabel("Time, s")
        self.axes.set_ylabel("Potential, mV")

    def update_figure(self):
        pass

# dynamic figure for temperature plot
class TempMplCanvas(MyMplCanvas):
    """A canvas that updates itself every second with a new plot."""

    def __init__(self, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)

    def compute_initial_figure(self):
        self.x = np.arange(10)
        self.y = np.zeros(10)
        self.li, = self.axes.plot(self.x, self.y, 'b')
        self.axes.set_title("Environment Temperature", fontweight='bold')
        self.axes.set_xlabel("Time, s")
        self.axes.set_ylabel("Temperature, ℃")

    def update_figure(self):
        pass

# main window
class ApplicationWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.showFullScreen() # full screen
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle("Wireless pH sensor")

        # === menu ===
        self.file_menu = QMenu('&File', self)
        self.file_menu.addAction(QIcon('exit.png'), '&Quit', self.fileQuit,
                                 Qt.CTRL + Qt.Key_Q)
        self.data_menu = QMenu('&Data', self)
        self.data_menu.addAction('&Export Data', self.exportData)
        self.data_menu.addAction('&Export Image', self.exportImage)
        self.data_menu.addAction('&Import Data', self.importData)
        self.help_menu = QMenu('&Help', self)
        self.help_menu.addAction('&About', self.about)
        self.menuBar().setNativeMenuBar(False) # for Mac
        self.menuBar().addMenu(self.file_menu)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.data_menu)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)

        # === statusbar ===
        self.statusBar().showMessage("Ready")

        # === layout ===
        self.main_widget = QWidget(self)

        # QVBoxLayout() lines up widgets vertically
        # QHBoxLayout() lines up widgets horizontally
        # QGridLayout() lays out widgets in a grid
        # vbox includes hbox1, hbox2, grid, hbox3, and hbox4 from top to bottom
        vbox = QVBoxLayout(self.main_widget)

        #sc = MyStaticMplCanvas(self.main_widget, width=5, height=4, dpi=100)
        #dc = MyDynamicMplCanvas(self.main_widget, width=5, height=4, dpi=100)
        self.ph_full_plot = PHMplCanvas(self.main_widget, width=14, height=3, dpi=100)
        self.ph_plot = PHMplCanvas(self.main_widget, width=7, height=3, dpi=100)
        self.temp_plot = TempMplCanvas(self.main_widget, width=7, height=3, dpi=100)

        # hbox1 is the full temporal plot of pH value
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.ph_full_plot)
        # hbox1.addStretch(1)

        # hbox2 includes the latest 10 s plot of pH and temperature, respectively
        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.ph_plot)
        hbox2.addWidget(self.temp_plot)
        # hbox2.addStretch(1)

        ph_label = QLabel('pH Value: ')
        temp_label = QLabel('Temperature, ℃: ')

        # set bold font to labels
        myFont=QFont()
        myFont.setBold(True)
        ph_label.setFont(myFont)
        temp_label.setFont(myFont)

        # displays a number with LCD-like digits
        self.ph_lcd = QLCDNumber(self)
        self.temp_lcd = QLCDNumber(self)

        # get the palette
        ph_lcd_palette = self.ph_lcd.palette()
        # foreground color
        ph_lcd_palette.setColor(ph_lcd_palette.WindowText, QColor(255, 0, 0))
        # set the palette
        self.ph_lcd.setPalette(ph_lcd_palette)

        # get the palette
        temp_lcd_palette = self.temp_lcd.palette()
        # foreground color
        temp_lcd_palette.setColor(temp_lcd_palette.WindowText, QColor(0, 0, 255))
        # set the palette
        self.temp_lcd.setPalette(temp_lcd_palette)

        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(ph_label, 1, 0, 1, 1)
        grid.addWidget(self.ph_lcd, 1, 1, 3, 1)

        grid.addWidget(temp_label, 1, 2, 1, 1)
        grid.addWidget(self.temp_lcd, 1, 3, 3, 1)

        # grid.addWidget(humi_label, 4, 0, 1, 1)
        # grid.addWidget(self.humi_lcd, 4, 1, 3, 1)
        #
        # grid.addWidget(freeCl_label, 4, 2, 1, 1)
        # grid.addWidget(self.freeCl_lcd, 4, 3, 3, 1)

        serial_label = QLabel('Serial Port: ')

        self.serial_combobox = QComboBox(self)
        self.serial_combobox.addItem("click refresh")

        refresh_button = QPushButton("Refresh")
        connect_button = QPushButton("Connect")
        disconnect_button = QPushButton("Disconnect")
        refresh_button.clicked.connect(self.refreshButton)
        connect_button.clicked.connect(self.connectButton)
        disconnect_button.clicked.connect(self.disconnectButton)

        # hbox3 includes serial ports display and operation
        hbox3 = QHBoxLayout()
        hbox3.addWidget(serial_label)
        hbox3.addWidget(self.serial_combobox)
        hbox3.addWidget(refresh_button)
        hbox3.addWidget(connect_button)
        hbox3.addWidget(disconnect_button)
        hbox3.addStretch(1)

        # === read pH calibration value ===
        self.readJson()

        # === show previous calibration information ===
        self.cal_label1 = QLabel('Calibration: E = k1*T - k2*T*(pH - pH7)')
        self.cal_label2 = QLabel('E_offset (k1*T): ' +
            str(round(self.ph_cal_dict['ph7_cal'], 1)) + ", mV")
        self.cal_label3 = QLabel('k2*T @ acid: ' +
            str(round((self.ph_cal_dict['ph4_cal']-self.ph_cal_dict['ph7_cal'])/3.0, 1)) +
            ", mV/pH")
        self.cal_label4 = QLabel('k2*T @ alkaline: ' +
            str(round((self.ph_cal_dict['ph7_cal']-self.ph_cal_dict['ph10_cal'])/3.0, 1)) +
            ", mV/pH")
        ph7_cal_button = QPushButton("pH 7 calibration")
        ph7_cal_button.clicked.connect(self.ph7CalButton)
        ph4_cal_button = QPushButton("pH 4 calibration")
        ph4_cal_button.clicked.connect(self.ph4CalButton)
        ph10_cal_button = QPushButton("pH 10 calibration")
        ph10_cal_button.clicked.connect(self.ph10CalButton)

        # hbox4 includes pH calibration buttons and displays
        hbox4 = QHBoxLayout()
        hbox4.addWidget(self.cal_label1)
        hbox4.addWidget(ph7_cal_button)
        hbox4.addWidget(self.cal_label2)
        hbox4.addWidget(ph4_cal_button)
        hbox4.addWidget(self.cal_label3)
        hbox4.addWidget(ph10_cal_button)
        hbox4.addWidget(self.cal_label4)

        # vbox.addWidget(sc)
        # vbox.addWidget(dc)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addLayout(grid)
        vbox.addLayout(hbox3)
        vbox.addLayout(hbox4)

        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)


        # === initial serial ports ===
        self.serial_devices = comm.SerialDevices()
        for i in self.serial_devices.ports:
            self.serial_combobox.addItem(i)

        # === dynamic update ===
        self.timer1 = QTimer(self)
        self.timer1.timeout.connect(self.updateFigs)

        # === make a data dir if run at the first time ===
        self.dataDir = os.path.join(os.getcwd(),"data")
        # print(self.dataDir)
        if not os.path.exists(self.dataDir):
            os.mkdir(self.dataDir)

    # read .json configure file
    def readJson(self):
        self.json_file = 'ph.json'
        try:
            with open(self.json_file) as f_obj:
                self.ph_cal_dict = json.load(f_obj)
        except FileNotFoundError: # create a .json file if it does not exist
            self.ph_cal_dict = {
                'Equations' : 'E = k1*T - k2*T*(pH - pH7)', # calibration equation
                'ph7_cal' : 0,    # mV, k1*T
                'ph4_cal' : 180,    # mV, k1*T + k2a*T*3, k2a means k2 in acid
                'ph10_cal' : -180,    # mV, k1*T - k2b*T*3, k2b means k2 in alkaline
                'T' : 300    # Kelvin, temperature of calibration
            }
            with open(self.json_file, 'w') as f_obj:
                json.dump(self.ph_cal_dict, f_obj, indent=4)


    def ph7CalButton(self):
        # save the current voltage as the calibrated value of pH 7
        self.ph_cal_dict['ph7_cal'] = round(np.mean(self.ph_plot.y),2)
        # save the current temperature for calibration, in Kelvin
        self.ph_cal_dict['T'] = round(np.mean(self.temp_plot.y),2) + 273.15


    def ph4CalButton(self):
        # save the current voltage as the calibrated value of pH 4
        self.ph_cal_dict['ph4_cal'] = round(np.mean(self.ph_plot.y),2)


    def ph10CalButton(self):
        # save the current voltage as the calibrated value of pH 10
        self.ph_cal_dict['ph10_cal'] = round(np.mean(self.ph_plot.y),2)

    # evaluate the current pH value
    def evalPH(self):
        ph7_cal = self.ph_cal_dict['ph7_cal']
        ph4_cal = self.ph_cal_dict['ph4_cal']
        ph10_cal = self.ph_cal_dict['ph10_cal']
        t = self.ph_cal_dict['T']
        delta_mv = np.mean(self.ph_plot.y) - ph7_cal/t*(np.mean(self.temp_plot.y)+273.15)
        if delta_mv >= 0: # acid
            pH = 7 - delta_mv/((ph4_cal - ph7_cal)/3/t*(np.mean(self.temp_plot.y)+273.15))
        else: # alkaline
            pH = 7 - delta_mv/((ph7_cal - ph10_cal)/3/t*(np.mean(self.temp_plot.y)+273.15))
        pH = round(pH, 2)
        if pH <= 0:
            return 0
        elif pH >= 14:
            return 14
        else:
            return pH

    # update the figures and diaplays
    def updateFigs(self):
        line = self.ser.readline() # read data from serial port, one line at a time
        self.data = [float(val) for val in line.split()] # split data to float numbers
        # the data read from the serial port should be 4 float numbers, otherwise neglect it.
        # the 4 float numbers are temperaure, humidity, voltage at reference electrode,
        # and voltage at pH electrode, respectively.
        if(len(self.data) == 4):
            self.temp_lcd.display(self.data[0])
            self.temp_plot.y = np.append(self.temp_plot.y, float(self.data[0]))
            self.temp_plot.y = np.delete(self.temp_plot.y, 0)
            self.temp_plot.li.set_ydata(self.temp_plot.y)
            self.temp_plot.axes.set_ylim(min(self.temp_plot.y)-1, max(self.temp_plot.y)+1)
            self.temp_plot.draw()

            # the galvanic voltage of a pH probe is the voltage difference between the
            # pH electrode (self.data[3]) and reference electrode (self.data[2]).
            self.data_pH = self.evalPH()
            self.ph_lcd.display(self.data_pH)
            self.ph_plot.y = np.append(self.ph_plot.y, float(self.data[3]-self.data[2]))
            self.ph_plot.y = np.delete(self.ph_plot.y, 0)
            self.ph_plot.li.set_ydata(self.ph_plot.y)
            self.ph_plot.axes.set_ylim(min(self.ph_plot.y)-1, max(self.ph_plot.y)+1)
            self.ph_plot.draw()

            self.ph_full_plot.y = np.append(self.ph_full_plot.y, float(self.data[3]-self.data[2]))
            self.ph_full_plot.x = np.append(self.ph_full_plot.x, self.ph_full_plot.x[-1] + 1)
            self.ph_full_plot.li.set_ydata(self.ph_full_plot.y)
            self.ph_full_plot.li.set_xdata(self.ph_full_plot.x)
            self.ph_full_plot.axes.set_ylim(min(self.ph_full_plot.y)-1, max(self.ph_full_plot.y)+1)
            self.ph_full_plot.axes.set_xlim(min(self.ph_full_plot.x), max(self.ph_full_plot.x))
            self.ph_full_plot.draw()

            self.cal_label2.setText('E_offset (k1*T): ' +
                str(round(self.ph_cal_dict['ph7_cal'], 1)) + ", mV")
            self.cal_label3.setText('k2*T @ acid: ' +
                str(round((self.ph_cal_dict['ph4_cal'] - self.ph_cal_dict['ph7_cal'])/3, 1)) +
                ", mV/pH")
            self.cal_label4.setText('k2*T @ alkaline: ' +
                str(round((self.ph_cal_dict['ph7_cal'] - self.ph_cal_dict['ph10_cal'])/3, 1)) +
                ", mV/pH")

            # save measured data to file
            with open(self.filename, 'a') as file_object:
                file_object.write(str(self.data[0]) + "    " +
                    str(self.data[1]) + "    " +
                    str(self.data[2]) + "    " +
                    str(self.data[3]) + "    " +
                    str(self.data[3] - self.data[2]) + "    " +
                    str(self.data_pH) + "\n")


    def fileQuit(self):
        # save the calibration data to .json file
        with open(self.json_file, 'w') as f_obj:
            json.dump(self.ph_cal_dict, f_obj, indent=4)
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QMessageBox.about(self, "About",
"""
Wireless pH sensor

Author: Hao Jin

Version: 0.1

Date: 2017.05.25
"""
            )

    def exportData(self):
        pass

    def exportImage(self):
        pass

    def importData(self):
        pass

    def refreshButton(self):
        """Refresh list of serial devices."""
        self.serial_devices.refresh()
        self.serial_combobox.clear()
        for i in self.serial_devices.ports:
            self.serial_combobox.addItem(i)

    # connect to the selected serial port
    # Bluetooth is a serial port as well as the USB port
    def connectButton(self):
        """connect to serial port"""
        self.ser = comm.serial.Serial(self.serial_combobox.currentText(), baudrate=9600, timeout=1)
        print(self.ser.name)
        self.timer1.start(1000)
        self.statusBar().showMessage("Connected.   " + self.ser.name)
        self.time_stamp = time.strftime("%Y%m%d_%H_%M_%S",time.localtime(time.time()))
        # create a file to store the measured data
        self.filename = "data_" + self.time_stamp + ".txt"
        self.filename = os.path.join(self.dataDir, self.filename)
        with open(self.filename, 'w') as file_object:
            file_object.write("# wireless pH sensor data log\n")
            file_object.write("# Date: " + self.time_stamp + "\n")
            file_object.write("# Temperature (℃), Relative Humidity (%)," +
                " Voltage of Ag/AgCl electrode (mV)," +
                " Voltage of pH electrode (mV)," +
                " Voltage difference (mV)," +
                " Evaluated pH Value\n")
            file_object.write("# \n")

    def disconnectButton(self):
        """disconnect to serial port"""
        self.ser.flush()
        self.ser.close()
        self.timer1.stop()
        self.statusBar().showMessage("Disconnected.")


if __name__ == '__main__':
    qApp = QApplication(sys.argv)
    aw = ApplicationWindow()
    aw.show()
    sys.exit(qApp.exec_())
