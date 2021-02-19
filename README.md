# CamCam

## Introduction
This is a fancy little tool that will allow you to put an overplay on your webcam. I developed it after being fed up with the lack of innovation in the online interview space. I've made this as simple as possible to anyone to set it up and for others to build on top of it. I hope this help you stand out or that you make some cool new innovations. I am new to a lot of these technologies an would appreciate any feedback and insights. Feel free to reach out on discord -> n0remac#9451.

There are three main components: a dummy cam that you can stream custom content into, and FFMpeg script to create the overlay and stream to the dummy cam, and an optional bit of OpenCV allow you to use gestures to effect the video stream. The name CamCam is in reference to taking input from your webcam and outputting it to a dummy cam, but it's also one of my nicknames :P

## Setup
The following works on Linux. If you are using Mac or Windows you will need to find another way to send the stream to a dummy webcam. One possible option is to stream to VLC, capture that with OBS, then use OBS Virtualcam. I tested streaming to VLC but that already had too much latency. I will put those instructions at the end just in case someone can figure out how to optimize them.

## Environment
I used virtualenv for this. If you don't have python 3.6 however I suggest anaconda as it is a really easy way to get new versions of python.

Set up environment with:<br>
`python3.6 -m venv venv`

Activate environment:<br>
`source venv/bin/activate`

Install requirements:<br>
`pip install -r requirements.txt`

If you only want the overlay without the OpenCV component you don't actually need any of the requirements.

## Dummy cam
I used a great kernal module called v4l2loopback. It's setup and use is well documented here https://github.com/umlaeute/v4l2loopback.

If you are on Windows or Mac the only option I came up with is to stream to VLC then pick that up with OBS and send it to OBS Virtualcam. Ooof. You best bet would be to install Linux then uninstall Windows (or just use virtualbox).

## FFMpeg
The basic install of FFMpeg can handle the overlay, but if you want to change the position of your overlay while the script is running you will need to compile FFMpeg with zmq. This was the hardest part for me to figure out. You will need to have `make` installed. If you use FFMpeg for other things be careful here. By doing this I lost some of the libraries that my default version of FFMpeg came with and needed to remake it.

What you need to do is download the source code from here https://ffmpeg.org/download.html or run:<br>
`git clone https://git.ffmpeg.org/ffmpeg.git ffmpeg`

Enter the ffmpeg directory.

Run: <br>
`./configure --enable-libzmq --enable-muxer=mpeg`
Run: <br>
`make`
Run: <br>
`sudo make install`

You can use the --enable-muxer=mpeg flag if you want to try streaming to VLC. I'll say it again; when I compiled this way I lost a lot of configurations so make sure this is what you want to do.

You can get more information here https://trac.ffmpeg.org/wiki/CompilationGuide. I used the "Generic compilation guide" for all platforms at the top.

## The code
If everything went well you should be good to go with the code.

Clone this repository.

Make sure the environment is started and you have created your dummy cam with (Described in that loopback link).

Run the code!
`python dynamic_overlay.py`

### Troubleshooting
You will need good and consistent lighting for the recognition to work. I had to tape paper over my windows to get the optimal setup.

If you restart your computer and have not setup the auto start for v4l2loopback you will need to run it again.

OpenCV requires python 3.6. If you have trouble getting this version, definitely checkout anaconda. https://docs.anaconda.com/anaconda/navigator/tutorials/

If you want to do more with FFMpeg this page has a lot of good examples https://trac.ffmpeg.org/wiki/StreamingGuide

I rely on discord to troubleshoot **a lot**. There are servers for many technologies. The Python Discord server is very useful. https://pythondiscord.com/


### Additional Goodies

To stream to VLC you can use this command:
```
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
    "-sdp_file", "vlcstream.sdp",
    "-f", "mpegts",
    "udp://localhost:1237"
]
```
Then in VLC go to Media > Open Network Stream and put in this url:<br>
udp://@localhost:1237/path/to/vlcstream.sdp

The latency is not good enough for zoom but maybe it can be optimized.


### Credits
Thanks to this dude for the fist cascade: https://github.com/Aravindlivewire/Opencv/tree/master/haarcascade