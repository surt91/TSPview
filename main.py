#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import re

from PyQt5 import uic, QtGui, QtCore, QtWidgets


class MainWindow(QtWidgets.QMainWindow):
    logging.info("Loading Ui: main window")
    mainForm, mainClass = uic.loadUiType("mainwidget.ui")

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.ui = self.mainForm()
        self.init_ui()

        self.testLP()
        self.TSPLIBinstances = {}
        self.populateTSPLIB()

    def init_ui(self):
        self.ui.setupUi(self)

        # Fenstereigenschaften
        self.setWindowIcon(QtGui.QIcon(os.path.join("img/icon.ico")))

        self.ui.comboMethod.activated.connect(self.changeMethod)
        self.ui.comboTSPLIB.activated.connect(self.initTSPLIB)

        self.ui.actionCities.triggered.connect(self.ui.view.changeColorCities)
        self.ui.actionTour.triggered.connect(self.ui.view.changeColorTour)
        self.ui.actionOptimalTour.triggered.connect(self.ui.view.changeColorConcorde)

        self.ui.pushButtonStep.clicked.connect(self.ui.view.step)
        self.ui.pushButtonRun.toggled.connect(self.ui.view.run)
        self.ui.pushButtonRandInit.clicked.connect(self.ui.view.randInit)
        self.ui.pushButtonDCE.clicked.connect(self.ui.view.DCEInit)
        self.ui.pushButtonClear.clicked.connect(self.ui.view.clearSolution)
        self.ui.pushButtonFinish.clicked.connect(self.ui.view.finish)

        self.ui.spinBoxN.valueChanged.connect(self.ui.view.setN)
        self.ui.spinBoxDelay.valueChanged.connect(self.ui.view.setTimestep)
        self.ui.spinBoxSigma.valueChanged.connect(self.ui.view.setSigma)

        self.ui.checkBox2Opt.toggled.connect(self.ui.view.setDo2Opt)
        self.ui.checkBoxConcorde.toggled.connect(self.ui.view.setDoConcorde)
        self.ui.checkBoxEdgeweight.toggled.connect(self.ui.view.setShowValues)

        self.ui.view.lenChanged.connect(self.ui.labelLen.setText)
        self.ui.view.twoOptChanged.connect(self.ui.label2Opt.setText)
        self.ui.view.optimumChanged.connect(self.ui.labelOpt.setText)
        self.ui.view.gapChanged.connect(self.ui.labelGap.setText)
        self.ui.view.twoOptAvailable.connect(self.ui.checkBox2Opt.setEnabled)
        self.ui.view.twoOptAvailable.connect(lambda x: self.ui.checkBoxEdgeweight.setEnabled(not x))
        self.ui.view.TSPLIBChange.connect(lambda x: self.ui.comboTSPLIB.setCurrentIndex(self.TSPLIBinstances[x]))
        self.ui.view.TSPLIBChange.connect(lambda x: self.ui.spinBoxN.setValue(int(re.sub("[^0-9]", "", x))))

        if os.path.exists("concorde"):
            self.ui.checkBoxConcorde.setEnabled(True)

    def changeMethod(self):
        self.ui.view.changeMethod(str(self.ui.comboMethod.currentText()))

    def getTSPLIB(self):
        from urllib import request
        request.urlretrieve(
            "http://www.iwr.uni-heidelberg.de/groups/comopt/software/TSPLIB95/tsp/ALL_tsp.tar.gz", "ALL_tsp.tar.gz")

        os.makedirs("TSPLIB", exist_ok=True)
        import tarfile
        tfile = tarfile.open("ALL_tsp.tar.gz", 'r:gz')
        tfile.extractall('TSPLIB')
        os.remove("ALL_tsp.tar.gz")

    def populateTSPLIB(self):
        import gzip

        doable = []
        # try:
        if not os.path.exists("TSPLIB"):
            self.getTSPLIB()
        # except:
        #     return

        for name in os.listdir("TSPLIB"):
            euclidean = False
            nodecoords = False
            displayable = False
            # do only take instances smaller than 500
            if ".tsp.gz" in name and int(re.sub("[^0-9]", "", name)) < 500:
                with gzip.open(os.path.join("TSPLIB", name), "rt") as f:
                    for i in f.readlines():
                        if "EUC_2D" in i:
                            euclidean = True
                        if "NODE_COORD_SECTION" in i:
                            nodecoords = True
                            break
                        if "DISPLAY_DATA_SECTION" in i:
                            displayable = True
                            break
                if euclidean and nodecoords or displayable:  # make all displayable available, though their solutions will deviate
                    doable.append(name)

        if doable:
            self.ui.comboTSPLIB.setEnabled(True)

        doable.sort(key=lambda x: int(re.sub("[^0-9]", "", x)))
        for i in doable:
            i = i.replace(".tsp.gz", "")
            self.ui.comboTSPLIB.addItem(i)
        self.TSPLIBinstances = {j: i for i, j in enumerate(doable)}

        self.ui.view.setTSPLIB([os.path.join("TSPLIB", i) for i in doable])

    def initTSPLIB(self):
        self.ui.view.TSPLIBInit(os.path.join("TSPLIB", self.ui.comboTSPLIB.currentText()+".tsp.gz"))

    def testLP(self):
        try:
            from lp.CplexTSPSolver import CplexTSPSolver
        except ImportError:
            self.ui.comboMethod.removeItem(4)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = MainWindow()

    mainWindow.show()

    app.exec_()
