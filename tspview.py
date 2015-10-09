from PyQt5 import QtGui, QtCore, QtWidgets

from configuration import Configuration

# TODO: let tspView inherit from Configuration -> calling super()
class tspView(QtWidgets.QWidget):
    lenChanged = QtCore.pyqtSignal(str)
    twoOptChanged = QtCore.pyqtSignal(str)
    gapChanged = QtCore.pyqtSignal(str)
    optimumChanged = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.conf = Configuration(updateCallback=self.update)
        self.N = 42

        self.timer = QtCore.QTimer()
        self.timestep = 500
        self.timer.timeout.connect(self.step)

        self.restartTimer = QtCore.QTimer()
        self.restartTimer.timeout.connect(self.restart)
        self.restartTimer.setSingleShot(True)

        self.scale = 1
        self.running = False

        self.randInit()

    def restart(self):
        self.randInit()
        self.run(True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.scale = min(self.size().height(), self.size().width())

    def paintEvent(self, event):
        p = QtGui.QPainter()
        p.begin(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        self.drawWays(p)
        self.drawCities(p)
        p.end()

    def drawCities(self, p):
        s = self.N*3/2
        transparent = QtGui.QColor("black")
        transparent.setAlphaF(0.8)

        pen = QtGui.QPen(QtGui.QColor("black"))
        pen.setWidth(1)
        p.setPen(pen)
        p.setBrush(transparent)
        for x, y in self.conf.getCities():
            x *= self.scale
            y *= self.scale
            p.drawEllipse(QtCore.QPoint(x, y), self.scale/s, self.scale/s)

    def drawWays(self, p):
        s = self.scale/self.N/2
        pen = QtGui.QPen(QtGui.QColor("black"))
        pen.setWidth(s)
        c = QtGui.QColor("black")

        if self.conf.doConcorde:
            # draw optimal
            c.setAlphaF(0.2)
            pen.setColor(c)
            p.setPen(pen)
            for a, b in self.conf.concordeCoordinates():
                x1, y1 = a
                x2, y2 = b
                x1 *= self.scale
                x2 *= self.scale
                y1 *= self.scale
                y2 *= self.scale
                p.drawLine(x1, y1, x2, y2)

        # draw heuristic
        c.setAlphaF(1)
        pen.setColor(c)
        p.setPen(pen)
        for a, b in self.conf.getWayCoordinates():
            x1, y1 = a
            x2, y2 = b
            x1 *= self.scale
            x2 *= self.scale
            y1 *= self.scale
            y2 *= self.scale
            p.drawLine(x1, y1, x2, y2)

    def setN(self, N):
        self.N = N

    def step(self):
        if self.conf.finishedFirst and (not self.conf.do2Opt or self.conf.finished2Opt):
            if self.running:
                self.run(False)
                self.restartTimer.start(self.timestep * 15)
            return True
        else:
            self.conf.step()
            self.update()
            self.lenChanged.emit("%.4f" % self.conf.length())
            self.twoOptChanged.emit("%d" % self.conf.n2Opt())
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

    def setTimestep(self, s: float):
        self.timestep = 1000*s
        self.run(False)
        self.run(True)

    def randInit(self):
        self.conf.randomInit(self.N)
        self.updateOptimum()
        self.update()

    def dceInit(self):
        self.conf.DCEInit(self.N)
        self.updateOptimum()
        self.update()

    def setDoConcorde(self, b):
        self.conf.setDoConcorde(b)
        self.updateOptimum()

    def updateOptimum(self):
        if self.conf.doConcorde:
            self.optimumChanged.emit("%.4f" % self.conf.optimalLength())
            gap = "%.2f%%" % ((self.conf.length()/self.conf.optimalLength()-1)*100)
        else:
            self.optimumChanged.emit("n/a")
            gap = "n/a"
        self.gapChanged.emit(gap)
