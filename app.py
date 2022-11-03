import io
import picamera
import logging
import socketserver
from threading import Condition
from http import server

PAGE="""\
<html lang="en">

<head>
    <!-- Required meta tags -->
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet"
        integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">
    <title>Robot Webpage</title>
</head>

<body>
    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg navbar navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">ROBOT UI</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>
            <div class="collapse navbar-collapse" id="navbarSupportedContent">
                <ul class="navbar-nav me-auto mb-2 mb-lg-0">
                    <li class="nav-item">
                        <a class="nav-link active" aria-current="page" href="#">Home</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#">About Us</a>
                    </li>
                </ul>
                <form class="d-flex">
                    <input class="form-control me-2" type="search" placeholder="Search" aria-label="Search">
                    <button class="btn btn-outline-success" type="submit">Search</button>
                </form>
            </div>
        </div>
    </nav>
    <center>
        <section>
            <div class="container-fluid" style="padding-top: 100px;">
                <h1>Welcome to TSU VR-Lab ROS User Interface</h1>
                <p style="font-size: 24px; font-weight: bold; color: #51995d;">Connection status:
                    <span id="status"></span>
                </p>
        </section>
        <!-- SPEED -->
        <!-- SPEED -->
        <div class="row">
            <div class="col-md-4"></div>
            <div class=" col-md-4">
                <label for="robot-speed">
                    <strong>Robot speed</strong>
                </label>
                <input type="range" min="15" max="80" class="custom-range" id="robot-speed">
            </div>
            <div class="col-md-4"></div>
        </div>
        <section>
            <div class="container" style="padding-top: 40px;">
                <div class="row">
                    <div class="col">
                        <section>
                            <!-- VIDEO -->
                            <img class="p-1 bg-dark" src="stream.mjpg" width="640" height="480">
                        </section>
                    </div>
                    <div class="col">
                        <section>
                            <!-- JOYSTICK -->
                            <div id="joystick" style="width: 210px; margin-top: 100px; position: relative;"></div>
                        </section>
                    </div>
                </div>
            </div>
        </section>
        <!-- INFO -->
        <div class="row my-4">
            <div class="col-md-2"></div>
            <div class="col-md-8">
                <div class="alert alert-success">
                    <h4 class="alert-heading">ROS + Bootstrap interface demo</h4>
                    <ul>
                        <li>set speed using a slider</li>
                        <li>use joystick or W(up) | A(left) | S(down) | D(right) keys on keyboard to move </li>
                    </ul>
                </div>
            </div>
            <div class="col-md-2"></div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"
            integrity="sha384-ka7Sk0Gln4gmtz2MlQnikT1wXgYsOg+OMhuP+IlRH9sENBO0LRn5q+8nbTov4+1p" crossorigin="anonymous">
        </script>
        <script type="text/javascript" src="http://static.robotwebtools.org/roslibjs/current/roslib.min.js"></script>
        <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/nipplejs/0.7.3/nipplejs.js"></script>
        <script src="https://static.robotwebtools.org/keyboardteleopjs/current/keyboardteleop.min.js"></script>
        <script>
            var twist;
            var cmdVel;
            var publishImmidiately = true;
            var robot_IP;
            var manager;
            var teleop;
            var ros;
            
	    window.onload = function () {
                // determine robot address automatically
                // robot_IP = location.hostname;
                // set robot address statically
                robot_IP = "172.24.214.149";
                // // Init handle for rosbridge_websocket
                ros = new ROSLIB.Ros({
                    url: "ws://" + robot_IP + ":9090"
                });
                ros.on('connection', function () {
                    document.getElementById("status").innerHTML = "Connected";
                });
                ros.on('error', function (error) {
                    document.getElementById("status").innerHTML = "Error";
                });
                ros.on('close', function () {
                    document.getElementById("status").innerHTML = "Closed";
                });
                initVelocityPublisher();
                createJoystick();
                initTeleopKeyboard();
            }
	    
	    function moveAction(linear, angular) {
                if (linear !== undefined && angular !== undefined) {
                    twist.linear.x = linear;
                    twist.angular.z = angular;
                } else {
                    twist.linear.x = 0;
                    twist.angular.z = 0;
                }
                cmdVel.publish(twist);
            }
            function initVelocityPublisher() {
                // Init message with zero values.
                twist = new ROSLIB.Message({
                    linear: {
                        x: 0,
                        y: 0,
                        z: 0
                    },
                    angular: {
                        x: 0,
                        y: 0,
                        z: 0
                    }
                });
                // Init topic object
                cmdVel = new ROSLIB.Topic({
                    ros: ros,
                    name: '/cmd_vel',
                    messageType: 'geometry_msgs/Twist'
                });
                // Register publisher within ROS system
                cmdVel.advertise();
            }
            function initTeleopKeyboard() {
                // Use w, s, a, d keys to drive your robot
                // Check if keyboard controller was aready created
                if (teleop == null) {
                    // Initialize the teleop.
                    teleop = new KEYBOARDTELEOP.Teleop({
                        ros: ros,
                        topic: '/cmd_vel'
                    });
                }
                // Add event listener for slider moves
                robotSpeedRange = document.getElementById("robot-speed");
                robotSpeedRange.oninput = function () {
                    teleop.scale = robotSpeedRange.value / 100
                }
            }
            function createJoystick() {
                // Check if joystick was aready created
                if (manager == null) {
                    joystickContainer = document.getElementById('joystick');
                    // joystck configuration, if you want to adjust joystick, refer to:
                    // https://yoannmoinet.github.io/nipplejs/
                    var options = {
                        zone: joystickContainer,
                        position: { left: 50 + '%', top: 105 + 'px' },
                        mode: 'static',
                        size: 200,
                        color: '#00853c',
                        restJoystick: true
                    };
                    manager = nipplejs.create(options);
                    // event listener for joystick move
                    manager.on('move', function (evt, nipple) {
                        // nipplejs returns direction is screen coordiantes
                        // we need to rotate it, that dragging towards screen top will move robot forward
                        var direction = nipple.angle.degree - 90;
                        if (direction > 180) {
                            direction = -(450 - nipple.angle.degree);
                        }
                        // convert angles to radians and scale linear and angular speed
                        // adjust if youwant robot to drvie faster or slower
                        var lin = Math.cos(direction / 57.29) * nipple.distance * 0.005;
                        var ang = Math.sin(direction / 57.29) * nipple.distance * 0.05;
                        // nipplejs is triggering events when joystic moves each pixel
                        // we need delay between consecutive messege publications to
                        // prevent system from being flooded by messages
                        // events triggered earlier than 50ms after last publication will be dropped
                        if (publishImmidiately) {
                            publishImmidiately = false;
                            moveAction(lin, ang);
                            setTimeout(function () {
                                publishImmidiately = true;
                            }, 50);
                        }
                    });
                    // event litener for joystick release, always send stop message
                    manager.on('end', function () {
                        moveAction(0, 0);
                    });
                }
            }
            
	    </script>
  </body>
</html>
"""

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
    output = StreamingOutput()
    #Uncomment the next line to change your Pi's Camera rotation (in degrees)
    #camera.rotation = 90
    camera.start_recording(output, format='mjpeg')
    try:
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        camera.stop_recording()
