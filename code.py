import time  
import board  
import displayio  
import digitalio
import terminalio  
import busio
import neopixel
import rtc
from adafruit_bitmap_font import bitmap_font  
from adafruit_display_text import label  
import adafruit_bh1750
import pwmio
from adafruit_motor import servo
import math
# Network libraries
import wifi
import socketpool
import ssl
import adafruit_requests
from adafruit_httpserver import Server, Request, Response, Websocket, GET
# BH1750Driver
i2c = board.I2C()  
sensor = adafruit_bh1750.BH1750(i2c)
# PWM Driver
pwm = pwmio.PWMOut(board.D10, duty_cycle=0, frequency=50)
servo = servo.Servo(pwm)
# ButtonDriver_Begin
Button0 = digitalio.DigitalInOut(board.BUTTON)
Button0.direction = digitalio.Direction.INPUT
Button0.pull = digitalio.Pull.UP
buttonBlue = digitalio.DigitalInOut(board.D6)  
buttonRed = digitalio.DigitalInOut(board.D9)  
buttonRed.switch_to_input(pull=digitalio.Pull.UP)  
buttonBlue.switch_to_input(pull=digitalio.Pull.UP)   
print("Button Init Success\n")

# Initialize parameters  
Time_cut = 0  
buttonRedTime_cut = 0  
buttonRedDown_flag = 0  
buttonBlueTime_cut = 0  
buttonBlueDown_flag = 0  
# Initialize display screen parameters
display = board.DISPLAY  
display.brightness = 0.88   # Change brightness  
display.rotation = 0    # Change direction, 0 for landscape and 90 for portrait 

# Pre-calculated exposure value arrays
AV = ["1  ", "1.4", "2  ", "2.8", "4  ", "5.6", "8  ", "11 ", "16 ", "22 ", "32 "]
TV = ["1     ", "1/2   ", "1/4   ", "1/8   ", "1/15  ", "1/30  ", "1/60  ", "1/125 ", "1/250 ", "1/500 ", "1/1000"]
SV = ["100 ", "200 ", "400 ", "800 ", "1600"]
MODE = ['SV','AV','TV']
MODECN = ['ISO优先','光圈优先(AV)','快门优先(TV)']
EV = 1
# Initial values
lux = 1000  # Assumed light intensity value
svIndex = 2  # ISO sensitivity index
avIndex = 5  # Aperture value index
tvIndex = 0  # Initialize tvIndex
change_mode = 0
RGBr, RGBg, RGBb = 8, 8, 8

wifi.radio.connect('ESP32', '12345678') #这里替换成需要连接的wifi ID及密码
print(f"My IP address: {wifi.radio.ipv4_address}")
# WiFi状态查询，未连接WIFI则不联网更新数据，开启AP模式
wificonnect_State = wifi.radio.connected
print("wificonnect_State",wificonnect_State)
if(wificonnect_State == False):
    wifi.radio.start_ap(ssid = 'ESP32', password = '12345678')
Wifi_Mode = 'STA' if(wificonnect_State == True) else 'AP'
Wifi_ip = wifi.radio.ipv4_address if(wificonnect_State == True) else wifi.radio.ipv4_address_ap

#构造函数――按键控制RGB
i = 0
Enter_flag = False
def Button0_Work():
    global i
    global Enter_flag
    global RGBr, RGBg, RGBb
    if(Button0.value == False and Enter_flag == False):
        time.sleep(0.05)#延时消抖
        if(Button0.value == False and Enter_flag == False):
            i+=1
            RGBr, RGBg, RGBb = 8*i, 8*i, 8*i
            pixels.fill((RGBr, RGBg, RGBb))
            Enter_flag = True
            print("pixels change\n",i)
            if(i>20):
                i = 0            
    elif(Button0.value == True and Enter_flag == True):
        time.sleep(0.05)#延时消抖
        if(Button0.value == True and Enter_flag == True):
            Enter_flag = False        
 
# RGBDriver_Begin
pixel_pin = board.NEOPIXEL
num_pixels = 1
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.2, auto_write=True)
pixels.fill((8, 8, 8))
# print("RGBDriver Init Success\n")
# RGBDriver_End

# Button callback functions
def change_iso():
    global svIndex
    if svIndex > len(SV) - 2:
        svIndex = 0
    else:
        svIndex = svIndex+1

def change_av():
    global avIndex, tvIndex,lux
    if avIndex > len(AV) - 2:
        avIndex = 0 
    else: 
        avIndex = avIndex+1
    EV = round(2 + math.log(lux / 10) / math.log(2))
    tvIndex = min(max(0, EV + svIndex - avIndex), len(TV) - 1)

