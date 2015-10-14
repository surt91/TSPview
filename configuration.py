from math import pi, sin, cos
import os
from random import random, randint, choice
from subprocess import call
import gzip

from heuristicgenerators import *
try:
    from lp.CplexTSPSolver import CplexTSPSolver
except ImportError:
    print("can not import LP solver")


class Configuration:
    def __init__(self, x: list = (), y: list = ()):
        self.__cities = tuple(zip(x, y))
        self.__ways = []
        self.__concordeWays = []
        self.__distanceMatrix = self.calcDistanceMatrix()
        self.__heuristic = None
        self.__twoOpt = None
        self.finishedFirst = True
        self.finished2Opt = True
        self.do2Opt = False
        self.doConcorde = False
        self.currentMethod = "Next Neighbor"
        self.currentEnsemble = "square"
        self.currentFile = ""
        self.TSPLIB = []
        self.__n2Opt = 0
        self.sigma = 0
        self.N = 42
        self.maxX = 1
        self.maxY = 1

        self.lp = False
        self.adjMatrix = [0]*self.N**2

    def init(self):
        self.__ways = []
        self.__concordeWays = []
        self.__distanceMatrix = self.calcDistanceMatrix()
        self.initMethod()
        self.finishedFirst = False
        self.finished2Opt = False
        self.__n2Opt = 0
        self.adjMatrix = [0]*self.N**2

        if self.doConcorde:
            self.concorde()

    def restart(self):
        if self.currentEnsemble == "square":
            self.randInit()
        elif self.currentEnsemble == "dce":
            self.DCEInit()
        elif self.currentEnsemble == "tsplib":
            self.currentFile = choice(self.TSPLIB)
            self.TSPLIBInit(self.currentFile)
        else:
            raise

    def randInit(self):
        self.currentEnsemble = "square"
        self.currentFile = ""
        self.maxX = 1
        self.maxY = 1
        self.__cities = tuple((random(), random()) for _ in range(self.N))
        self.init()

    def displace(self, city):
        r = random() * self.sigma
        phi = random() * 2 * pi
        dx = r * cos(phi)
        dy = r * sin(phi)

        return city[0] + dx, city[1] + dy

    def DCEInit(self):
        self.currentEnsemble = "dce"
        self.currentFile = ""
        self.maxX = 1
        self.maxY = 1
        self.__cities = tuple(
            self.displace((0.5 + 0.25 * cos(2 * pi / self.N * i), 0.5 + 0.25 * sin(2 * pi / self.N * i))) for i in
            range(self.N))
        self.init()

    def getCitiesFromTSPLIB(self, file):
        tmp = []
        started = False
        with gzip.open(file, "rt") as f:
            for i in f.readlines():
                if "NODE_COORD_SECTION" in i or "DISPLAY_DATA_SECTION" in i:
                    started = True
                    continue
                if not started:
                    continue
                if "EOF" in i:
                    break

                n, x, y = i.split()
                tmp.append((float(x), float(y)))
        return self.adjust_cities(tmp)

    def adjust_cities(self, cities):
        minX = min(cities)[0]
        maxY = max(cities, key=lambda x: x[1])[1]  # y-axis in Qt and TSPLIB are in different directions
        return tuple((x-minX, maxY-y) for x, y in cities)

    def TSPLIBInit(self, file):
        self.currentEnsemble = "tsplib"
        self.currentFile = file
        self.__cities = self.getCitiesFromTSPLIB(file)
        self.maxX = max(self.__cities)[0]
        self.maxY = max(self.__cities, key=lambda x: x[1])[1]
        self.N = len(self.__cities)
        self.init()

    def calcDistanceMatrix(self):
        return tuple(tuple(dist(i, j) for j in self.__cities) for i in self.__cities)

    def getCities(self):
        return self.__cities

    def getWays(self):
        return tuple(self.__ways)

    def getWayCoordinates(self):
        return tuple((self.__cities[i], self.__cities[j]) for i, j in self.__ways)

    def concordeCoordinates(self):
        return tuple((self.__cities[i], self.__cities[j]) for i, j in self.__concordeWays)

    def valid(self, newWay):
        # raise NotImplementedError
        return True

    def removeWay(self, way):
        try:
            self.__ways.remove(way)
        except ValueError:
            self.__ways.remove((way[1], way[0]))

    def addWay(self, way):
        if self.valid(way):
            self.__ways.append(way)
        else:
            raise

    def initMethod(self):
        self.changeMethod(self.currentMethod)

    def changeMethod(self, method: str):
        if method == "LP & Cutting Planes":
            self.__heuristic = self.cuttingPlanes()
            self.lp = True
            self.do2Opt = False
        else:
            self.lp = False

            if method == "Next Neighbor":
                self.__heuristic = nextNeighborGenerator(self.__cities, self.getWays())
            elif method == "Greedy":
                self.__heuristic = greedyGenerator(self.__cities, self.getWays())
            elif method == "Farthest Insertion":
                self.__heuristic = farInGenerator(self.__cities, self.getWays())
            elif method == "Random":
                self.__heuristic = randomGenerator(self.__cities, self.getWays())
            else:
                self.__heuristic = None

        if not self.currentMethod == method:
            self.currentMethod = method
            self.clearSolution()

    def step(self):
        if not self.__heuristic:
            return True
        if self.lp and not self.finishedFirst:
            try:
                self.adjMatrix = next(self.__heuristic)
            except StopIteration:
                self.finishedFirst = True

        elif not self.finishedFirst:
            try:
                toRemove, toAdd = next(self.__heuristic)
                for i in toRemove:
                    self.removeWay(i)
                for i in toAdd:
                    self.addWay(i)
            except StopIteration:
                self.finishedFirst = True
                self.__twoOpt = twoOptGenerator(tourFromWays(self.__ways), self.__distanceMatrix)
                pass

        elif self.do2Opt and not self.finished2Opt:
            try:
                toRemove, toAdd = next(self.__twoOpt)
                self.__n2Opt += 1
                for i in toRemove:
                    self.removeWay(i)
                for i in toAdd:
                    self.addWay(i)
            except StopIteration:
                self.finished2Opt = True

    def length(self):
        l = 0
        if self.lp:
            c = self.getCities()
            for i in range(self.N):
                for j in range(i):
                    l += self.adjMatrix[i*self.N+j] * dist(c[i], c[j])
        else:
            for a, b in self.getWayCoordinates():
                l += dist(a, b)
        return l

    def optimalLength(self):
        l = 0
        for a, b in self.concordeCoordinates():
            l += dist(a, b)
        return l

    def n2Opt(self):
        return self.__n2Opt

    def setN(self, N):
        if N < 3:
            return
        self.N = N

    def setSigma(self, s):
        self.sigma = s / 2 / len(self.__cities) * pi
        if self.currentEnsemble:
            self.DCEInit()

    def setDo2Opt(self, b):
        self.do2Opt = b

    def setDoConcorde(self, b):
        self.doConcorde = b
        if b:
            self.concorde()

    def clearSolution(self):
        self.__ways = []
        self.adjMatrix = [0]*self.N**2
        self.__n2Opt = 0
        self.finishedFirst = False
        self.finished2Opt = False
        self.initMethod()

    def saveTSPLIB(self, name):
        if self.currentFile:
            with gzip.open(self.currentFile, "rt") as read:
                with open(name, "w") as f:
                    f.write(read.read())
        else:
            tsplib = "COMMENT : Random Euclidian (Schawe)\n"
            tsplib += "TYPE : TSP\n"
            tsplib += "DIMENSION : {}\n".format(len(self.__cities))
            tsplib += "EDGE_WEIGHT_TYPE : EUC_2D\n"
            tsplib += "NODE_COORD_SECTION\n"

            for n, coord in enumerate(self.__cities):
                x, y = coord
                tsplib += "{} {} {}\n".format(n, x * 10 ** 5, y * 10 ** 5)

            with open(name, "w") as f:
                f.write(tsplib)

    def loadTSPLIB(self, name):
        raise NotImplementedError

    def concorde(self):
        if self.__concordeWays:
            # we already have the optimum
            return

        name = "%06d" % randint(0, 10 ** 6)
        self.saveTSPLIB(name)
        call(["./concorde", "-x", "-v", name])
        with open(name + ".sol") as f:
            _ = int(f.readline())
            tour = [int(j) for i in f.readlines() for j in i.split()]
        os.remove(name)
        os.remove(name + ".sol")

        prev = tour[0]
        for i in tour[1:]:
            self.__concordeWays.append((prev, i))
            prev = i
        self.__concordeWays.append((tour[-1], tour[0]))

    def cuttingPlanes(self):
        # flatten distance matrix
        d = [i for j in self.__distanceMatrix for i in j]
        c = CplexTSPSolver(self.N, d)
        adjMatrix = c.nextRelaxation()
        while adjMatrix:
            yield adjMatrix
            adjMatrix = c.nextRelaxation()

    def setTSPLIB(self, tsplib):
        self.TSPLIB = tsplib
