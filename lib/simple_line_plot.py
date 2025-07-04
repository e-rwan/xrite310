from PySide6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from typing import Dict, List, Tuple
from datetime import datetime

from constants import COLOR_SET


class SimpleLinePlot(QWidget):
    def __init__(self, title: str = "", ylabel: str = "", parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.canvas)
        self.title = title
        self.ylabel = ylabel

    def update_plot(self, data: Dict[str, List[Tuple[datetime, float]]], reference: Dict[str, float] = None):
        self.ax.clear()
        self.ax.set_title(self.title)
        self.ax.set_ylabel(self.ylabel)
        self.ax.set_xlabel("Date")

        for channel, points in data.items():
            dates, values = zip(*points)
            self.ax.plot(dates, values, label=channel)

        if reference:
            for channel, y in reference.items():
                self.ax.axhline(y=y, linestyle="--", color="gray", label=f"ref {channel}")

        self.ax.legend()
        self.ax.grid(True)
        self.canvas.draw()
