import os
import sys
import subprocess

from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QTabBar, QFileDialog,
)
import warnings
from ui.curve_ui import CurveWidget
from ui.communications_ui import CommunicationWidget
from lib.communications import DensitometerReader
from constants import MEASURES_PATH, ICON_PATH


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.raise_()
        self.activateWindow()

        self.setWindowIcon(QIcon(ICON_PATH))

        # top menu bar
        menu_bar = self.menuBar()

        # File
        file_menu = menu_bar.addMenu("Fichier")
        # File > Open
        open_action = QAction("Ouvrir", self)
        file_menu.addAction(open_action)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.import_meas_file)
        # File > Save
        save_action = QAction("Sauvegarder", self)
        file_menu.addAction(save_action)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.export_meas_file)
        # File > Open meas folder
        open_meas_folder_action = QAction("Ouvrir le dossier des mesures", self)
        file_menu.addAction(open_meas_folder_action)
        open_meas_folder_action.setShortcut("Ctrl+alt+O")
        open_meas_folder_action.triggered.connect(lambda: self.open_folder(MEASURES_PATH))
        # File > Separator
        file_menu.addSeparator()
        # File > Quit
        quit_action = QAction("Quitter", self)
        file_menu.addAction(quit_action)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        

        # Edit
        edit_menu = menu_bar.addMenu("Édition")        
        # Edit > Clear
        clear_action = QAction("Réinitialiser", self)
        edit_menu.addAction(clear_action)
        clear_action.setShortcut("Ctrl+R")
        clear_action.triggered.connect(self.clear_measures)
        # # Edit > Undo
        # undo_action = QAction("Annuler", self)
        # edit_menu.addAction(undo_action)
        # undo_action.setShortcut("Ctrl+Z")
        # undo_action.triggered.connect(self.undo_measures)
        # # Edit > Redo
        # redo_action = QAction("Rétablir", self)
        # edit_menu.addAction(redo_action)
        # redo_action.setShortcut("Ctrl+Y")
        # redo_action.triggered.connect(self.redo_measures)

        # Help
        help_menu = menu_bar.addMenu("Aide")
        xrite_doc_action = help_menu.addAction("x-rite Densitometer Operation Manual")
        about_action = help_menu.addAction("À propos")

        about_action.triggered.connect(self.show_about_dialog)
        doc_path = os.path.join(os.path.dirname(__file__), "../docs/310-42_310_Densitometer_Operation_Manual_en.pdf")
        xrite_doc_action.triggered.connect(lambda: self.open_pdf(doc_path))

        self.reader = DensitometerReader()
        self.setWindowTitle("X-Rite 310 - Densitomètre")
        self.setMinimumSize(1200, 600)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)

        self.curve_widgets = []

        layout = QVBoxLayout()
        container = QWidget()
        container.setLayout(layout)
        layout.addWidget(self.tabs)
        self.setCentralWidget(container)

        # Communication tab (fixed, non-closable)
        self.com_widget = CommunicationWidget(reader=self.reader)
        self.tabs.addTab(self.com_widget, "Communication")
        self.tabs.tabBar().setTabButton(0, QTabBar.ButtonPosition.RightSide, None)

        # "+" tab at the end
        self.plus_tab = QWidget()
        self.tabs.addTab(self.plus_tab, "+")
        self.tabs.tabBar().setTabButton(self.tabs.indexOf(self.plus_tab), QTabBar.ButtonPosition.RightSide, None)

        # First curve tab
        self.add_new_curve_tab("Sensito")

        # Activate initial tab listener
        self.update_active_receiver()

        # DensitometerReader connection handler
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.handle_tab_change)

        # set COmmunications as default opened tab
        self.tabs.setCurrentWidget(self.com_widget)


# Tab handlers
    def add_new_curve_tab(self, title="Sensito"):
        widget = CurveWidget(reader=self.reader, tabs=self.tabs)
        self.curve_widgets.append(widget)

        index = self.tabs.count() - 1  # Insert before "+"
        self.tabs.insertTab(index, widget, title)
        self.tabs.setCurrentIndex(index)

        self.update_active_receiver()


    def close_tab(self, index):
        widget = self.tabs.widget(index)
        if not isinstance(widget, CurveWidget):
            return

        if widget in self.curve_widgets:
            self.curve_widgets.remove(widget)

        # Force active previous tab
        if self.tabs.count() > 1:
            new_index = index - 1 if index > 0 else 0
            self.tabs.setCurrentIndex(new_index)

        self.tabs.removeTab(index)
        widget.deleteLater()
        self.update_active_receiver()


    def handle_tab_change(self, index):
        current_widget = self.tabs.widget(index)
        if current_widget == self.plus_tab:
            self.add_new_curve_tab()
        else:
            self.update_active_receiver()


    def update_active_receiver(self):
        # Disconnect all
        for widget in self.curve_widgets:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", RuntimeWarning)
                    self.reader.parsed_measurement.disconnect(widget.receive_measurements)
            except (TypeError, RuntimeError):
                pass

        # Connect current one
        current = self.tabs.currentWidget()
        if isinstance(current, CurveWidget):
            self.reader.parsed_measurement.connect(current.receive_measurements)


# top menu actions
    def show_about_dialog(self):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(self, "À propos", "Densitomètre X-Rite 310\nVersion 1.0")


    def open_pdf(self, filepath):
        if sys.platform.startswith('darwin'):
            subprocess.call(['open', filepath])  # macOS
        elif os.name == 'nt':
            os.startfile(filepath)  # Windows
        elif os.name == 'posix':
            subprocess.call(['xdg-open', filepath])  # Linux


    def import_meas_file(self):
        current_widget = self.tabs.currentWidget()
        if not isinstance(current_widget, CurveWidget):
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importer un fichier JSON",
            MEASURES_PATH,
            "Fichiers JSON (*.json)"
        )

        if file_path:
            current_widget.import_selected_file(
                inputs=current_widget.meas_inputs,
                file=file_path,
                toclear="meas"
            )

    def export_meas_file(self):
        current_widget = self.tabs.currentWidget()
        if not isinstance(current_widget, CurveWidget):
            return

        current_widget.export_meas_file()

    def clear_measures(self):
        current_widget = self.tabs.currentWidget()
        if not isinstance(current_widget, CurveWidget):
            return

        current_widget.clear_inputs()

    def open_folder(self, path: str):
        if sys.platform.startswith("darwin"):  # macOS
            subprocess.run(["open", path])
        elif os.name == "nt":  # Windows
            os.startfile(path)
        elif os.name == "posix":  # Linux/Unix
            subprocess.run(["xdg-open", path])