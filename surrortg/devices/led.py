import asyncio
import logging

import pigpio


class LED:
    """Simple to use LED class implemented with pigpio

    :param pin: GPIO pin number
    :type pin: int
    :param initial_state_off: Determines whether the LED should be
        turned off when initialized. If set to False, the LED is
        turned on at init. Defaults to True.
    :type initial_state_off: bool, optional
    :raises RuntimeError: If cannot connect to pigpio daemon
    :raises RuntimeError: If methods are called after calling stop
    """

    def __init__(self, pin, initial_state_off=True):
        self._pin = pin
        self._stopped = False
        self._state_before_blinking = None
        self._blink_task = None

        self._pi = pigpio.pi()
        if not self._pi.connected:
            raise RuntimeError("Could not connect to pigpio daemon")
        self._pi.set_mode(self._pin, pigpio.OUTPUT)

        if initial_state_off:
            self.off()
        else:
            self.on()

    def on(self):
        """Turns the LED on"""
        self._check_if_stopped()
        # Stop possible blinking
        self.stop_blinking()

        self._pi.write(self._pin, pigpio.HIGH)

    def off(self):
        """Turns the LED off"""
        self._check_if_stopped()
        # Stop possible blinking
        self.stop_blinking()

        self._pi.write(self._pin, pigpio.LOW)

    def toggle(self):
        """Toggles the LED's state

        Turns the LED on if the state was previously off, and vice versa.
        """
        self._check_if_stopped()

        if self.is_on():
            self.off()
        else:
            self.on()

    async def blink_once(self, blink_time):
        """Blinks the LED once, waiting blink_time seconds in between

        :param blink_time: Time in seconds to wait between turning the LED
            on and off
        :type blink_time: float or int
        """
        assert isinstance(blink_time, float) or isinstance(
            blink_time, int
        ), "blink_time should be float or int"
        self._check_if_stopped()

        if self.is_on():
            logging.warning(
                "LED is already on when blinking once! Will turn LED off "
                f"in {blink_time} seconds."
            )

        self.on()
        await asyncio.sleep(blink_time)
        self.off()

    def start_blinking(self, blinking_rate, on_off_ratio=1):
        """Starts blinking the LED in the background

        :param blinking_rate: Rate of the blinking, i.e. how many times
            the LED blinks in a second.
        :type blinking_rate: float or int
        :param on_off_ratio: Ratio between on and off time, defaults to 1.
        :type on_off_ratio: float or int, optional
        """
        assert isinstance(blinking_rate, float) or isinstance(
            blinking_rate, int
        ), "blinking_rate should be float or int"
        assert isinstance(on_off_ratio, float) or isinstance(
            on_off_ratio, int
        ), "on_off_ratio should be float or int"
        assert blinking_rate > 0, "blinking_rate must be positive"
        assert on_off_ratio > 0, "on_off_ratio must be positive"
        self._check_if_stopped()

        # Stop possible blinking
        self.stop_blinking()

        # Save current led state
        self._state_before_blinking = self._pi.read(self._pin)

        off_time = 1.0 / blinking_rate / (1 + on_off_ratio)
        on_time = on_off_ratio * off_time

        # Start background task
        self._blink_task = asyncio.create_task(
            self._keep_blinking(on_time, off_time)
        )

    def stop_blinking(self):
        """Stops any active blinking of the LED"""
        self._check_if_stopped()

        if self.is_blinking():
            self._blink_task.cancel()
            self._blink_task = None

            # Restore led state to what it was before blinking started
            self._pi.write(self._pin, self._state_before_blinking)

    def is_on(self):
        """Checks if the LED is turned on

        :return: True if the LED is turned on
        :rtype: bool
        """
        self._check_if_stopped()

        return bool(self._pi.read(self._pin))

    def is_off(self):
        """Checks if the LED is turned off

        :return: True if the LED is turned off
        :rtype: bool
        """
        self._check_if_stopped()

        return not self.is_on()

    def is_blinking(self):
        """Checks if the LED is blinking

        :return: True if the LED is blinking
        :rtype: bool
        """
        self._check_if_stopped()

        return self._blink_task is not None

    def stop(self):
        """Sets the pin to input state and stops pigpio daemon connection"""
        self._check_if_stopped()

        self._pi.set_pull_up_down(self._pin, pigpio.PUD_OFF)
        self._pi.set_mode(self._pin, pigpio.INPUT)
        self._pi.stop()
        self._stopped = True

    def _check_if_stopped(self):
        if self._stopped:
            raise RuntimeError("LED already stopped")

    async def _keep_blinking(self, on_time, off_time):
        while True:
            self._pi.write(self._pin, pigpio.HIGH)
            await asyncio.sleep(on_time)
            self._pi.write(self._pin, pigpio.LOW)
            await asyncio.sleep(off_time)


if __name__ == "__main__":

    async def main():
        led = LED(16)
        await asyncio.sleep(0.5)

        print("Turning the LED on")
        led.on()
        await asyncio.sleep(1)
        print("Turning the LED off")
        led.off()
        await asyncio.sleep(2)

        print("Blinking the LED once for 1 second")
        await led.blink_once(1)
        await asyncio.sleep(2)
        print("Toggle LED state")
        led.toggle()
        print(f"LED is now on: {led.is_on()}")
        await asyncio.sleep(1)
        print("Toggle LED state again")
        led.toggle()
        print(f"LED is now off: {led.is_off()}")
        await asyncio.sleep(2)

        print("Start blinking the LED once per second")
        led.start_blinking(1)
        print("Waiting 4 seconds")
        await asyncio.sleep(2)
        print(f"LED is blinking: {led.is_blinking()}")
        await asyncio.sleep(2)
        print("Turning the LED on")
        led.on()
        await asyncio.sleep(1)

        print("Start blinking the LED twice per second, on/off ratio 0.5")
        print("Waiting 4 seconds")
        led.start_blinking(2, 0.5)
        await asyncio.sleep(4)
        print("Stop blinking")
        led.stop_blinking()
        print("Waiting for a while, led should be turned on")
        await asyncio.sleep(2)

        led.stop()

    asyncio.run(main())
