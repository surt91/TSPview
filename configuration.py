from math import sqrt
from random import random


def dist(a: tuple, b: tuple):
    return sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)


def tourFromWays(ways):
    raise NotImplementedError


def nextNeighborFactory(cities, ways):
    def f():
        if len(cities) <= 1:
            raise ValueError

        candidates = set(range(1, len(cities)))
        tour = [0]
        nextIdx = 1
        best = -1

        while candidates:
            for i in candidates:
                d = dist(cities[i], cities[tour[-1]])
                if d < best or best < 0:
                    best = d
                    nextIdx = i

            best = -1
            candidates.remove(nextIdx)
            yield (), ((tour[-1], nextIdx), )
            tour.append(nextIdx)

        yield (), ((tour[-1], tour[0]), )

    return f


def greedyFactory(cities, ways):
    def f():
        raise NotImplementedError
        yield nextEdge

    return f


def farInFactory(cities, ways):
    def f():
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
                next = i+1
                if next == len(tour):
                    next = 0
                d = dist(cities[city], cities[tour[i]]) + dist(cities[city], cities[tour[next]]) - dist(cities[tour[i]], cities[tour[next]])

                if d < best or best < 0:
                    best = d
                    minIdx = next

            yield ((tour[minIdx], tour[minIdx-1]), ), ((city, tour[minIdx]), (city, tour[minIdx-1]))
            tour.insert(minIdx, city)
            best = -1

    return f


def randomFactory(cities, ways):
    def f():
        raise NotImplementedError
        yield nextEdge

    return f


def twoOptFactory(cities, ways):
    def f():
        raise NotImplementedError
        yield nextEdge

    return f


class Configuration:
    def __init__(self, x: list=(), y: list=()):
        self.__cities = tuple(zip(x, y))
        self.__ways = []
        self.__distanceMatrix = self.calcDistanceMatrix()
        self.finished = True
        self.currentMethod = "Next Neighbor"

    def randomInit(self, N: int):
        self.__cities = tuple((random(), random()) for _ in range(N))
        self.__ways = []
        self.calcDistanceMatrix()
        self.initMethod()
        self.finished = False

    def calcDistanceMatrix(self):
        return tuple(tuple(dist(i, j) for j in self.__cities) for i in self.__cities)

    def getCities(self):
        return self.__cities

    def getWays(self):
        return tuple(self.__ways)

    def getWayCoordinates(self):
        return tuple((self.__cities[i], self.__cities[j]) for i, j in self.__ways)

    def valid(self, newWay):
        # raise NotImplementedError
        return True

    def removeWay(self, way):
        print(way, self.__ways)
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
        print(method)
        if method == "Next Neighbor":
            self.__heuristic = nextNeighborFactory(self.__cities, self.getWays())()
        elif method == "Greedy":
            self.__heuristic = greedyFactory(self.__cities, self.getWays())()
        elif method == "Farthest Insertion":
            self.__heuristic = farInFactory(self.__cities, self.getWays())()
        elif method == "Random":
            self.__heuristic = randomFactory(self.__cities, self.getWays())()
        else:
            raise ValueError
        self.currentMethod = method

    def step(self):
        try:
            toRemove, toAdd = next(self.__heuristic)
            for i in toRemove:
                self.removeWay(i)
            for i in toAdd:
                self.addWay(i)

        except StopIteration:
            self.finished = True
            pass

    def length(self):
        l = 0
        for a, b in self.getWayCoordinates():
            l += dist(a, b)
        return l
