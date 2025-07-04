import matplotlib.pyplot as plt
from PySide6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from datetime import datetime
from typing import List, Dict

class HistoryGammaPlot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.canvas = FigureCanvas(plt.Figure())
        layout.addWidget(self.canvas)
        self.ax = self.canvas.figure.add_subplot(111)

    def plot(self,
             dates: List[datetime],
             gamma_values: Dict[str, List[float]],
             ref_values: Dict[str, float] = None):
        self.ax.clear()

        # Choisir x-axis
        if len(dates) <= 30:
            x = list(range(len(dates)))
            self.ax.set_xticks(x)
            self.ax.set_xticklabels([d.strftime('%Y-%m-%d') for d in dates], rotation=45, ha='right')
        else:
            x = dates
            self.ax.xaxis_date()
            self.canvas.figure.autofmt_xdate()

        # Courbes gamma par canal
        colors = {"R": "red", "G": "green", "B": "blue"}
        for channel in ["R", "G", "B"]:
            if channel in gamma_values:
                self.ax.plot(x, gamma_values[channel], label=f"Gamma {channel}", color=colors[channel])

        # Référence horizontale
        if ref_values:
            for channel in ["R", "G", "B"]:
                if channel in ref_values:
                    self.ax.axhline(ref_values[channel], linestyle="--", color=colors[channel], label=f"Réf {channel}")

        self.ax.set_ylabel("Gamma")
        self.ax.set_title("Évolution des gammas")
        self.ax.legend()
        self.canvas.draw()
