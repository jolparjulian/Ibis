from http.server import BaseHTTPRequestHandler, HTTPServer
import RPi.GPIO as GPIO
from urllib.parse import parse_qs
import json
import requests
import threading
import numpy as np
import time
from stepper import Stepper #grab stepper class

#Set up GPIOs
GPIO.setmode(GPIO.BCM)
laser_pin = 26 #check this
GPIO.setup(laser_pin, GPIO.OUT)
laser_time = 2.5

# Set up steppers
vert = Stepper()
hor = Stepper()

vert.zero()
hor.zero()

vert.start_process()
hor.start_process()

# Positional variables
position = [0,0,0] # xyz
cyl_position = [0,0,0] # r theta z
ref_positions = [] # place r/t/z/stepper angles into here to math later
angle = [0,0] #pitch/yaw

json_data = [] # to put json in later

ip_string = "192.168.1.254" # defaults to his 
ip_string = "172.20.10.4" # mine

# some random stuff
pos_tol = 3 * np.pi/180 # angular tolerance between us and the next turret over
assumed_height = 0.2 # turret height for everyone else
us_turret_num = 1 # our turret number, to find our position and also remove from json
jog_amount = 1 #degrees to jog each arrow click
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
            font-family: Arial, sans-serif;
            margin: 40px;
        }}
        .box {{
            border: 3px solid black;
            padding: 20px;
            display: inline-block;
            border-radius: 10px;
            margin: 20px;
        }}
        .btn {{
            padding: 10px 20px;
            margin: 5px;
            border: 2px solid black;
            border-radius: 10px;
            background: #fff;
            cursor: pointer;
            font-size: 16px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr;
            justify-items: center;
        }}
        .row {{
            display: flex;
            justify-content: center;
        }}
        .inputbox {{
            border: 2px solid black;
            border-radius: 10px;
            padding: 5px;
            width: 100px;
            margin-right: 10px;
        }}
        .huge-button {{
            font-size: 48px; 
            padding: 30px 60px;
        }}
        #afterJSON{{
            display: none;
        }}
    </style>
</head>

<body>

<!-- LEFT SIDE: Arrow buttons + JSON + zero -->
<div style="display:flex; align-items:flex-start; gap:40px;">
    <div class="box">

        <!-- Arrow controls -->
        <div class="grid">
            <div class="row">
                <button onmousedown="startJog('up')" onmouseup="stopJog()" onmouseleave="stopJog()">up</button>
            </div>
            <div class="row">
                <button onmousedown="startJog('left')" onmouseup="stopJog()" onmouseleave="stopJog()">left</button>
                <button onmousedown="startJog('right')" onmouseup="stopJog()" onmouseleave="stopJog()">right</button>
            </div>
            <div class="row">
                <button onmousedown="startJog('down')" onmouseup="stopJog()" onmouseleave="stopJog()">down</button>
            </div>
        </div>

        <br><br>

        <!-- JSON fetch -->
        <div class="row">
            <button class="btn" onclick="jsonButton()">get them jsons</button>
        </div>


        <br>

        <!-- Zero -->
        <div class="row">
            <button class="btn" onclick="send('zero')">zero</button>
        </div>

    </div>

    <div style="position:relative; text-align:center; margin-top:50px;">

        <button id="laserBtn" class="huge-button" style="padding:20px 40px;" onclick="Laser()">
            fire the laser
        </button>

        <!-- Overlay GIF -->
        <video id="laserGif"
            src=""
            style="
                position:absolute;
                top:50%;
                left:50%;
                transform:translate(-50%, -50%);
                width:400px;
                display:none;
                pointer-events:none;
            muted
            plays-inline
            ">
    </div>
    <div id="afterJSON" style="position:relative; text-align:center; margin-top:300px;">
        <button class="btn" onclick="send('find')">play peekaboo</button>
        <button class="btn" onclick="send('kill')">kill them all</button>
    </div>

</div>

<!-- BOTTOM: r, theta, z reference -->
<div style="display:flex; align-items:flex-start; gap:40px;">

    <div class="box">
        <input id="rval" class="inputbox" placeholder="r">
        <input id="tval" class="inputbox" placeholder="theta">
        <input id="zval" class="inputbox" placeholder="z">
        <button class="btn" onclick="reference()">reference</button>
    </div>
    <div class="box">
        <input id="rval2" class="inputbox" placeholder="r">
        <input id="tval2" class="inputbox" placeholder="theta">
        <input id="zval2" class="inputbox" placeholder="z">
        <button class="btn" onclick="sendTo()">go here</button>
    </div>

</div>
<audio id="laserSound" src="laser_sound.mp3"></audio>

