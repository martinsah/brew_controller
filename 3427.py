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

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

enable = 4
ch1 = 17
ch2 = 27

GPIO.setup(enable, GPIO.OUT)
GPIO.setup(ch1, GPIO.OUT)
GPIO.setup(ch2, GPIO.OUT)

pwm_hlt = GPIO.PWM(ch1, 0.2)
pwm_boil = GPIO.PWM(ch2, 0.2)
pwm_hlt.start(0)
pwm_boil.start(0)


I2C_SLAVE=0x0703

CHANNEL_0 = 0
CHANNEL_1 = 1

CMD_RESET = "\x06"
CMD_LATCH = "\x04"
CMD_CONVERSION = "\x08"
CMD_READ_CH0_16BIT = "\x88"
CMD_READ_CH1_16BIT = "\xA8"

msleep = lambda x: time.sleep(x/1000.0)

def enable_heater_hlt():
	GPIO.output(enable, 0)
	GPIO.output(ch1,1)
	GPIO.output(ch2,0)

def enable_heater_boil():
	GPIO.output(enable, 1)
	GPIO.output(ch1,0)
	GPIO.output(ch2,1)

def disable_heaters():
	GPIO.output(enable, 0)
	GPIO.output(ch1,0)
	GPIO.output(ch2,0)
	
BIN = "{0:8b}"


def pt100_to_temperature(resistance):
   return (resistance-100.)/.384

def adc_to_voltage(lsb):
   return lsb*4.096/65536.

def celsius_to_f(c):
   return c*9./5.+32.



class i2c(object):
   def __init__(self, device, bus):
      self.fr = io.open("/dev/i2c-"+str(bus), "rb", buffering=0)
      self.fw = io.open("/dev/i2c-"+str(bus), "wb", buffering=0)
      # set device address
      fcntl.ioctl(self.fr, I2C_SLAVE, device)
      fcntl.ioctl(self.fw, I2C_SLAVE, device)
   def write(self, bytes):
      self.fw.write(bytes)
   def read(self, bytes):
      return self.fr.read(bytes)
   def __del__(self):
      self.fw.close()
      self.fr.close()

class MCP342X(object):
    def __init__(self, address):
        self.dev = i2c(address, 1)

    def reset(self):
        self.dev.write(CMD_RESET)

    def latch(self):
        self.dev.write(CMD_LATCH)

    def conversion(self):
        self.dev.write(CMD_CONVERSION)

    def configure(self, channel = 0):
        if channel == 1:
            self.dev.write(CMD_READ_CH1_16BIT)
        else:
            self.dev.write(CMD_READ_CH0_16BIT)
        msleep(300)

    def read(self):
        try:
            data = self.dev.read(3)
            buf = array.array('B', data)
            status = buf[2]
            result = None
            if status & 128 != 128: #check ready bit = 0
                result = buf[0] << 8 | buf[1]
        except:
            result = None
            
        return result



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
#		print "pwm_pid_controller debug: ,p,%3.1f,   i,%3.1f,   d,%3.1f, dc,%2.1f, setpoint,%3.1f, input,%3.1f, hlt,%3.1f" % (self.p_v,self.i_v,self.d_v,self.dc,setpoint,input,hlt)
		sys.stdout.flush()
		self.last_input = input
		self.last_d = self.d
		self.pwm_update_counter = self.pwm_update_counter + 1
		if(self.pwm_update_counter == self.pwm_update_iteration):
			self.pwm_update_counter = 0
		self.pwm.ChangeDutyCycle(self.dc)

		
if __name__ == "__main__":
	
	hlt_pid = pwm_pid_controller(pwm_hlt,10.0,0.01,-10.0)

	enable_heater_boil()	
	#enable_heater_hlt()
	
	while (1):
		adc = MCP342X(0x68)
		adc.reset()
		msleep(1)
		adc.conversion()
		msleep(1)
		adc.configure(CHANNEL_0)
		mash_tun =  celsius_to_f(pt100_to_temperature(adc_to_voltage(adc.read())*1000.))
		adc.configure(CHANNEL_1)
		hlt =  celsius_to_f(pt100_to_temperature(adc_to_voltage(adc.read())*1000.))
		msg_temps = "HLT: %3.1f MASH: %3.1f" % (hlt, mash_tun)
		print msg_temps
		time.sleep(1)
#		hlt_pid.update(161.6,hlt,hlt)
#		hlt_pid.update(180.0,mash_tun,hlt)
		
		pwm_boil.ChangeDutyCycle(85.0)
