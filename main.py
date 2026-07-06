# main.py

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from PySide6.QtNetwork import QLocalSocket, QLocalServer
from PySide6.QtCore import Qt
from ui.main_window import MainWindow
from constants import UNIQUE_APP_ID, ICON_PATH, BASE_PATH



def is_another_instance_running():
    """Checks if another instance of the application is running.

    Connects to a local server using a unique application ID. If connected,
    sends a "raise" message to bring the existing instance to the foreground.

    Returns:
        bool: True if another instance is running, False otherwise.
    """
    socket = QLocalSocket()
    socket.connectToServer(UNIQUE_APP_ID)
    if socket.waitForConnected(100):
        socket.write(b"raise")
        socket.flush()
        socket.waitForBytesWritten(100)
        socket.disconnectFromServer()
        return True
    return False


def create_single_instance_server(main_window):
    """Creates a server to enforce single instance of the application.
    
    Removes any existing server with the same ID and creates a new one.
    Listens for incoming connections and raises the main window if the 
    "raise" message is received.

    Args:
        main_window (MainWindow): The main window instance to be raised.

    Returns:
        QLocalServer: The server object or None if it failed to listen.
    """
    server = QLocalServer()
    try:
        QLocalServer.removeServer(UNIQUE_APP_ID)
    except:
        pass

    if not server.listen(UNIQUE_APP_ID):
        print("Impossible d'écouter sur le socket.")
        return None

    def on_new_connection():
        socket = server.nextPendingConnection()
        if socket and socket.waitForReadyRead(100):
            message = bytes(socket.readAll().data()).decode()
            if message == "raise":
                main_window.show()
                main_window.raise_()
                main_window.activateWindow()
                main_window.setWindowState(
                    main_window.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive
                )
        socket.disconnectFromServer()

    server.newConnection.connect(on_new_connection)
    return server


def load_stylesheet(app, path: str | Path):
    """Loads a stylesheet from a file and applies it to the application.

    Args:
        app (QApplication): The application instance to style.
        path (str | Path): Path to the stylesheet file.
    """
    stylesheet_path = Path(path)
    if not stylesheet_path.is_absolute():
        stylesheet_path = BASE_PATH / stylesheet_path

    with open(stylesheet_path, "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())


def main():
    """Main entry point for the application.

    Checks for another instance of the app, initializes the application,
    applies the stylesheet, sets up the main window, and ensures single
    instance operation.
    """
    if is_another_instance_running():
        print("App is already running.")
        sys.exit(0)


    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    load_stylesheet(app, "qss/style.qss")

    app.setWindowIcon(QIcon(ICON_PATH))

    main_window = MainWindow()
    main_window.resize(1600, 800)
    main_window.show()

    create_single_instance_server(main_window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
