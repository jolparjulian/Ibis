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
    html = f"""
    <html>
    <head>
        <title>LED Brightness Control</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 20px;
                background-color: #f8f9fa;
            }}
            .slider-container {{
                margin: 20px auto;
                width: 300px;
                text-align: left;
                background: #ffffff;
                border-radius: 10px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.15);
                padding: 20px;
            }}
            input[type="range"] {{
                width: 100%;
            }}
            label {{
                display: block;
                font-weight: bold;
                margin-bottom: 5px;
            }}
            span {{
                float: right;
            }}
        </style>
        <script>
            function updateBrightness(ledIndex, value) {{
                document.getElementById('val' + ledIndex).innerText = value + "%";

                // Send POST request without reloading page
                fetch('/Lab7q2', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }},
                    body: 'LEDList=LED_' + ledIndex + '&brightness=' + value
                }})
                .then(response => response.text())
                .then(data => {{
                    console.log("Brightness updated for LED " + ledIndex + ": " + value);
                }})
                .catch(error => {{
                    console.error("Error:", error);
                }});
            }}
        </script>
    </head>
    <body>
        <h1>LED Brightness Control</h1>

        <div class="slider-container">
            <label for="led1">LED 1 <span id="val1">{brightnessArray[0]}%</span></label>
            <input type="range" id="led1" min="0" max="100" value="{brightnessArray[0]}"
                   oninput="updateBrightness(1, this.value)">
        </div>

        <div class="slider-container">
            <label for="led2">LED 2 <span id="val2">{brightnessArray[1]}%</span></label>
            <input type="range" id="led2" min="0" max="100" value="{brightnessArray[1]}"
                   oninput="updateBrightness(2, this.value)">
        </div>

        <div class="slider-container">
            <label for="led3">LED 3 <span id="val3">{brightnessArray[2]}%</span></label>
            <input type="range" id="led3" min="0" max="100" value="{brightnessArray[2]}"
                   oninput="updateBrightness(3, this.value)">
        </div>
    </body>
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
                pwm[ledIndex].start(int(brightnessArray[ledIndex]))
        
        #conn.send(b'HTTP/1.1 200 OK\r\n')                  # status line
        #conn.send(b'Content-Type: text/html\r\n')          # headers
        #conn.send(b'Connection: close\r\n\r\n')   
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