<script>

    function send(cmd) {{
        fetch("/", {{
            method: "POST",
            headers: {{ "Content-Type": "application/x-www-form-urlencoded" }},
            body: "cmd=" + cmd
        }});
    }}
    function jsonButton(){{
        send('json');
        document.getElementById("afterJSON").style.display = 'block'; //show stuff
    }}
    function Laser(){{
    	send('fire');
    }}
    function fireLaser(){{
        const gif = document.getElementById("laserGif");
        const audio = document.getElementById("laserSound");

        gif.style.display = "block";

        const src = "laser_gif.mp4";
        gif.src = src;
        gif.currentTime = 0;
        gif.play();

        audio.currentTime = 0;
        audio.play();

        gif.onended = () => {{
            gif.style.display = "none";
        }};


        send('fire'); // trigger server action
    }}   
    let jogInterval = null;
    function startJog(direction) {{
        send(direction);                      // initial press
        jogInterval = setInterval(()=> send(direction), 150); // repeat every 150ms
    }}
    function stopJog() {{
        if (jogInterval) {{ clearInterval(jogInterval); jogInterval = null; }}
    }}

    function reference() {{
        let r = document.getElementById("rval").value;
        let t = document.getElementById("tval").value;
        let z = document.getElementById("zval").value;

        fetch("/", {{
            method: "POST",
            headers: {{ "Content-Type": "application/x-www-form-urlencoded" }},
            body: "ref=1&r=" + r + "&t=" + t + "&z=" + z
        }});
    }}

    function sendTo() {{
        let r = document.getElementById("rval2").value;
        let t = document.getElementById("tval2").value;
        let z = document.getElementById("zval2").value;

        fetch("/", {{
            method: "POST",
            headers: {{ "Content-Type": "application/x-www-form-urlencoded" }},
            body: "goTo=1&r=" + r + "&t=" + t + "&z=" + z
        }});
    }}
</script>

</body>
</html>
"""
# --- Request Handler ---
class WebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        '''
        if self.path != "/" and os.path.isfile(self.path.lstrip("/")):
            filepath = self.path.lstrip("/")
            mime = mimetypes.guess_type(filepath)[0] or "application/octet-stream"

            self.send_response(200)
            self.send_header("Content-type", mime)
            self.end_headers()

            with open(filepath, "rb") as f:
                self.wfile.write(f.read())
            return
        '''
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
                    jog(vert, jog_amount)
                elif cmd == "down":
                    jog(vert, -jog_amount)
                elif cmd == "right":
                    jog(hor, -jog_amount)
                elif cmd == "left":
                    jog(hor, jog_amount)
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
                    # will prompt for ip address
                    json_data = requests.get(f"http://{ip_string}:8000/positions.json")
                    json_data = json_data.json()
                    if json_data == None:
                    	print("ya fucked up the ip address")
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
                elif cmd == "kill":
                    if test_mode:
                        #test_json(positions)
                        test_json(json_data)
                    else:
                        destroy(json_data)
                        #destroy(positions)

            if "ref" in data and "r" in data and "t" in data and "z" in data:
                pos = [float(data["r"][0]), float(data["t"][0]), float(data["z"][0])]
                reference(pos[0],pos[1],pos[2]) # add as a reference

            if "goTo" in data and "r" in data and "t" in data and "z" in data:
                pos = [float(data["r"][0]), float(data["t"][0]), float(data["z"][0])]
                print(pos)
                print(hor.angle.value)
                print(vert.angle.value)
                hor.goToAngle(pos[0])
                vert.goToAngle(pos[1])
                #aim_at(pos[0],pos[1],pos[2]) # point at

        except:
            pass

def jog(motor, amount): # bc the rotate function got removed
	curr = motor.angle.value #current angle
	motor.goToAngle(curr+amount)
	#print(f"{motor} going to {curr+amount}")

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
		t = ref_positions[i][1]
		z = ref_positions[i][2]
		pitch = ref_positions[i][3]
		yaw = ref_positions[i][4]
		d = angles(pitch, yaw) # make 3d angle vector
		d = d/np.linalg.norm(d) # unit vector
		L = np.asarray([r*np.cos(t),r*np.sin(t),z]) # aimed position, cartesian
		M = np.eye(3) - np.outer(d,d) # projection matrix
		A += M
		b += M.dot(L) 
	P = np.linalg.pinv(A).dot(b) # pinv does least squares inverse
	global cyl_position
	# put in the cylinder coords for checks later
	cyl_position[0] = np.sqrt(P[0]**2 + P[1]**2) # r
	x = P[0]
	y = P[1]
	cyl_position[1] = np.arctan2(y,x) % (2*np.pi) #radians, positive from 
	cyl_position[2] = P[2]
	print(P)
	return P

def angles(pitch, yaw):
	# makes 3d angle vector from pitch and yaw
	# assumes degrees
	pitch = pitch*2*np.pi/360
	yaw = yaw*2*np.pi/360
	return np.array([np.cos(pitch)*np.cos(yaw), np.cos(pitch)*np.sin(yaw), np.sin(yaw)])

def system_zero(): # zeros the motors, run when pointing at origin
	vert.zero()
	hor.zero()
	print("zero")

def aim_at(radius, angle, height):
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

	# go motors go
	print(f"hor going to {pitch}, vert going to {yaw}")
	hor.goToAngle(pitch)
	vert.goToAngle(yaw)

def destroy(json):
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
        if int(tid) != us_turret_num: # this should work better
            targets.append([r, t, z]) # keeeeel
    for globe in json.get("globes",[]):
        r = globe["r"]
        t = globe["theta"]
        z = globe["z"]
        targets.append([r, t, z])
    for target in targets:
        aim_at(target[0], target[1], target[2])
        print(f"shooting at {target}")
        fire_laser()

def test_motors():
	# test code to check if the motors work
	# start by checking goToAngle
	test_angle = 45
	print(f"vert at {vert.angle.value}, hor at {hor.angle.value}")
	print(f"goToAngle to {test_angle}")
	vert.goToAngle(test_angle)
	hor.goToAngle(test_angle)
	while(not (hor.at_target and vert.at_target)):
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

def find_position(json):
    stuff = json.get("turrets",{}).items()
    for tid, turret in stuff:
        if int(tid) == us_turret_num:
            r = turret["r"]
            t = turret["theta"]
            us_pos = [r, t]
            print(f"we live at r: {us_pos[0]}, theta: {us_pos[1]}")
            break





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
	run_server()