def change_tv():
    global tvIndex, avIndex,lux
    if tvIndex > len(TV) - 2:
        tvIndex = 0 
    else: 
        tvIndex = tvIndex+1       
    EV = round(2 + math.log(lux / 10) / math.log(2))
    avIndex = min(max(0, EV + svIndex - tvIndex), len(AV) - 1)

def ChangeMode():
    global change_mode
    if change_mode > 1:
       change_mode = 0 
    else:
       change_mode = change_mode+1

def Adjust():
    global change_mode
    if change_mode==0:#自动曝光            
       change_iso()
    if change_mode==1:  #光圈优先
       change_av()                
    if change_mode==2: #快门优先
       change_tv()

def Shoot():
    servo.angle = 0
    time.sleep(0.5)
    servo.angle = 180
    time.sleep(0.2)
    servo.fraction = None
    
text = label.Label(  
    font=terminalio.FONT,    
    text="EEPW-DigiKey MKSHI \nlux:        EV:\nISO:        AV:\nTV:       MODE: ",  # 显示的文本  
    x=-10,  # 文本的起始X坐标  
    y=0,  # 文本的起始Y坐标  
    color=0xa5a555,  # 文本颜色  
)  
# 显示WiFi IP 和 Mode
text_Wifi = "WiFi:{}\n{}:1080/client".format(Wifi_Mode,Wifi_ip)#更新RGB状态
text_Wifi_title = label.Label(font=terminalio.FONT, text=text_Wifi, color = 0xffffff)
text_Wifi_title.x = 5
text_Wifi_title.y = 55

text_lux = label.Label(font=terminalio.FONT, text="lux", color=0x11FF44)  # y_bottom label
text_lux.anchor_point = (0, 0.5)  # set the anchorpoint
text_lux.anchored_position = (15, 15 ,)  # set the text anchored position to the upper right of the graph  
text_EV = label.Label(font=terminalio.FONT, text="EV", color=0x11FF44)  # y_bottom label
text_EV.anchor_point = (0, 0.5)  # set the anchorpoint
text_EV.anchored_position = (80,15,)  # set the text anchored position to the upper right of the graph    
text_ISO = label.Label(font=terminalio.FONT, text="ISO", color=0x11FF44)  # y_bottom label
text_ISO.anchor_point = (0, 0.5)  # set the anchorpoint
text_ISO.anchored_position = (15, 30 ,)  # set the text anchored position to the upper right of the graph  
text_AV = label.Label(font=terminalio.FONT, text="AV", color=0x11FF44)  # y_bottom label
text_AV.anchor_point = (0, 0.5)  # set the anchorpoint
text_AV.anchored_position = (80, 30 ,)  # set the text anchored position to the upper right of the graph  
text_TV = label.Label(font=terminalio.FONT, text="TV", color=0x11FF44)  # y_bottom label
text_TV.anchor_point = (0, 0.5)  # set the anchorpoint
text_TV.anchored_position = (10, 45 ,)  # set the text anchored position to the upper right of the graph 
text_MODE = label.Label(font=terminalio.FONT, text="MODE", color=0x11FF44)  # y_bottom label
text_MODE.anchor_point = (0, 0.5)  # set the anchorpoint
text_MODE.anchored_position = (80, 45 ,)  # set the text anchored position to the upper right of the graph 

# 启动屏幕显示  
show_group = displayio.Group(scale=2, x=20, y=20)    
show_group.append(text)
show_group.append(text_lux)
show_group.append(text_EV)
show_group.append(text_ISO)
show_group.append(text_AV)
show_group.append(text_TV)
show_group.append(text_MODE)
#show_group.append(text_Wifi_title)
display.root_group = show_group  

# GetandSetHttp_Begin
pool = socketpool.SocketPool(wifi.radio) # 网络管理，触发http操作
server = Server(pool, debug=True)

websocket: Websocket = None
next_message_time = time.monotonic()#数据更新时钟，以秒为单位变化

