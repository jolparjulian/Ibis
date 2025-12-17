from http.server import BaseHTTPRequestHandler, HTTPServer
import RPi.GPIO as GPIO
from urllib.parse import parse_qs
import json
import requests
import threading
import numpy as np
import time
import os
import mimetypes
from stepper import Stepper #grab stepper class

#Set up GPIOs
GPIO.setmode(GPIO.BCM)
laser_pin = 27 #check this
GPIO.setup(laser_pin, GPIO.OUT)
laser_time = 2.5

# Set up steppers, with steps/deg input
hor = Stepper(1024*4/360) # laser pitch
vert = Stepper(1024/360) # plate yaw

vert.zero()
hor.zero()

vert.start_process()
hor.start_process()

# Positional variables
cyl_position = [172.4,np.radians(299.68),8.23] # r t z
position = [0,0,0] # disregard
ref_positions = [] # place r/t/z/stepper angles into here to math later
angle = [0,0] #pitch/yaw
# replace the second number with our degrees position
offset = 360-301 # so we can reference yaw angle to center

json_data = [] # to put json in later

ip_string = "192.168.1.254" # defaults to his 
ip_string = "172.20.10.4" # mine

# some random stuff
pos_tol = 3 * np.pi/180 # angular tolerance between us and the next turret over
assumed_height = 25 # turret height for everyone else
us_turret_num = 1 # our turret number, to find our position and also remove from json
jog_amount = 0.4 #degrees to jog each arrow click
# one step is ~0.35 degrees, 0.4 should stop itself after one step
test_mode = True # change this when i want to shoot everything

# flow goes:
# set up guy and point it at origin, somehow call system_zero
# then zero the stepper angles off of that
# then point it at a couple of known points, input r/theta/z and add to ref list
# then call calibrate and math out our position

# --- HTML + JS ---
def make_page():
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Control Panel</title>

<style>
    body {{
        font-family: Impact;
        color: white;
        margin: 40px;
        background-image: url("devoe.jpg");
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-size: 100% 100%;
    }}
    .stuff{{
        font-family: Impact;
        margin: 40px;
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        grid-gap: 30px;
    }}
    .box {{
        border: 3px solid black;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        background-image: url("devoe.jpg");
        background-repeat: no-repeat;
        background-size: 100% 100%;
    }}
    .btn {{
        padding: 10px 15px;
        margin: 4px;
        border: 2px solid black;
        border-radius: 8px;
        background:white;
        cursor:pointer;
        /*
        background-image: url("devoe.jpg");
        background-repeat: no-repeat;
        background-size: 100% 100%;
        */
    }}
    .inputBox{{
        cursor:text;
        /*
        background-image: url("devoe.jpg");
        background-repeat: no-repeat;
        background-size: 100% 100%;
        */
    #refList, #jsonActions, #calibratedDisplay {{
        display:none;
    }}
    .refItem {{
        display:flex;
        justify-content: space-between;
        margin:3px;
        border:1px solid black;
        padding:3px;
    }}
</style>
</head>

<body>
<header>
    <h1> ONLY INPUT IN DEGREES AND MM </h1>
</header>

<div class="stuff">
<!-- Arrows + yaw/pitch input + Zero -->
<div class="box">
    <h3>Arrows</h3>

    <button class="btn" onmousedown="startJog('up')" onmouseup="stopJog()" onmouseleave="stopJog()">up</button><br>
    <button class="btn" onmousedown="startJog('left')" onmouseup="stopJog()" onmouseleave="stopJog()">left</button>
    <button class="btn" onmousedown="startJog('right')" onmouseup="stopJog()" onmouseleave="stopJog()">right</button><br>
    <button class="btn" onmousedown="startJog('down')" onmouseup="stopJog()" onmouseleave="stopJog()">down</button>
    
    <br><br>
    
    <h4>Horizontal / Vertical Input</h4>
    
    <input class="inputBox" id="yawval" class="inputbox" placeholder="horizontal">
    <input class="inputBox" id="pitchval" class="inputbox" placeholder="vertical">
    <button class="btn" onclick="motorAngles()">angles here</button>
    
    <br><br>

    <button class="btn" onclick="send('zero')">Zero</button>
</div>

