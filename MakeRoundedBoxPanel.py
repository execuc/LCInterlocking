#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 execuc                                             *
# *                                                                         *
# *   This file is part of LCInterlocking module.                           *
# *   LCInterlocking module is free software; you can redistribute it and/or*
# *   modify it under the terms of the GNU Lesser General Public            *
# *   License as published by the Free Software Foundation; either          *
# *   version 2.1 of the License, or (at your option) any later version.    *
# *                                                                         *
# *   This module is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU     *
# *   Lesser General Public License for more details.                       *
# *                                                                         *
# *   You should have received a copy of the GNU Lesser General Public      *
# *   License along with this library; if not, write to the Free Software   *
# *   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,            *
# *   MA  02110-1301  USA                                                   *
# *                                                                         *
# ***************************************************************************

from FreeCAD import Gui
import FreeCAD
import FreeCADGui
import Part
import os
import math
import Draft
import copy
from panel.roundedbox import RoundedBoxProperties, TopBottomRoundedProperties, DimensionRoundedBoxParam, BottomRoundedBoxParam, TopBoxRoundedParam
from lasercut import makeroundedbox


__dir__ = os.path.dirname(__file__)
iconPath = os.path.join(__dir__, 'icons')
from PySide import QtCore, QtGui


class GroupRoundedBox:
    def __init__(self, obj):
        obj.addProperty("App::PropertyPythonObject", "box_properties").box_properties = RoundedBoxProperties()
        obj.addProperty("App::PropertyPythonObject", "top_properties").top_properties = TopBottomRoundedProperties()
        obj.addProperty("App::PropertyPythonObject", "bottom_properties").bottom_properties = TopBottomRoundedProperties()
        obj.addProperty('App::PropertyPythonObject', 'need_recompute').need_recompute = False
        obj.addProperty('App::PropertyLinkList', 'parts').parts= []
        obj.Proxy = self

    def onChanged(self, fp, prop):
        if prop == "need_recompute":
            self.execute(fp)

    def execute(self, fp):
        if fp.need_recompute:
            fp.need_recompute = False

            document = fp.Document
            computed_parts = makeroundedbox.make_rounded_box(fp.box_properties, fp.top_properties, fp.bottom_properties)

            object_list = fp.parts
            if len(computed_parts) != len(object_list):
                for part in object_list:
                    document.removeObject(part.Name)

                object_list = []
                for part in computed_parts:
                    new_shape = document.addObject("Part::Feature", part['name'])
                    object_list.append(new_shape)

            for index in range(len(computed_parts)):
                object_list[index].Shape = computed_parts[index]['shape']

            fp.parts = object_list
            FreeCADGui.getDocument(document.Name).ActiveView.fitAll()
            document.recompute()


class ViewProviderGroupRoundedBox:
    def __init__(self, vobj):
        vobj.Proxy = self

    def setEdit(self, vobj=None, mode=0):
        if mode == 0:
            FreeCADGui.Control.showDialog(MakeRoundedBox(self.Object))
            return True

    def setupContextMenu(self, obj, menu):
        action = menu.addAction("Edit")
        action.triggered.connect(self.setEdit)

    def onChanged(self, vp, prop):
        pass

    def __getstate__(self):
        ''' When saving the document this object gets stored using Python's cPickle module.
        Since we have some un-pickable here -- the Coin stuff -- we must define this method
        to return a tuple of all pickable objects or None.
        '''
        return None

    def __setstate__(self, state):
        ''' When restoring the pickled object from document we have the chance to set some
        internals here. Since no data were pickled nothing needs to be done here.
        '''
        return None

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def claimChildren(self):
        return self.Object.parts



class MakeRoundedBox:

    def __init__(self, obj_box):
        self.form = []
        self.main_widget = QtGui.QWidget()
        self.main_widget.setWindowTitle("Make rounded box")
        self.parts_vbox = QtGui.QGridLayout(self.main_widget)
        self.form.append(self.main_widget)

        self.preview_button = QtGui.QPushButton('Preview', self.main_widget)
        self.parts_vbox.addWidget(self.preview_button, 0, 0, 1, 2)
        self.preview_button.clicked.connect(self.preview)

        self.obj_box = obj_box
        self.box_properties_origin = copy.deepcopy(self.obj_box.box_properties)
        self.bottom_properties_origin = copy.deepcopy(self.obj_box.bottom_properties)
        self.top_properties_origin = copy.deepcopy(self.obj_box.top_properties)

        self.box_properties = DimensionRoundedBoxParam(self.obj_box.box_properties)
        self.bottom_box_param = BottomRoundedBoxParam(self.obj_box.bottom_properties)
        self.top_box_param = TopBoxRoundedParam(self.obj_box.top_properties)

        self.param_widget = QtGui.QWidget()
        self.param_widget.setWindowTitle("Parameters")
        self.form.append(self.param_widget)
        self.params_vlayout = QtGui.QVBoxLayout(self.param_widget)

        dim_group_box, grid = self.box_properties.get_group_box(self.param_widget)
        top_group_box, grid = self.top_box_param.get_group_box(self.param_widget)
        bottom_group_box, grid = self.bottom_box_param.get_group_box(self.param_widget)

        self.params_vlayout.addWidget(dim_group_box)
        self.params_vlayout.addWidget(top_group_box)
        self.params_vlayout.addWidget(bottom_group_box)

        radius_widget = self.box_properties.get_widget("inradius")
        radius_widget.valueChanged.connect(self.preview)
        nb_face_widget = self.box_properties.get_widget("nb_face")
        nb_face_widget.valueChanged.connect(self.preview)

        self.actual_parts = []
        self.document = FreeCAD.ActiveDocument
        self.preview()
        return

    def accept(self):
        self.preview()
        return True

    def reject(self):
        self.obj_box.box_properties = self.box_properties_origin
        self.obj_box.bottom_properties = self.bottom_properties_origin
        self.obj_box.top_properties = self.top_properties_origin
        self.obj_box.need_recompute = True
        return True

    def preview(self):
        self.box_properties.get_properties().compute_information()
        self.box_properties.update_information()
        self.bottom_box_param.get_properties()
        self.top_box_param.get_properties()
        self.obj_box.need_recompute = True


class MakeRoundedBoxCommand:

    def __init__(self):
        return

    def GetResources(self):
        return {'Pixmap': os.path.join(iconPath, 'roundbox.xpm'),  # the name of a svg file available in the resources
                'MenuText': "Rounded box",
                'ToolTip': "Make rounded box without tab"}

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        groupRoundedBox = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "RoundedBox")
        GroupRoundedBox(groupRoundedBox)
        vp = ViewProviderGroupRoundedBox(groupRoundedBox.ViewObject)
        vp.setEdit(ViewProviderGroupRoundedBox)
        return


Gui.addCommand('make_rounded_box_command', MakeRoundedBoxCommand())
