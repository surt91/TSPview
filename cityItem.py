from PyQt5 import QtCore, QtWidgets


class CityItem(QtWidgets.QGraphicsEllipseItem):
    clicked = QtCore.pyqtSignal(int)

    def __init__(self, x, y, ps, idx, callback):
        super().__init__(x - ps / 2, y - ps / 2, ps, ps)
        self.idx = idx
        self.callback = callback

    def mousePressEvent(self, event):
        self.callback(self.idx)
