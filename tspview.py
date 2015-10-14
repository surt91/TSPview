from math import sqrt

from PyQt5 import QtGui, QtCore, QtWidgets

from configuration import Configuration
from cityItem import CityItem


class tspView(QtWidgets.QGraphicsView, Configuration):
    lenChanged = QtCore.pyqtSignal(str)
    twoOptChanged = QtCore.pyqtSignal(str)
    gapChanged = QtCore.pyqtSignal(str)
    optimumChanged = QtCore.pyqtSignal(str)
    twoOptAvailable = QtCore.pyqtSignal(bool)
    TSPLIBChange = QtCore.pyqtSignal(str)
    zoomChange = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.scene = QtWidgets.QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        #self.setDragMode(self.ScrollHandDrag)
        self.setResizeAnchor(self.AnchorUnderMouse)
        self.setTransformationAnchor(self.AnchorUnderMouse)
        self.cityItems = []
        self.edgeItems = []
        self.textItems = []
        self.edgeConcordeItems = []

        self.timer = QtCore.QTimer()
        self.timestep = 500
        self.timer.timeout.connect(self.step)

        self.restartTimer = QtCore.QTimer()
        self.restartTimer.timeout.connect(self.restart)
        self.restartTimer.setSingleShot(True)

        self.citySelected = False
        self.manualTour = []
        self.currentLine = None
        self.cursorPosition = None

        self.running = False
        self.showValues = False

        self.initScale = self.transform()
        self.zoomlevel = 0
        self.mat = None

        self.cityPen = QtGui.QPen(QtGui.QColor("black"))
        self.cityPen.setWidth(1)
        self.tourPen = QtGui.QPen(QtGui.QColor("black"))
        self.tourPenIncomplete = QtGui.QPen(QtGui.QColor("black"))
        self.tourPenIncomplete.setStyle(QtCore.Qt.DotLine)

        c = QtGui.QColor("black")
        c.setAlphaF(0.2)
        self.concordePen = QtGui.QPen(c)

        c.setAlphaF(0.8)
        self.cityBrush = QtGui.QBrush(c)
        self.pointsize = 1

        self.updatePen()

        self.randInit()

    def wheelEvent(self, e):
        if e.angleDelta().y() > 0:
            self.zoomlevel += 5
        else:
            self.zoomlevel -= 5
        self.zoom(self.zoomlevel)
        e.accept()

    def zoom(self, z):
        scale = pow(2, z / 100.0)
        self.mat = QtGui.QTransform(self.initScale)
        self.mat.scale(scale, scale)
        self.setTransform(self.mat)
        self.zoomChange.emit(z)

    def fit(self):
        self.zoomlevel = 0
        self.zoom(0)
        self.fitInView(0, 0, 1, 1, QtCore.Qt.KeepAspectRatio)

    def updatePen(self):
        s = 1 / sqrt(self.N) / 10

        self.concordePen.setWidth(s/2)
        self.cityPen.setWidth(s/2)
        self.tourPen.setWidth(s/2)
        self.tourPenIncomplete.setWidth(s/2)
        self.pointsize = s

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
        self.updatePen()

    def drawWays(self):
        # draw adjMatrix or ways?
        if self.lp:
            c = self.getCities()
            for i in range(self.N):
                for j in range(i):
                    w = self.adjMatrix[i*self.N+j]
                    if w > 10e-5:
                        x1, y1 = c[i]
                        x2, y2 = c[j]
                        item = QtWidgets.QGraphicsLineItem(x1, y1, x2, y2)
                        if w < 1-10e-5:
                            item.setPen(self.tourPenIncomplete)
                        else:
                            item.setPen(self.tourPen)
                        self.edgeItems.append(item)
                        self.scene.addItem(item)

                        if w != 1:
                            text = QtWidgets.QGraphicsTextItem("%.2f" % w)
                            text.setPos((x1+x2)/2, (y1+y2)/2)
                            text.setScale(2/1000)
                            text.setVisible(self.showValues)
                            self.textItems.append(text)
                            self.scene.addItem(text)

        else:
            # draw heuristic
            for a, b in self.getWayCoordinates():
                x1, y1 = a
                x2, y2 = b
                item = QtWidgets.QGraphicsLineItem(x1, y1, x2, y2)
                item.setPen(self.tourPen)
                self.edgeItems.append(item)
                self.scene.addItem(item)

    def step(self):
        if self.finishedFirst and (not self.do2Opt or self.finished2Opt):
            if self.running:
                self.run(False)
                # self.restartTimer.start(self.timestep * 15)
                self.restartTimer.start(10 * 1000)
            return True
        else:
            if super().step():
                return True

            self.updateWays()
            return False

    def updateWays(self):
        for e in self.edgeItems:
            self.scene.removeItem(e)
        self.edgeItems.clear()
        for t in self.textItems:
            self.scene.removeItem(t)
        self.textItems.clear()
        self.drawWays()

        self.update()
        self.lenChanged.emit("%.4f" % self.length())
        self.twoOptChanged.emit("%d" % self.n2Opt())
        self.updateOptimum()

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

        for e in self.edgeItems:
            self.scene.removeItem(e)
        self.edgeItems.clear()
        for t in self.textItems:
            self.scene.removeItem(t)
        self.textItems.clear()
        self.citySelected = None
        self.update()

    def init(self):
        super().init()
        self.rescale()
        # add all cities
        self.cityItems.clear()
        self.clearSolution()
        self.scene.clear()

        for n, point in enumerate(self.getCities()):
            x, y = point
            item = CityItem(x, y, self.pointsize, n, self.cityClicked)
            item.setPen(self.cityPen)
            item.setBrush(self.cityBrush)
            self.cityItems.append(item)
            self.scene.addItem(item)

        self.fit()
        self.initScale = self.transform()

        self.update()

    def mouseMoveEvent(self, e):
        self.cursorPosition = self.mapToScene(e.pos())
        if self.currentLine and not self.finishedFirst:
            c = self.getCities()
            self.currentLine.setLine(QtCore.QLineF(QtCore.QPointF(*c[self.citySelected]), self.cursorPosition))

    def cityClicked(self, idx):
        if self.currentMethod != "Manual" or self.finishedFirst:
            return

        if self.citySelected is None:
            c = self.getCities()
            self.currentLine = QtWidgets.QGraphicsLineItem(QtCore.QLineF(QtCore.QPointF(*c[idx]), self.cursorPosition))
            self.currentLine.setPen(self.tourPen)
            self.scene.addItem(self.currentLine)
            self.manualTour = [idx]
            self.citySelected = idx
        else:
            edge = (self.citySelected, idx)
            if idx not in self.manualTour:
                self.manualTour.append(idx)
                self.addWay(edge)
                # close to the last city
                if len(self.manualTour) == self.N:
                    self.addWay((self.manualTour[-1], self.manualTour[0]))
                    self.finishedFirst = True
                self.updateWays()

                self.citySelected = idx

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

        if b:
            # draw optimal
            for a, b in self.concordeCoordinates():
                x1, y1 = a
                x2, y2 = b
                item = QtWidgets.QGraphicsLineItem(x1, y1, x2, y2)
                item.setPen(self.concordePen)
                self.edgeConcordeItems.append(item)
                self.scene.addItem(item)
        else:
            for e in self.edgeConcordeItems:
                self.scene.removeItem(e)
            self.edgeConcordeItems.clear()

        self.update()

    def setShowValues(self, b):
        self.showValues = b
        for i in self.textItems:
            i.setVisible(b)
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