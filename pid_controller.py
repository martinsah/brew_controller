#!/usr/bin/python
import struct, array, time, io, fcntl
import RPi.GPIO as GPIO
import time
import sys

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

class pwm_pid_controller(object):
    def __init__(self, pwm,p,i,d):
        self.pwm = pwm
        self.p = 0
        self.i = 0
        self.d = 0
        self.gain_p = p
        self.gain_i = i
        self.gain_d = d
        self.input = 0
        self.last_input = 0
        self.blank = 1
        self.lower_limit = 10.0
        self.last_d = 0
        self.p_v = 0
        self.i_v = 0
        self.d_v = 0
        self.dc = 0
        self.i_cap = 20.0
        self.pwm_update_iteration = 10
        self.pwm_update_counter = 0
        self.hlt_gain = 10.0
    
    def reset(self):
        self.p = 0.0
        self.i = 0.0
        self.d = 0.0
        self.d_v = 0.0
        self.p_v = 0.0
        self.i_v = 0.0

    def stop(self):
        self.pwm.stop()
        
    def update(self, setpoint, input, hlt):
        self.setpoint = setpoint
        self.p = self.setpoint - input
        self.d = 0.5 * self.last_d + 0.5 * (self.last_input - input)
        self.i = self.i + self.p
        
        if (self.blank > 0):
            self.blank = self.blank - 1
        else:
            self.hlt_correction = self.hlt_gain * (hlt-setpoint)
            if(self.hlt_correction < 0):
                self.hlt_correction = 0

            self.p_v = self.p * self.gain_p - self.hlt_correction
            if(self.p < 0):
                self.p = 0
                
            self.i_v = self.i * self.gain_i
            self.d_v = self.d * self.gain_d
            if(self.i_v > self.i_cap):
                self.i_v = self.i_cap
            
            self.dc = self.p_v + self.i_v + self.d_v
            if (self.dc > 100.0):
                self.dc = 100.0
            if (self.dc < self.lower_limit and self.dc > 0.0):
                self.dc = self.lower_limit
            if (self.dc < 0.0):
                self.dc = 0.0
        print "pwm_pid_controller debug: ,p,%3.1f,   i,%3.1f,   d,%3.1f, dc,%2.1f, setpoint,%3.1f, input,%3.1f, hlt,%3.1f" % (self.p_v,self.i_v,self.d_v,self.dc,setpoint,input,hlt)
        sys.stdout.flush()
        self.last_input = input
        self.last_d = self.d
        self.pwm_update_counter = self.pwm_update_counter + 1
        if(self.pwm_update_counter == self.pwm_update_iteration):
            self.pwm_update_counter = 0
        self.pwm.ChangeDutyCycle(self.dc)

