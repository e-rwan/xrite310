# ui/densito_ui.py

# pyright: reportAttributeAccessIssue=false

import os
import json
from math import sqrt

from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
	QWidget, QVBoxLayout, QLabel, QComboBox, QCheckBox, QRadioButton, QSizePolicy, QFrame,
	QButtonGroup, QHBoxLayout, QGridLayout, QPushButton, QLineEdit, QFileDialog, QSplitter, QTabWidget
)

from PySide6.QtCore import Qt, QEvent, QPointF, QRectF

from PySide6.QtGui import QStandardItemModel, QPainter, QColor, QPen, QPolygonF

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar

from lib.densito import CurveManager
from utils.plot_utils import draw_curve_graph
from model.measurement_set import MeasurementSet, ChannelCurve
from lib.communications import DensitometerReader
from lib.gamma import GammaAnalyzer
from constants import MEASURES_PATH, COLOR_SET, STATS_LABELS

class AdditiveCurveWidget(QWidget):
	"""Custom additive curve view used to blend channel fills in plus mode."""

	def __init__(self, parent=None):
		super().__init__(parent)
		self.curves = {}
		self.title = "Histogramme additif"
		self.xlabel = "Measurement"
		self.ylabel = "Density"
		self.x_tick_labels = []
		self.setMinimumHeight(320)


	def set_plot_data(self, curves=None, title="", xlabel="Measurement", ylabel="Density", x_tick_labels=None):
		self.curves = curves or {}
		self.title = title or "Histogramme additif"
		self.xlabel = xlabel
		self.ylabel = ylabel
		self.x_tick_labels = list(x_tick_labels or [])
		self.update()


	def _build_valid_curves(self):
		valid_curves = []
		global_xmin, global_xmax = float("inf"), float("-inf")
		global_ymax = 0.0

		for label, data in self.curves.items():
			raw_y_vals = data.get("y", [])
			raw_x_vals = data.get("x", [i + 1 for i in range(len(raw_y_vals))])
			valid_points = [
				(float(x), float(y))
				for x, y in zip(raw_x_vals, raw_y_vals)
				if isinstance(x, (int, float)) and isinstance(y, (int, float))
			]
			if not valid_points:
				continue

			x_vals = [point[0] for point in valid_points]
			y_vals = [point[1] for point in valid_points]
			valid_curves.append((label, data, x_vals, y_vals))

			global_xmin = min(global_xmin, min(x_vals))
			global_xmax = max(global_xmax, max(x_vals))
			global_ymax = max(global_ymax, max(y_vals))

		tick_max = len(self.x_tick_labels) if self.x_tick_labels else 21
		x_min = 1.0 if global_xmin == float("inf") else min(1.0, global_xmin)
		x_max = float(tick_max) if global_xmax == float("-inf") else max(float(tick_max), global_xmax)

		if global_ymax <= 0.05:
			step = 0.01
		elif global_ymax <= 0.2:
			step = 0.02
		elif global_ymax <= 0.5:
			step = 0.05
		elif global_ymax <= 1:
			step = 0.1
		elif global_ymax <= 2:
			step = 0.2
		else:
			step = round(global_ymax / 10, 1)

		y_max = max(step * ((global_ymax // step) + 1), step * 2)
		return valid_curves, x_min, x_max, y_max, step


	def _resolve_display_color(self, raw_color):
		"""Return fully saturated colors for additive rendering and legend display."""
		color_key = str(raw_color or "").strip().lower()
		palette = {
			"red": "#ff0000",
			"green": "#00ff00",
			"blue": "#0000ff",
			"cyan": "#00ffff",
			"magenta": "#ff00ff",
			"yellow": "#ffff00",
			"grey": "#b0b0b0",
			"gray": "#b0b0b0",
		}
		color = QColor(palette.get(color_key, str(raw_color or "#ffffff")))
		if not color.isValid():
			color = QColor("#ffffff")
		return color


	def _draw_legend(self, painter: QPainter, plot_rect: QRectF, valid_curves):

		if not valid_curves:
			return

		legend_items = []
		max_text_width = 0
		for label, data, _, _ in valid_curves:
			metrics = painter.fontMetrics()
			max_text_width = max(max_text_width, metrics.horizontalAdvance(label))
			legend_items.append((label, data))

		item_height = 18
		legend_width = min(max_text_width + 42, int(plot_rect.width() * 0.45))
		legend_height = len(legend_items) * item_height + 12
		legend_rect = QRectF(
			plot_rect.right() - legend_width - 12,
			plot_rect.top() + 12,
			legend_width,
			legend_height,
		)

		painter.save()
		painter.setPen(QPen(QColor(255, 255, 255, 50), 1))
		painter.setBrush(QColor(0, 0, 0, 150))
		painter.drawRoundedRect(legend_rect, 6, 6)

		for index, (label, data) in enumerate(legend_items):
			color = self._resolve_display_color(data.get("color", "#ffffff"))


			y = legend_rect.top() + 8 + index * item_height + 8
			line_x1 = legend_rect.left() + 8
			line_x2 = line_x1 + 18

			pen = QPen(color, 2)
			if data.get("linestyle") == "--":
				pen.setStyle(Qt.PenStyle.DashLine)
			painter.setPen(pen)
			painter.drawLine(QPointF(line_x1, y), QPointF(line_x2, y))

			if data.get("fill", False):
				painter.fillRect(QRectF(line_x1, y - 5, 10, 10), color)

			painter.setPen(QColor("#f0f0f0"))
			text_rect = QRectF(line_x2 + 6, y - 8, legend_width - 34, 16)
			painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, label)

		painter.restore()


	def paintEvent(self, event):
		super().paintEvent(event)

		painter = QPainter(self)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)
		painter.fillRect(self.rect(), QColor("#1d1f23"))

		left_margin = 64
		right_margin = 24
		top_margin = 38
		bottom_margin = 68
		plot_rect = QRectF(
			left_margin,
			top_margin,
			max(10, self.width() - left_margin - right_margin),
			max(10, self.height() - top_margin - bottom_margin),
		)

		painter.setPen(QColor("#f0f0f0"))
		painter.drawText(QRectF(0, 8, self.width(), 20), Qt.AlignmentFlag.AlignHCenter, self.title)
		painter.drawText(QRectF(0, self.height() - 28, self.width(), 20), Qt.AlignmentFlag.AlignHCenter, self.xlabel)

		painter.save()
		painter.translate(20, self.height() / 2)
		painter.rotate(-90)
		painter.drawText(QRectF(-self.height() / 2, -20, self.height(), 20), Qt.AlignmentFlag.AlignCenter, self.ylabel)
		painter.restore()

		painter.fillRect(plot_rect, QColor("#050505"))
		painter.setPen(QPen(QColor(255, 255, 255, 70), 1))
		painter.drawRect(plot_rect)

		valid_curves, x_min, x_max, y_max, y_step = self._build_valid_curves()

		def map_x(value):
			span = max(1.0, x_max - x_min)
			return plot_rect.left() + ((value - x_min) / span) * plot_rect.width()

		def map_y(value):
			span = max(y_step, y_max)
			return plot_rect.bottom() - (value / span) * plot_rect.height()

		tick_count = len(self.x_tick_labels) if self.x_tick_labels else max(21, int(x_max))
		for index in range(1, tick_count + 1):
			x = map_x(float(index))
			painter.setPen(QPen(QColor(255, 255, 255, 20), 1))
			painter.drawLine(QPointF(x, plot_rect.top()), QPointF(x, plot_rect.bottom()))

			if index < tick_count:
				mid_x = map_x(index + 0.5)
				painter.setPen(QPen(QColor(255, 255, 255, 20), 1, Qt.PenStyle.DotLine))
				painter.drawLine(QPointF(mid_x, plot_rect.top()), QPointF(mid_x, plot_rect.bottom()))

			label = self.x_tick_labels[index - 1] if index - 1 < len(self.x_tick_labels) else str(index)
			lines = str(label).split("\n")
			for line_index, line in enumerate(lines):
				text_rect = QRectF(x - 24, plot_rect.bottom() + 8 + line_index * 13, 48, 12)
				painter.setPen(QColor("#d0d0d0"))
				painter.drawText(text_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, line)


		y_minor_step = y_step / 10
		y_value = 0.0
		while y_value <= y_max + (y_step / 2):
			y = map_y(y_value)
			painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
			painter.drawLine(QPointF(plot_rect.left(), y), QPointF(plot_rect.right(), y))

			minor_value = y_value + y_minor_step
			while minor_value < y_value + y_step and minor_value <= y_max:
				minor_y = map_y(minor_value)
				painter.setPen(QPen(QColor(255, 255, 255, 20), 1, Qt.PenStyle.DotLine))
				painter.drawLine(QPointF(plot_rect.left(), minor_y), QPointF(plot_rect.right(), minor_y))
				minor_value += y_minor_step

			painter.setPen(QColor("#d0d0d0"))
			painter.drawText(QRectF(6, y - 8, left_margin - 14, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"{y_value:.2f}")
			y_value += y_step

		if x_min <= 11 <= x_max:
			middle_x = map_x(11.0)
			painter.setPen(QPen(QColor(255, 255, 255, 55), 1, Qt.PenStyle.DashLine))
			painter.drawLine(QPointF(middle_x, plot_rect.top()), QPointF(middle_x, plot_rect.bottom()))

		if not valid_curves:
			painter.setPen(QColor("#a0a0a0"))
			painter.drawText(plot_rect, Qt.AlignmentFlag.AlignCenter, "Aucune donnée")
			return

		baseline_y = map_y(0.0)

		painter.save()
		painter.setClipRect(plot_rect)
		painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
		for _, data, x_vals, y_vals in valid_curves:
			if not data.get("fill", False):
				continue

			color = self._resolve_display_color(data.get("color", "#ffffff"))
			fill_color = QColor(color)
			fill_color.setAlphaF(0.5)

			polygon_points = [QPointF(map_x(x_vals[0]), baseline_y)]
			polygon_points.extend(QPointF(map_x(x_val), map_y(y_val)) for x_val, y_val in zip(x_vals, y_vals))
			polygon_points.append(QPointF(map_x(x_vals[-1]), baseline_y))

			painter.setPen(Qt.PenStyle.NoPen)
			painter.setBrush(fill_color)
			painter.drawPolygon(QPolygonF(polygon_points))

		painter.restore()

		painter.save()
		painter.setClipRect(plot_rect)
		for _, data, x_vals, y_vals in valid_curves:
			color = self._resolve_display_color(data.get("color", "#ffffff"))

			pen = QPen(color.lighter(145), 2)

			if data.get("linestyle") == "--":
				pen.setStyle(Qt.PenStyle.DashLine)

			painter.setPen(pen)
			painter.setBrush(Qt.BrushStyle.NoBrush)
			painter.drawPolyline(QPolygonF([QPointF(map_x(x_val), map_y(y_val)) for x_val, y_val in zip(x_vals, y_vals)]))
		painter.restore()

		self._draw_legend(painter, plot_rect, valid_curves)



class ShapeIndicator(QWidget):
	"""Small widget used to display a row marker shape."""

	def __init__(self, shape_name: str, parent=None):
		super().__init__(parent)
		self.shape_name = shape_name
		self.is_highlighted = False
		self.setFixedSize(20, 20)


	def set_highlighted(self, highlighted: bool):
		if self.is_highlighted != highlighted:
			self.is_highlighted = highlighted
			self.update()

	def paintEvent(self, event):
		super().paintEvent(event)

		painter = QPainter(self)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)

		if self.is_highlighted:
			fill_color = QColor("#942645")
		elif self.shape_name == "circle":
			fill_color = QColor("#aaa")
		elif self.shape_name == "octagon":
			fill_color = QColor("#fff")
		else:
			fill_color = QColor("#555")

		painter.setBrush(fill_color)
		painter.setPen(QPen(QColor("#ffffff"), 1.5))

		rect = QRectF(self.rect()).adjusted(1.0, 1.0, -1.0, -1.0)

		if self.shape_name == "circle":
			painter.drawEllipse(rect)
		elif self.shape_name == "octagon":
			diagonal_ratio = 1.8
			size = min(rect.width(), rect.height())
			offset_x = (rect.width() - size) / 2
			offset_y = (rect.height() - size) / 2
			left = rect.left() + offset_x
			right = left + size
			top = rect.top() + offset_y
			bottom = top + size
			corner_cut = (diagonal_ratio * size) / (sqrt(2) + 2 * diagonal_ratio)
			points = [
				QPointF(left + corner_cut, top),
				QPointF(right - corner_cut, top),
				QPointF(right, top + corner_cut),
				QPointF(right, bottom - corner_cut),
				QPointF(right - corner_cut, bottom),
				QPointF(left + corner_cut, bottom),
				QPointF(left, bottom - corner_cut),
				QPointF(left, top + corner_cut),
			]
			painter.drawPolygon(QPolygonF(points))
		else:
			painter.drawRect(rect)



class CurveWidget(QWidget):
	"""
	CurveWidget class manage curves tabp, inputs and graph
	Args:
		reader (DensitometerReader): DensitometerReader
		parent
	"""

	def __init__(self, reader:DensitometerReader, tabs=None, parent=None):
		"""Init"""
		super().__init__(parent)

		self.inputs_color_map = ['a', 'b', 'c', 'd']
		
		# "square", "circle", "octagon"
		self.row_shapes = (
			["square"] * 7
			+ ["circle"]
			+ ["square"] * 2
			+ ["octagon"]
			+ ["square"] * 2
			+ ["circle"]
			+ ["square"] * 3
			+ ["circle"]
			+ ["square"] * 3
		)

		self.reader = reader
		self.connect_signals()
		self.tabs = tabs

		self.manager = CurveManager()
		self.manager.data_updated.connect(self.update_plot)

		self.layout_main = QSplitter(Qt.Horizontal)  # type: ignore
		main_layout = QVBoxLayout(self)
		main_layout.addWidget(self.layout_main)

		self.layout_main.setSizes([700, 300])
		self.layout_main.setStretchFactor(0, 3)
		self.layout_main.setStretchFactor(1, 2)
		self.color_mode = 'vrgb'

		self.right_widget = QWidget()
		self._setup_plot()
		self._setup_controls()

		self.selected_index = 0
		self.update_input_labels()
		self.update_plot()

		for color_dict in (self.ref_inputs, self.meas_inputs):

			for fields in color_dict.values():
				for field in fields:
					field.installEventFilter(self)

	def _setup_plot(self):
		"""
		Init graph and gamma layout (with QSS support).
		"""
		plot_layout = QVBoxLayout()
		plot_widget = QWidget()
		plot_widget.setLayout(plot_layout)

		# Gamma widget/layout
		self.stats_layout = QHBoxLayout()
		self.stats_rows_layout = QVBoxLayout()
		self.stats_layout.addLayout(self.stats_rows_layout, 1)
		stats_widget = QWidget()
		stats_widget.setLayout(self.stats_layout)
		stats_widget.setMaximumHeight(120)
		plot_layout.addWidget(stats_widget)

		self.stat_row_layouts = {}


		# Sensito + delta graph tabs
		self.plot_tabs = QTabWidget()
		self.plot_tabs.setTabPosition(QTabWidget.West)

		# Graph containers
		self.sensito_canvas = FigureCanvas(Figure(figsize=(6, 4)))
		self.ax_sensito = self.sensito_canvas.figure.add_subplot(111)
		self.sensito_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

		self.sensito_canvas.figure.subplots_adjust(left=0.10, right=0.98, top=0.90, bottom=0.16)

		self.sensito_toolbar = NavigationToolbar(self.sensito_canvas, self)
		sensito_graph_layout = QVBoxLayout()
		sensito_graph_layout.addWidget(self.sensito_canvas)
		sensito_graph_layout.addWidget(self.sensito_toolbar)
		sensito_graph_widget = QWidget()
		sensito_graph_widget.setLayout(sensito_graph_layout)

		self.deltad_canvas = FigureCanvas(Figure(figsize=(6, 4)))
		self.ax_deltad = self.deltad_canvas.figure.add_subplot(111)
		self.deltad_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

		self.deltad_canvas.figure.subplots_adjust(left=0.10, right=0.98, top=0.90, bottom=0.16)

		self.deltad_toolbar = NavigationToolbar(self.deltad_canvas, self)
		deltad_graph_layout = QVBoxLayout()
		deltad_graph_layout.addWidget(self.deltad_canvas)
		deltad_graph_layout.addWidget(self.deltad_toolbar)
		deltad_graph_widget = QWidget()
		deltad_graph_widget.setLayout(deltad_graph_layout)

		self.rgbdelta_canvas = FigureCanvas(Figure(figsize=(6, 4)))
		self.ax_rgbdelta = self.rgbdelta_canvas.figure.add_subplot(111)
		self.rgbdelta_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

		self.rgbdelta_canvas.figure.subplots_adjust(left=0.10, right=0.98, top=0.90, bottom=0.16)

		self.rgbdelta_toolbar = NavigationToolbar(self.rgbdelta_canvas, self)
		rgbdelta_graph_layout = QVBoxLayout()
		rgbdelta_graph_layout.addWidget(self.rgbdelta_canvas)
		rgbdelta_graph_layout.addWidget(self.rgbdelta_toolbar)
		rgbdelta_graph_widget = QWidget()
		rgbdelta_graph_widget.setLayout(rgbdelta_graph_layout)

		self.additive_curve_widget = AdditiveCurveWidget()
		additive_graph_layout = QVBoxLayout()
		additive_graph_layout.addWidget(self.additive_curve_widget)
		additive_graph_widget = QWidget()
		additive_graph_widget.setLayout(additive_graph_layout)

		self.plot_tabs.addTab(sensito_graph_widget, "Sensito")
		self.plot_tabs.addTab(additive_graph_widget, "Courbe")
		self.plot_tabs.addTab(deltad_graph_widget, "delta-d")
		self.plot_tabs.addTab(rgbdelta_graph_widget, "ΔRGB")
		plot_layout.addWidget(self.plot_tabs)

		# Stats bloc
		self.stat_labels = {}
		for stat_type in STATS_LABELS:
			row_layout = QHBoxLayout()
			row_layout.setSpacing(8)
			row_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
			self.stat_row_layouts[stat_type] = row_layout

			for stat_key in STATS_LABELS[stat_type]:
				vbox = QVBoxLayout()
				vbox.setSpacing(2)
				vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)

				title = QLabel(stat_key)
				title.setStyleSheet("color: #ffffff;")
				title.setObjectName(f"title_{stat_key.replace(' ', '_').lower()}")
				title.setProperty("class", "stat-title")
				title.setAlignment(Qt.AlignmentFlag.AlignCenter)

				value = QLabel("--")
				value.setObjectName(f"value_{stat_key.replace(' ', '_').lower()}")
				value.setProperty("class", "stat-value")
				value.setAlignment(Qt.AlignmentFlag.AlignCenter)
				value.setMinimumSize(110, 20)
				value.setMaximumWidth(110)

				value.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)

				vbox.addWidget(title)
				vbox.addWidget(value)
				row_layout.addLayout(vbox)
				self.stat_labels[stat_key] = value

			self.stats_rows_layout.addLayout(row_layout)

		# Step selector
		step_layout = QVBoxLayout()
		step_layout.setSpacing(2)
		step_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

		step_title = QLabel("Step value")
		step_title.setObjectName("title_step_selector")
		step_title.setProperty("class", "stat-title")
		step_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

		self.step_selector = QComboBox()
		self.step_selector.setObjectName("step_selector")
		self.step_selector.setProperty("class", "step-selector")
		self.step_selector.addItems(["0.15", "0.20"])
		self.step_selector.setFixedSize(80, 20)
		self.step_selector.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
		self.step_selector.currentIndexChanged.connect(self.update_stats)

		step_layout.addWidget(step_title)
		step_layout.addWidget(self.step_selector)
		self.stats_layout.addLayout(step_layout)

		# Final layout
		self.layout_main.addWidget(plot_widget)
		self.layout_main.addWidget(self.right_widget)


	def _setup_controls(self):
		"""Init graph controls"""
		self.right_layout = QVBoxLayout(self.right_widget)

		self.title_input = QLineEdit()
		self.title_input.setText("Sensito")
		self.title_input.setStyleSheet("font-size: 18px;")
		self.title_input.setAlignment(Qt.AlignmentFlag.AlignHCenter)
		self.right_layout.addWidget(self.title_input)
		self.title_input.textChanged.connect(self.update_tab_title)

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
		self.mode_selector.addSpacing(16)
		self.reverse_measure_checkbox = QCheckBox("inverser sens de mesure")
		self.reverse_measure_checkbox.toggled.connect(self.update_measure_direction)
		self.mode_selector.addWidget(self.reverse_measure_checkbox)
		self.mode_selector.addStretch(1)

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

		self.ref_inputs = {k: [QLineEdit() for _ in range(21)] for k in self.inputs_color_map}
		self.meas_inputs = {k: [QLineEdit() for _ in range(21)] for k in self.inputs_color_map}

		controls_grid = QGridLayout()
		controls_grid.setHorizontalSpacing(6)
		controls_grid.setVerticalSpacing(6)
		self.shape_indicators = []
		self.row_number_labels = []


		ref_label = QLabel("Référence")
		controls_grid.addWidget(ref_label, 0, 0, 1, 4, Qt.AlignmentFlag.AlignHCenter)

		number_header_spacer = QWidget()
		number_header_spacer.setFixedWidth(46)
		controls_grid.addWidget(number_header_spacer, 0, 4, 1, 1, Qt.AlignmentFlag.AlignCenter)

		shape_header_spacer = QWidget()
		shape_header_spacer.setFixedWidth(38)
		controls_grid.addWidget(shape_header_spacer, 0, 5, 1, 1, Qt.AlignmentFlag.AlignCenter)

		meas_label = QLabel("Mesures en cours")
		controls_grid.addWidget(meas_label, 0, 6, 1, 4, Qt.AlignmentFlag.AlignHCenter)


		self.import_ref_selector = QComboBox()
		self.import_ref_selector.addItem("Charger ref")
		self.populate_file_selector(self.import_ref_selector, MEASURES_PATH)
		self.import_ref_selector.currentIndexChanged.connect(
			lambda: self.import_selected_file(self.ref_inputs, self.import_ref_selector.currentData(), "ref", MEASURES_PATH)
		)
		controls_grid.addWidget(self.import_ref_selector, 1, 0, 1, 4)

		self.import_meas_selector = QComboBox()
		self.import_meas_selector.addItem("Charger")
		self.populate_file_selector(self.import_meas_selector, MEASURES_PATH)
		self.import_meas_selector.currentIndexChanged.connect(
			lambda: self.import_selected_file(self.meas_inputs, self.import_meas_selector.currentData(), "meas", MEASURES_PATH)
		)

		export_btn = QPushButton("\U0001F4BE")
		export_btn.setToolTip("Sauvegarder le fichier de mesures")
		export_btn.clicked.connect(self.export_meas_file)
		export_btn.setMaximumWidth(30)

		reload_btn = QPushButton("\U0001F5D8")
		reload_btn.setToolTip("Recharger la list des mesures")
		reload_btn.clicked.connect(self.refresh_file_selectors)
		reload_btn.setMaximumWidth(30)

		meas_header_widget = QWidget()
		meas_header_layout = QHBoxLayout(meas_header_widget)
		meas_header_layout.setContentsMargins(0, 0, 0, 0)
		meas_header_layout.setSpacing(6)
		meas_header_layout.addWidget(self.import_meas_selector)
		meas_header_layout.addWidget(export_btn)
		meas_header_layout.addWidget(reload_btn)
		controls_grid.addWidget(meas_header_widget, 1, 6, 1, 4)


		row_height = max(
			self.ref_inputs[self.inputs_color_map[0]][0].sizeHint().height(),
			self.meas_inputs[self.inputs_color_map[0]][0].sizeHint().height(),
		)

		for color in self.inputs_color_map:
			for field in self.ref_inputs[color] + self.meas_inputs[color]:
				field.setFixedWidth(45)
				field.setFixedHeight(row_height)
				field.editingFinished.connect(self.update_from_fields)

		measurement_labels = self._measurement_step_labels()
		measurement_markers = self._measurement_step_markers()
		for row in range(21):
			grid_row = row + 2
			step_value = int(measurement_labels[row])
			has_marker = step_value in measurement_markers
			controls_grid.setRowMinimumHeight(grid_row, row_height + (14 if has_marker else 0))
			for col, color in enumerate(self.inputs_color_map):
				controls_grid.addWidget(self.ref_inputs[color][row], grid_row, col)

			row_number_widget = QWidget()
			row_number_layout = QVBoxLayout(row_number_widget)
			row_number_layout.setContentsMargins(0, 0, 0, 0)
			row_number_layout.setSpacing(0)
			row_number_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

			row_number_label = QLabel(measurement_labels[row])
			row_number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
			row_number_layout.addWidget(row_number_label)

			if has_marker:
				marker_label = QLabel(measurement_markers[step_value])
				marker_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
				marker_label.setStyleSheet("font-size: 10px; color: #aaaaaa;")
				row_number_layout.addWidget(marker_label)

			self.row_number_labels.append(row_number_label)
			controls_grid.addWidget(row_number_widget, grid_row, 4, 1, 1, Qt.AlignmentFlag.AlignCenter)

			indicator = ShapeIndicator(self.row_shapes[row])


			self.shape_indicators.append(indicator)
			controls_grid.addWidget(indicator, grid_row, 5, 1, 1, Qt.AlignmentFlag.AlignCenter)

			for col, color in enumerate(self.inputs_color_map):
				controls_grid.addWidget(self.meas_inputs[color][row], grid_row, 6 + col)

		clear_ref_btn = QPushButton("Clear")
		clear_meas_btn = QPushButton("Clear")
		clear_ref_btn.clicked.connect(lambda: self.clear_inputs("ref"))
		clear_meas_btn.clicked.connect(lambda: self.clear_inputs("meas"))
		controls_grid.addWidget(clear_ref_btn, 23, 0, 1, 4, Qt.AlignmentFlag.AlignHCenter)
		controls_grid.addWidget(clear_meas_btn, 23, 6, 1, 4, Qt.AlignmentFlag.AlignHCenter)

		controls_grid.setColumnMinimumWidth(4, 46)

		controls_grid.setColumnMinimumWidth(5, 38)


		controls_widget = QWidget()
		controls_widget.setLayout(controls_grid)
		self.right_layout.addWidget(controls_widget, 0, Qt.AlignmentFlag.AlignLeft)

		self.right_widget.setMaximumWidth(600)
		self.right_layout.addStretch(1)


	def _measurement_step_labels(self):
		return [str(21 - i) for i in range(21)]


	def _graph_step_labels(self):
		markers = self._measurement_step_markers()
		return [
			f"{step}\n{markers[step]}" if step in markers else str(step)
			for step in range(21, 0, -1)
		]


	def _measurement_step_markers(self):
		return {
			21: "D-min",
			14: "LD",
			8: "MD",
			4: "HD",
			1: "D-max",
		}


	def _reverse_step_position(self, position):
		if position is None:
			return None
		return 22 - position


	def _format_gamma_tooltip(self, reading):
		ld = "--" if reading.ld is None else f"{reading.ld:.2f}"
		md = "--" if reading.md is None else f"{reading.md:.2f}"
		hd = "--" if reading.hd is None else f"{reading.hd:.2f}"
		search_start = self._reverse_step_position(reading.search_range.start)
		search_end = self._reverse_step_position(reading.search_range.end)
		gamma_start = self._reverse_step_position(reading.gamma_range.start)
		gamma_end = self._reverse_step_position(reading.gamma_range.end)
		return (
			f"gamma\t\t\t: {reading.gamma:.2f}\n"
			f"step_value\t\t: {reading.step_value:.2f}\n"
			f"d_min\t\t\t: {reading.d_min:.2f}\n"
			f"d_max\t\t\t: {reading.d_max:.2f}\n"
			f"LD\t\t\t: {ld}\n"
			f"MD\t\t\t: {md}\n"
			f"HD\t\t\t: {hd}\n"
			f"search_range\t\t: [{search_start:.2f} - {search_end:.2f}]\n"
			f"gamma_range\t\t: [{gamma_start:.2f} - {gamma_end:.2f}]"
		)

	
	def update_input_labels(self):
		"""
		Update measurements inputs labels(v, c, m, y or v, r, g, b)
		"""
		labels = COLOR_SET['vcmy'].name if self.radio_vcmy.isChecked() else COLOR_SET['vrgb'].name
		self.color_mode = 'vcmy' if self.radio_vcmy.isChecked() else 'vrgb'
		for i, key in enumerate(self.inputs_color_map):
			label = labels[i]
			self.channel_checkboxes[key].setText(label)
			for field in self.ref_inputs[key]:
				field.setPlaceholderText(label)
			for field in self.meas_inputs[key]:
				field.setPlaceholderText(label)
		self.update_input_visibility()


	def _get_measure_boundary_index(self):
		"""Returns the first active row based on the selected measurement direction."""
		return 20 if self.reverse_measure_checkbox.isChecked() else 0


	def _get_measure_field_for_row(self, row_index=None):
		"""Returns the first visible measurement input for the requested row."""
		if row_index is None:
			row_index = self.selected_index
		row_index = max(0, min(20, row_index))

		for key in self.inputs_color_map:
			field = self.meas_inputs[key][row_index]
			if field.isVisible():
				return field
		return self.meas_inputs[self.inputs_color_map[0]][row_index]


	def _focus_selected_measure_input(self):
		"""Focuses the measurement input corresponding to the active row."""
		if not hasattr(self, "selected_index"):
			return
		self._get_measure_field_for_row(self.selected_index).setFocus()



	def update_measure_direction(self):
		"""Updates the current row when the measurement direction is toggled."""
		if not any(field.text().strip() for fields in self.meas_inputs.values() for field in fields):
			self.selected_index = self._get_measure_boundary_index()
		self._highlight_selected_row()
		self._focus_selected_measure_input()


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
		self.selected_index = self._get_measure_boundary_index()
		self._highlight_selected_row()
		self._focus_selected_measure_input()

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
		self._focus_selected_measure_input()



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
		self.draw_additive_graph()
		self.draw_deltad_graph()
		self.draw_rgb_delta_graph()
		self.update_stats()


	def _build_density_curves(self, fill_measurements=False):
		curves = {}
		for key, values in self.manager.data.items():
			if not any(values):
				continue

			prefix, abcd = key.split("_")
			if not self.channel_checkboxes.get(abcd, QCheckBox()).isChecked():
				continue

			x_vals = [i + 1 for i, value in enumerate(values) if value is not None]
			y_vals = [value for value in values if value is not None]
			if not x_vals or not y_vals:
				continue

			color_letter = COLOR_SET[self.color_mode].channel_from_abcd(abcd)
			if fill_measurements and color_letter == "v":
				continue

			color_name = COLOR_SET[self.color_mode].get_color_name(color_letter)
			label = f"{prefix.capitalize()} {color_letter}"

			curves[label] = {
				"x": x_vals,
				"y": y_vals,
				"color": color_name,
				"linestyle": "--" if prefix == "ref" else "-",
				"fill": fill_measurements and prefix == "meas",
			}
		return curves


	def draw_sensito_graph(self):
		"""
		Update sensito plot for each visible channel.
		"""
		curves = self._build_density_curves()

		draw_curve_graph(
			ax=self.ax_sensito,
			canvas=self.sensito_canvas,
			curves=curves,
			title="Density curves",
			xlabel="Measurement",
			ylabel="Density",
			x_tick_labels=self._graph_step_labels(),
		)
		
		self.ax_sensito.axvline(x=11, color="black", linestyle="--", linewidth=1.0, alpha=0.2)
		self.sensito_canvas.draw()


	def draw_additive_graph(self):
		"""Update additive filled curve view for visible channels."""
		self.additive_curve_widget.set_plot_data(
			curves=self._build_density_curves(fill_measurements=True),
			title="Histogramme",
			xlabel="Measurement",
			ylabel="Density",
			x_tick_labels=self._graph_step_labels(),
		)


	def draw_deltad_graph(self):
		"""
		Update delta-d plot (meas - ref) for each visible channel using draw_curve_graph.
		"""
		curves = {}

		for abcd in self.inputs_color_map:
			meas_key = f"meas_{abcd}"
			ref_key = f"ref_{abcd}"

			meas_vals = self.manager.data.get(meas_key, [])
			ref_vals = self.manager.data.get(ref_key, [])

			if not self.channel_checkboxes.get(abcd, QCheckBox()).isChecked():
				continue
			if not any(meas_vals) or not any(ref_vals):
				continue

			x_vals, delta_vals = [], []
			for i, (m, r) in enumerate(zip(meas_vals, ref_vals)):
				if m is not None and r is not None:
					x_vals.append(i + 1)
					delta_vals.append(abs(m - r))

			if x_vals and delta_vals:
				color_letter = COLOR_SET[self.color_mode].channel_from_abcd(abcd)
				color_name = COLOR_SET[self.color_mode].get_color_name(color_letter)
				label = f"Δ {color_letter.upper()}"
				curves[label] = {
					"x": x_vals,
					"y": delta_vals,
					"color": color_name,
					"linestyle": "-",
				}

				draw_curve_graph(
			ax=self.ax_deltad,
			canvas=self.deltad_canvas,
			curves=curves,
			title="Delta Curves",
			xlabel="Measurement",
			ylabel="Δ Density (meas - ref)",
			x_tick_labels=self._graph_step_labels(),

		)


	def draw_rgb_delta_graph(self):
		"""Draw ΔRG, ΔGB and ΔRB curves for meas and ref in VRGB mode."""
		curves = {}

		if self.color_mode != "vrgb":
			draw_curve_graph(
				ax=self.ax_rgbdelta,
				canvas=self.rgbdelta_canvas,
				curves=curves,
				title="ΔRG / ΔGB / ΔRB",
				xlabel="Measurement",
				ylabel="Δ Color diff",
				x_tick_labels=self._graph_step_labels(),
			)


			return

		pair_defs = [
			("ΔRG", "b", "c", "#FFCC00"),
			("ΔGB", "c", "d", "#00CCFF"),
			("ΔRB", "b", "d", "#CC00FF"),
		]

		for label, left_abcd, right_abcd, color in pair_defs:
			if not self.channel_checkboxes.get(left_abcd, QCheckBox()).isChecked():
				continue
			if not self.channel_checkboxes.get(right_abcd, QCheckBox()).isChecked():
				continue

			meas_x, meas_y = self._build_pair_delta_values(
				self.manager.data.get(f"meas_{left_abcd}", []),
				self.manager.data.get(f"meas_{right_abcd}", []),
			)
			if meas_x:
				curves[label] = {
					"x": meas_x,
					"y": meas_y,
					"color": color,
					"linestyle": "-",
				}

			ref_x, ref_y = self._build_pair_delta_values(
				self.manager.data.get(f"ref_{left_abcd}", []),
				self.manager.data.get(f"ref_{right_abcd}", []),
			)
			if ref_x:
				curves[f"Réf {label}"] = {
					"x": ref_x,
					"y": ref_y,
					"color": color,
					"linestyle": "--",
				}

		draw_curve_graph(
			ax=self.ax_rgbdelta,
			canvas=self.rgbdelta_canvas,
			curves=curves,
			title="ΔRG / ΔGB / ΔRB",
			xlabel="Measurement",
			ylabel="Δ Color diff",
			x_tick_labels=self._graph_step_labels(),
		)


	def _format_stat_value(self, value):
		return "--" if value is None else f"{value:.2f}"


	def _set_stat_value(self, key: str, value=None, tooltip: str = ""):
		label = self.stat_labels.get(key)
		if not label:
			return
		label.setText(self._format_stat_value(value))
		label.setToolTip(tooltip)


	def _build_pair_delta_values(self, left_values, right_values):
		x_vals, delta_vals = [], []
		for i, (left, right) in enumerate(zip(left_values, right_values)):
			if left is not None and right is not None:
				x_vals.append(i + 1)
				delta_vals.append(abs(left - right))
		return x_vals, delta_vals


	def update_stats(self):
		"""
		Update the stat blocks with contrast and gamma readings.
		"""

		# do not include channel v in gamma calculation
		v_abcd = COLOR_SET[self.color_mode].channel_to_abcd.get("v", "a")
		visible_channels = [
			key for key, cb in self.channel_checkboxes.items()
			if cb.isChecked() and key != v_abcd
		]

		for key in self.stat_labels:
			self._set_stat_value(key)

		if not visible_channels:
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
			return

		def average_step_density(prefix: str, step: int):
			row_index = 21 - step
			values = []
			for key in visible_channels:
				curve_values = self.manager.data.get(f"{prefix}_{key}", [])
				if row_index < len(curve_values):
					value = curve_values[row_index]
					if value is not None:
						values.append(value)
			return sum(values) / len(values) if values else None

		ref_ld_value = average_step_density("ref", 14)
		ref_hd_value = average_step_density("ref", 4)
		if ref_ld_value is not None and ref_hd_value is not None:
			contrast_ref = ref_hd_value - ref_ld_value
			contrast_ref_tooltip = (
				f"contrast\t: {contrast_ref:.2f}\n"
				f"formula\t: HD - LD\n"
				f"HD (step 4)\t: {ref_hd_value:.2f}\n"
				f"LD (step 14)\t: {ref_ld_value:.2f}"
			)
			self._set_stat_value("Contrast ref", contrast_ref, contrast_ref_tooltip)

		reading_ref = results.get("ref")

		if reading_ref:
			tooltip = self._format_gamma_tooltip(reading_ref)
			self._set_stat_value("Gamma ref", reading_ref.gamma, tooltip)


		for abcd_key, stat_key in zip(['b', 'c', 'd'], STATS_LABELS["ref"][2:]):

			reading = results.get(f"ref_{abcd_key}")
			if reading:
				self._set_stat_value(stat_key, reading.gamma, self._format_gamma_tooltip(reading))

		meas_ld_value = average_step_density("meas", 14)
		meas_hd_value = average_step_density("meas", 4)
		if meas_ld_value is not None and meas_hd_value is not None:
			contrast_meas = meas_hd_value - meas_ld_value
			contrast_meas_tooltip = (
				f"contrast\t: {contrast_meas:.2f}\n"
				f"formula\t: HD - LD\n"
				f"HD (step 4)\t: {meas_hd_value:.2f}\n"
				f"LD (step 14)\t: {meas_ld_value:.2f}"
			)
			self._set_stat_value("Contrast", contrast_meas, contrast_meas_tooltip)

		reading_all = results.get("all")
		if reading_all:
			tooltip = self._format_gamma_tooltip(reading_all)
			self._set_stat_value("Gamma", reading_all.gamma, tooltip)


		for abcd_key, stat_key in zip(['b', 'c', 'd'], STATS_LABELS["meas"][2:]):
			if abcd_key in visible_channels:
				reading = results.get(abcd_key)
				if reading:
					self._set_stat_value(stat_key, reading.gamma, self._format_gamma_tooltip(reading))


	def populate_file_selector(self, selector: QComboBox, path: str):
		"""Populate the file selector

		Add list of parsed json file to selector

		Args:
			Selector (QComboBox)
		"""
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
					
					name = data.get("name", os.path.splitext(fname)[0])
					values = data.get("values", {})
					date_str = data.get("date", "?")
					try:
						date_obj = datetime.strptime(date_str, "%Y-%m-%d")
					except ValueError:
						date_obj = datetime.min

					# we only take used color channels
					used_channels = list(values.keys())  # ex: ['b']
					channel_order = ['v', 'r', 'g', 'b', 'c', 'm', 'y']
					channel_str = ",".join(k.upper() for k in channel_order if k in used_channels)

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
	

	def refresh_file_selectors(self):
		self.populate_file_selector(self.import_meas_selector, MEASURES_PATH)
		self.populate_file_selector(self.import_ref_selector, MEASURES_PATH)


	def import_selected_file(self, inputs, file, toclear, path=""):
		self.clear_inputs(toclear, False)

		if not isinstance(file, str) or not file.endswith(".json"):
			self.update_from_fields()
			return

		try:
			filepath = file if os.path.isabs(file) else os.path.join(os.path.dirname(__file__), path, file)
			mset = MeasurementSet.load_from_file(Path(filepath))
	
			if not mset:
				return

			self.title_input.setText(mset.name or "")
			self.color_mode = mset.color
			self.radio_vcmy.setChecked(mset.color == 'vcmy')
			self.radio_vrgb.setChecked(mset.color == 'vrgb')

			mapping = COLOR_SET[mset.color].channel_to_abcd

			for color_key, curve in mset.curves.items():
				abcd_key = mapping.get(color_key.lower())
				if not abcd_key:
					continue
				for i, val in enumerate(curve.values):
					if i < 21:
						inputs[abcd_key][i].setText(str(val))

		except Exception as e:
			print("JSON loading error:", e)

		self.update_from_fields()


	def export_meas_file(self):
		"""Exports measurement data to a JSON file.

		This function collects measurement data including name, color mode, and curves,
		then formats it into a structured JSON file. A dialog prompts the user for a
		save location. It updates file selectors post-exportation.

		Raises:
			Exception: If an error occurs during the JSON file export.
		"""
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
		curves = {}
		for channel in ['v', 'r', 'g', 'b', 'c', 'm', 'y']:
			abcd = COLOR_SET[self.color_mode].channel_to_abcd.get(channel)
			if abcd and any(field.text().strip() for field in self.meas_inputs[abcd]):
				used_channels.append(channel.upper())
				values = []
				for field in self.meas_inputs[abcd]:
					try:
						values.append(float(field.text()))
					except ValueError:
						values.append(0.0)
				curves[channel.upper()] = ChannelCurve(channel.upper(), values)

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
			mset = MeasurementSet(
				path=Path(fname),
				name=name,
				color=self.color_mode,
				date=datetime.fromisoformat(date_str),
				curves=curves
			)
			mset.export_to_file(fname)
			self.refresh_file_selectors()
		except Exception as e:
			print("Erreur sauvegarde JSON:", e)


	def eventFilter(self, obj, event):
		"""Handles focus events for user input fields.

		This function detects when a text input field gains focus and updates the
		currently selected index. It highlights the row corresponding to this index.

		Args:
			obj: The object that triggered the event.
			event: The event triggered (specifically looking for focus in events).

		Returns:
			bool: Whether the event is consumed by the filter.
		"""
		if event.type() == QEvent.Type.FocusIn:
			for group in (self.ref_inputs, self.meas_inputs):
				for key in group:
					if obj in group[key]:
						self.selected_index = group[key].index(obj)
						self._highlight_selected_row()
						break
		return super().eventFilter(obj, event)


	def receive_measurements(self, values: dict[str, float]):
		"""Populates input fields with provided measurement values.

		This function updates input fields based on the received measurement values,
		maps channels to their respective fields, and progresses the selected index.

		Args:
			values (dict[str, float]): A dictionary of measurement values keyed by channel.
		"""
		mode = 'vcmy' if self.radio_vcmy.isChecked() else 'vrgb'
		channel_map = COLOR_SET[mode].channel_to_abcd

		for k, val in values.items():
			if k not in channel_map:
				continue
			abcd = channel_map[k]
			if abcd in self.meas_inputs and 0 <= self.selected_index < 21:
				self.meas_inputs[abcd][self.selected_index].setText(f"{val:.2f}")

		next_index = self.selected_index - 1 if self.reverse_measure_checkbox.isChecked() else self.selected_index + 1
		if 0 <= next_index < 21:
			self.selected_index = next_index
		self._highlight_selected_row()
		self._focus_selected_measure_input()

		self.update_from_fields()


	def _highlight_selected_row(self):
		"""Visually highlights the currently selected input row.

		This function changes the background color of the currently selected row's input fields,
		providing a visual cue for users during data entry.
		"""
		for group in (self.meas_inputs,):
			for key in group:
				for i, field in enumerate(group[key]):
					if i == self.selected_index:
						field.setStyleSheet("background-color: #eee; color: #000000;")
					else:
						field.setStyleSheet("")

		for i, indicator in enumerate(getattr(self, "shape_indicators", [])):
			indicator.set_highlighted(i == self.selected_index)

		for i, label in enumerate(getattr(self, "row_number_labels", [])):
			if i == self.selected_index:
				label.setStyleSheet("color: #ff88aa; border-radius: 4px;")
			else:
				label.setStyleSheet("")


	def connect_signals(self):
		"""Connects signals for measurement data reception.

		This function sets up the necessary signal connections to handle incoming parsed
		measurement data, allowing real-time updates of the input fields.
		"""
		self.reader.parsed_measurement.connect(self.receive_measurements)


	def update_tab_title(self):
		"""Updates the title of the tab containing this widget.

		Adjusts the displayed tab title based on the user's input. If no title is provided,
		it defaults to "Courbes".

		Note:
			Only updates the title if the widget is contained within a tab widget.
		"""
		title = self.title_input.text().strip()
		if self.tabs:
			index = self.tabs.indexOf(self)
			self.tabs.setTabText(index, title if title else "Courbes")

