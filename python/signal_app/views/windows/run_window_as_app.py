import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QDesktopWidget

def create_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

def run_window_as_app(win: type[QWidget] | QWidget, title="Untitled Window", size=(1000,600)):

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    main_win = QMainWindow()
    main_win.setWindowTitle(title)
    if isinstance(win, type):
        widget = win()
    else:
        widget = win

    main_win.setCentralWidget(widget)

    main_win.resize(*size)

    # center application
    qt_rectangle = main_win.frameGeometry()
    center_screen = QDesktopWidget().availableGeometry().center()
    qt_rectangle.moveCenter(center_screen)
    main_win.move(qt_rectangle.topLeft())

    main_win.show()

    app._main_win = main_win
    sys.exit(app.exec_())

if __name__ == "__main__":
    app = create_app()
    run_window_as_app(win=QWidget(), title="Untitled Window")