import os
import subprocess
import time

import RPi.GPIO as GPIO
import picamera

from my_debug import printdebug
from pfconfig import *


def takePic():
    printdebug(1, "Got to takePic")
    # detect if we have a camera
    camdetect = int(subprocess.check_output(["vcgencmd", "get_camera"]).decode().strip()[-1])
    if (camdetect):
        # we have a camera
        printdebug(1, "We have a camera")
        try:
            with picamera.PiCamera() as camera:
                ledlight("on")
                camera.hflip = True
                camera.vflip = True
                timenow = time.strftime("%b-%d %H:%M:%S", time.localtime(time.time()))
                camera.annotate_text = timenow
                camera.annotate_text_size = 50
                camera.resolution = (640, 480)
                camera.brightness = 55
                camera.exposure_mode = 'auto'
                camera.start_preview()
                printdebug(1, "Capturing image...")
                camera.capture(PICFILE)
                ledlight("off")
                printdebug(1, "Done")
            return True
        except picamera.PiCameraError:
            return False
    else:
        # did not detect camera
        return False


def ledlight(command):
    printdebug(1, "Came into ledlight")
    if command == "on":
        GPIO.output(LEDLIGHT, True)
    elif command == "off":
        GPIO.output(LEDLIGHT, False)


def saveLastFeed(FEEDFILE, lastFeed):
    with open(FEEDFILE, 'w') as file:
        file.write(str(lastFeed))
    pass


def initialize():
    # Initialize the GPIO system
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # Initialize the pin for the motor control
    GPIO.setup(MOTORCONTROLPIN, GPIO.OUT)
    GPIO.output(MOTORCONTROLPIN, False)

    # Initialize the pin for the LED light
    GPIO.setup(LEDLIGHT, GPIO.OUT)
    GPIO.output(LEDLIGHT, False)

    # Initialize the pin for the feed and reset buttons
    GPIO.setup(FEEDBUTTONPIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(RESETBUTTONPIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Initialize lastFeed
    if os.path.isfile(FEEDFILE):
        printdebug(1, "Found the file " + FEEDFILE + " during initialization\n")
        feedFile = open(FEEDFILE, 'r')
        lastFeed = float(feedFile.read())
        printdebug(1, "Feed string is " + str(lastFeed))
        feedFile.close()
    else:
        printdebug(1, "Could not find the file during initialization")
        lastFeed = time.time()
        printdebug(1, "Initializing saveLastFeed from initialize()")
        saveLastFeed(FEEDFILE, lastFeed)

    return lastFeed


if __name__ == "__main__":
    exit(0)
