import socket
import RPi.GPIO as gpio
import threading

gpio.setmode(gpio.BCM) 
pins = [17, 27, 22]
pwm = [None] * 3
brightnessArray = [0, 0, 0]

for i in range(3):
    gpio.setup(pins[i], gpio.OUT)
    pwm[i] = gpio.PWM(pins[i], 500)
    pwm[i].start(brightnessArray[i])


def page():
    html = """
    <html>
    <head>
        <title>LED Brightness</title>
    </head>
    <form action="/Lab7q1" method="POST">
        <div>
            <p>Brightness level:</p>
            <input type="range" id="brightness" name="brightness" min="0" max="100" value="0"/>
        </div>
        <div>
            <p>Select LED:</p>
            <div>
                <input type="radio" id="LED_1" name="LEDList" value="LED_1" checked />
                <label for="LED 1">LED 1 (""" + brightnessArray[0] + """%)</label>
            </div>
            <div>
                <input type="radio" id="LED_2" name="LEDList" value="LED_2" unchecked />
                <label for="LED 2">LED 2(""" + brightnessArray[1] + """%)</label>
            </div>
            <div>
                <input type="radio" id="LED_3" name="LEDList" value="LED_3" unchecked />
                <label for="LED 3">LED 3(""" + brightnessArray[2] + """%)</label>
            </div>
        </div>
        <br>
        <div>
            <input type="submit" value="Change Brightness" />
        </div>
    </form>
    </html>
    """
    return bytes(html, 'utf-8')

def parsePOSTdata(data):
    #devoe code
    data_dict = {}
    idx = data.find('\r\n\r\n')+4
    data = data[idx:]
    data_pairs = data.split('&')
    for pair in data_pairs:
        key_val = pair.split('=')
        if len(key_val) == 2:
            data_dict[key_val[0]] = key_val[1]
    return data_dict

def serve_web_page():
    #devoe code
    while True:
        print('Waiting for connection...')
        conn, (client_ip, client_port) = s.accept()     # blocking call
        print(f'Connection from {client_ip} on client port {client_port}')
        client_message = conn.recv(2048).decode('utf-8')
        print(f'Message from client:\n{client_message}')
        data_dict = parsePOSTdata(client_message)
       
        if "LEDList" in data_dict.keys():
            ledStr = data_dict["LEDList"]
            ledIndex = int(ledStr[-1]) - 1
            if "brightness" in data_dict.keys():
                brightnessArray[ledIndex] = data_dict["brightness"]
                pwm[ledIndex].start(brightnessArray[ledIndex])
        
        conn.send(b'HTTP/1.1 200 OK\r\n')                  # status line
        conn.send(b'Content-Type: text/html\r\n')          # headers
        conn.send(b'Connection: close\r\n\r\n')   
        try:
            conn.sendall(page())                       # body
        finally:
            conn.close()

#devoe code
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # pass IP addr & socket type
s.bind(('', 8080))     # bind to given port
s.listen(3)          # up to 3 queued connections

webpageThread = threading.Thread(target=serve_web_page)
webpageThread.daemon = True
webpageThread.start()

# Do whatever we want while the web server runs in a separate thread:
try:
    while True:
        pass
except:
    print('Joining webpageTread')
    webpageThread.join()
    print('Closing socket')
    s.close()