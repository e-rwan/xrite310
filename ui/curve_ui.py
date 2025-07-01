# ui/curve_ui.py

import os
import json
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QCheckBox, QRadioButton, QSizePolicy, QTextEdit,
    QButtonGroup, QHBoxLayout, QPushButton, QLineEdit, QFileDialog, QInputDialog, QSplitter, QTabWidget
)
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QStandardItemModel

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import numpy as np

from lib.curves import CurveManager
from lib.curves import ColorChannelSet
from lib.communications import DensitometerReader
from lib.gamma import GammaAnalyzer, GammaReading, Range
from constants import MEASURES_PATH


class CurveWidget(QWidget):
    """
    CurveWidget class manage curves tabp, inputs and graph
    Args:
        reader (DensitometerReader): DensitometerReader
        parent

    """
    def __init__(self, reader:DensitometerReader, tabs=None, parent=None):
        """
        Init
        """
        super().__init__(parent)
        

        self.inputs_color_map = ['a', 'b', 'c', 'd']
        self.color_set = {
            'vcmy': ColorChannelSet('vcmy', ['grey', 'cyan', 'magenta', 'yellow'], 'abcd'),
            'vrgb': ColorChannelSet('vrgb', ['grey', 'red', 'green', 'blue'], 'abcd'),
        }

        self.reader = reader
        self.connect_signals()
        self.tabs = tabs

        self.manager = CurveManager()
        self.manager.data_updated.connect(self.update_plot)

        self.layout_main = QSplitter(Qt.Horizontal)  # type: ignore
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.layout_main)

        self.layout_main.setSizes([600, 300]) 

        self.color_mode = 'vrgb'

        self.right_widget = QWidget()
        self._setup_plot()
        self._setup_controls()

        self.update_input_labels()
        self.update_plot()

        self.selected_index = 0
        for color_dict in (self.ref_inputs, self.meas_inputs):
            for fields in color_dict.values():
                for i, field in enumerate(fields):
                    field.installEventFilter(self)


    def _setup_plot(self):
        """
        Init graph and gamma layout
        """ 

        plot_layout = QVBoxLayout()
        plot_widget = QWidget()
        plot_widget.setLayout(plot_layout)

        # gamma widget/layout
        self.stats_layout = QHBoxLayout()
        stats_widget = QWidget()
        stats_widget.setLayout(self.stats_layout)
        plot_layout.addWidget(stats_widget)
        stats_widget.setMaximumHeight(50)

        # sensito graph widget/layout
        sensito_graph_layout = QVBoxLayout()
        sensito_graph_widget = QWidget()
        sensito_graph_widget.setLayout(sensito_graph_layout)
        sensito_graph_widget.setMinimumWidth(800)
        sensito_graph_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # delta-d graph widget/layout
        deltad_graph_layout = QVBoxLayout()
        deltad_graph_widget = QWidget()
        deltad_graph_widget.setLayout(deltad_graph_layout)
        deltad_graph_widget.setMinimumWidth(800)
        deltad_graph_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.plot_tabs = QTabWidget()
        self.plot_tabs.setTabPosition(QTabWidget.West)  # type: ignore

        self.plot_tabs.addTab(sensito_graph_widget, "Sensito")
        self.plot_tabs.addTab(deltad_graph_widget, "delta-d")

        plot_layout.addWidget(self.plot_tabs)

        ## Stats bloc
        self.stat_labels = {}
        stats = [
            "Gamma ref", "Gamma global", "Gamma",
            "Gamma r/c", "Gamma g/m", "Gamma b/y"
        ]
        for stat_key in stats:
            vbox = QVBoxLayout()
            vbox.setSpacing(2)
            vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)

            title = QLabel(stat_key)
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title.setStyleSheet("font-size: 10px; color: #666;")

            value = QLabel("--")
            value.setObjectName(stat_key.replace(" ", "_").lower())
            value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            value.setMinimumSize(80, 20)
            value.setMaximumWidth(80)
            value.setStyleSheet("""
                padding: 4px 8px;
                border: 1px solid #bbb;
                border-radius: 4px;
                background-color: #f2f2f2;
            """)
            value.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)

            vbox.addWidget(title)
            vbox.addWidget(value)

            self.stats_layout.addLayout(vbox)
            self.stat_labels[stat_key] = value

        # Step value select (QComboBox)
        step_layout = QVBoxLayout()
        step_layout.setSpacing(2)
        step_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        step_title = QLabel("Step value")
        step_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        step_title.setStyleSheet("font-size: 10px; color: #666;")

        self.step_selector = QComboBox()
        self.step_selector.addItems(["0.15", "0.20"])
        self.step_selector.setFixedSize(80, 20)
        self.step_selector.setStyleSheet("""
            padding: 2px;
            background-color: #f2f2f2;
        """)
        self.step_selector.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.step_selector.currentIndexChanged.connect(self.update_stats)

        step_layout.addWidget(step_title)
        step_layout.addWidget(self.step_selector)
        self.stats_layout.addLayout(step_layout)


        # sensito curves
        self.sensito_canvas = FigureCanvas(Figure(figsize=(6, 4)))
        self.sensito_canvas.setMinimumWidth(800)
        sensito_graph_layout.addWidget(self.sensito_canvas)
        self.ax_sensito = self.sensito_canvas.figure.add_subplot(111)
        self.sensito_canvas.figure.subplots_adjust(
            left=0.09,
            right=0.98,
            top=0.99,
            bottom=0.07
        )

        # delta-d curves
        self.deltad_canvas = FigureCanvas(Figure(figsize=(6, 4)))
        self.deltad_canvas.setMinimumWidth(800)
        deltad_graph_layout.addWidget(self.deltad_canvas)
        self.ax_deltad = self.deltad_canvas.figure.add_subplot(111)
        self.deltad_canvas.figure.subplots_adjust(
            left=0.09,
            right=0.98,
            top=0.99,
            bottom=0.07
        )

        self.layout_main.addWidget(plot_widget)
        self.layout_main.addWidget(self.right_widget)


    def _setup_controls(self):
        """
        Init graph controls
        """
        self.right_layout = QVBoxLayout(self.right_widget)

        # project title
        self.title_input = QLineEdit()
        self.title_input.setText("Sensito")
        self.title_input.setStyleSheet("font-size: 18px;")
        self.title_input.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.right_layout.addWidget(self.title_input)
        self.title_input.textChanged.connect(self.update_tab_title)
        
        # color mode selector
        mode_label = QLabel("Mode :")
        self.radio_vcmy = QRadioButton("VCMY")
        self.radio_vrgb = QRadioButton("VRGB")
        self.radio_vrgb.setChecked(True)
        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.radio_vcmy)
        self.mode_group.addButton(self.radio_vrgb)
        self.radio_vcmy.toggled.connect(self.update_input_labels)
        self.radio_vrgb.toggled.connect(self.update_input_labels)
        self.mode_selector = QHBoxLayout()
        self.mode_selector.addWidget(mode_label)
        self.mode_selector.addWidget(self.radio_vcmy)
        self.mode_selector.addWidget(self.radio_vrgb)

        # color channel checkboxes
        self.checkbox_layout = QHBoxLayout()
        self.channel_checkboxes = {}
        for key in self.inputs_color_map:
            cb = QCheckBox()
            cb.setChecked(True)
            cb.stateChanged.connect(self.update_input_visibility)
            self.channel_checkboxes[key] = cb
            self.checkbox_layout.addWidget(cb)
        self.checkbox_layout.addStretch(1)   
        
        self.color_controls = QHBoxLayout()
        self.color_controls.addLayout(self.mode_selector)
        self.color_controls.addStretch(1)
        self.color_controls.addLayout(self.checkbox_layout)
        self.right_layout.addLayout(self.color_controls)

        # ref and measurements inputs
        top_controls = QHBoxLayout()
        self.ref_inputs = {k: [QLineEdit() for _ in range(21)] for k in self.inputs_color_map}
        self.meas_inputs = {k: [QLineEdit() for _ in range(21)] for k in self.inputs_color_map}

        # saved ref selector
        ref_column = QVBoxLayout()
        ref_column.addWidget(QLabel("Référence"))
        self.import_ref_selector = QComboBox()
        self.import_ref_selector.addItem("Charger ref")
        self.populate_file_selector(self.import_ref_selector, MEASURES_PATH)
        self.import_ref_selector.currentIndexChanged.connect(
            lambda: self.import_selected_file(self.ref_inputs, self.import_ref_selector.currentData(), "ref", MEASURES_PATH)
        )
        # self.import_ref_selector.setMaximumWidth(200)
        ref_column.addWidget(self.import_ref_selector)
        self._add_input_grid(self.ref_inputs, ref_column)

        # saved measures selector
        meas_column = QVBoxLayout()
        meas_column.addWidget(QLabel("Mesures en cours"))
        file_buttons = QHBoxLayout()
        self.import_meas_selector = QComboBox()
        self.import_meas_selector.addItem("Charger")
        self.populate_file_selector(self.import_meas_selector, MEASURES_PATH)
        self.import_meas_selector.currentIndexChanged.connect(
            lambda: self.import_selected_file(self.meas_inputs, self.import_meas_selector.currentData(), "meas", MEASURES_PATH)
        )
        # self.import_meas_selector.setMaximumWidth(160)
    
        file_buttons.addWidget(self.import_meas_selector)
        export_btn = QPushButton("\U0001F4BE") # save button
        export_btn.setToolTip("Sauvegarder le fichier de mesures")
        export_btn.clicked.connect(self.export_meas_file)
        export_btn.setMaximumWidth(30)
        file_buttons.addWidget(export_btn)
        meas_column.addLayout(file_buttons)
        self._add_input_grid(self.meas_inputs, meas_column)

        # Reset button
        clear_ref_btn = QPushButton("Clear")
        clear_meas_btn = QPushButton("Clear")
        clear_ref_btn.clicked.connect(lambda: self.clear_inputs("ref"))
        clear_meas_btn.clicked.connect(lambda: self.clear_inputs("meas"))
        # clear_ref_btn.setFixedWidth(25)
        # clear_meas_btn.setFixedWidth(25)
        ref_column.addWidget(clear_ref_btn)
        meas_column.addWidget(clear_meas_btn)

        top_controls.addLayout(ref_column)
        top_controls.addLayout(meas_column)
        self.right_layout.addLayout(top_controls)

        self.right_widget.setMaximumWidth(600)
        self.right_layout.addStretch(1)


    def _add_input_grid(self, inputs_dict, parent_layout):
        """
        Create measurements inputs list
        Args:
            inputs_dict (dict): dict of measure inputs
            parent_layout (Qt Layout): column to add layout to
        """
        row = QHBoxLayout()
        for color, fields in inputs_dict.items():
            col = QVBoxLayout()
            for i, field in enumerate(fields):
                field.setFixedWidth(45)
                field.editingFinished.connect(self.update_from_fields)
                col.addWidget(field)
            row.addLayout(col)
        parent_layout.addLayout(row)


    def update_input_labels(self):
        """
        Update measurements inputs labels(v, c, m, y or v, r, g, b)
        """
        labels = self.color_set['vcmy'].name if self.radio_vcmy.isChecked() else self.color_set['vrgb'].name
        self.color_mode = 'vcmy' if self.radio_vcmy.isChecked() else 'vrgb'
        for i, key in enumerate(self.inputs_color_map):
            label = labels[i]
            self.channel_checkboxes[key].setText(label)
            for field in self.ref_inputs[key]:
                field.setPlaceholderText(label)
            for field in self.meas_inputs[key]:
                field.setPlaceholderText(label)
        self.update_input_visibility()


    def clear_inputs(self, toclear="all", reset_selectors=True):
        """
        Clear all input fields for reference and measurement,
        reset selection and focus.
        Args:
            toclear (str): which curves data to clear(all: clear all, ref: clear ref, meas: clear measures)
        """
        for i, key in enumerate(self.inputs_color_map):
            if toclear == "all" or toclear == "ref":
                for field in self.ref_inputs[key]:
                    field.setText("")
                if self.import_ref_selector.currentIndex() > 0 and reset_selectors:
                    self.import_ref_selector.setCurrentIndex(0)
            if toclear == "all" or toclear == "meas":
                for field in self.meas_inputs[key]:
                    field.setText("")
                if self.import_meas_selector.currentIndex() > 0 and reset_selectors:
                    self.import_meas_selector.setCurrentIndex(0)
        self.selected_index = 0
        self._highlight_selected_row()
        
        first_visible = self.meas_inputs['a'][0]
        if first_visible.isVisible():
            first_visible.setFocus()

        self.update_from_fields()


    def update_input_visibility(self):
        """
        Update measurements inputs visibility based on checked checkboxes
        """
        for key in self.inputs_color_map:
            visible = self.channel_checkboxes[key].isChecked()
            for f in self.ref_inputs[key] + self.meas_inputs[key]:
                f.setVisible(visible)
        self.update_plot()


    def update_from_fields(self):
        """
        Update graph from inputs
        """
        self.manager.blockSignals(True)
        for color in self.inputs_color_map:
            for i in range(21):
                ref_text = self.ref_inputs[color][i].text()
                meas_text = self.meas_inputs[color][i].text()
                try:
                    ref_val = float(ref_text)
                except ValueError:
                    ref_val = None
                try:
                    meas_val = float(meas_text)
                except ValueError:
                    meas_val = None
                self.manager.set_value("ref", color, i, ref_val)
                self.manager.set_value("meas", color, i, meas_val)
        self.manager.blockSignals(False)
        self.update_plot()


    def update_plot(self, data=None):
        """
        Update graphs
        """
        self.draw_sensito_graph()
        self.draw_deltad_graph()
        self.update_stats()


    def draw_sensito_graph(self):
        """
        Update sensito plot for each visible channel.
        """
        # sensito curves
        self.ax_sensito.clear()
        self.ax_sensito.set_xlim(1, 21)
        self.ax_sensito.set_ylim(0.0, 4.5)
        self.ax_sensito.set_xlabel("Measurement")
        self.ax_sensito.set_ylabel("Density")
        self.ax_sensito.set_xticks(list(range(1, 22)))
        # self.ax_sensito.set_title("Density curves")
        self.ax_sensito.grid(True, linestyle='--', linewidth=0.5, alpha=0.2)
        for key, values in self.manager.data.items():
            if not any(values):
                continue
            x_vals = [i + 1 for i, v in enumerate(values) if v is not None]
            y_vals = [v for v in values if v is not None]
            if x_vals and y_vals:
                prefix, abcd = key.split("_")  # e.g. 'ref_a' -> ['ref', 'a']
                if not self.channel_checkboxes.get(abcd, QCheckBox()).isChecked():
                    continue
                color_letter = self.color_set[self.color_mode].channel_from_abcd(abcd)
                color_name = self.color_set[self.color_mode].get_color_name(color_letter)
                label = f"{prefix.capitalize()} {color_letter}"
                graph_line =  '--' if prefix == "ref" else '-'
                self.ax_sensito.plot(
                    x_vals, y_vals, 
                    linestyle=graph_line, 
                    color=color_name, 
                    marker='.', 
                    label=label, 
                    alpha=0.5)

        if self.ax_sensito.get_lines():
            self.ax_sensito.legend()
        self.sensito_canvas.draw()

        
    def draw_deltad_graph(self):
        """
        Update delta-d plot (meas - ref) for each visible channel.
        """
        self.ax_deltad.clear()
        self.ax_deltad.set_xlim(1, 21)
        self.ax_deltad.set_ylim(0, 5)
        self.ax_deltad.set_xlabel("Measurement")
        self.ax_deltad.set_ylabel("Δ Density (meas - ref)")
        self.ax_deltad.set_xticks(list(range(1, 22)))
        self.ax_deltad.set_yticks(list(np.arange(0, 5, 0.25)))
        self.ax_deltad.set_title("Delta Curves")
        self.ax_deltad.grid(True, linestyle='--', linewidth=0.5, alpha=0.2)

        for abcd in self.inputs_color_map:
            meas_key = f"meas_{abcd}"
            ref_key = f"ref_{abcd}"

            meas_vals = self.manager.data.get(meas_key, [])
            ref_vals = self.manager.data.get(ref_key, [])

            if not self.channel_checkboxes.get(abcd, QCheckBox()).isChecked():
                continue
            if not any(meas_vals) or not any(ref_vals):
                continue

            delta_vals = []
            x_vals = []

            for i, (m, r) in enumerate(zip(meas_vals, ref_vals)):
                if m is not None and r is not None:
                    delta_vals.append(abs(m - r))
                    x_vals.append(i + 1)

            if x_vals and delta_vals:
                color_letter = self.color_set[self.color_mode].channel_from_abcd(abcd)
                color_name = self.color_set[self.color_mode].get_color_name(color_letter)
                label = f"Δ {color_letter.upper()}"
                self.ax_deltad.plot(
                    x_vals, delta_vals,
                    linestyle="-",
                    color=color_name,
                    marker=".",
                    label=label,
                    alpha=0.8
                )

        if self.ax_deltad.get_lines():
            self.ax_deltad.legend()
        self.deltad_canvas.draw()


    def update_stats(self):
        """
        Update the stat blocks with gamma readings.
        """
        # do not include channel v in gamma calculation
        v_abcd = self.color_set[self.color_mode].channel_to_abcd.get("v", "a")
        visible_channels = [
            key for key, cb in self.channel_checkboxes.items()
            if cb.isChecked() and key != v_abcd
        ]

        # Clear if no data
        if not visible_channels:
            for label in self.stat_labels.values():
                label.setText("--")
            return

        GA = GammaAnalyzer()
        try:
            step_value = float(self.step_selector.currentText()) if hasattr(self, "step_selector") else 0.15

            results = GA.get_gamma_from_curve_data(
                self.manager.data,
                visible_channels,
                step_value=step_value
            )
        except Exception:
            for label in self.stat_labels.values():
                label.setText("--")
            return

        # stat update
        # ref gamma
        reading_ref = results.get("ref")
        if reading_ref:
            self.stat_labels["Gamma ref"].setText(f"{reading_ref.gamma:.2f}")
            self.stat_labels["Gamma ref"].setToolTip("Valeur de densité Visuelle")
            self.stat_labels["Gamma ref"].setToolTip(str(reading_ref))
        else:
            self.stat_labels["Gamma ref"].setText("--")
            self.stat_labels["Gamma ref"].setToolTip("")
        # gamma and global gamma
        reading_all = results.get("all")
        if reading_all:
            self.stat_labels["Gamma"].setText(f"{reading_all.gamma:.2f}")
            self.stat_labels["Gamma"].setToolTip(str(reading_all))
            self.stat_labels["Gamma global"].setText(f"{reading_all.global_gamma:.2f}")
            self.stat_labels["Gamma global"].setToolTip(str(reading_all))
        else:
            self.stat_labels["Gamma"].setText("--")
            self.stat_labels["Gamma"].setToolTip("")
            self.stat_labels["Gamma global"].setText("--")
            self.stat_labels["Gamma global"].setToolTip("")

        # single channel Gamma
        for abcd_key, stat_key in zip(['b', 'c', 'd'], ["Gamma r/c", "Gamma g/m", "Gamma b/y"]):
            if abcd_key in visible_channels and abcd_key in results:
                reading = results.get(abcd_key)
                self.stat_labels[stat_key].setText(f"{results[abcd_key].gamma:.2f}")
                self.stat_labels[stat_key].setToolTip(str(reading))
            else:
                self.stat_labels[stat_key].setText("--")
                self.stat_labels[stat_key].setToolTip("")


    def populate_file_selector(self, selector: QComboBox, path: str):
        selector.blockSignals(True)
        selector.clear()
        selector.addItem("importer")

        abs_base = os.path.join(os.path.dirname(__file__), path)
        channel_order = ['v', 'r', 'g', 'b', 'c', 'm', 'y']
        entries_by_folder = {}

        for root, _, files in os.walk(abs_base):
            rel_folder = os.path.relpath(root, abs_base)
            entries = []

            for fname in sorted(files):
                if not fname.endswith(".json"):
                    continue

                full_path = os.path.join(root, fname)

                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    # Récupération des champs depuis le JSON
                    name = data.get("name", os.path.splitext(fname)[0])
                    values = data.get("values", {})
                    date_str = data.get("date", "?")
                    try:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        date_obj = datetime.min

                    # Correction ici : on prend uniquement les canaux *effectivement présents*
                    used_channels = list(values.keys())  # ex: ['b']
                    channel_order = ['v', 'r', 'g', 'b', 'c', 'm', 'y']
                    channel_str = ",".join(k.upper() for k in channel_order if k in used_channels)

                    # Construction du label final
                    label = f"{name} - {channel_str} - {date_str}"

                    rel_path = os.path.relpath(full_path, abs_base)
                    entries.append((date_obj, label, rel_path))

                except Exception as e:
                    print(f"Reading error {fname} : {e}")
                    continue

            if entries:
                # sort by date
                entries.sort(key=lambda t: t[0], reverse=True)
                entries_by_folder[rel_folder] = entries

        # sort by folder
        for folder in sorted(entries_by_folder, key=lambda f: (f != ".", f.lower())):
            if folder != ".":
                selector.addItem(f"⎯⎯⎯ {folder.upper()}")
                idx = selector.count() - 1
                model = selector.model()
                if isinstance(model, QStandardItemModel):
                    model.item(idx).setEnabled(False)

            for _, label, rel_path in entries_by_folder[folder]:
                selector.addItem(label, userData=rel_path)

        selector.blockSignals(False)


    def import_selected_file(self, inputs, file, toclear, path=""):
        self.clear_inputs(toclear, False)

        file = file
        if not isinstance(file, str) or not file.endswith(".json"):
            self.update_from_fields()
            return

        try:
            if os.path.isabs(file):
                filepath = file
            else:
                filepath = os.path.join(os.path.dirname(__file__), path, file)
            name, mode, values = self.manager.import_from_file(filepath)

            # update project title with json "name"
            self.title_input.setText(name)

            # update color mode
            self.color_mode = mode
            self.radio_vcmy.setChecked(mode == 'vcmy')
            self.radio_vrgb.setChecked(mode == 'vrgb')

            mapping = self.color_set[mode].channel_to_abcd

            for color_key, vals in values.items():
                if color_key not in mapping:
                    continue
                abcd_key = mapping[color_key]
                for i, val in enumerate(vals):
                    if i < 21:
                        inputs[abcd_key][i].setText(str(val))

        except Exception as e:
            print("JSON loading error:", e)

        self.update_from_fields()


    def export_meas_file(self):
        # measure name
        name = self.title_input.text()

        # color mode
        if self.radio_vcmy.isChecked():
            self.color_mode = 'vcmy'
            self.manager.color_mode = 'vcmy'
        else:
            self.color_mode = 'vrgb'
            self.manager.color_mode = 'vrgb'

        # used color channels
        used_channels = []
        for channel in ['v', 'r', 'g', 'b', 'c', 'm', 'y']:
            abcd = self.color_set[self.color_mode].channel_to_abcd.get(channel)
            if abcd and any(field.text().strip() for field in self.meas_inputs[abcd]):
                used_channels.append(channel.upper())

        # Date
        date_str = datetime.now().strftime("%Y-%m-%d_%H%M")

        filename = f"{name}_{''.join(used_channels)}_{date_str}.json"

        default_path = os.path.join(MEASURES_PATH, filename)
        fname, _ = QFileDialog.getSaveFileName(self, "Sauvegarder", default_path, "Fichiers JSON (*.json)")

        if not fname:
            return
        if not fname.lower().endswith(".json"):
            fname += ".json"
        try:
            self.manager.export_to_file(fname)
        except Exception as e:
            print("Erreur sauvegarde JSON:", e)


    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusIn:
            for group in (self.ref_inputs, self.meas_inputs):
                for key in group:
                    if obj in group[key]:
                        self.selected_index = group[key].index(obj)
                        self._highlight_selected_row()
                        break
        return super().eventFilter(obj, event)


    def receive_measurements(self, values: dict[str, float]):
        mode = 'vcmy' if self.radio_vcmy.isChecked() else 'vrgb'
        channel_map = self.color_set[mode].channel_to_abcd

        for k, val in values.items():
            if k not in channel_map:
                continue
            abcd = channel_map[k]
            if abcd in self.meas_inputs and 0 <= self.selected_index < 21:
                self.meas_inputs[abcd][self.selected_index].setText(f"{val:.2f}")

        if self.selected_index < 20:
            self.selected_index += 1
        self._highlight_selected_row()

        self.update_from_fields()


    def _highlight_selected_row(self):
        for group in (self.meas_inputs,):
            for key in group:
                for i, field in enumerate(group[key]):
                    if i == self.selected_index:
                        field.setStyleSheet("background-color: #ffffaa")
                    else:
                        field.setStyleSheet("")


    def connect_signals(self):
        """
        Signal connection with communications.py
        """
        self.reader.parsed_measurement.connect(self.receive_measurements)


    def update_tab_title(self):
        title = self.title_input.text().strip()
        if self.tabs:
            index = self.tabs.indexOf(self)
            self.tabs.setTabText(index, title if title else "Courbes")
            