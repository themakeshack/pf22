# This is a  rewrite of petfeeder with parallelism
# The following inputs will be supported
#       Button press
#       Email input
#       API call - subsequently this can replace email with a corresponding mobile app
# In addition there will be a bit more modularity on the system

import queue
import re
import threading
import time

import RPi.GPIO as GPIO
from flask import Flask, request

import lcd
import mailer
import my_rpi
import pfconfig
from my_debug import printdebug
from my_rpi import saveLastFeed, ledlight
from pfconfig import *
import sheets


def itsTimeToFeed():
    global lastFeed, READYTOFEED
    feedFile = open(FEEDFILE, 'r')
    lastFeed = float(feedFile.read())
    if (time.time() - lastFeed) > FEEDINTERVAL:
        READYTOFEED = True
    else:
        READYTOFEED = False
    return READYTOFEED


def findLastFeed():
    feedFile = open(FEEDFILE, 'r')
    lastFeed = float(feedFile.read())
    return lastFeed


def validate_email_id(email_id):
    # Make a regular expression
    # for validating an Email
    regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
    # pass the regular expression
    # and the string in search() method
    if (re.search(regex, email_id)):
        return email_id
    else:
        # if the email_id is absent or malformed set it to EMAIL_FROM
        return EMAIL_FROM


def checkmail_thread():
    while True:
        try:
            printdebug(1, "Just about to call checkmail from thread")
            mailer.checkmail()
        except:
            printdebug(1, "Could not start checkmail")
        time.sleep(MAILCHECK_INTERVAL)


def webserver_thread(lcd_text_q):
    global lastFeed, lcd_line_2
    try:
        # Create the app object
        app = Flask(__name__)

        @app.route("/")
        def do_nothing():
            return ("Base call - do nothing")

        @app.route("/FEED/")
        @app.route("/FEED")
        def feed():
            global lastFeed
            email_to=EMAIL_FROM
            input_method='API'
            if 'email_to' in request.args:
                email_to = request.args.get('email_to')
            if 'input_method' in request.args:
                input_method = request.args.get('input_method')
            # Validate to make sure the email is formed ok
            email_to = validate_email_id(email_to)
            # Check if we are ready to feed
            if itsTimeToFeed():
                lastFeed = time.time()
                saveLastFeed(FEEDFILE, lastFeed)
                printdebug(1, "Feeding now and sending email to " + email_to)
                # Update the LCD message
                lcd_text_q.put("START")
                lcd_text_q.put("Feeding...      ")
                if MOTORON:
                    GPIO.output(MOTORCONTROLPIN, True)
                    time.sleep(MOTORTIME)
                    GPIO.output(MOTORCONTROLPIN, False)
                lcd_text_q.put("Feeding...done  ")
                sheets.update_sheet(input_method)
                time.sleep(3)
                lcd_text_q.put("START")
                lcd_text_q.put("Photo...        ")
                my_rpi.takePic()
                lcd_text_q.put("Photo...done    ")
                timeString = time.strftime("%A %d %B %Y at %H:%M:%S.", time.gmtime(lastFeed))
                fedMessage = "Fed Lucky on " + timeString + "using method " + input_method
                lcd_text_q.put("START")
                lcd_text_q.put("Emailing...     ")
                mailer.SendMessage(EMAIL_FROM, email_to, "Lucky is fed", fedMessage, ATTACHMENT_DIR, ATTACHMENT_FILE)
                lcd_text_q.put("Emailing...done ")
                return ("Fed\n")
            else:
                lcd_text_q.put("START")
                lcd_text_q.put("Wait to feed    ")
                lastFeed = findLastFeed()
                timeString = time.strftime("%Hh:%Mm:%Ss", time.gmtime(lastFeed + FEEDINTERVAL - time.time()))
                mailer.SendMessage(EMAIL_FROM, email_to, "Not ready to be fed yet",
                                   "Got your feeding request\nBut there is still " + timeString + " needed to feed\n")
                lcd_text_q.put("Come back later ")
                return ("Not ready to be fed yet\n")

        @app.route("/PIC/")
        @app.route("/PIC")
        def pic():
            printdebug(1, "Taking pic")
            email_to=EMAIL_FROM
            input_method='API'
            if 'email_to' in request.args:
                email_to = request.args.get('email_to')
            if 'input_method' in request.args:
                input_method = request.args.get('input_method')
            # Validate to make sure the email is formed ok
            email_to = validate_email_id(email_to)
            lcd_text_q.put("START")
            lcd_text_q.put("Taking pic...   ")
            my_rpi.takePic()
            lcd_text_q.put("Taking pic..done")
            lcd_text_q.put("START")
            lcd_text_q.put("Emailing pic... ")
            mailer.SendMessage(EMAIL_FROM, email_to, "Photo is here", "Here is your requested photo", ATTACHMENT_DIR,
                               ATTACHMENT_FILE)
            lcd_text_q.put("Emailing...done ")
            return ("Took pic\n")

        @app.route("/STATUS/")
        @app.route("/STATUS")
        def status():
            global LastFeed
            email_to=EMAIL_FROM
            input_method='API'
            if 'email_to' in request.args:
                email_to = request.args.get('email_to')
            if 'input_method' in request.args:
                input_method = request.args.get('input_method')
            # Validate to make sure the email is formed ok
            email_to = validate_email_id(email_to)
            lastFeed = findLastFeed()
            timeString = time.strftime("%b %d %H:%M:%S", time.gmtime(lastFeed))
            message = "Lucky was last fed on " + timeString + "\n"

            if itsTimeToFeed():
                message += "Ready to feed now. Send a message with FEED as subject"

            else:
                timeLeft = time.strftime("%Hh:%Mm:%Ss", time.gmtime(lastFeed + FEEDINTERVAL - time.time()))
                message += "Not ready to be fed yet. There is still " + timeLeft + " left to feed"

            mailer.SendMessage(EMAIL_FROM, email_to, "Response to your query", message)

            return ("Replied with STATUS\n")

        # Start the web server
        app.run('0.0.0.0')

    except:
        printdebug(1, "Could not start web server")