<!-- Current Angles + Calibrated Position -->
<div class="box">
    <h3>Current Angles</h3>

    <ul>
        <li id="horAngle">{hor.angle.value}</li>
        <li id="vertAngle">{vert.angle.value}</li>

    </ul>

    <br>

    <h3>Calibrated Position</h3>

    <ul>
        <li id="usR">{cyl_position[0]}</li>
        <li id="usT">{cyl_position[1]*180/np.pi}</li>
        <li id="usZ">{cyl_position[2]}</li>

    </ul>
</div>

<!-- Laser Fire -->
<div class="box">
    <h3>Laser Fire</h3>
    <button id="laserBtn" class="btn" onclick="fireLaser()">Fire</button><br><br>
    <video id="laserGif" src="laser_gif.mp4" style="width:260px; display:none; pointer-events:none"></video>
</div>

<!-- Reference / Go To -->
<div class="box">
    <h3>Reference / Go Input</h3>
    <input class="inputBox" id="r" placeholder="r">
    <input class="inputBox" id="t" placeholder="theta">
    <input class="inputBox" id="z" placeholder="z"><br>
    <button class="btn" onclick="doReference()">Reference</button>
    <button class="btn" onclick="sendTo()">Go</button>
</div>

<!-- Reference Points List -->
<div class="box">
    <h3>Reference Points List</h3>
    <div id="refList"></div>
</div>

<!-- Get JSON + Test + Destroy -->
<div class="box">
    <h3>Commands</h3>
    <button class="btn" onclick="getJSON()">Get JSON</button>
    <div id="jsonActions">
        <button class="btn" onclick="send('test')">Test</button>
        <button class="btn" onclick="send('destroy')">Destroy</button>
    </div>
</div>
</div>

<audio id="laserSound" src="laser_sound.mp3"></audio>

<script>

//// ---- NETWORK ---- ////
function send(cmd) {{
    fetch("/", {{
        method:"POST",
        headers:{{"Content-Type":"application/x-www-form-urlencoded"}},
        body: "cmd=" + cmd
    }});
}}

//// ---- JSON ---- ////
function getJSON() {{
    send("json");
    document.getElementById("jsonActions").style.display = "block";
}}
//// points ////
function sendTo() {{
    let r = document.getElementById("r").value;
    let t = document.getElementById("t").value;
    let z = document.getElementById("z").value;

    fetch("/", {{
        method: "POST",
        headers: {{ "Content-Type": "application/x-www-form-urlencoded" }},
        body: "goTo=1&r=" + r + "&t=" + t + "&z=" + z
    }});
}}

//// ---- Reference ---- ////
let refPoints = [];

function doReference() {{
    let r = document.getElementById("r").value;
    let t = document.getElementById("t").value;
    let z = document.getElementById("z").value;
    fetch("/", {{
            method: "POST",
            headers: {{ "Content-Type": "application/x-www-form-urlencoded" }},
            body: "ref=1&r=" + r + "&t=" + t + "&z=" + z
        }}).then(() => {{
            fetchRefs();
        }});
}}

function updateRefList() {{
    const box = document.getElementById("refList");
    box.innerHTML = "";
    refPoints.forEach((p,i) => {{
        const div = document.createElement("div");
        div.id = `ref-${{i}}`; // add unique ID
        div.className="refItem";
        div.innerHTML = `${{p.r}}, ${{p.t}}, ${{p.z}} <button onclick="removePoint(${{i}})">X</button>`;
        box.appendChild(div);
    }});
}}

function fetchRefs() {{
    fetch("/refs")
        .then(res => res.json())
        .then(data => {{
            // data is list of {{r,t,z}} objects
            refPoints = data.map(item => ({{ r: item.r, t: item.t, z: item.z }}));
            if (refPoints.length > 0) {{
                document.getElementById("refList").style.display = "block";
            }}
            updateRefList();
        }})
        .catch(err => {{
            console.error("fetchRefs error", err);
        }});
}}

function removePoint(index) {{
    const el = document.getElementById(`ref-${{index}}`);
    if (el) el.style.display = "none"; // instant visual feedback

    fetch("/", {{
        method: "POST",
        headers: {{ "Content-Type": "application/x-www-form-urlencoded" }},
        body: "removeRef=" + index
    }}).then(() => {{
        fetchRefs();
    }});
}}
//// ---- Laser ---- ////
function fireLaser() {{
    const gif = document.getElementById("laserGif");
    const audio = document.getElementById("laserSound");
    gif.style.display = "block";
    gif.currentTime = 0;
    gif.play();
    audio.currentTime = 0;
    audio.play();
    gif.onended = () => {{
        gif.style.display = "none";
    }};
    send("fire");
}}

