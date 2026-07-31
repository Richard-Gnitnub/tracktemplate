"""Provide the minimal Coin protocol used by standalone Phase 5 tests."""


class _Field:
    def __init__(self):
        self.value = None

    def setValue(self, *values):
        self.value = values[0] if len(values) == 1 else tuple(values)

    def setValues(self, start, count, values):
        assert start == 0
        assert count == len(values)
        self.value = tuple(tuple(value) for value in values)

    def getValue(self):
        return self.value


class _Group:
    def __init__(self):
        self.children = []

    def addChild(self, child):
        self.children.append(child)

    def findChild(self, child):
        try:
            return self.children.index(child)
        except ValueError:
            return -1

    def removeChild(self, child_or_index):
        if isinstance(child_or_index, int):
            del self.children[child_or_index]
        else:
            self.children.remove(child_or_index)

    def removeAllChildren(self):
        self.children.clear()

    def replaceChild(self, old_child, new_child):
        self.children[self.children.index(old_child)] = new_child

    def getChild(self, index):
        return self.children[index]


class _BaseColor:
    def __init__(self):
        self.rgb = _Field()


class _DrawStyle:
    def __init__(self):
        self.lineWidth = _Field()


class _Coordinate3:
    def __init__(self):
        self.point = _Field()


class _LineSet:
    def __init__(self):
        self.numVertices = _Field()


class _SelectionRoot(_Group):
    pass


class _SelectionType:
    def createInstance(self):
        return _SelectionRoot()


class _SoType:
    @staticmethod
    def fromName(name):
        assert name == "SoFCSelection"
        return _SelectionType()


class _FakeCoin:
    SoSeparator = _Group
    SoBaseColor = _BaseColor
    SoDrawStyle = _DrawStyle
    SoCoordinate3 = _Coordinate3
    SoLineSet = _LineSet
    SoType = _SoType
