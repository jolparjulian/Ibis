import socket
import RPi.GPIO as gpio
import threading
import time

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
                <input type="radio" id="LED 1" name="LEDList" value="LED 1" checked />
                <label for="LED 1">LED 1</label>
            </div>
            <div>
                <input type="radio" id="LED 2" name="LEDList" value="LED 2" unchecked />
                <label for="LED 2">LED 2</label>
            </div>
            <div>
                <input type="radio" id="LED 3" name="LEDList" value="LED 3" unchecked />
                <label for="LED 3">LED 3</label>
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
        if 'led_byte' in data_dict.keys():   # make sure data was posted
            led_byte = data_dict["led_byte"]
        else:   # web page loading for 1st time so start with 0 for the LED byte
            led_byte = '0'
        conn.send(b'HTTP/1.1 200 OK\r\n')                  # status line
        conn.send(b'Content-Type: text/html\r\n')          # headers
        conn.send(b'Connection: close\r\n\r\n')   
        try:
            conn.sendall(page())                       # body
        finally:
            conn.close()

#devoe code
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # pass IP addr & socket type
s.bind(('', 80))     # bind to given port
s.listen(3)          # up to 3 queued connections

webpageTread = threading.Thread(target=serve_web_page)
webpageTread.daemon = True
webpageTread.start()

# Do whatever we want while the web server runs in a separate thread:
try:
    while True:
        pass
except:
    print('Joining webpageTread')
    webpageTread.join()
    print('Closing socket')
    s.close()