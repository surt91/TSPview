from math import sqrt, pi, sin, cos
import os
from random import random, randint, shuffle
from subprocess import call
import heapq

from unionfind import UnionFindWrapper


def dist(a: tuple, b: tuple):
    return sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def argmax(iterable):
    return max(enumerate(iterable), key=lambda x: x[1])


def argmin(iterable):
    return min(enumerate(iterable), key=lambda x: x[1])


def tourFromWays(ways_in):
    ways = list(ways_in)
    tour = []
    start = ways.pop()
    tour.append(start[0])
    tour.append(start[1])
    while ways:
        for n in range(len(ways)):
            i, j = ways[n]
            if i == tour[-1]:
                tour.append(j)
                ways.pop(n)
                break
            elif j == tour[-1]:
                tour.append(i)
                ways.pop(n)
                break
    return tour


def nextNeighborFactory(cities, ways):
    if len(cities) <= 1:
        raise ValueError

    candidates = list(range(1, len(cities)))
    tour = [0]

    while candidates:
        nextIdx = candidates[argmin(dist(cities[i], cities[tour[-1]]) for i in candidates)[0]]

        candidates.remove(nextIdx)
        yield (), ((tour[-1], nextIdx),)
        tour.append(nextIdx)

    yield (), ((tour[-1], tour[0]),)


def greedyFactory(cities, ways):
    heap = [(dist(cities[i], cities[j]), (i, j)) for i in range(len(cities)) for j in range(i)]
    heapq.heapify(heap)

    uf = UnionFindWrapper(range(len(cities)))
    num = [0 for _ in range(len(cities))]
    ctr = 0
    while heap:
        d, edge = heapq.heappop(heap)
        i, j = edge
        if (uf.find(i) != uf.find(j)) and (num[i] <= 1 and num[j] <= 1):  # does not make a loop (except last)
            num[i] += 1
            num[j] += 1
            uf.union(i, j)
            yield (), ((i, j),)
            ctr += 1
            if ctr == len(cities) - 1:
                break

    c1 = len(cities)
    c2 = len(cities)
    for i, j in enumerate(num):
        if j == 1 and not c1 < len(cities):
            c1 = i
        elif j == 1:
            c2 = i
            break

    yield (), ((c1, c2),)


def farInFactory(cities, ways):
    candidates = set(range(1, len(cities)))
    tour = [0]

    best = -1
    while candidates:
        # find farthest node
        for i in candidates:
            d = min(dist(cities[i], cities[j]) for j in tour)
            if d > best or best < 0:
                best = d
                city = i
        candidates.remove(city)
        best = -1

        if len(tour) == 1:
            tour.append(city)
            yield (), ((tour[0], city), (tour[0], city))
            continue

        for i in range(len(tour)):
            n = (i + 1) % len(tour)

            d = dist(cities[city], cities[tour[i]]) \
                + dist(cities[city], cities[tour[n]]) \
                - dist(cities[tour[i]], cities[tour[n]])

            if d < best or best < 0:
                best = d
                minIdx = n

        yield ((tour[minIdx], tour[minIdx - 1]),), ((city, tour[minIdx]), (city, tour[minIdx - 1]))
        tour.insert(minIdx, city)
        best = -1


def randomFactory(cities, ways):
    tour = list(range(len(cities)))
    shuffle(tour)
    for i in range(1, len(tour)):
        yield (), ((tour[i - 1], tour[i]),)
    yield (), ((tour[-1], tour[0]),)


def twoOptFactory(t, d):
    def swap():
        n = len(t)
        for i in range(n):
            for j in range(i + 1, n):

                # if sum(neueKanten) < sum(alteKanten)
                if d[t[i]][t[j]] + d[t[i + 1]][t[(j + 1) % n]] < d[t[i]][t[i + 1]] + d[t[j]][t[(j + 1) % n]]:
                    # tausche die Reihenfolge von j bis i+1 um
                    ct = j - i
                    for m in range(ct // 2):
                        t[i + ct - m], t[i + 1 + m] = t[i + 1 + m], t[i + ct - m]
                    return False, ((t[i], t[j]), (t[i + 1], t[(j + 1) % n])), ((t[i], t[i + 1]), (t[j], t[j + 1]))

        return True, (), ()

    finished = False
    while not finished:
        finished, toRemove, toAdd = swap()
        yield toRemove, toAdd


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
        self.__n2Opt = 0
        self.sigma = 0
        self.N = 42

    def init(self):
        self.__ways = []
        self.__concordeWays = []
        self.__distanceMatrix = self.calcDistanceMatrix()
        self.initMethod()
        self.finishedFirst = False
        self.finished2Opt = False
        self.__n2Opt = 0

        if self.doConcorde:
            self.concorde()

    def randInit(self):
        self.__cities = tuple((random(), random()) for _ in range(self.N))
        self.init()

    def displace(self, city):
        r = random() * self.sigma
        phi = random() * 2 * pi
        dx = r * cos(phi)
        dy = r * sin(phi)

        return city[0] + dx, city[1] + dy

    def DCEInit(self):
        self.__cities = tuple(
            self.displace((0.5 + 0.25 * cos(2 * pi / self.N * i), 0.5 + 0.25 * sin(2 * pi / self.N * i))) for i in
            range(self.N))
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
        if method == "Next Neighbor":
            self.__heuristic = nextNeighborFactory(self.__cities, self.getWays())
        elif method == "Greedy":
            self.__heuristic = greedyFactory(self.__cities, self.getWays())
        elif method == "Farthest Insertion":
            self.__heuristic = farInFactory(self.__cities, self.getWays())
        elif method == "Random":
            self.__heuristic = randomFactory(self.__cities, self.getWays())
        else:
            raise ValueError

        if not self.currentMethod == method:
            self.currentMethod = method
            self.__ways = []

    def step(self):
        if not self.finishedFirst:
            try:
                toRemove, toAdd = next(self.__heuristic)
                for i in toRemove:
                    self.removeWay(i)
                for i in toAdd:
                    self.addWay(i)
            except StopIteration:
                self.finishedFirst = True
                self.__twoOpt = twoOptFactory(tourFromWays(self.__ways), self.__distanceMatrix)
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

    def setDo2Opt(self, b):
        self.do2Opt = b

    def setDoConcorde(self, b):
        self.doConcorde = b
        if b:
            self.concorde()

    def clearSolution(self):
        self.__ways = []
        self.__n2Opt = 0
        self.finishedFirst = False
        self.finished2Opt = False
        self.initMethod()

    def saveTSPLIB(self, name):
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
