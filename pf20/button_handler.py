import threading
import time
from my_debug import printdebug
import RPi.GPIO as GPIO

class ButtonHandler():
    def __init__(self, pin, edge, func, cooldown_time_s=0.1):

        self.pin = pin
        self.edge = edge
        self.func = func
        self.cooldown_time_s = cooldown_time_s  # The time after a found trigger until another trigger can happen in seconds
        self.last_trigger = 0
        self.trigger_count = 0
        self.lock = threading.Lock()
        printdebug(1, "In the init for ButtonHandler, yay!")
        GPIO.add_event_detect(pin, edge, callback=self)

    def __call__(self, *args):
        # print("trigger")

        if time.time() < self.last_trigger + self.cooldown_time_s:
            printdebug(1, "Looking for trigger blocked because still on cooldown")
            return

        if not self.lock.acquire(blocking=False):
            printdebug(1, "Looking for trigger blocked because already looking")
            return

        t = threading.Thread(None, self.look_for_triggers, args=args, daemon=True)
        t.start()

    def look_for_triggers(self, *args):

        if self.edge == GPIO.FALLING:
            trigger_value = GPIO.LOW
            printdebug(1, "count low")
        elif self.edge == GPIO.RISING:
            trigger_value = GPIO.HIGH
            printdebug(1, "count high")
        else:
            raise Exception("Either rising or falling edge, both makes no sence?")

        # Look 10 timeframes for a button-trigger
        for i in range(10):
            # Look in 20ms intervals for triggers
            rate = self.check_timeframe(trigger_value, 0.02)
            printdebug(1, f"rate={rate}")

            # If the watched timeframe contains a minimum of 90% the trigger_value, then a button-trigger is detected
            if rate > 0.9:
                self.last_trigger = time.time()
                self.trigger_count += 1
                printdebug(1, f"trigger_count=({self.trigger_count})")
                self.func(*args)
                break

        self.lock.release()

    def check_timeframe(self, trigger_value, timeout_s=0.5):
        """
        Get the percentage the pin has the 'trigger_value' in the 'timeout_s'-timeframe
        Arguments:
            trigger_value: The value that should be counted
            timeout_s: The timeframe in which the pin will be watched
        Returns:
            The percentage the pin has the value of 'trigger_value'
        """
        timeout_start = time.time()

        pinval_counter = 0
        poll_counter = 0

        while time.time() < timeout_start + timeout_s:
            pinval = GPIO.input(self.pin)
            # printdebug(1, f"Pinval={pinval} ({self.button_press_count})")
            if pinval == trigger_value:
                pinval_counter += 1

            poll_counter += 1

        timeout_stop = time.time()
        # print(f"start={timeout_start} stop={timeout_stop} poll_counter={poll_counter} pinval_counter={pinval_counter}")

        rate = pinval_counter / poll_counter
        return rate
