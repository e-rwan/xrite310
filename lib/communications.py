# lib/communication.py
from PySide6.QtCore import QObject, Signal
import serial
import threading

from constants import BAUDRATE

class DensitometerReader(QObject):
    message_received = Signal(str)
    parsed_measurement = Signal(dict)
    error_occurred = Signal(str)
    connected = Signal(str)
    disconnected = Signal(str)


    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.r_thread = None
        self.keep_reading = False


    def toggle_connection(self, port: str, baudrate: int) -> bool:
        if self.serial_port:
            self.keep_reading = False
            if self.r_thread and self.r_thread.is_alive():
                self.r_thread.join(timeout=1)
            try:
                self.serial_port.close()
                self.serial_port = None
                self.disconnected.emit(port)
                return False
            except Exception as e:
                self.error_occurred.emit(f"Erreur fermeture port : {e}")
                return False
        else:
            try:
                self.serial_port = serial.Serial(
                    port=port,
                    baudrate=baudrate,
                    bytesize=serial.SEVENBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=1
                )
                self.keep_reading = True
                self.r_thread = threading.Thread(target=self.read_serial, daemon=True)
                self.r_thread.start()
                self.connected.emit(port)
                return True
            except serial.SerialException as e:
                self.error_occurred.emit(f"Erreur ouverture port : {e}")
                return False


    def read_serial(self):
        while self.keep_reading:
            try:
                if self.serial_port:
                    line = self.serial_port.readline()
                    if line:
                        text = line.decode("ascii", errors="ignore").strip()
                        self.message_received.emit(text)
                        parsed = self.parse_measurement_line(text)
                        if parsed:
                            self.parsed_measurement.emit(parsed)
            except Exception as e:
                self.error_occurred.emit(f"Read error : {e}")


    def parse_measurement_line(self, line: str):
            """
            Parse a line such as:
            - "v001" (single value)
            - "v001 r123 g045 b087" (multiple values)

            Args:
                line (str): text to parse
            """
            parts = line.strip().lower().split()
            values = {}

            for part in parts:
                if len(part) == 4 and part[0] in "vrcgby" and part[1:].isdigit():
                    values[part[0]] = int(part[1:]) / 100

            return values if values else None


    def send_command(self, command: str):
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write(command.encode('ascii'))
            except Exception as e:
                self.error_occurred.emit(f"Erreur envoi : {e}")


    def close(self):
        if self.serial_port:
            self.keep_reading = False
            if self.r_thread and self.r_thread.is_alive():
                self.r_thread.join(timeout=1)
            try:
                self.serial_port.close()
            except:
                pass
