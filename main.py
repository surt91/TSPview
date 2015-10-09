#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging

from PyQt5 import uic, QtGui, QtCore, QtWidgets


class MainWindow(QtWidgets.QMainWindow):
    logging.info("Loading Ui: main window")
    mainForm, mainClass = uic.loadUiType("mainwidget.ui")

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.ui = self.mainForm()
        self.init_ui()

    def init_ui(self):
        self.ui.setupUi(self)

        # Fenstereigenschaften
        self.setWindowIcon(QtGui.QIcon(os.path.join("img/icon.ico")))

        self.ui.comboMethod.activated.connect(self.changeMethod)

        self.ui.pushButtonStep.clicked.connect(self.ui.view.step)
        self.ui.pushButtonRun.toggled.connect(self.ui.view.run)
        self.ui.pushButtonRandInit.clicked.connect(self.ui.view.randInit)
        self.ui.pushButtonClear.clicked.connect(self.ui.view.conf.clearSolution)
        self.ui.pushButtonFinish.clicked.connect(self.ui.view.finish)

        self.ui.spinBoxN.valueChanged.connect(self.ui.view.setN)
        self.ui.spinBoxDelay.valueChanged.connect(self.ui.view.setTimestep)

        self.ui.checkBox2Opt.toggled.connect(self.ui.view.conf.setDo2Opt)
        self.ui.checkBoxConcorde.toggled.connect(self.ui.view.setDoConcorde)

        self.ui.view.lenChanged.connect(self.ui.labelLen.setText)
        self.ui.view.twoOptChanged.connect(self.ui.label2Opt.setText)
        self.ui.view.optimumChanged.connect(self.ui.labelOpt.setText)
        self.ui.view.gapChanged.connect(self.ui.labelGap.setText)

        if os.path.exists("concorde"):
            self.ui.checkBoxConcorde.setEnabled(True)

    def changeMethod(self):
        self.ui.view.conf.changeMethod(str(self.ui.comboMethod.currentText()))

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = MainWindow()

    mainWindow.show()

    app.exec_()