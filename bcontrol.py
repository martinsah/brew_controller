#!/usr/bin/python

# MIT License

# Copyright (c) 2018 Martin Klingensmith

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import struct, array, time, io, fcntl
import RPi.GPIO as GPIO
import time
import sys
import paho.mqtt.subscribe as subscribe
import paho.mqtt.publish as publish
import threading

class bcontrol(object):

    def __init__(self):
        self.enable = 4
        self.ch1 = 17
        self.ch2 = 27
        self.BIN = "{0:8b}"
        
        self.htexch = 0.
        self.mash_tun = 0.
        self.hlt = 0.
        self.pwm1 = 0.
        self.pwm2 = 0.
        
        self.rotenc_input = 0.
        self.sub_topics = ["adc/1", "adc/2", "rotenc", "pwm1", "pwm2"]
        
        self.th1 = threading.Thread(target=self.thread_sub, args=())
        self.th1.daemon = True
        self.th1.start()

    def cb(self, client, userdata, message):
        if message.topic == "adc/1":
            self.mash_tun = float(message.payload.decode("utf-8"))
        elif message.topic == "adc/2":
            self.hlt = float(message.payload.decode("utf-8"))
        elif message.topic == "rotenc":
            inp = float(message.payload.decode("utf-8"))
            print ("rotenc %2.0f" % inp)
            self.rotenc_input = self.rotenc_input + inp
        elif message.topic == "pwm1":
            self.pwm1 = float(message.payload.decode("utf-8"))
        elif message.topic == "pwm2":
            self.pwm2 = float(message.payload.decode("utf-8"))
        else:
            print("%s %s" % (message.topic, message.payload.decode("utf-8")))
            
    def thread_sub(self):
        subscribe.callback(self.cb, self.sub_topics, qos=0, userdata=self, hostname="localhost")    
    
    def pid_set(self, setpoint):
        publish.single("pid/set", "%2.2f" % setpoint, hostname="localhost")
    def pwm2_set(self, setpoint):
        publish.single("pwm2", "%2.2f" % setpoint, hostname="localhost")

    def pid_set_sensor_source(self, sensortopic):
        publish.single("sensortopic", sensortopic, hostname="localhost")
        
    def enable_heater_hlt(self):
        print("enable_heater_hlt")

    def enable_heater_boil(self):
        print("enable_heater_boil")
    
    def disable_heaters(self):
        print("disable_heaters")


    # Convert PT100 resistance to temperature (Celsius)
    # this equation works pretty well between 0C and 105C
    # The error is less than 0.1 degree for most of that range.
    def pt100_to_temperature(self,resistance):
        try:
            c=(resistance-100.1)/.3847 
        except:
            c=None
        return c   

    def adc_to_voltage(self,lsb):
        try:
            volts=lsb*4.096/65536.
        except:
            volts=None
        return volts

    def celsius_to_f(self,c):
        try:
            f=c*9./5.+32.
        except:
            f=None
        return f

    def ohms_to_f(self,ohms):
        return self.celsius_to_f(self.pt100_to_temperature(ohms))
        
    def adc_to_f(self,lsb):
        try:
            f=self.celsius_to_f(self.pt100_to_temperature(self.adc_to_voltage(lsb)*1000.))
        except:
            f=None
        return f
        
    def init_temp_sensors(self):
        pass        
        
    def read_temp_sensor(self):
        adc1_ch0 = 1.0
        adc1_ch1 = 1.1
        rtd_0 = (adc1_ch0 - 2.0 * adc1_ch1)*1000.0
        #self.mash_tun = 0 #self.ohms_to_f(rtd_0) + self.cal_mash_tun_sensor
