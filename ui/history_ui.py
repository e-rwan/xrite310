# ui/history_ui.py

# pyright: reportAttributeAccessIssue=false

import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLineEdit,
    QComboBox, QLabel, QSplitter, QTabWidget, QApplication, QPushButton
)
from PySide6.QtCore import Qt, QDate
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar

from constants import MEASURES_PATH
from model.measurement_set import MeasurementSet
from lib.history_analyzer import HistoryAnalyzer
from ui.history_gamma_plot import HistoryGammaPlot
from ui.history_charts import (
    draw_gamma_plot,
    draw_dmin_plot,
    draw_dmax_plot,
    draw_d11_plot,
    draw_ld_plot,
    draw_md_plot,
    draw_hd_plot,
    draw_contrast_plot,
)



class HistoryWidget(QWidget):
    """Provides a graphical user interface to analyze historical measurement data.

    The HistoryWidget allows users to select and visualize historical measurement data.
    It includes features for filtering, selecting reference curves, and plotting
    gamma, D-min, and D-max curves.

    Methods:
        load_files: Loads measurement files into the display.
        filter_files: Filters displayed files based on user input and date criteria.
        get_selected_files: Retrieves the list of currently selected file paths.
        load_reference_files: Loads and populates reference measurement files.
        get_reference_file: Returns the currently selected reference file path.
        toggle_item_check_state: Toggles the check state of tree items, enabling selection.
        refresh_plot: Updates plots with selected measurement data.
        auto_resize_columns: Adjusts tree column widths to fit contents.
    """

    def __init__(self, parent=None):
        """Initializes the HistoryWidget, setting up its layout and components.

        Args:
            parent: The parent widget, defaults to None.
        """
        super().__init__(parent)

        # Splitter
        splitter = QSplitter(Qt.Horizontal)

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(splitter)

        # gamma
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)
        self.gamma_plot = HistoryGammaPlot()
        self.tabs.addTab(self.gamma_plot, "Gammas")
        # D-min
        dmin_widget = QWidget()
        dmin_layout = QVBoxLayout()
        dmin_widget.setLayout(dmin_layout)
        self.dmin_fig = Figure()
        self.dmin_canvas = FigureCanvas(self.dmin_fig)
        self.dmin_ax = self.dmin_fig.add_subplot(111)
        self.dmin_toolbar = NavigationToolbar(self.dmin_canvas, self)
        dmin_layout.addWidget(self.dmin_canvas)
        dmin_layout.addWidget(self.dmin_toolbar)
        self.tabs.addTab(dmin_widget, "D-min")
        # D-max
        dmax_widget = QWidget()
        dmax_layout = QVBoxLayout()
        dmax_widget.setLayout(dmax_layout)
        self.dmax_fig = Figure()
        self.dmax_canvas = FigureCanvas(self.dmax_fig)
        self.dmax_ax = self.dmax_fig.add_subplot(111)
        self.dmax_toolbar = NavigationToolbar(self.dmax_canvas, self)
        dmax_layout.addWidget(self.dmax_canvas)
        dmax_layout.addWidget(self.dmax_toolbar)
        self.tabs.addTab(dmax_widget, "D-max")
        # D-11
        d11_widget = QWidget()
        d11_layout = QVBoxLayout()
        d11_widget.setLayout(d11_layout)
        self.d11_fig = Figure()
        self.d11_canvas = FigureCanvas(self.d11_fig)
        self.d11_ax = self.d11_fig.add_subplot(111)
        self.d11_toolbar = NavigationToolbar(self.d11_canvas, self)
        d11_layout.addWidget(self.d11_canvas)
        d11_layout.addWidget(self.d11_toolbar)
        self.tabs.addTab(d11_widget, "D-11")
        # LD
        ld_widget = QWidget()
        ld_layout = QVBoxLayout()
        ld_widget.setLayout(ld_layout)
        self.ld_fig = Figure()
        self.ld_canvas = FigureCanvas(self.ld_fig)
        self.ld_ax = self.ld_fig.add_subplot(111)
        self.ld_toolbar = NavigationToolbar(self.ld_canvas, self)
        ld_layout.addWidget(self.ld_canvas)
        ld_layout.addWidget(self.ld_toolbar)
        self.tabs.addTab(ld_widget, "LD")
        # MD
        md_widget = QWidget()
        md_layout = QVBoxLayout()
        md_widget.setLayout(md_layout)
        self.md_fig = Figure()
        self.md_canvas = FigureCanvas(self.md_fig)
        self.md_ax = self.md_fig.add_subplot(111)
        self.md_toolbar = NavigationToolbar(self.md_canvas, self)
        md_layout.addWidget(self.md_canvas)
        md_layout.addWidget(self.md_toolbar)
        self.tabs.addTab(md_widget, "MD")
        # HD
        hd_widget = QWidget()
        hd_layout = QVBoxLayout()
        hd_widget.setLayout(hd_layout)
        self.hd_fig = Figure()
        self.hd_canvas = FigureCanvas(self.hd_fig)
        self.hd_ax = self.hd_fig.add_subplot(111)
        self.hd_toolbar = NavigationToolbar(self.hd_canvas, self)
        hd_layout.addWidget(self.hd_canvas)
        hd_layout.addWidget(self.hd_toolbar)
        self.tabs.addTab(hd_widget, "HD")
        # Contrast
        contrast_widget = QWidget()
        contrast_layout = QVBoxLayout()
        contrast_widget.setLayout(contrast_layout)
        self.contrast_fig = Figure()
        self.contrast_canvas = FigureCanvas(self.contrast_fig)
        self.contrast_ax = self.contrast_fig.add_subplot(111)
        self.contrast_toolbar = NavigationToolbar(self.contrast_canvas, self)
        contrast_layout.addWidget(self.contrast_canvas)
        contrast_layout.addWidget(self.contrast_toolbar)
        self.tabs.addTab(contrast_widget, "Contrast")
 
        splitter.addWidget(self.tabs)

        # File selection panel
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        right_panel.setMinimumWidth(300)
        # ref selector
        self.ref_selector = QComboBox()
        self.ref_selector.setPlaceholderText("Référence")
        right_layout.addWidget(QLabel("Courbe de référence"))
        right_layout.addWidget(self.ref_selector)
        # search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher un fichier...")
        self.search_input.textChanged.connect(self.filter_files)
        # filter by date
        self.date_filter = QComboBox()
        self.date_filter.addItems(["Toutes dates", "Aujourd’hui", "Ce mois-ci", "Cette année"])
        self.date_filter.currentIndexChanged.connect(self.filter_files)
        # file list
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["", "Nom", "Date"])
        self.tree.setRootIsDecorated(True)
        self.tree.setSelectionMode(QTreeWidget.ExtendedSelection)

        right_layout.addWidget(QLabel("Filtres"))
        right_layout.addWidget(self.search_input)
        right_layout.addWidget(self.date_filter)
        right_layout.addWidget(QLabel("Mesures disponibles"))

        # reload measures list button
        reload_btn = QPushButton("\U0001F5D8")
        reload_btn.setToolTip("Recharger la list des mesures")
        reload_btn.clicked.connect(self.load_files)
        reload_btn.setMaximumWidth(30)
        right_layout.addWidget(reload_btn)

        right_layout.addWidget(self.tree)
        self.tree.setColumnWidth(0, 30)   # Checkbox
        self.tree.setColumnWidth(1, 100)  # Nom
        self.tree.setColumnWidth(2, 75)  # Date

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        self.load_files()
        self.load_reference_files()

        self.last_clicked_item = None

        self.ref_selector.currentIndexChanged.connect(self.refresh_plot)
        self.tree.itemChanged.connect(self.refresh_plot)
        self.tree.itemClicked.connect(self.toggle_item_check_state)


    def load_files(self):
        """Loads measurement files into the UI.

        This function clears existing tree data and loads new measurement files
        from a specified directory, adding them to the tree widget for display.
        """
        self.tree.clear()
        for root, dirs, files in os.walk(MEASURES_PATH):
            folder_name = os.path.basename(root)
            folder_item = QTreeWidgetItem(["", folder_name, ""])
            font = folder_item.font(1)
            font.setBold(True)
            for col in range(self.tree.columnCount()):
                folder_item.setFont(col, font)
            added = False

            measurements = []
            for fname in files:
                if fname.endswith(".json"):
                    fpath = os.path.join(root, fname)
                    measurement = MeasurementSet.load_from_file(Path(fpath))
                    if measurement:
                        measurements.append((measurement, fpath))

            # sort by date
            measurements.sort(key=lambda tup: tup[0].date)

            for measurement, fpath in measurements:
                name = measurement.name or Path(fpath).stem
                date_str = measurement.date.strftime("%Y-%m-%d")

                item = QTreeWidgetItem(["", name, date_str])
                item.setData(0, Qt.UserRole, str(fpath))
                item.setCheckState(0, Qt.Unchecked)
                item.setFlags(
                    (item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled) & ~Qt.ItemIsUserCheckable
                )
                folder_item.addChild(item)
                added = True

            if added:
                self.tree.addTopLevelItem(folder_item)
                folder_item.setExpanded(True)


    def filter_files(self):
        """Filters displayed measurement files based on search text and date filter.

        This function hides or shows files in the tree widget based on whether they
        match user-entered text or a selected date criterion.
        """
        text = self.search_input.text().lower()
        period = self.date_filter.currentText()
        now = QDate.currentDate()

        for i in range(self.tree.topLevelItemCount()):
            folder_item = self.tree.topLevelItem(i)
            if folder_item is None:
                continue
            visible = False
            for j in range(folder_item.childCount()):
                child = folder_item.child(j)
                label = child.text(0).lower()
                m = MeasurementSet.load_from_file(Path(child.data(0, Qt.UserRole)))
                if not m:
                    continue
                json_date = m.date.strftime("%Y-%m-%d")
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


    def get_selected_files(self) -> list:
        """Gets the file paths of currently selected measurement files.

        Returns:
            list: A list of file paths corresponding to selected files.
        """
        selected = []
        for i in range(self.tree.topLevelItemCount()):
            folder_item = self.tree.topLevelItem(i)
            if folder_item is None:
                continue
            for j in range(folder_item.childCount()):
                child = folder_item.child(j)
                if child.checkState(0) == Qt.Checked:
                    selected.append(child.data(0, Qt.UserRole))
        return selected


    def load_reference_files(self):
        """Loads reference files to be available for plot comparison.

        This function searches a designated folder for reference files and populates
        a combo box with these references.
        """
        self.ref_selector.clear()
        ref_path = os.path.join(MEASURES_PATH, "ref")
        if not os.path.exists(ref_path):
            return

        for fname in sorted(os.listdir(ref_path)):
            if fname.endswith(".json"):
                fpath = os.path.join(ref_path, fname)
                self.ref_selector.addItem(fname, fpath)


    def get_reference_file(self):
        """Retrieves the currently selected reference file.

        Returns:
            The file path of the selected reference file, or None if not selected.
        """
        return self.ref_selector.currentData()


    def toggle_item_check_state(self, item):
        """Toggles the check state for a tree widget item and its children.

        Args:
            item: The QTreeWidgetItem to toggle.
        """
        if item.childCount() > 0:
            all_checked = all(item.child(i).checkState(0) == Qt.Checked for i in range(item.childCount()))
            new_state = Qt.Unchecked if all_checked else Qt.Checked
            for i in range(item.childCount()):
                item.child(i).setCheckState(0, new_state)
            return

        modifiers = QApplication.keyboardModifiers()
        current_state = item.checkState(0)

        if modifiers == Qt.ShiftModifier and self.last_clicked_item:
            all_items = []
            for i in range(self.tree.topLevelItemCount()):
                parent = self.tree.topLevelItem(i)
                if parent is None:
                    continue
                for j in range(parent.childCount()):
                    all_items.append(parent.child(j))

            try:
                i1 = all_items.index(self.last_clicked_item)
                i2 = all_items.index(item)
                start, end = sorted([i1, i2])
                new_state = Qt.Checked if current_state != Qt.Checked else Qt.Unchecked
                for it in all_items[start:end + 1]:
                    it.setCheckState(0, new_state)
            except ValueError:
                item.setCheckState(0, Qt.Checked if current_state != Qt.Checked else Qt.Unchecked)
        else:
            # Simple toggle
            new_state = Qt.Unchecked if current_state == Qt.Checked else Qt.Checked
            item.setCheckState(0, new_state)

        self.last_clicked_item = item


    def refresh_plot(self):
        """Refreshes plot displays with selected measurements and reference data.
        This function updates the gamma, density, and LD/MD/HD plots using the
        currently selected measurement files and reference curves.

        """
        ref_path = self.get_reference_file()
        if not ref_path:
            print("no ref path found")
            return

        ref = MeasurementSet.load_from_file(Path(ref_path))
        if not ref:
            print("no file found:", ref_path)
            return

        selected_paths = self.get_selected_files()
        measures = [MeasurementSet.load_from_file(Path(p)) for p in selected_paths]
        measures = [m for m in measures if m is not None]
        if not measures:
            print(f"no measures found in: {selected_paths}")
            return
        measures.sort(key=lambda m: m.date)
        
        analyzer = HistoryAnalyzer(ref, measures)

        dates = [m.date for m in measures]
        str_dates = [d.strftime("%Y-%m-%d") for d in dates]

        # draw each curves in each tab
        draw_gamma_plot(self.gamma_plot.ax, self.gamma_plot.canvas, analyzer, ref, str_dates)
        draw_dmin_plot(self.dmin_ax, self.dmin_canvas, analyzer, ref, str_dates)
        draw_dmax_plot(self.dmax_ax, self.dmax_canvas, analyzer, ref, str_dates)
        draw_d11_plot(self.d11_ax, self.d11_canvas, analyzer, ref, str_dates)
        draw_ld_plot(self.ld_ax, self.ld_canvas, analyzer, ref, str_dates)
        draw_md_plot(self.md_ax, self.md_canvas, analyzer, ref, str_dates)
        draw_hd_plot(self.hd_ax, self.hd_canvas, analyzer, ref, str_dates)
        draw_contrast_plot(self.contrast_ax, self.contrast_canvas, analyzer, ref, str_dates)

        print("Measures:", len(measures))
        print("Channels:", list(ref.curves.keys()))
        print("Dates:", dates)


    def auto_resize_columns(self):
        """Automatically resizes tree widget columns to fit their contents.

        This helps ensure that filenames, dates, and other details are fully visible.
        """
        for col in range(self.tree.columnCount()):
            self.tree.resizeColumnToContents(col)


    def clear_selection(self):
        """
        Uncheck all child items and clear the plot.
        """
        for i in range(self.tree.topLevelItemCount()):
            folder_item = self.tree.topLevelItem(i)
            if folder_item is None: return
            for j in range(folder_item.childCount()):
                child = folder_item.child(j)
                child.setCheckState(0, Qt.Unchecked)