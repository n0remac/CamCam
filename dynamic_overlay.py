import cv2
import subprocess as sp
import time
import zmq
import sys


# You can specify the overlay image with the first command line argument.
# If you want a default image you can change example.png and image_size.
if len(sys.argv) > 1:
    overlay_file = sys.argv[1]
else:
    overlay_file = "example.png"
    image_size = 100

# If you specified an image you can pass in an image size as well.
if len(sys.argv) > 2:
    overlay_file = sys.argv[2]

# Set up zmq. The socket sends to the FFMpeg script through a tcp port. The poller helps the wait for a recv message.
context = zmq.Context()
socket = context.socket(zmq.REQ)
poller = zmq.Poller()
poller.register(socket, zmq.POLLIN)
socket.connect("tcp://localhost:1236")

# This cascade will recognize your fist. It works best on my right hand so millage may vary.
# cv2 comes with more cascades located in venv/lib/python3.6/site-packages/cv2/data/
hand_cascade = cv2.CascadeClassifier('haarcascade/closed_frontal_palm.xml')

# The number that video capture takes is your webcam. 0 should be the default one. For my usb camera I use 3.
videocapture = cv2.VideoCapture(0)
ret, frame = videocapture.read()
height, width, ch = frame.shape
dimensions = f"{width}x{height}"

# Place initial image location in top corner.
image_x = 35
image_y = 65

# Depending on your set up you might need to change the output, which is the last entry.
# In my case it has always been /dev/video2.
command = [
    "ffmpeg",
    "-y",
    "-f", "rawvideo",
    '-vcodec','rawvideo',
    '-pix_fmt', 'bgr24',
    '-s', dimensions,
    "-i", "-",
    "-i", overlay_file,
    "-filter_complex", "[1:v]scale="+str(image_size)+":-1[ovrl], [0:v][ovrl]overlay="+str(image_x)+":"+str(image_y)+",zmq=bind_address=tcp\\\://127.0.0.1\\\:1236[v]",
    "-pix_fmt", "yuv420p",
    "-map", "[v]",
    "-f", "v4l2",
    "/dev/video2"
]

# This starts and saves a reference to the FFMpeg stream.
proc = sp.Popen(command, stdin=sp.PIPE, stderr=sp.STDOUT, bufsize=0)

grabbing = False
x_turn = True

def move_overlay(num, pos):
    '''
    Function to move the overlay. Sends a message to the ffmpeg process using zmq.

    num: Determines which axis to change
    pos: The position the overlay will move to
    '''

    global grabbing

    # When zmq sends a message it needs to get a response before another message can be sent.
    # The grabbing variable and poller were my solution to this, though there might be a better way. ¯\_(ツ)_/¯
    if grabbing:
        evts = poller.poll(0)
        if len(evts) > 0:
            socket.recv()
            grabbing = False

    if not grabbing:
        grabbing = True
        if num == 0:
            axis = 'x'
        else:
            axis = 'y'
        zmq_message = f'Parsed_overlay_1 {axis} {str(pos)}'
        socket.send(zmq_message.encode())


scale_factor = 1.2
coords = []
prev = time.time()

while True:
    # Get a frame from the video feed, convert it to grayscale, and put it though the cascade to detect any fists.
    ret_, frame = videocapture.read()
    gray_img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    hands = hand_cascade.detectMultiScale(gray_img, scale_factor, minNeighbors=5, minSize=(50,50))

    # Save the position, width, and height of the hands for later use.
    for (x, y, w, h) in hands:
        # You can uncomment the next line if you want to draw a box around your fist.
        #cv2.rectangle(pic, (x, y), (x + w, y+ h ), (255, 0, 0), 2)
        coords = [x, y, w, h]

    elapse = time.time() - prev

    # I couldn't figure out how to get zmq to modify both the x and y position with one message so I did this.
    if x_turn and len(hands) > 0:
        move_overlay(0, coords[0])
        if elapse > 0.05:
            prev = time.time()
            x_turn = False
    elif not x_turn and len(hands) > 0:
        move_overlay(1, coords[1])
        if elapse > 0.05:
            prev = time.time()
            x_turn = True

    # You can uncomment this if you also want a version of the stream in another window.
    # Doing this will actually let you close the program by pressing q
    # I just close the process with ctr-c like a barbarian.
    #cv2.imshow('stream', frame)

    # Send the frame into the ffmpeg stream
    proc.stdin.write(frame.tobytes())

    # This only work when you have cv2.imshow('stream', frame) enabled
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

# Who needs to gracefully exit in python anyways?
videocapture.release()
cv2.destroyAllWindows()
proc.stdin.close()

# ????
# Profit!!!
