# === custom module for serial ports communication ===
import serial
from serial.tools import list_ports


class SerialDevices(object):
    """Retrieves and stores list of serial devices in self.ports"""
    def __init__(self):
        try:
            self.ports, _, _ = zip(*list_ports.comports())
        except ValueError:
            self.ports = []
            print("No serial ports found")

    def refresh(self):
        """Refreshes list of ports."""
        self.ports, _, _ = zip(*list_ports.comports())

class delayedSerial(serial.Serial):
    """Extends Serial.write so that characters are output individually
    with a slight delay
    """
    def write(self, data):
        for i in data:
            serial.Serial.write(self, i)
            # the unit is sec, so this statement delay 1 ms after writing every char
            time.sleep(.001)
