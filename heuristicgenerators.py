from math import sqrt
from random import shuffle
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


def nextNeighborGenerator(cities, ways):
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


def greedyGenerator(cities, ways):
    heap = [(dist(cities[i], cities[j]), (i, j)) for i in range(len(cities)) for j in range(i)]
    heapq.heapify(heap)

    ctr = 0
    valid, lastEdge = tourStaysValid(len(cities))
    while heap:
        d, edge = heapq.heappop(heap)
        if valid(edge):
            yield (), (edge,)
            ctr += 1
            if ctr == len(cities) - 1:
                break

    yield (), (lastEdge(),)


def farInGenerator(cities, ways):
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


def randomGenerator(cities, ways):
    tour = list(range(len(cities)))
    shuffle(tour)
    for i in range(1, len(tour)):
        yield (), ((tour[i - 1], tour[i]),)
    yield (), ((tour[-1], tour[0]),)


def twoOptGenerator(t, d):
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


def tourStaysValid(N):
    uf = UnionFindWrapper(range(N))
    num = [0 for _ in range(N)]

    def f(edge):
        i, j = edge
        if (uf.find(i) != uf.find(j)) and (num[i] <= 1 and num[j] <= 1):  # does not make a loop (except last)
            num[i] += 1
            num[j] += 1
            uf.union(i, j)
            return True
        else:
            return False

    def g():
        c1 = N
        c2 = N
        for i, j in enumerate(num):
            if j == 1 and not c1 < N:
                c1 = i
            elif j == 1:
                c2 = i
                break
        return c1, c2
    return f, g
