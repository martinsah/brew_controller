# brew_controller
Raspberry Pi brew controller using Kivy and i2c sensors.

# Installation process

0. Enable SPI and I2C ports on the Raspberry Pi
```
$ sudo raspi-config
```
5 - interfacing options
  - enable SPI
  - enable I2C
  Reboot
  
1. Install prerequisites

```
$ sudo apt install mosquitto
$ sudo systemctl enable mosquitto.service
$ sudo systemctl start mosquitto.service
$ sudo apt-get install build-essential gcc make cmake 
```

2. Install [paho-mqtt-c](https://github.com/eclipse/paho.mqtt.c)

```
$ git clone https://github.com/eclipse/paho.mqtt.c.git
$ cd paho.mqtt.c
$ git checkout v1.3.1

$ cmake -Bbuild -H. -DPAHO_WITH_SSL=ON -DPAHO_ENABLE_TESTING=OFF
$ sudo cmake --build build/ --target install
$ sudo ldconfig
```

3. Install [paho-mqtt-cpp](https://github.com/eclipse/paho.mqtt.cpp)

```
$ git clone https://github.com/eclipse/paho.mqtt.cpp
$ cd paho.mqtt.cpp
$ cmake -Bbuild -H. 
$ sudo cmake --build build/ --target install
$ sudo ldconfig
```

4. Install [mcp3427_mqtt](https://github.com/martinsah/mcp3427_mqtt)

5. Install [mqtt_pid](https://github.com/martinsah/mqtt_pid)

6. Install [mqtt_rotary_encoder](https://github.com/martinsah/mqtt_rotary_encoder)
```
$ sudo systemctl enable mqtt_pigpio.service
$ sudo systemctl start mqtt_pigpio.service
```
