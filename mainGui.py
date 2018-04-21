import sys
from PyQt5.QtWidgets import QApplication
from MainWindow import MainWindow


def start():
    app = QApplication(sys.argv)
    gui = MainWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    start()
