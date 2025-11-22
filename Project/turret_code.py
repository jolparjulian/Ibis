from http.server import BaseHTTPRequestHandler, HTTPServer
import RPi.GPIO as GPIO
from urllib.parse import parse_qs
import json
import threading
import numpy as np
import time
from stepper import Stepper #grab stepper class

#Set up GPIOs
GPIO.setmode(GPIO.BCM)
laser_pin = 17 #check this
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
position = [] # xyz
cyl_position = [] # r theta z
ref_positions = [] # place r/t/z/stepper angles into here to math later
angle = [] #pitch/yaw

# some random stuff
pos_tol = 2 # angular tolerance between us and the next turret over
assumed_height = 0.2 # turret height for everyone else


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
		body {
			font-family: Arial, sans-serif;
			margin: 40px;
		}
		.box {
			border: 3px solid black;
			padding: 20px;
			display: inline-block;
			border-radius: 10px;
			margin: 20px;
		}
		.btn {
			padding: 10px 20px;
			margin: 5px;
			border: 2px solid black;
			border-radius: 10px;
			background: #fff;
			cursor: pointer;
			font-size: 16px;
		}
		.grid {
			display: grid;
			grid-template-columns: 1fr;
			justify-items: center;
		}
		.row {
			display: flex;
			justify-content: center;
		}
		.inputbox {
			border: 2px solid black;
			border-radius: 10px;
			padding: 5px;
			width: 100px;
			margin-right: 10px;
		}
	</style>
</head>

<body>

<!-- LEFT SIDE: Arrow buttons + JSON + zero -->
<div class="box">

	<!-- Arrow controls -->
	<div class="grid">
		<div class="row">
			<button class="btn" onclick="send('up')">up</button>
		</div>
		<div class="row">
			<button class="btn" onclick="send('right')">right</button>
			<button class="btn" onclick="send('left')">left</button>
		</div>
		<div class="row">
			<button class="btn" onclick="send('down')">down</button>
		</div>
	</div>

	<br><br>

	<!-- JSON fetch -->
	<div class="row">
	    <button class="btn" onclick="fetchJSON()">load positions.json</button>
	</div>


	<br>

	<!-- Zero -->
	<div class="row">
		<button class="btn" onclick="send('zero')">zero</button>
	</div>

</div>


<!-- RIGHT SIDE: r, theta, reference + fire -->
<div style="display:flex; align-items:flex-start; gap:40px;">

	<div class="box">
		<input id="rval" class="inputbox" placeholder="r">
		<input id="tval" class="inputbox" placeholder="theta">
		<input id="zval" class="inputbox" placeholder="z">
		<button class="btn" onclick="reference()">reference</button>
	</div>

	<div class="box" style="width:250px; height:250px;">
		<div style="text-align:center; margin-top:100px;">
			<button class="btn" style="padding:20px 40px;" onclick="send('fire')">fire</button>
		</div>
	</div>

</div>


<script>
	function send(cmd) {
		fetch("/", {
			method: "POST",
			headers: { "Content-Type": "application/x-www-form-urlencoded" },
			body: "cmd=" + cmd
		});
	}

	function fetchJSON() {
	    fetch("http://192.168.1.254:8000/positions.json")
	        .then(r => r.text())
	        .then(txt => {
	            fetch("/", {
	                method: "POST",
	                headers: { "Content-Type": "application/x-www-form-urlencoded" },
	                body: "fetchjson=1&data=" + encodeURIComponent(txt)
	            });
	        })
	        .catch(err => alert("Failed to fetch JSON file"));
		}

	function reference() {
		let r = document.getElementById("rval").value;
		let t = document.getElementById("tval").value;
		let z = document.getElementById("zval").value;

		fetch("/", {
			method: "POST",
			headers: { "Content-Type": "application/x-www-form-urlencoded" },
			body: "ref=1&r=" + r + "&t=" + t + "&z=" + z
		});
	}
</script>

</body>
</html>
"""

# --- Request Handler ---
class LEDHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		self.wfile.write(make_page().encode())

	def do_POST(self):
		length = int(self.headers['Content-Length'])
		body = self.rfile.read(length).decode()
		data = parse_qs(body)

		try:
			if "cmd" in data:
				cmd = data["cmd"][0]
				# first four are motor jog u/d/l/r
				if cmd == "up":
					jog(vert, 1)
				elif cmd == "down":
					jog(vert, -1)
				elif cmd == "right":
					jog(hor, 1)
				elif cmd == "left":
					jog(hor, -1)
				# then fire
				elif cmd == "fire":
					# thread it rah
					laser = threading.Thread(target=fire_laser())
					laser.daemon = True
					laser.start()
				# then zero
				elif cmd == "zero":
					system_zero()

			if "fetchjson" in data and "data" in data:
				# do json stuff
				raw = data["data"][0]

				positions = json.loads(raw)
				destroy(positions)

			if "ref" in data and "r" in data and "t" in data and "z" in data:
				pos = [float(data["r"][0]), float(data["t"][0]), float(data["z"][0])]
				reference(pos[0],pos[1],pos[2]) # add as a reference


		except:
			pass

def jog(motor, amount): # bc the rotate function got removed
	curr = motor.angle.value #current angle
	motor.goToAngle(curr+amount)

def reference(r, t, z): #run this when im hitting a known location
	global ref_positions
	global position
	# add the r/theta we tell it its aiming at and the angles of the two steppers
	ref_positions.append([r, t, z, hor.angle.value, vert.angle.value])
	if len(ref_positions) >= 3:
		position = calibrate() # after enough points, calibrate to get true pos

def fire_laser():
	GPIO.output(laser_pin, 1)
	time.sleep(laser_time)
	GPIO.output(laser_pin, 0)

def calibrate(): # run this after enough reference points
	A = np.zeros((3,3)) #initialize some stuff
	b = np.zeros(3)
	for i in range(len(ref_positions)):
		d = angles(ref_positions[i,4], ref_positions[i,5]) # make 3d angle vector
		d = d/np.linalg.norm(d) # unit vector
		L = np.asarray(ref_positions[i][1:3]) # aimed position
		M = np.eye(3) - np.outer(d,d) # projection matrix
		A += M
		b += M*L 
	P = np.linalg.pinv(A).dot(b) # pinv does least squares inverse
	global cyl_position
	# put in the cylinder coords for checks later
	cyl_position[0] = np.sqrt(P[0]**2 + P[1]**2) # r
	x = P[0]
	y = P[1]
	cyl_position[1] = np.arctan2(y,x) % 2*np.pi #radians, positive from 
	cyl_position[2] = P[2]
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

def aim_at(radius, angle, height):
	phi = cyl_position[2] - angle


def destroy(json):
	targets = []
	# add targets from dicts
	for tid, turret in json["turrets"].items():
		r = turret["r"]
		t = turret["t"]
		z = assumed_height
		if abs(theta-cyl_position[1]) >= pos_tol: # make sure we dont try to kill ourselves
			targets.append([r, t, z]) # add to kill list
	for globe in json["globes"].items():
		r = gloeb["r"]
		t = globe["t"]
		z = globe["z"]
		targets.append([r, t, z])
	for target in targets:
		# multiprocessing is gonna make this weird i think
		# prolly gonna need to give the steppers an ok variable or a check or something
		aim_at(target[0], target[1], target[2])
		fire_laser()



# --- Server setup ---
def run_server():
	server = HTTPServer(("", 8080), LEDHandler)
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