def lcd_thread(lcd_display, lcd_text_q):
    global lastFeed
    lcd_display.clear()
    while True:
        lcd.lcd_update(lcd_display, lcd_text_q, lastFeed)
        time.sleep(.1)


def feedbutton_thread():
    def feedbutton_callback(channel):
        mailer.processKeyword("FEED", EMAIL_FROM, "button")
        printdebug(1, "Got a feedbutton press")
    printdebug(1, "yo, got to the feedbutton thread")
    GPIO.add_event_detect(FEEDBUTTONPIN, GPIO.RISING, callback=feedbutton_callback)  # Setup event on pin FEEDBUTTONPIN rising edge
    while True:
        pass


if __name__ == "__main__":
    global lastFeed

    try:
        pfconfig.init()
        # Let's take care of all initializations
        # Initialize the GPIO for the Raspberry Pi
        lastFeed = my_rpi.initialize()

        # Initialize the LCD
        lcd_display = lcd.lcd_initialize()
        # Create a message queue for the LCD text
        lcd_text_q = queue.Queue()

        # Create the threads
        run_event = threading.Event()
        run_event.set()

        # Create the LCD thread
        threadLCD = threading.Thread(target=lcd_thread, args=[lcd_display, lcd_text_q])
        # Create the web (Flask) thread
        threadWebServer = threading.Thread(target=webserver_thread, args=[lcd_text_q])
        # Create the email thread
        threadMail = threading.Thread(target=checkmail_thread, args=())
        # Create the button check thread
        threadButton = threading.Thread(target=feedbutton_thread, args=())

        # Start all the threads
        threadLCD.start()
        threadWebServer.start()
        threadMail.start()
        threadButton.start()

    except KeyboardInterrupt:
        run_event.clear()

        # Finish the threads
        threadLCD.join()
        print("LCD thread closed")
        threadWebServer.join()
        print("Web thread closed")
        threadMail.join()
        print("Mail thread closed")
        threadButton.join()
        print("Button thread closed")

        GPIO.cleanup()
        print("GPIO cleaned up")
