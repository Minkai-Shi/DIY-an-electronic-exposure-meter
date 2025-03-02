---
title: DIY Light Meter Project
date: 2024-12-20 15:21:30
tags: EEPW Activity
categories: EEPW Activity
---
# DIY Light Meter Project: Hardware Integration & Software Development

## Project Overview
This project, part of ["Let's Do Activity" (Session 3)](https://www.eepw.com.cn/event/action/digikey/diy_third.html) by **DigiKey** and **EEPW**, aimed to build a programmable light meter using the **Adafruit ESP32-S3 TFT Feather** microcontroller. The device measures ambient light intensity, calculates optimal photography parameters (ISO, aperture, shutter speed), and enables remote control via WiFi. 

---

## Table of Contents
1. [Hardware Components](#hardware-components)  
2. [System Architecture](#system-architecture)  
3. [Software Implementation](#software-implementation)  
4. [Exposure Control Logic](#exposure-control-logic)  
5. [Technical Innovations](#technical-innovations)  
6. [Project Links](#project-links)  

---

## Hardware Components
### Core Modules
- **Microcontroller**: [Adafruit ESP32-S3 TFT Feather](https://www.adafruit.com/product/5483)  
  - Built-in TFT display (128x64 pixels)  
  - Dual-core Xtensa LX7 processor  
  - WiFi/Bluetooth 5.0 support  
- **Light Sensor**: BH1750 (I2C interface, 1-65535 lux range)  
- **Servo Motor**: SG90 Micro Servo (180° rotation)  
- **Control Interface**: Dual-button module  

![Hardware Assembly](https://minkai-shi.github.io/upload/hardware_assembly.jpg) 
![Hardware Assembly](https://minkai-shi.github.io/upload/hardware_assembly2.jpg)  
*Final prototype with labeled components*

---

## System Architecture
### Circuit Design
| Component      | ESP32 Connection        | Protocol  |
|----------------|-------------------------|-----------|
| BH1750 Sensor  | GPIO6 (SDA), GPIO7 (SCL)| I2C       |
| Servo Motor    | GPIO10                  | PWM       |
| Red Button     | GPIO9                   | Digital   |
| Blue Button    | GPIO6                   | Digital   |
### Key Challenges & Solutions
1. **Debugging of Remote Control Methods**  
   - When the mobile phone can be used for control, Bluetooth or MQTT methods are planned to be adopted. However, the official manual of this version of the firmware does not support Bluetooth, and there is too little reference information for MQTT setup on io.adafruit. Later, the code for controlling WS2812B via the network found on the Internet was referenced and modified.
   -The WiFi control part exchanges data with the web page through WebSocket. The websocket.send_message function transmits the measured and calculated data such as light intensity to the web page for display. The websocket.receive function receives the instructions from the buttons on the web page and calls the mode switching, parameter adjustment, and shooting functions respectively to realize the mobile phone remote control function.Enter http://192.168.66.121:1080/client in the browser of a computer or mobile phone to access the control website. Replace the IP address with the IP address output by the console.
2. **Selection of Exposure Parameter Calculation Method**  
   -Direct calculation requires multiple mathematical operations, which slows down the processing speed and affects the shooting effect. When using exposure calculation formulas that involve complex mathematical operations such as logarithms and exponents, the code complexity is high.
   -The lookup table method is chosen for calculation. Looking up a table only requires directly finding the corresponding output value based on the input value, avoiding complex mathematical operations. Therefore, the calculation speed is very fast, which is especially suitable for applications with high real-time requirements. In embedded systems, due to limited resources, simple lookup table code is easier to implement and debug.
---

## Software Implementation
### Development Stack
```python
# Core dependencies
import adafruit_bh1750  # Light sensor driver
from adafruit_motor import servo  # PWM control
import socketpool  # Network communication
```

### Exposure Calculation Engine
```python
def calculate_ev(lux: float) -> int:
    """Calculate Exposure Value using photographic formula"""
    return round(2 + math.log(lux/10)/math.log(2))
```

---

## Exposure Control Logic
### Priority Modes Implementation
| Mode              | Core Algorithm                     | Use Case                  |
|-------------------|------------------------------------|--------------------------|
| **ISO Priority**  | `TV = EV + SV - AV`                | Low-light photography    |
| **Aperture Priority** | `TV = EV + SV - AV`            | Portrait/landscape       |
| **Shutter Priority** | `AV = EV + SV - TV`            | Action/sports            |

### Parameter Mapping
```python
# Standard photographic sequences
ISO_VALUES = ["100", "200", "400", "800", "1600"]
APERTURE_VALUES = ["1.0", "1.4", "2.0", "2.8", "4.0", "5.6", "8.0"]
SHUTTER_VALUES = ["1", "1/2", "1/4", "1/8", "1/15", "1/30", "1/60"]
```

---


### Demo Video
[![Demo](https://img.youtube.com/vi/znmnvBf8Q34/0.jpg)](https://youtu.be/znmnvBf8Q34)

---

## Technical Innovations
1. **Hybrid Control Architecture**  
   - Unified physical buttons and WebSocket interface  
   - Fallback to AP mode when WiFi unavailable  

2. **Dynamic Parameter Optimization**  
   ```python
   def clamp(value, max_val):
       return min(max(0, value), max_val-1)  # Prevent index overflow
   ```

3. **Real-time Telemetry**  
   ```python
   websocket.send(f"Lux:{lux} EV:{ev} ISO:{SV[sv]} AV:{AV[av]} TV:{TV[tv]}")
   ```

---

## Project Links
- **Full Source Code**: [GitHub Repository](https://github.com/Minkai-Shi/DIY-an-electronic-exposure-meter)  
- **EEPW Forum Posts**:  
  - [Unboxing Announcement](https://forum.eepw.com.cn/thread/388122/1) 
  - [Award Announcement](https://forum.eepw.com.cn/thread/388123/1)  
  - [Technical Documentation](https://forum.eepw.com.cn/thread/388125/1)
- **Demo Video**: [YouTube](https://youtu.be/DJd1A43Qwbo)  

---
