import FreeCAD
import FreeCADGui
from FreeCAD import Gui, Matrix
from lasercut.material import MaterialProperties
from lasercut.tabproperties import TabProperties
from lasercut.hingesproperties import HingesProperties
import json

class Empty(object):
    pass

class PropertiesList():
    def __init__(self):
        self.lst = []

    def append(self, obj):
        self.lst.append(obj)

    def __getitem__(self, index):
        return self.lst[index]

    def __len__(self):
        return len(self.lst)

    def pop(self, index):
        self.lst.pop(index)

    def __getstate__(self):
        json_string = json.dumps([ob.__dict__ for ob in self.lst])
        return json_string

    def __setstate__(self, state):
        self.lst = []
        bckp = json.loads(state)
        for obj in bckp:
            tmp = Empty()
            tmp.__class__ = eval(obj["obj_class"]) # Class defined must be in import
            for k, v in obj.items():
                setattr(tmp, k, v)
            self.lst.append(tmp)
        return None