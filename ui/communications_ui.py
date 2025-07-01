# ui/com.py

from PySide6.QtWidgets import (
	QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton, QTextEdit,
	QHBoxLayout, QSplitter, QSizePolicy
)
from PySide6.QtCore import Qt
from serial.tools import list_ports
from lib.communications import DensitometerReader


class CommunicationWidget(QWidget):
	def __init__(self, reader:DensitometerReader, parent=None):
		"""
		Init
		"""
		super().__init__(parent)

		self.reader = reader
		self.init_ui()
		self.connect_signals()

	def init_ui(self):
		"""
		UI Init
		"""
		layout = QVBoxLayout(self)
		
		self.measure_buffer = {}

		comunication_selector = QHBoxLayout()
		layout.addLayout(comunication_selector)
		
		# Port selector
		self.port_selector = QComboBox()
		ports = [p.device for p in list_ports.comports()]
		self.port_selector.addItems(ports)
		comunication_selector.addWidget(QLabel("Port série :"))
		comunication_selector.addWidget(self.port_selector)
		comunication_selector.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.port_selector.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

		# Baud rate selector
		self.baud_selector = QComboBox()
		baudrates = ["1200", "300"]
		self.baud_selector.addItems(baudrates)
		comunication_selector.addWidget(QLabel("Baud rate :"))
		comunication_selector.addWidget(self.baud_selector)
		self.baud_selector.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)		
		

		# Connexion button
		self.connect_btn = QPushButton("Connecter")
		self.connect_btn.clicked.connect(self.toggle_connection)
		layout.addWidget(self.connect_btn)

		# Command input
		layout.addWidget(QLabel("Commande :"))
		self.command_input = QTextEdit()
		self.command_input.setFixedHeight(40)
		layout.addWidget(self.command_input)

		# Send command butoon
		send_layout = QHBoxLayout()
		self.send_btn = QPushButton("Envoyer")
		self.send_btn.clicked.connect(self.send_command)
		send_layout.addWidget(self.send_btn)

		# clear text zone button
		self.clear_btn = QPushButton("Effacer l'historique")
		self.clear_btn.clicked.connect(self.clear_output)
		send_layout.addWidget(self.clear_btn)
		layout.addLayout(send_layout)

		# text zone
		splitter = QSplitter(Qt.Vertical)  # type: ignore
		# input console
		self.output_sent = QTextEdit()
		self.output_sent.setReadOnly(True)
		self.output_sent.setPlaceholderText("Commandes envoyées")
		splitter.addWidget(self.output_sent)

		# output console
		self.output_received = QTextEdit()
		self.output_received.setReadOnly(True)
		self.output_received.setPlaceholderText("Données reçues")
		splitter.addWidget(self.output_received)

		splitter.setSizes([100, 300])
		layout.addWidget(splitter)



	def connect_signals(self):
		"""
		Signal connection with communications.py
		"""
		self.reader.message_received.connect(self.log_received)
		self.reader.error_occurred.connect(lambda msg: self.log_received(f"[Erreur] {msg}"))
		self.reader.connected.connect(self.on_connected)
		self.reader.disconnected.connect(self.on_disconnected)


	def toggle_connection(self):
		"""
		Port connexion
		"""
		port = self.port_selector.currentText()
		baudrate = int(self.baud_selector.currentText())
		success = self.reader.toggle_connection(port, baudrate)
		self.log_sent(f"{'Connexion' if success else 'Déconnexion'} au port {port}")


	def send_command(self):
		"""
		Send command to densitometer
		"""
		cmd = self.command_input.toPlainText().strip()
		if cmd:
			self.reader.send_command(cmd)
			self.log_sent(cmd)


	def clear_output(self):
		"""
		Clear console(input and ouput text zone)
		"""
		self.output_sent.clear()
		self.output_received.clear()


	def log_sent(self, text):
		"""
		print log to input text zone

		Args:
			text (str): text to print
		"""
		self.output_sent.append(f"COMMAND : {repr(text)}")
		print(f"input: {repr(text)}")


	def log_received(self, text):
		"""
		print log to output text zone

		Args:
			text (str): text to print
		"""
		self.output_received.append(f"DEVICE : {repr(text)}")
		print(f"output: {repr(text)}")


	def on_connected(self, port):
		"""
		change connexion button text
		"""
		self.connect_btn.setText("Déconnecter")


	def on_disconnected(self, port):
		"""
		change connexion button text
		"""
		self.connect_btn.setText("Connecter")


	def closeEvent(self, event):
		"""
		close serial port
		"""
		self.reader.close()
		event.accept()
