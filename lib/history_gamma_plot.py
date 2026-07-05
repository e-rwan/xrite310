# lib/history_gamma_plot.py

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from PySide6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from datetime import datetime
import numpy as np
from typing import List, Dict, Optional

class HistoryGammaPlot(QWidget):
	"""Qt widget used to display the history of gamma values.

	This class embeds a Matplotlib figure inside a QWidget in order to
	visualize the evolution of the R, G, and B gamma channels over time.
	Optional reference values can also be displayed as horizontal lines.
	"""

	def __init__(self, parent=None):
		"""Initialize the plotting widget.

		Creates the main layout, the Matplotlib canvas, and the axis used
		to display the curves.
		"""
		super().__init__(parent)

		# Create a vertical layout to hold the plotting area.
		layout = QVBoxLayout(self)

		# Create the Matplotlib figure embedded in the Qt widget.
		self.canvas = FigureCanvas(Figure())
		layout.addWidget(self.canvas)

		# Create the main axis on which the curves will be drawn.
		self.ax = self.canvas.figure.add_subplot(111)

	def plot(self,
			dates: List[datetime],
			gamma_values: Dict[str, List[float]],
			ref_values: Optional[Dict[str, float]] = None
			):
		"""Plot gamma evolution for the R, G, and B channels.

		Args:
			dates: List of measurement dates.
			gamma_values: Dictionary containing gamma series for each
				channel, for example {"R": [...], "G": [...], "B": [...]}.
			ref_values: Optional dictionary of reference values by channel,
				displayed as horizontal lines.
		"""
		# Clear the previous plot before drawing new data.
		self.ax.clear()

		# Choose the X-axis display mode.
		# For a small number of points, show readable text labels.
		# Otherwise, use a Matplotlib date axis directly.
		if len(dates) <= 30:
			x = list(range(len(dates)))
			self.ax.set_xticks(x)
			self.ax.set_xticklabels([d.strftime('%Y-%m-%d') for d in dates], rotation=45, ha='right')
		else:
			x = dates
			self.ax.xaxis_date()
			self.canvas.figure.autofmt_xdate()

		# Convert datetime values to the numeric format expected by
		# Matplotlib when working with date-based data.
		if x and isinstance(x[0], datetime):
			x_values = np.asarray(mdates.date2num(x), dtype=float)
			self.ax.xaxis_date()
		else:
			x_values = np.asarray(x, dtype=float)

		# Define the display color for each gamma channel.
		colors = {"R": "red", "G": "green", "B": "blue"}

		# Plot the gamma curves for all available channels.
		for channel in ["R", "G", "B"]:
			if channel in gamma_values:
				self.ax.plot(x_values, gamma_values[channel], label=f"Gamma {channel}", color=colors[channel])

		# Add a horizontal reference line for each provided channel.
		if ref_values:
			for channel in ["R", "G", "B"]:
				if channel in ref_values:
					self.ax.axhline(ref_values[channel], linestyle="--", color=colors[channel], label=f"Ref {channel}")

		# Configure the graph labels and legend.
		self.ax.set_ylabel("Gamma")
		self.ax.set_title("Gamma evolution")
		self.ax.legend()

		# Refresh the canvas to display the updated plot.
		self.canvas.draw()