HTML_TEMPLATE = """
<html lang="en">
    <head>
    <!--注释：强制html使用utf-8编码-->
    <meta http-equiv="Content-Type" content="text/html;charset=utf-8"/>
        <title>EEPW&&DigiKEY Light meter</title>
    </head>
    <body>
        <p>EEPW&&DigiKEY Light meter</p>
        <p>Design by MinkaiShi</p>
        <p><strong>-</strong></p>
        <button onclick="sendRed()">Mode</button>
        <button onclick="sendBlue()">Adjust</button>
        <button onclick="sendShoot()">Shoot</button>
        <script>
            const Button_count = document.querySelector('strong');
            let ws = new WebSocket('ws://' + location.host + '/connect-websocket');
            ws.onopen = () => console.log('WebSocket connection opened');
            ws.onclose = () => console.log('WebSocket connection closed');
            ws.onmessage = event => Button_count.textContent = event.data;
            ws.onerror = error => Button_count.textContent = error;
            function sendRed() {
            		ws.send("1Mode");
            }
            function sendBlue() {
            		ws.send("2Adjust");
            }
            function sendShoot() {
            		ws.send("3Shoot");
            }
            
        </script>
    </body>
</html>
"""
#创建Http服务器
@server.route("/client", GET)
def client(request: Request):
    return Response(request, HTML_TEMPLATE, content_type="text/html")
#创建websocket服务
@server.route("/connect-websocket", GET)
def connect_client(request: Request):
    global websocket  # pylint: disable=global-statement
    if websocket is not None:
        print("websocket.close")
        websocket.close()  # Close any existing connection
    websocket = Websocket(request)
    return websocket

#判断网络模式，设定location.host
if(wificonnect_State == True):
    server.start(str(wifi.radio.ipv4_address), port = 1080)
else:
    server.start(str(wifi.radio.ipv4_address_ap), port = 1080)   
# GetandSetHttp_Begin
time.sleep(2)#等待2秒进入循环

while True:  
    time.sleep(0.01)  
    Time_cut = Time_cut + 1  
    if Time_cut > 100:  
        print("%.2fLux  %s ISO%s 光圈%s 快门%s" % (sensor.lux,MODECN[change_mode],SV[svIndex],AV[avIndex],TV[tvIndex]))
        text_lux.text = str(round(sensor.lux,0))
        lux = sensor.lux
        EV = round(2 + math.log(lux / 10) / math.log(2))
        text_EV.text = str(round(EV,0))
        Time_cut = 0
            # Ensure the equation EV = AV + TV - SV is satisfied
        total_index =  EV + svIndex
        avIndex = min(max(0, total_index - tvIndex), len(AV) - 1)
    
        text_ISO.text = SV[svIndex]
        text_AV.text = AV[avIndex]
        text_TV.text = TV[tvIndex]
        text_MODE.text = MODE[change_mode]    
      
    if (( buttonBlue.value)and(not buttonRed.value)):  
        if not buttonRedDown_flag:  
            buttonRedTime_cut = buttonRedTime_cut + 1  
            if buttonRedTime_cut > 15:  
                print("buttonRed is down") #自动曝光 光圈优先  快门优先
                ChangeMode()
                buttonRedDown_flag = 1  
    if buttonRed.value:  
        buttonRedTime_cut = 0  
        buttonRedDown_flag = 0  
          
    if ((not buttonBlue.value)and( buttonRed.value)):  
        if not buttonBlueDown_flag:  
            buttonBlueTime_cut = buttonBlueTime_cut + 1  
            if buttonBlueTime_cut > 15:  
                print("buttonBlue is down")
                Adjust()
                buttonBlueDown_flag = 1  
    if buttonBlue.value:  
        buttonBlueTime_cut = 0  
        buttonBlueDown_flag = 0  
        
    if ((not buttonBlue.value)and(not buttonRed.value)):  
        if not buttonDoubleDown_flag:  
            buttonDoubleTime_cut = buttonDoubleTime_cut + 1  
            if buttonDoubleTime_cut > 15:  
                #print("buttonDouble is down")
                Shoot()          
                buttonDoubleDown_flag = 1  
    if (buttonBlue.value or buttonRed.value):  
        buttonDoubleTime_cut = 0  
        buttonDoubleDown_flag = 0          
    #httpSeverLoop_Begin
    server.poll()
    # Check for incoming messages from client
    if websocket is not None:
        if (data := websocket.receive(True)) is not None:
            print("%s WebControl" % data)
            WebControl = int(data[0], 16)
            if WebControl == 1:
                ChangeMode()
            if WebControl == 2:
                Adjust()
            if WebControl == 3:
                Shoot()
    # Send a message every second
    if websocket is not None and next_message_time < time.monotonic():
        time.sleep(0.2)
        if websocket is not None:
            WebShow = "光强:%slux； 曝光度:%s；  ISO:%s;  AV:%s;  TV:%s;  %s"%(str(round(sensor.lux,0)),str(round(EV,0)),SV[svIndex],AV[avIndex],TV[tvIndex],MODECN[change_mode])
            websocket.send_message(WebShow)
            next_message_time = time.monotonic() + 1
            
    #httpSeverLoop_End    
    Button0_Work()       
   