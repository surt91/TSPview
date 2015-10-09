#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'surt91'


class UnionFind:
    def __init__(self, info):
        self.info = info
        self.parent = None
        self.size = 1

    def union(self, other):
        # find representatives
        root = self.find()
        other = other.find()

        # are already in one Cluster
        if other == root:
            return

        # We are not the root node
        # -> append other at the root node
        if self.parent:
            root.union(other)
            return

        # weighted
        # -> append shorter Tree to longer
        if self.size < other.size:
            other.union(self)
            return

        # update size
        self.size += other.size

        other.parent = root

    def find(self):
        """Find the root and compress the path in a recursive manner"""
        if not self.parent:
            return self

        root = self.parent.find()

        # path compression
        self.parent = root

        return root


class UnionFindWrapper():
    def __init__(self, vertices):
        self.S = {i: UnionFind(i) for i in vertices}

    def union(self, r, s):
        self.S[s].union(self.S[r])

    def find(self, x):
        return self.S[x].find().info

    def size(self, x):
        return self.S[x].find().size

