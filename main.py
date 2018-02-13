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

import kivy
kivy.require('1.1.0')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty, StringProperty
from kivy.clock import Clock
from bcontrol import *
import urllib2

class Controller(FloatLayout):
    ctrl = ObjectProperty(None)
    
    enable_text = StringProperty()
    sensor_text = StringProperty()
    heater_text = StringProperty()
    temp_text = StringProperty()
    control_text = StringProperty()
    setpoint_text = StringProperty()
    
    hlt_temp_text = StringProperty()
    mash_temp_text = StringProperty()
    hlt_pwm_text = StringProperty()
    
    def __init__(self, **kwargs):
        super(Controller,self).__init__(**kwargs)

        # init default values
        self.setpoint = 155.0
        self.temperature = 0.0
        self.enabled = False
        self.sensor = 0.0
        self.heater = 0.0
        self.pwm = 100.0

        # brewery control object
        self.bc = bcontrol()
        self.bc.init_temp_sensors()
        
        self.control = 'HLT'
        self.sensor = 'HLT'
        self.fmt_temp_text = '[b][size=60]'
        self.fmt_btn_text = '[b][size=30]'
        self.fmt_control_text = '[b][size=90]'
        self.hlt_temp_text = ''
        self.mash_temp_text = ''
        self.hlt_pwm_text = ''
        # init default values(derivatives)
        self.sensor_text = self.fmt_btn_text + 'Sensor HLT'
        self.heater_text = self.fmt_btn_text + 'Heater HLT'
        self.update_temp_display()
        self.update_setpoint_display()
        self.update_control_text()
        self.update_enable()
        
       
        
    def update_setpoint_display(self):
        if self.control == 'HLT' or self.control == 'MASH':
            self.setpoint_text = self.fmt_temp_text + "%3.1f F" % self.setpoint
        else:
            self.setpoint_text = self.fmt_temp_text + "%3.0f" % self.pwm + '%'
        
    def update_temp_display(self,temperature = None):
        if temperature != None:
            self.temp_text = self.fmt_temp_text + "%3.1f" % temperature
        else:
            self.temp_text = self.fmt_temp_text + '---.-'
    
    def update_sensor_button_text(self,temperature = None):
        if temperature != None:
            self.sensor_text = self.fmt_btn_text + self.sensor + ' ' + "%3.1f" % temperature
        else:
            self.sensor_text = self.fmt_btn_text + self.sensor
    
    def update_control_text(self,mode = 'HLT'):
        self.control = mode
        self.control_text = self.fmt_control_text + self.control
        self.update_setpoint_display()
    
    def update_enable(self):
        if self.enabled:
            self.enable_text = self.fmt_btn_text + 'Disable'
        else:
            self.enable_text = self.fmt_btn_text + 'Enable'
            self.bc.disable_heaters()
    
    # periodic timer callback
    def update(self,dt):            
        self.hlt_temp_text = 'HLT Temp ' + "%3.1f" % self.bc.hlt + ' F'
        self.mash_temp_text = 'Mash Temp ' + "%3.1f" % self.bc.mash_tun + ' F'
        self.hlt_pwm_text = 'HLT PWM ' + "%3.0f" % self.bc.hlt_pid.dc + '%'
        
    def update_controller(self,dt):
        self.bc.read_temp_sensor()
        if self.control == 'HLT':
            self.update_temp_display(self.bc.hlt)
            self.bc.hlt_pid.update(self.setpoint,self.bc.hlt,self.bc.hlt)
            print ' HLT MODE'
        if self.control == 'MASH':
            self.update_temp_display(self.bc.mash_tun)
            self.bc.hlt_pid.update(self.setpoint,self.bc.mash_tun,self.bc.hlt)
            print ' MASH MODE'
        if self.control == 'BOIL':
            self.update_temp_display()
            self.bc.pwm_boil.ChangeDutyCycle(self.pwm)
            print ' BOIL MODE'
        if self.control == 'COOL':
            self.update_temp_display(self.bc.htexch)
            print ' COOL MODE'
    
    
    # button UP. can be PWM or temperature depending on mode
    def btn_up(self):
        if self.control == 'HLT' or self.control == 'MASH':
            if (self.setpoint < 220.0):
                self.setpoint = self.setpoint + 0.5
                print "button down pressed. self.setpoint = %2.1f" % self.setpoint
        elif self.control == 'BOIL':
            if (self.pwm < 100.0):
                self.pwm = self.pwm + 2.0
                print "button up pressed. self.pwm = %2.0f" % self.pwm
        else:
            pass
        self.update_setpoint_display()
        
    # button DOWN. can be PWM or temperature depending on mode  
    def btn_down(self):
        if self.control == 'HLT' or self.control == 'MASH':
            if (self.setpoint > 0.0):
                self.setpoint = self.setpoint - 0.5
                print "button down pressed. self.setpoint = %2.1f" % self.setpoint
        elif self.control == 'BOIL':
            if (self.pwm > 0.0):
                self.pwm = self.pwm - 2.0
                print "button down pressed. self.pwm = %2.0f" % self.pwm
        else:
            pass
        self.update_setpoint_display()
        
    # HLT --> MASH --> BOIL --> COOL -->
    def btn_control(self):
        if self.control == 'HLT':
            self.update_control_text('MASH')
            self.bc.enable_heater_hlt()
            self.bc.hlt_pid.reset()
            self.bc.pwm_boil.ChangeDutyCycle(0)
        elif self.control == 'MASH':
            self.update_control_text('BOIL')
            self.bc.enable_heater_boil()
            self.bc.pwm_hlt.ChangeDutyCycle(0)
        elif self.control == 'BOIL':
            self.update_control_text('COOL')
            self.bc.disable_heaters()
            self.bc.pwm_hlt.ChangeDutyCycle(0)
            self.bc.pwm_boil.ChangeDutyCycle(0)
        else:
            self.update_control_text('HLT')
            self.bc.enable_heater_hlt()
            self.bc.hlt_pid.reset()
            self.bc.pwm_boil.ChangeDutyCycle(0)
        
    def btn_enable(self):
        if self.enabled <> True:
            self.enabled = True
        else:
            self.enabled = False
        self.update_enable()
    
    
    def btn_sensor(self):
        if self.sensor == 'HLT':
            self.sensor = 'MASH'
        elif self.sensor == 'MASH':
            self.sensor = 'HTEXCH'
        else:
            self.sensor = 'HLT'
        self.update_sensor_button_text()

        
class ControllerApp(App):
    def build(self):
        app = Controller()
        Clock.schedule_interval(app.update, 0.1)
        Clock.schedule_interval(app.update_controller, 1.0)
        return app 

if __name__ == '__main__':
    ControllerApp().run()
    