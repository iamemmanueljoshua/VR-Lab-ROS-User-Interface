import io
import picamera
import logging
import socketserver
from threading import Condition
from http import server

PAGE="""\
<html  lang="en">
<head>
<!-- Required meta tags -->
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1">

<!-- Bootstrap CSS -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">

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
          <p style="font-size: 24px; font-weight: bold; color: green;">Connection status: <span id="status"></span></p>
      </section>

       <!-- SPEED -->
      <section>
        <div>
            <label for="robot-speed">
                <strong>Robot speed</strong>
            </label>
            <input type="range" min="15" max="80" class="custom-range" id="robot-speed">
        </div>
      </section>
      
      <section> 
        <div class="container" style="padding-top: 40px;">
          <div class="row">
            <div class="col">
              <section>
                 <!-- VIDEO -->
                 <img src="stream.mjpg" width="640" height="480">
              </section>
            </div>
            <div class="col">
              <section  style="margin-top: 250px;">
                <!-- JOYSTICK -->
                <div id="zone_joystick" style="position: relative;" ></div>
              </section>
            </div>
          </div>
        </div>
      </section>
  </center>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-ka7Sk0Gln4gmtz2MlQnikT1wXgYsOg+OMhuP+IlRH9sENBO0LRn5q+8nbTov4+1p" crossorigin="anonymous"></script>
    <script type="text/javascript" src="http://static.robotwebtools.org/roslibjs/current/roslib.min.js"></script>
    <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/nipplejs/0.7.3/nipplejs.js"></script>
    <script>
        var ros = new ROSLIB.Ros({
            url : 'ws://172.24.232.239:9090'
        });

        ros.on('connection', function() {
            document.getElementById("status").innerHTML = "Connected";
        });

        ros.on('error', function(error) {
            document.getElementById("status").innerHTML = "Error";
        });

        ros.on('close', function() {
            document.getElementById("status").innerHTML = "Closed";
        });


        // Listener
        var txt_listener = new ROSLIB.Topic({
            ros : ros,
            name : '/txt_msg',
            messageType : 'std_msgs/String'
        });

        txt_listener.subscribe(function(m) {
            document.getElementById("msg").innerHTML = m.data;
            move(1,0);
        });

        // Publisher
        cmd_vel_listener = new ROSLIB.Topic({
            ros : ros,
            name : "/cmd_vel",
            messageType : 'geometry_msgs/Twist'
        });

        move = function (linear, angular) {
            var twist = new ROSLIB.Message({
            linear: {
                x: linear,
                y: 0,
                z: 0
            },
            angular: {
                x: 0,
                y: 0,
                z: angular
            }
            });
            cmd_vel_listener.publish(twist);
        }


        createJoystick = function () {
            var options = {
            zone: document.getElementById('zone_joystick'),
            threshold: 0.1,
            position: { left: 50 + '%' },
            mode: 'static',
            size: 150,
            color: '#000000',
            };
            manager = nipplejs.create(options);

            linear_speed = 0;
            angular_speed = 0;

            self.manager.on('start', function (event, nipple) {
            console.log("Movement start");
            });

            self.manager.on('move', function (event, nipple) {
            console.log("Moving");
            });

            self.manager.on('end', function () {
            console.log("Movement end");
            });


        manager.on('start', function (event, nipple) {
            timer = setInterval(function () {
            move(linear_speed, angular_speed);
            }, 25);
        });


        manager.on('end', function () {
            if (timer) {
            clearInterval(timer);
            }
            self.move(0, 0);
        });


        manager.on('move', function (event, nipple) {
            max_linear = 5.0; // m/s
            max_angular = 2.0; // rad/s
            max_distance = 75.0; // pixels;
            linear_speed = Math.sin(nipple.angle.radian) * max_linear * nipple.distance/max_distance;
            angular_speed = -Math.cos(nipple.angle.radian) * max_angular * nipple.distance/max_distance;
        });
        }
        window.onload = function () {
            createJoystick();
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
