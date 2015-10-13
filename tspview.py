from math import sqrt

from PyQt5 import QtGui, QtCore, QtWidgets

from configuration import Configuration


class tspView(QtWidgets.QWidget, Configuration):
    lenChanged = QtCore.pyqtSignal(str)
    twoOptChanged = QtCore.pyqtSignal(str)
    gapChanged = QtCore.pyqtSignal(str)
    optimumChanged = QtCore.pyqtSignal(str)
    twoOptAvailable = QtCore.pyqtSignal(bool)
    TSPLIBChange = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)


        self.timer = QtCore.QTimer()
        self.timestep = 500
        self.timer.timeout.connect(self.step)

        self.restartTimer = QtCore.QTimer()
        self.restartTimer.timeout.connect(self.restart)
        self.restartTimer.setSingleShot(True)

        self.scale = 1
        self.correction = 1
        self.running = False
        self.showValues = False

        self.cityPen = QtGui.QPen(QtGui.QColor("black"))
        self.cityPen.setWidth(1)
        self.tourPen = QtGui.QPen(QtGui.QColor("black"))
        self.tourPenIncomplete = QtGui.QPen(QtGui.QColor("black"))
        self.tourPenIncomplete.setStyle(QtCore.Qt.DotLine)
        self.updatePen()
        c = QtGui.QColor("black")
        c.setAlphaF(0.2)
        self.concordePen = QtGui.QPen(c)

        c.setAlphaF(0.8)
        self.cityBrush = QtGui.QBrush(c)
        self.pointsize = 1

        self.randInit()

    def updatePen(self):
        self.tourPen.setWidth(self.scale * self.correction / sqrt(self.N) / 30)
        self.tourPenIncomplete.setWidth(self.scale * self.correction / sqrt(self.N) / 30)

        s = 1 / sqrt(self.N) / 15
        self.pointsize = self.scale * self.correction * s

    def getColorFromDialog(self, initial=QtCore.Qt.black):
        return QtWidgets.QColorDialog.getColor(initial, self, "Pick a Color", QtWidgets.QColorDialog.ShowAlphaChannel)

    def changeColorCities(self):
        color = self.getColorFromDialog(self.cityPen.color())
        self.cityPen.setColor(color)
        self.cityBrush.setColor(color)
        self.update()

    def changeColorTour(self):
        color = self.getColorFromDialog(self.tourPen.color())
        self.tourPen.setColor(color)
        self.tourPenIncomplete.setColor(color)
        self.update()

    def changeColorConcorde(self):
        self.concordePen.setColor(self.getColorFromDialog(self.concordePen.color()))
        self.update()

    def changeMethod(self, method: str):
        super().changeMethod(method)
        self.twoOptAvailable.emit(not self.lp)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.rescale()

    def rescale(self):
        self.scale = min(self.size().height()/self.maxY, self.size().width()/self.maxX)
        self.correction = max(self.maxX, self.maxY)

        self.updatePen()

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QtGui.QPainter()
        p.begin(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.eraseRect(0, 0, self.scale*self.correction, self.scale*self.correction)
        self.drawWays(p)
        self.drawCities(p)
        p.end()

    def addMargin(self, x):
        return (x + 0.05*self.correction) * self.scale * 0.9

    def drawCities(self, p):
        p.setPen(self.cityPen)
        p.setBrush(self.cityBrush)
        for x, y in self.getCities():
            x = self.addMargin(x)
            y = self.addMargin(y)
            p.drawEllipse(QtCore.QPoint(x, y), self.pointsize, self.pointsize)

    def drawWays(self, p):
        if self.doConcorde:
            # draw optimal
            p.setPen(self.concordePen)
            for a, b in self.concordeCoordinates():
                self.drawLine(p, a, b)

        p.setPen(self.tourPen)
        # draw adjMatrix or ways?
        if self.lp:
            c = self.getCities()
            for i in range(self.N):
                for j in range(i):
                    if self.adjMatrix[i*self.N+j] > 10e-5:
                        if self.adjMatrix[i*self.N+j] < 1-10e-5:
                            p.setPen(self.tourPenIncomplete)
                        else:
                            p.setPen(self.tourPen)
                        self.drawLine(p, c[i], c[j], self.adjMatrix[i*self.N+j])

        else:
            # draw heuristic
            for a, b in self.getWayCoordinates():
                self.drawLine(p, a, b)

    def drawLine(self, p, a, b, w=1.0):
        x1, y1 = a
        x2, y2 = b
        x1 = self.addMargin(x1)
        x2 = self.addMargin(x2)
        y1 = self.addMargin(y1)
        y2 = self.addMargin(y2)
        p.drawLine(x1, y1, x2, y2)
        if w != 1 and self.showValues:
            p.drawText((x1+x2)//2, (y1+y2)//2, "%.2f" % w)

    def step(self):
        if self.finishedFirst and (not self.do2Opt or self.finished2Opt):
            if self.running:
                self.run(False)
                # self.restartTimer.start(self.timestep * 15)
                self.restartTimer.start(10 * 1000)
            return True
        else:
            super().step()
            self.update()
            self.lenChanged.emit("%.4f" % self.length())
            self.twoOptChanged.emit("%d" % self.n2Opt())
            self.updateOptimum()
            return False

    def finish(self):
        while not self.step():
            self.repaint()

    def run(self, b=True):
        self.running = b
        if b:
            self.timer.start(self.timestep)
        else:
            self.timer.stop()
            self.restartTimer.stop()

    def restart(self):
        super().restart()
        self.run(True)

    def setTimestep(self, s: float):
        self.timestep = 1000 * s
        self.run(False)
        self.run(True)

    def clearSolution(self):
        super().clearSolution()
        self.update()

    def init(self):
        super().init()
        self.rescale()

    def randInit(self):
        super().randInit()
        self.updateOptimum()
        self.update()

    def DCEInit(self):
        super().DCEInit()
        self.updateOptimum()
        self.update()

    def TSPLIBInit(self, file):
        super().TSPLIBInit(file)
        self.TSPLIBChange.emit(self.currentFile.replace("TSPLIB/", ""))
        self.updateOptimum()
        self.update()

    def setDoConcorde(self, b):
        super().setDoConcorde(b)
        self.updateOptimum()
        self.update()

    def setShowValues(self, b):
        self.showValues = b
        self.update()

    def updateOptimum(self):
        if self.doConcorde:
            self.optimumChanged.emit("%.4f" % self.optimalLength())
            gap = "%.2f%%" % ((self.length() / self.optimalLength() - 1) * 100)
        else:
            self.optimumChanged.emit("n/a")
            gap = "n/a"
        self.gapChanged.emit(gap)

    def saveSVG(self, name):
        pass
        #img = QtGui.QImage(self.size(), QtGui.QImage.)
        #p = QtGui.QPainter(img)
        #self.render(p)

        #img.save(name)