//// ---- Jog + Keyboard ---- ////
let jogInterval = null;

function startJog(dir) {{
    send(dir);
    jogInterval = setInterval(()=>send(dir), 140);
}}

function stopJog() {{
    clearInterval(jogInterval);
}}
function motorAngles() {{
    let pitch = document.getElementById("pitchval").value;
    let yaw = document.getElementById("yawval").value;

    fetch("/", {{
        method: "POST",
        headers: {{ "Content-Type": "application/x-www-form-urlencoded" }},
        body: "motorAngles=1&pitch=" + pitch + "&yaw=" + yaw
    }});
}}
document.addEventListener("keydown", (e)=>{{
    if(e.repeat) return;
    if(e.key==="ArrowUp") startJog("up");
    if(e.key==="ArrowDown") startJog("down");
    if(e.key==="ArrowLeft") startJog("left");
    if(e.key==="ArrowRight") startJog("right");
}});
setInterval(fetchStuff, 300);
function fetchStuff() {{
    fetch("/angles")
        .then(res => res.json())
        .then(data => {{
            document.getElementById("horAngle").innerText = data.hor.toFixed(2);
            document.getElementById("vertAngle").innerText = data.vert.toFixed(2);
            document.getElementById("usR").innerText = data.r.toFixed(2);
            document.getElementById("usT").innerText = data.t.toFixed(2);
            document.getElementById("usZ").innerText = data.z.toFixed(2);
        }});
}}


document.addEventListener("keyup", ()=>stopJog());
fetchRefs();

</script>
</body>
</html>

