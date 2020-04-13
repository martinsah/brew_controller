# brew_controller
Raspberry Pi brew controller using Kivy and i2c sensors.

# Installation process

0. Enable SPI and I2C ports on the Raspberry Pi
```
sudo raspi-config
```
5 - interfacing options
  - enable SPI
  - enable I2C
  Reboot
  
1. Install prerequisites

```
sudo apt install mosquitto
sudo systemctl enable mosquitto.service
sudo systemctl start mosquitto.service
sudo apt-get install build-essential gcc make cmake libssl-dev \
libboost-dev libboost-thread-dev libboost-program-options-dev \
libpigpiod-if-dev

```

2. Install [paho-mqtt-c](https://github.com/eclipse/paho.mqtt.c)

```
git clone https://github.com/eclipse/paho.mqtt.c.git
cd paho.mqtt.c
git checkout v1.3.1

cmake -Bbuild -H. -DPAHO_WITH_SSL=ON -DPAHO_ENABLE_TESTING=OFF
sudo cmake --build build/ --target install
sudo ldconfig
cd ..
```

3. Install [paho-mqtt-cpp](https://github.com/eclipse/paho.mqtt.cpp)

```
git clone https://github.com/eclipse/paho.mqtt.cpp
cd paho.mqtt.cpp
cmake -Bbuild -H. 
sudo cmake --build build/ --target install
sudo ldconfig
cd ..
```

4. Install [mcp3427_mqtt](https://github.com/martinsah/mcp3427_mqtt)

```
git clone https://github.com/martinsah/mcp3427_mqtt.git
cd mcp3427_mqtt/
cmake -Bbuild -H. 
sudo cmake --build build/ --target install
cd ..
```

5. Install [mqtt_pid](https://github.com/martinsah/mqtt_pid)

```
git clone https://github.com/martinsah/mqtt_pid.git
cd mqtt_pid/
cmake -Bbuild -H. 
sudo cmake --build build/ --target install
cd ..
```


6. Install [mqtt_rotary_encoder](https://github.com/martinsah/mqtt_rotary_encoder)

```
git clone https://github.com/martinsah/mqtt_rotary_encoder.git
cd mqtt_rotary_encoder/
cmake -Bbuild -H.
sudo cmake --build build/ --target install
cd ..
```

7. Enable and start services
```
sudo systemctl enable mqtt_pigpio.service
sudo systemctl start mqtt_pigpio.service
sudo systemctl enable mcp3427_mqtt.service
sudo systemctl start mcp3427_mqtt.service
sudo systemctl enable mqtt_pid.service
sudo systemctl start mqtt_pid.service
sudo systemctl enable mqtt_pigpio.service
sudo systemctl start mqtt_pigpio.service
```

8. Check that services are running
```
sudo systemctl status mqtt_pigpio.service 
● mqtt_pigpio.service - MQTT PIGPIO service
   Loaded: loaded (/etc/systemd/system/mqtt_pigpio.service; enabled; vendor preset: enabled)
   Active: active (running) since Mon 2020-04-13 21:36:48 BST; 34s ago
 Main PID: 3450 (mqtt_pigpio)
    Tasks: 6 (limit: 4915)
   Memory: 1.0M
   CGroup: /system.slice/mqtt_pigpio.service
           └─3450 /usr/local/bin/mqtt_pigpio

Apr 13 21:36:48 raspberrypi systemd[1]: Started MQTT PIGPIO service.
Apr 13 21:36:48 raspberrypi mqtt_pigpio[3450]: done parsing command line
Apr 13 21:36:48 raspberrypi mqtt_pigpio[3450]: Connecting to server 'tcp://localhost:1883'...OK
```
```
sudo systemctl status mcp3427_mqtt.service 
● mcp3427_mqtt.service - MCP3427 MQTT service
   Loaded: loaded (/etc/systemd/system/mcp3427_mqtt.service; enabled; vendor preset: enabled)
   Active: active (running) since Mon 2020-04-13 21:27:30 BST; 10min ago
 Main PID: 2461 (mcp3427_mqtt)
    Tasks: 3 (limit: 4915)
   Memory: 7.6M
   CGroup: /system.slice/mcp3427_mqtt.service
           └─2461 /usr/local/bin/mcp3427_mqtt --pt100 --usa

Apr 13 21:27:30 raspberrypi systemd[1]: Started MCP3427 MQTT service.
Apr 13 21:27:31 raspberrypi mcp3427_mqtt[2461]: Connecting to server 'tcp://localhost:1883'...OK
```
```
sudo systemctl status mqtt_pid
● mqtt_pid.service - MQTT PID service
   Loaded: loaded (/etc/systemd/system/mqtt_pid.service; enabled; vendor preset: enabled)
   Active: active (running) since Mon 2020-04-13 21:30:12 BST; 8min ago
 Main PID: 2819 (mqtt_pid_pwm)
    Tasks: 3 (limit: 4915)
   Memory: 876.0K
   CGroup: /system.slice/mqtt_pid.service
           └─2819 /usr/local/bin/mqtt_pid_pwm

Apr 13 21:30:12 raspberrypi mqtt_pid_pwm[2819]: td= 0.1
Apr 13 21:30:12 raspberrypi mqtt_pid_pwm[2819]: intcap= 0.1
Apr 13 21:30:12 raspberrypi mqtt_pid_pwm[2819]: pwmtopic= pwm1
Apr 13 21:30:12 raspberrypi mqtt_pid_pwm[2819]: setpointtopic= pid/set
Apr 13 21:30:12 raspberrypi mqtt_pid_pwm[2819]: sensortopic= adc/1
Apr 13 21:30:12 raspberrypi mqtt_pid_pwm[2819]: sensortopictopic= sensortopic
Apr 13 21:30:12 raspberrypi mqtt_pid_pwm[2819]: pwmtopictopic= pid/pwmtopic
Apr 13 21:30:12 raspberrypi mqtt_pid_pwm[2819]: topic_kp= pid/kp
Apr 13 21:30:12 raspberrypi mqtt_pid_pwm[2819]: topic_ki= pid/ki
Apr 13 21:30:12 raspberrypi mqtt_pid_pwm[2819]: topic_kd= pid/kdConnecting to server 'tcp://localhost:1883'...OK
```

