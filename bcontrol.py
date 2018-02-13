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
from MCP3427 import *
from pid_controller import *


class bcontrol(object):

    def __init__(self):
        self.enable = 4
        self.ch1 = 17
        self.ch2 = 27
        self.BIN = "{0:8b}"
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(enable, GPIO.OUT)
        GPIO.setup(ch1, GPIO.OUT)
        GPIO.setup(ch2, GPIO.OUT)

        self.pwm_hlt = GPIO.PWM(ch1, 0.2)
        self.pwm_hlt.start(0)

        self.pwm_boil = GPIO.PWM(ch2, 0.2)
        self.pwm_boil.start(0)
        
        self.hlt_pid = pwm_pid_controller(self.pwm_hlt,10.0,0.01,-10.0)

        self.msleep = lambda x: time.sleep(x/1000.0)

        self.cal_mash_tun_sensor = 4.5
        self.cal_hlt_sensor = 3.0
        self.cal_htexch_sensor = 3.0

        self.htexch = 0.
        self.mash_tun = 0.
        self.hlt = 0.

    def enable_heater_hlt(self):
        GPIO.output(self.enable, 0)
        GPIO.output(self.ch1,1)
        GPIO.output(self.ch2,0)

    def enable_heater_boil(self):
        GPIO.output(self.enable, 1)
        GPIO.output(self.ch1,0)
        GPIO.output(self.ch2,1)

    def disable_heaters(self):
        GPIO.output(self.enable, 0)
        GPIO.output(self.ch1,0)
        GPIO.output(self.ch2,0)
        
    


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

        self.adc1 = MCP342X(0x68)
        self.adc1.reset()
        self.msleep(1.0)
        self.adc1.conversion()
        
        self.adc2 = MCP342X(0x6a)
        self.adc2.reset()
        self.msleep(1.0)
        self.adc2.conversion()
        
        self.adc3 = MCP342X(0x6c)
        self.adc3.reset()
        self.msleep(1.0)
        self.adc3.conversion()
        
        
        self.read_temp_sensor()
        
    def read_temp_sensor(self):
        self.adc1.conversion()
        self.adc2.conversion()
        self.adc3.conversion()
        self.msleep(1.0)
        try:
            self.adc1.configure(CHANNEL_0)
            adc1_ch0 = self.adc_to_voltage(self.adc1.read())
            self.adc1.configure(CHANNEL_1)
            adc1_ch1 = self.adc_to_voltage(self.adc1.read())
            print "adc1 ch0 %3.4f" % (adc1_ch0)
            print "adc1 ch1 %3.4f" % (adc1_ch1)
            rtd_0 = (adc1_ch0 - 2.0 * adc1_ch1)*1000.0
            print "rtd_0 %3.2f" % (rtd_0)
            self.mash_tun = self.ohms_to_f(rtd_0) + self.cal_mash_tun_sensor
        except:
            pass
        
        try:
            self.adc2.configure(CHANNEL_0)
            adc2_ch0 = self.adc_to_voltage(self.adc2.read())
            self.adc2.configure(CHANNEL_1)
            adc2_ch1 = self.adc_to_voltage(self.adc2.read())
            print "adc2 ch0 %3.4f" % (adc2_ch0)
            print "adc2 ch1 %3.4f" % (adc2_ch1)
            rtd_1 = (adc2_ch0 - 2.0 * adc2_ch1)*1000.0
            print "rtd_1 %3.2f" % (rtd_1)
            self.hlt = self.ohms_to_f(rtd_1) + self.cal_hlt_sensor
        except:
            pass
        
        try:
            self.adc3.configure(CHANNEL_0)
            adc3_ch0 = self.adc_to_voltage(self.adc3.read())
            self.adc3.configure(CHANNEL_1)
            adc3_ch1 = self.adc_to_voltage(self.adc3.read())
            print "adc3 ch0 %3.4f" % (adc3_ch0)
            print "adc3 ch1 %3.4f" % (adc3_ch1)
            rtd_2 = (adc3_ch0 - 2.0 * adc3_ch1)*1000.0
            print "rtd_2 %3.2f" % (rtd_2)
            self.htexch = self.ohms_to_f(rtd_2) + self.cal_htexch_sensor
        except:
            pass
            
        print "HLT: %3.1f MASH: %3.1f HTEXCH: %3.1f " % (self.hlt, self.mash_tun, self.htexch)