"""
# --- Request Handler ---
class WebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/" and os.path.isfile(self.path.lstrip("/")):
            filepath = self.path.lstrip("/")
            mime = mimetypes.guess_type(filepath)[0] or "application/octet-stream"

            self.send_response(200)
            self.send_header("Content-type", mime)
            self.end_headers()

            with open(filepath, "rb") as f:
                self.wfile.write(f.read())
            return
        if self.path == "/angles":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = {
                "hor": hor.angle.value,
                "vert": vert.angle.value,
                "r": cyl_position[0],
                "t": cyl_position[1]*180/np.pi,
                "z": cyl_position[2]
            }
            self.wfile.write(json.dumps(resp).encode())
            return
        if self.path == "/refs":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            simple = [{"r": p[0], "t": p[1], "z": p[2]} for p in ref_positions]
            self.wfile.write(json.dumps(simple).encode())
            return
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(make_page().encode())


    def do_POST(self):
        length = int(self.headers['Content-Length'])
        body = self.rfile.read(length).decode()
        data = parse_qs(body)
        global json_data

        try:
            if "cmd" in data:
                cmd = data["cmd"][0]
                print(cmd)
                # first four are motor jog u/d/l/r
                if cmd == "up":
                    vert.goStep(1)
                elif cmd == "down":
                    vert.goStep(-1)
                elif cmd == "right":
                    hor.goStep(-1)
                elif cmd == "left":
                    hor.goStep(1)
                # then fire
                elif cmd == "fire":
                    # thread it rah
                    laser = threading.Thread(target=fire_laser)
                    laser.daemon = True
                    laser.start()
                # then zero
                elif cmd == "zero":
                    system_zero()
                elif cmd == "json":
                    #data = requests.get("http://192.168.1.254:8000/positions.json")
                    json_data = requests.get(f"http://{ip_string}:8000/positions.json")
                    json_data = json_data.json()
                    #raw = data["data"][0]
                    print(json_data)
                    #raw = data[0]
                    #print(raw)
                    #global positions
                    #positions = json.loads(raw)
                    #print(positions)
                elif cmd == "find":
                    # find position
                    find_position(json_data)
                elif cmd == "test":
                    test_json(json_data)
                elif cmd == "destroy":
                    destroy(json_data)
                    #destroy(positions)

            if "ref" in data and "r" in data and "t" in data and "z" in data:
                pos = [float(data["r"][0]), float(data["t"][0]), float(data["z"][0])]
                reference(pos[0],pos[1],pos[2]) # add as a reference
                self.respond_ok()

            if "goTo" in data and "r" in data and "t" in data and "z" in data:
                pos = [float(data["r"][0]), float(data["t"][0]), float(data["z"][0])]
                print(pos)
                aim_at(pos[0],pos[1],pos[2]) # point at
            if "motorAngles" in data and "pitch" in data and "yaw" in data:
                print("turn damn it")
                print(float(data["yaw"][0]))
                print(float(data["pitch"][0]))
                #straight motor angles
                hor.goToAngle(float(data["yaw"][0]))
                vert.goToAngle(float(data["pitch"][0]))
            if "removeRef" in data:
                idx = int(data["removeRef"][0])
                if 0 <= idx < len(ref_positions):
                    ref_positions.pop(idx)
                print(ref_positions)

        except:
            pass


    def respond(self, msg, js_func):
        # Return script call so browser executes JS
        script = f"<script>{js_func}('{msg}')</script>"
        self.send_response(200)
        self.send_header("Content-Type","text/html")
        self.send_header("Content-Length", str(len(script)))
        self.end_headers()
        self.wfile.write(script.encode())
    def respond_ok(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")


def jog(motor, amount): # bc the rotate function got removed
    curr = motor.angle.value #current angle
    motor.goToAngle(curr+amount)
    # print(f"{motor} going to {curr+amount}")

def reference(r, t, z): #run this when im hitting a known location
    global ref_positions
    global position
    # add the r/theta we tell it its aiming at and the angles of the two steppers
    # motors send angle vals in degrees, will get converted later
    ref_positions.append([r, t, z, hor.angle.value, vert.angle.value])
    if len(ref_positions) >= 3:
        position = calibrate() # after enough points, calibrate to get true pos

def fire_laser():
    GPIO.output(laser_pin, 1)
    print("pew pew")
    time.sleep(laser_time)
    GPIO.output(laser_pin, 0)
    print("no more pew pew")

def calibrate(): # run this after enough reference points
    A = np.zeros((3,3)) #initialize some stuff
    b = np.zeros(3)
    for i in range(len(ref_positions)):
        r = ref_positions[i][0]
        t = ref_positions[i][1]*np.pi/180
        z = ref_positions[i][2]
        yaw = ref_positions[i][3]
        pitch = ref_positions[i][4]
        d = angles(pitch, yaw) # make 3d angle vector
        d = d/np.linalg.norm(d) # unit vector
        L = np.array([r*np.cos(t),r*np.sin(t),z]) # aimed position, cartesian
        M = np.eye(3) - np.outer(d,d) # projection matrix
        A += M
        b += M @ L 
    P = np.linalg.pinv(A) @ b # pinv does least squares inverse
    global cyl_position
    # put in the cylinder coords for checks later
    cyl_position[0] = (np.sqrt(P[0]**2 + P[1]**2)).item() # r
    x = P[0]
    y = P[1]
    cyl_position[1] = (np.arctan2(y,x) % (2*np.pi)).item() #radians, positive from 
    #cyl_position[2] = P[2].item()
    print(cyl_position)
    return P

def angles(pitch, yaw):
    # makes 3d angle vector from pitch and yaw
    # assumes degrees
    pitch = np.radians(pitch)
    yaw = np.radians(yaw+offset)
    return np.array([np.cos(pitch)*np.cos(yaw),
                     np.cos(pitch)*np.sin(yaw), 
                     np.sin(pitch)]).tolist()

def system_zero(): # zeros the motors, run when pointing at origin
    vert.zero()
    hor.zero()
    print("zero")

def find_offset():
    global offset
    angle = cyl_position[1]*180/np.pi
    radius = cyl_position[0]
    if angle < 180:
        offset = -(180-angle)
    else:
        angle = abs(360-angle)
        offset = (180-angle)

def aim_at(radius, angle, height):
    '''
    # this shit wasnt working so i went back to rect math
    # cyl position goes r,theta,z
    # pitch
    # get angle between two rays
    theta = cyl_position[1]-angle 
    # get 3rd side length
    d = np.sqrt(radius**2 + cyl_position[0]**2-2*radius*cyl_position[0]*np.cos(theta))
    # law of sines to grab angle i want
    pitch = np.arcsin(radius*np.sin(theta)/d)
    # yaw
    # get height diff
    dh = height-cyl_position[2]
    # get hypotenuse using previously found dist
    d3 = np.sqrt(dh**2 + d**2)
    # trig rules to grab angle
    yaw = np.arcsin(dh/d3)
    '''
    r0, theta0, z0 = cyl_position
    #rect coords
    x = radius*np.cos(np.radians(angle))
    y = radius*np.sin(np.radians(angle))
    x0 = r0 * np.cos(theta0)
    y0 = r0 * np.sin(theta0)
    # side lengths
    dx = x - x0
    dy = y - y0
    dz = height - z0
    # triangle math
    yaw = np.arctan2(dy,dx)*180/np.pi - offset
    pitch = np.arctan2(dz,np.sqrt(dx**2 + dy**2))*180/np.pi

    # go motors go
    print(f"hor going to {yaw}, vert going to {pitch}")
    hor.goToAngle(yaw)
    vert.goToAngle(pitch)

def destroy(json):
    targets = []
    # add targets from dicts
    for tid, turret in json.get("turrets",{}).items():
        r = turret["r"]
        t = turret["theta"]*180/np.pi
        z = assumed_height
        '''
        if abs(t-cyl_position[1]) >= pos_tol: # make sure we dont try to kill ourselves
            targets.append([r, t, z]) # add to kill list
        '''
        if int(tid) != us_turret_num: # this should work better
            targets.append([r, t, z]) # keeeeel
    for globe in json.get("globes",[]):
        r = globe["r"]
        t = globe["theta"]*180/np.pi
        z = globe["z"]
        targets.append([r, t, z])
    for target in targets:
        print(hor.angleFlag, vert.angleFlag)
        aim_at(target[0], target[1], target[2])
        print(f"shooting at {target}")
        time.sleep(5)
        '''
        while(not (hor.angleFlag and vert.angleFlag)):
            # this blocks until the goToAngle commands are both done
            time.sleep(1)
            print(hor.angleFlag,vert.angleFlag)
        '''
        fire_laser()

def test_motors():
    # test code to check if the motors work
    # start by checking goToAngle
    test_angle = 45
    print(f"vert at {vert.angle.value}, hor at {hor.angle.value}")
    print(f"goToAngle to {test_angle}")
    vert.goToAngle(test_angle)
    hor.goToAngle(test_angle)
    while(not (hor.angleFlag and vert.angleFlag)):
        # this blocks until the goToAngle commands are both done
        pass
    print("goToAngle done")
    print(f"vert at {vert.angle.value}, hor at {hor.angle.value}")
    # then check that jog works properly
    test_jog = 1
    for i in range(10):
        print(f"jogging by {test_jog}")
        jog(vert, test_jog)
        jog(hor, test_jog)
    print(f"vert at {vert.angle.value}, hor at {hor.angle.value}")

def find_position(json):
    stuff = json.get("turrets",{}).items()
    for tid, turret in stuff:
        if int(tid) == us_turret_num:
            r = turret["r"]
            t = turret["theta"]
            us_pos = [r, t]
            print(f"we live at r: {us_pos[0]}, theta: {us_pos[1]}")
            break

def test_json(json):
    # test to make sure json can be read
    # this just goes through the json and prints out all the positions

    # remember to put back the destroy function once tests are done
    targets = []
    # add targets from dicts
    for tid, turret in json.get("turrets",{}).items():
        r = turret["r"]
        t = turret["theta"]
        z = assumed_height
        '''
        if abs(t-cyl_position[1]) >= pos_tol: # make sure we dont try to kill ourselves
            targets.append([r, t, z]) # add to kill list
        '''
        if int(tid) != us_turret_num:
            targets.append([r, t, z]) # keeeeel
        if targets != []:
            print(f"TURRET {tid} r: {targets[-1][0]}, theta: {targets[-1][1]}, z: {targets[-1][2]}")
    for globe in json.get("globes",[]):
        r = globe["r"]
        t = globe["theta"]
        z = globe["z"]
        targets.append([r, t, z])
        print(f"GLOBE r: {targets[-1][0]}, theta: {targets[-1][1]}, z: {targets[-1][2]}")





# --- Server setup ---
def run_server():
	server = HTTPServer(("", 8080), WebHandler)
	print("Server running at http://localhost:8080 (Ctrl+C to stop)")
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		print("\nStopping server...")
	finally:
		server.shutdown()
		server.server_close()
		GPIO.cleanup()
		print("Clean exit complete.")

if __name__ == "__main__":
    find_offset()
    run_server()
