import queue
import time
from datetime import datetime
from subprocess import Popen, PIPE
from time import sleep

import adafruit_character_lcd.character_lcd as characterlcd
import board
import digitalio

from my_debug import printdebug
from pfconfig import FEEDINTERVAL


def lcd_initialize():
    # Modify this if you have a different sized character LCD
    lcd_columns = 16
    lcd_rows = 2

    # compatible with all versions of RPI as of Jan. 2019
    # v1 - v3B+
    lcd_rs = digitalio.DigitalInOut(board.D22)
    lcd_en = digitalio.DigitalInOut(board.D17)
    lcd_d4 = digitalio.DigitalInOut(board.D25)
    lcd_d5 = digitalio.DigitalInOut(board.D24)
    lcd_d6 = digitalio.DigitalInOut(board.D23)
    lcd_d7 = digitalio.DigitalInOut(board.D18)

    # Initialise the lcd.py class
    lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6,
                                          lcd_d7, lcd_columns, lcd_rows)

    return lcd


# looking for an active Ethernet or WiFi device
def find_interface():
    find_device = "ip addr show"
    interface_parse = run_cmd(find_device)
    for line in interface_parse.splitlines():
        if "state UP" in line:
            dev_name = line.split(':')[1]
    return dev_name


# find an active IP on the first LIVE network device
def parse_ip(interface):
    find_ip = "ip addr show %s" % interface
    ip_parse = run_cmd(find_ip)
    for line in ip_parse.splitlines():
        if "inet " in line:
            ip = line.split(' ')[5]
            ip = ip.split('/')[0]
    return ip


# run unix shell command, return as ASCII
def run_cmd(cmd):
    p = Popen(cmd, shell=True, stdout=PIPE)
    output = p.communicate()[0]
    return output.decode('ascii')


# wipe LCD screen before we start
# lcd.py.clear()

# before we start the main loop - detect active network device and ip address
sleep(2)
interface = find_interface()
ip_address = parse_ip(interface)


# print( "IP Address is ", ip_address)

def lcd_update(lcd, lcd_text_q, lastFeed):
    if lcd_text_q.empty():
        lcd_line_1 = datetime.now().strftime('%b %d  %H:%M:%S\n')
        if (time.time() - lastFeed) > FEEDINTERVAL:
            lcd_line_2 = "Ready to feed   "
        else:
            # Calculate the amount of time that is required to do the next feed
            lcd_line_2 = "Next in " + time.strftime("%H:%M:%S", time.gmtime(lastFeed + FEEDINTERVAL - time.time()))
        lcd.message = lcd_line_1 + lcd_line_2
        #printdebug(1, "lcd_line_2 is " + lcd_line_2)
    else:
        lcd_line_2 = lcd_text_q.get_nowait()
        #printdebug(1, "lcd_line_2 is " + lcd_line_2)
        # THere is a special non-display text message called "START" that signals that the second line should stay in a loop for a while
        # with the text that follows the START. The text will stay the same until a new text gets placed in the queue
        if lcd_line_2 is "START":
            lcd_line_2 = lcd_text_q.get_nowait()
            while lcd_text_q.empty():
                lcd_line_1 = datetime.now().strftime('%b %d  %H:%M:%S\n')
                lcd.message = lcd_line_1 + lcd_line_2
                #printdebug(1, "lcd_line_2 is " + lcd_line_2)
            lcd_line_2 = lcd_text_q.get_nowait()
            lcd_line_1 = datetime.now().strftime('%b %d  %H:%M:%S\n')
            lcd.message = lcd_line_1 + lcd_line_2
            #printdebug(1, "lcd_line_2 is " + lcd_line_2)
            time.sleep(1)


if __name__ == "__main__":
    lcd = lcd_initialize()
    q = queue.Queue()
    lcd_update(lcd, q)
