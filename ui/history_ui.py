import os
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLineEdit,
    QComboBox, QLabel, QSplitter, QTabWidget
)
from PySide6.QtCore import Qt, QDate
from constants import MEASURES_PATH
from model.measurement_set import load_measurement_file
from lib.history_analyzer import HistoryAnalyzer
from lib.gamma import GammaAnalyzer
from ui.history_gamma_plot import HistoryGammaPlot
from utils.plot_utils import draw_curve_graph


class HistoryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Splitter horizontal : gauche (courbes), droite (fichiers)
        splitter = QSplitter(Qt.Horizontal)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(splitter)

        # --- Courbes/stats ---
        self.tabs = QTabWidget()
        self.gamma_plot = HistoryGammaPlot()
        self.tabs.addTab(self.gamma_plot, "Gammas")
        splitter.addWidget(self.tabs)

        # --- Sélection des fichiers ---
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)

        self.ref_selector = QComboBox()
        self.ref_selector.setPlaceholderText("Référence")
        right_layout.addWidget(QLabel("Courbe de référence"))
        right_layout.addWidget(self.ref_selector)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher un fichier...")
        self.search_input.textChanged.connect(self.filter_files)

        self.date_filter = QComboBox()
        self.date_filter.addItems(["Toutes dates", "Aujourd’hui", "Ce mois-ci", "Cette année"])
        self.date_filter.currentIndexChanged.connect(self.filter_files)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Nom"])
        self.tree.setColumnCount(1)
        self.tree.setRootIsDecorated(True)

        right_layout.addWidget(QLabel("Filtres"))
        right_layout.addWidget(self.search_input)
        right_layout.addWidget(self.date_filter)
        right_layout.addWidget(QLabel("Mesures disponibles"))
        right_layout.addWidget(self.tree)

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        self.load_files()
        self.load_reference_files()

        self.ref_selector.currentIndexChanged.connect(self.refresh_plot)
        self.tree.itemChanged.connect(self.refresh_plot)

    def load_files(self):
        self.tree.clear()
        for root, dirs, files in os.walk(MEASURES_PATH):
            folder_item = QTreeWidgetItem([os.path.basename(root)])
            added = False
            for fname in sorted(files):
                if fname.endswith(".json"):
                    fpath = os.path.join(root, fname)
                    measurement = load_measurement_file(Path(fpath))
                    if not measurement:
                        continue
                    name = measurement.name or Path(fpath).stem
                    channels = ", ".join(measurement.curves.keys())
                    date_str = measurement.json_date or measurement.date.strftime("%Y-%m-%d")
                    label = f"{name} [{channels}] - {date_str}"
                    item = QTreeWidgetItem([label])
                    item.setData(0, Qt.UserRole, str(fpath))
                    item.setCheckState(0, Qt.Unchecked)
                    folder_item.addChild(item)
                    added = True
            if added:
                self.tree.addTopLevelItem(folder_item)
                folder_item.setExpanded(True)

    def filter_files(self):
        text = self.search_input.text().lower()
        period = self.date_filter.currentText()
        now = QDate.currentDate()

        for i in range(self.tree.topLevelItemCount()):
            folder_item = self.tree.topLevelItem(i)
            visible = False
            for j in range(folder_item.childCount()):
                child = folder_item.child(j)
                label = child.text(0).lower()
                m = load_measurement_file(Path(child.data(0, Qt.UserRole)))
                if not m:
                    continue
                json_date = m.json_date or m.date.strftime("%Y-%m-%d")
                fdate = QDate.fromString(json_date, "yyyy-MM-dd")

                match_text = text in label
                match_date = True
                if period == "Aujourd’hui":
                    match_date = (fdate == now)
                elif period == "Ce mois-ci":
                    match_date = (fdate.month() == now.month() and fdate.year() == now.year())
                elif period == "Cette année":
                    match_date = (fdate.year() == now.year())

                is_match = match_text and match_date
                child.setHidden(not is_match)
                visible = visible or is_match
            folder_item.setHidden(not visible)

    def get_selected_files(self):
        selected = []
        for i in range(self.tree.topLevelItemCount()):
            folder_item = self.tree.topLevelItem(i)
            for j in range(folder_item.childCount()):
                child = folder_item.child(j)
                if child.checkState(0) == Qt.Checked:
                    selected.append(child.data(0, Qt.UserRole))
        return selected

    def load_reference_files(self):
        self.ref_selector.clear()
        ref_path = os.path.join(MEASURES_PATH, "ref")
        if not os.path.exists(ref_path):
            return

        for fname in sorted(os.listdir(ref_path)):
            if fname.endswith(".json"):
                fpath = os.path.join(ref_path, fname)
                self.ref_selector.addItem(fname, fpath)

    def get_reference_file(self):
        return self.ref_selector.currentData()

    def refresh_plot(self):
        ref_path = self.get_reference_file()
        if not ref_path:
            print("no ref path found")
            return

        ref = load_measurement_file(Path(ref_path))
        if not ref:
            print("no file found: ", ref_path)
            return

        selected_paths = self.get_selected_files()
        measures = [load_measurement_file(Path(p)) for p in selected_paths]
        measures = [m for m in measures if m is not None]
        if not measures:
            print(f"no measures found in: {selected_paths}")
            return

        analyzer = HistoryAnalyzer(ref, measures)
        gamma_data = analyzer.get_gamma_evolution()

        gamma_ref = {}
        gamma_tool = GammaAnalyzer()
        for ch, curve in ref.curves.items():
            try:
                reading = gamma_tool.get_gamma_from_values(curve.values)
                gamma_ref[ch] = reading.gamma
            except Exception as e:
                print(f"error computing gamma for ref {ch}: {e}")

        dates = [m.date for m in measures]
        str_dates = [d.strftime("%Y-%m-%d") for d in dates]

        # Préparation des courbes pour draw_curve_graph
        curves = {}
        for ch, values in gamma_data.items():
            curves[ch] = {
                "x": str_dates,
                "y": values,
                "color": {"R": "red", "G": "green", "B": "blue"}.get(ch, None),
                "linestyle": "-"
            }
        for ch, val in gamma_ref.items():
            curves[f"Réf {ch}"] = {
                "x": str_dates,
                "y": [val] * len(str_dates),
                "color": {"R": "red", "G": "green", "B": "blue"}.get(ch, None),
                "linestyle": "--"
            }

        draw_curve_graph(
            ax=self.gamma_plot.ax,
            canvas=self.gamma_plot.canvas,
            curves=curves,
            title="Évolution des gammas",
            xlabel="Date",
            ylabel="Gamma",
            nb_x_ticks=len(str_dates)
        )

        print("Measures:", len(measures))
        print("Channels:", list(ref.curves.keys()))
        print("Dates:", dates)
