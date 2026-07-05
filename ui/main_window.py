# ui/main_window.py


import os
import sys
import subprocess
import warnings

from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QTabBar, QFileDialog,
)

from ui.densito_ui import CurveWidget
from ui.communications_ui import CommunicationWidget
from ui.history_ui import HistoryWidget
from utils.md_viewer import MarkdownWebViewer

from lib.communications import DensitometerReader
from constants import MEASURES_PATH, ICON_PATH, DOC_MANUAL_PATH, DOC_XRITEMANUAL_PATH

class MainWindow(QMainWindow):
    def __init__(self):
        """Initializes the main window with menus and tabs.

        Sets up the user interface, including the menu bar with various
        options and interactive tabs, such as communication and history.
        """
        super().__init__()

        self.raise_()
        self.activateWindow()
        self.setWindowIcon(QIcon(ICON_PATH))

        menu_bar = self.menuBar()

        # Configures the "File" menu.
        file_menu = menu_bar.addMenu("Fichier")
        open_action = QAction("Ouvrir", self)
        file_menu.addAction(open_action)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.import_meas_file)
        # File > save
        save_action = QAction("Sauvegarder", self)
        file_menu.addAction(save_action)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.export_meas_file)
        # File > open
        open_meas_folder_action = QAction("Ouvrir le dossier des mesures", self)
        file_menu.addAction(open_meas_folder_action)
        open_meas_folder_action.setShortcut("Ctrl+alt+O")
        open_meas_folder_action.triggered.connect(lambda: self.open_folder(MEASURES_PATH))
        file_menu.addSeparator()
        # File > quit
        quit_action = QAction("Quitter", self)
        file_menu.addAction(quit_action)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)

        # Configures the "Edit" menu.
        edit_menu = menu_bar.addMenu("Édition")
        clear_action = QAction("Réinitialiser", self)
        edit_menu.addAction(clear_action)
        clear_action.setShortcut("Ctrl+R")
        clear_action.triggered.connect(self.clear_measures)

        # Configures the "Help" menu.
        help_menu = menu_bar.addMenu("Aide")
        xrite_doc_action = help_menu.addAction("x-rite Densitometer Operation Manual")
        densitometer_doc_path = os.path.join(os.path.dirname(__file__), "../docs/310-42_310_Densitometer_Operation_Manual_en.pdf")
        xrite_doc_action.triggered.connect(lambda: self.open_pdf(DOC_XRITEMANUAL_PATH))

        manual_action = help_menu.addAction("Manuel utilisateur")
        doc_path = os.path.join(os.path.dirname(__file__), "../docs/X-Rite 310 App - user manual.md")
        manual_action.triggered.connect(lambda: MarkdownWebViewer(DOC_MANUAL_PATH).exec())

        about_action = help_menu.addAction("À propos")
        about_action.triggered.connect(self.show_about_dialog)

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

        # communication tab
        self.com_widget = CommunicationWidget(reader=self.reader)
        self.tabs.addTab(self.com_widget, "Communication")
        self.tabs.tabBar().setTabButton(0, QTabBar.ButtonPosition.RightSide, None)

        # historic tab
        self.file_tab = HistoryWidget()
        self.tabs.addTab(self.file_tab, "Historic")
        self.tabs.tabBar().setTabButton(1, QTabBar.ButtonPosition.RightSide, None)

        #sensito tab
        self.plus_tab = QWidget()
        self.tabs.addTab(self.plus_tab, "+")
        self.tabs.tabBar().setTabButton(self.tabs.indexOf(self.plus_tab), QTabBar.ButtonPosition.RightSide, None)

        self.add_new_curve_tab("Sensito")
        self.update_active_receiver()

        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.handle_tab_change)

        self.tabs.setCurrentWidget(self.com_widget)


    def add_new_curve_tab(self, title="Sensito"):
        """Adds a new curve tab to the tab widget.

        Args:
            title (str): Title for the new tab.
        """
        widget = CurveWidget(reader=self.reader, tabs=self.tabs)
        self.curve_widgets.append(widget)

        index = self.tabs.count() - 1  # Insert before "+"
        self.tabs.insertTab(index, widget, title)
        self.tabs.setCurrentIndex(index)

        self.update_active_receiver()


    def close_tab(self, index):
        """Closes a specified tab.

        Args:
            index (int): Index of the tab to close.
        """
        widget = self.tabs.widget(index)
        if not isinstance(widget, CurveWidget):
            return

        if widget in self.curve_widgets:
            self.curve_widgets.remove(widget)

        # Switch to previous tab if possible
        if self.tabs.count() > 1:
            new_index = index - 1 if index > 0 else 0
            self.tabs.setCurrentIndex(new_index)

        self.tabs.removeTab(index)
        widget.deleteLater()
        self.update_active_receiver()


    def handle_tab_change(self, index):
        """Handles changes to the current tab.

        Args:
            index (int): Index of the newly activated tab.
        """
        current_widget = self.tabs.widget(index)
        if current_widget == self.plus_tab:
            self.add_new_curve_tab()
        else:
            self.update_active_receiver()


    def update_active_receiver(self):
        """Updates the active receiver for curve widget measurements.

        Disconnects previous curve widgets and connects the current one to
        receive measurements.
        """
        # Disconnect all current connections
        for widget in self.curve_widgets:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", RuntimeWarning)
                    self.reader.parsed_measurement.disconnect(widget.receive_measurements)
            except (TypeError, RuntimeError):
                pass

        # Connect the current active widget
        current = self.tabs.currentWidget()
        if isinstance(current, CurveWidget):
            self.reader.parsed_measurement.connect(current.receive_measurements)


    def show_about_dialog(self):
        """Displays the 'About' dialog with application information."""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(self, "À propos", "Densitomètre X-Rite 310\nVersion 1.0")


    def open_pdf(self, filepath):
        """Opens a PDF file with the default system viewer.

        Args:
            filepath (str): Path to the PDF file to open.
        """
        if sys.platform.startswith('darwin'):
            subprocess.call(['open', filepath])  # macOS
        elif os.name == 'nt':
            os.startfile(filepath)  # Windows
        elif os.name == 'posix':
            subprocess.call(['xdg-open', filepath])  # Linux

    def import_meas_file(self):
        """Imports a measurement file into the current curve widget."""
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
        """Exports the measurement data from the current curve widget to a file."""
        current_widget = self.tabs.currentWidget()
        if not isinstance(current_widget, CurveWidget):
            return
        current_widget.export_meas_file()


    def clear_measures(self):
        """Clears the measurement inputs in the current curve widget."""
        current_widget = self.tabs.currentWidget()
        if isinstance(current_widget, CurveWidget):
            current_widget.clear_inputs()
        elif isinstance(current_widget, HistoryWidget):
            current_widget.clear_selection()


    def open_folder(self, path: str):
        """Opens a folder in the system's file explorer.

        Args:
            path (str): Path to the folder to open.
        """
        if sys.platform.startswith("darwin"):  # macOS
            subprocess.run(["open", path])
        elif os.name == "nt":  # Windows
            os.startfile(path)
        elif os.name == "posix":  # Linux/Unix
            subprocess.run(["xdg-open", path])