import os, platform, pathlib
from PyQt5 import QtCore, QtWidgets, QtGui
from pathlib import Path

QtCore.QCoreApplication.setOrganizationName('moonwalker')
QtCore.QCoreApplication.setOrganizationDomain('moonwalker.me')
QtCore.QCoreApplication.setApplicationName('WallHeaven')

setting = QtCore.QSettings('./setting.ini', QtCore.QSettings.IniFormat)


class SettingDialog(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setting_tabs = QtWidgets.QTabWidget()

        self.download_setting_tab = QtWidgets.QWidget()
        self.change_download_path_button = QtWidgets.QPushButton()
        self.download_path_edit = QtWidgets.QLineEdit()
        if not setting.value('download_path'):
            self.download_path = str(Path(pathlib.PurePath(pathlib.Path.home(), 'Pictures', 'WallHaven')))
        else:
            self.download_path = setting.value('download_path')
        self.init_file_setting_tab()

        self.setting_tabs.addTab(self.download_setting_tab, '下载设置')
        self.setLayout(QtWidgets.QVBoxLayout(self))
        self.layout().addWidget(self.setting_tabs)
        self.init_dialog()

    def init_dialog(self):
        self.setModal(True)
        self.resize(600, 300)
        self.hide()

    def init_file_setting_tab(self):
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
        self.download_setting_tab.setLayout(QtWidgets.QVBoxLayout())
        download_path_setting = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel('壁纸下载路径:')
        self.download_path_edit.setReadOnly(True)
        self.download_path_edit.setText(str(self.download_path))
        self.change_download_path_button.setText('更改')
        self.change_download_path_button.clicked.connect(self.change_download_path_slot)
        download_path_setting.addWidget(label)
        download_path_setting.addWidget(self.download_path_edit)
        download_path_setting.addWidget(self.change_download_path_button)
        self.download_setting_tab.layout().addLayout(download_path_setting)

    @QtCore.pyqtSlot()
    def change_download_path_slot(self):
        new_path = QtWidgets.QFileDialog.getExistingDirectory(caption='选择文件夹',
                                                              directory=str(self.download_path))
        if new_path:
            self.download_path = new_path
            self.download_path_edit.setText(self.download_path)
            setting.setValue('download_path', self.download_path)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    sd = SettingDialog()
    sd.show()
    app.exec()