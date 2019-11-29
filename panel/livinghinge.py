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
import FreeCADGui
import FreeCAD
from PySide import QtCore, QtGui
import os
import copy

from panel.hingeswidget import GlobalLivingHingeWidget, LivingHingeWidget
from panel import selection
from lasercut.makehinges import create_linked_part
from panel.propertieslist import PropertiesList
from lasercut.hingesproperties import GlobalLivingMaterialProperties, HingesProperties

__dir__ = os.path.dirname(__file__)
iconPath = os.path.join(__dir__, '../icons')


class LivingHingesPanel:

    def __init__(self, obj):
        self.form = []

        self.obj = obj
        self.global_properties_origin = copy.deepcopy(obj.globalProperties)
        self.hinges_origin = copy.deepcopy(obj.hinges)

        self.global_properties = obj.globalProperties
        self.global_properties_widget = GlobalLivingHingeWidget(self.global_properties)
        self.hinges = obj.hinges

        self.param_widget = QtGui.QWidget()
        self.param_widget.setWindowTitle("Global parameters")
        self.form.append(self.param_widget)
        self.params_vlayout = QtGui.QVBoxLayout(self.param_widget)

        global_box, grid = self.global_properties_widget.get_group_box(self.param_widget)
        self.params_vlayout.addWidget(global_box)

        self.main_con_widget = QtGui.QWidget()
        self.main_con_widget.setWindowTitle("Living hinges")
        self.parts_vbox = QtGui.QVBoxLayout(self.main_con_widget)
        self.form.append(self.main_con_widget)

        self.con_button = QtGui.QPushButton('Add connection', self.main_con_widget)
        self.parts_vbox.addWidget(self.con_button)
        self.con_button.clicked.connect(self.add_connection)

        self.connection_vbox = QtGui.QVBoxLayout(self.param_widget)
        self.parts_vbox.addLayout(self.connection_vbox)

        self.connection_widget_list = []
        self.document = FreeCAD.ActiveDocument

        link_clearance_widget = self.global_properties_widget.get_widget("link_clearance")
        link_clearance_widget.valueChanged.connect(self.update_connection_from_global_parameters)

        for hinge in self.hinges:
            self.connection_widget_list.append(LivingHingeWidget(hinge))

        try:
            if len(self.hinges) == 0:
                self.add_connection()
        except ValueError as err:
            FreeCAD.Console.PrintError(err)
            pass

        self.draw_connections()
        return

    def accept(self):
        self.compute_parts()
        return True

    def reject(self):
        self.obj.globalProperties = self.global_properties_origin
        self.obj.hinges = self.hinges_origin
        return True

    def compute_parts(self):
        self.global_properties_widget.get_properties()
        for conn in self.connection_widget_list:
            conn.get_properties()

        self.obj.need_recompute = True

    def create_object(self, document, flat_part, solid_part):
        if self.global_properties_widget.get_properties().generate_solid is True:
            solid_obj = document.addObject("Part::Feature", self.global_properties_widget.get_properties().solid_name)
            solid_obj.Shape = solid_part
        flat_part_obj = document.addObject("Part::Feature", self.global_properties_widget.get_properties().new_name)
        flat_part_obj.Shape = flat_part
        document.recompute()

    def get_last_object(self):
        if len(self.connection_widget_list) == 0:
            return self.global_properties_widget.properties().freecad_object_name
        else:
            return self.connection_widget_list[-1].properties().freecad_object_2_name

    def add_connection(self, reversed_angle=False):
        faces_list = selection.get_freecad_faces_objects_list()
        if len(faces_list) == 0 or len(faces_list) % 2 == 1:
            raise ValueError("Please select at least two faces (multiple of two)")

        for index in range(0, len(faces_list)-1, 2):
            current_last_object = self.get_last_object()
            if faces_list[index]["freecad_object"].Name == current_last_object:
                face_1 = faces_list[index]
                face_2 = faces_list[index+1]
            else:
                raise ValueError("Please select a face belonging to the last part")

            hinge = HingesProperties(freecad_face_1=face_1['face'], freecad_face_1_name=face_1['name'], freecad_object_1=face_1['freecad_object'],
                                     freecad_face_2=face_2['face'],  freecad_face_2_name=face_2['name'], freecad_object_2=face_2['freecad_object'],
                                     reversed_angle=reversed_angle)
            link_clearance = self.global_properties_widget.get_properties().link_clearance
            if link_clearance != 0.:
               hinge.compute_min_link(link_clearance)

            widget = LivingHingeWidget(hinge)
            self.hinges.append(hinge)
            self.connection_widget_list.append(widget)
        self.draw_connections()
        return

    def add_rev_connection(self):
        return self.add_connection(True)

    def update_connection_from_global_parameters(self, value):
        self.draw_connections(True)

    def draw_connections(self, updateLinkClearance = False):
        if updateLinkClearance:
            link_clearance = self.global_properties_widget.get_properties().link_clearance
            for index in range(self.connection_vbox.count()):
                if link_clearance != 0.:
                    self.connection_widget_list[index].get_properties().compute_min_link(link_clearance)
        self.remove_items_widgets()
        for con_widget in self.connection_widget_list:
            group_box, grid = con_widget.get_group_box(self.main_con_widget)
            self.connection_vbox.addWidget(group_box)
        return

    def remove_items_widgets(self):
        for cnt in reversed(range(self.connection_vbox.count())):
            # takeAt does both the jobs of itemAt and removeWidget
            # namely it removes an item and returns it
            widget = self.connection_vbox.takeAt(cnt).widget()

            if widget is not None:
                # widget will be None if the item is a layout
                widget.deleteLater()



class LivingHinges:
    def __init__(self, obj, freecad_obj):
        obj.addProperty('App::PropertyPythonObject', 'globalProperties').globalProperties = GlobalLivingMaterialProperties(freecad_object=freecad_obj)
        obj.addProperty('App::PropertyPythonObject', 'hinges').hinges = PropertiesList()
        obj.addProperty('App::PropertyPythonObject', 'need_recompute').need_recompute = False
        obj.addProperty('App::PropertyLink', 'solid').solid = None
        obj.addProperty('App::PropertyLink', 'obj').obj = None
        obj.Proxy = self

    def onChanged(self, fp, prop):
        if prop == "need_recompute":
            self.execute(fp)

    def execute(self, fp):
        if fp.need_recompute:
            fp.need_recompute = False

            document = fp.Document

            global_prop = copy.deepcopy(fp.globalProperties)
            hinges_lst = []
            for hinge in fp.hinges.lst:
                cp_hinge = copy.deepcopy(hinge)
                freecad_obj_1 = document.getObject(cp_hinge.freecad_object_1_name)
                freecad_obj_2 = document.getObject(cp_hinge.freecad_object_2_name)
                freecad_face_1 = freecad_obj_1.Shape.getElement(cp_hinge.freecad_face_1_name)
                freecad_face_2 = freecad_obj_2.Shape.getElement(cp_hinge.freecad_face_2_name)
                cp_hinge.recomputeInit(freecad_obj_1, freecad_face_1, freecad_obj_2, freecad_face_2)
                hinges_lst.append(cp_hinge)

            flat_part, solid_part=create_linked_part(hinges_lst, global_prop)

            if global_prop.generate_solid is True:
                if fp.solid is None:
                    fp.solid = document.addObject("Part::Feature", global_prop.solid_name)
                fp.solid.Shape = solid_part
                fp.solid.Label = global_prop.solid_name
            else:
                if fp.solid is not None:
                    document.removeObject(fp.solid.Name)
                    fp.solid = None

            if fp.obj is None:
                fp.obj = document.addObject("Part::Feature", global_prop.new_name)
            fp.obj.Shape = flat_part
            fp.obj.Label = global_prop.new_name

            document.recompute()


class LivingHingesViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self

    def setEdit(self, vobj=None, mode=0):
        if mode == 0:
            FreeCADGui.Control.showDialog(LivingHingesPanel(self.Object))
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
        lst = []
        if self.Object.obj:
            lst.append(self.Object.obj)
        if self.Object.solid:
            lst.append(self.Object.solid)
        return lst


class LivingHingeCommand:

    def __init__(self):
        return

    def GetResources(self):
        return {'Pixmap': os.path.join(iconPath, 'corner.xpm'),  # the name of a svg file available in the resources
                'MenuText': "Living hinges",
                'ToolTip': "Living hinges"}

    def IsActive(self):
        nb_connection = len(selection.get_freecad_faces_objects_list())
        return nb_connection > 1 and nb_connection % 2 == 0

    def Activated(self):
        living_hinge_part = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "living_hinges")
        LivingHinges(living_hinge_part, selection.get_freecad_objects_list()[0])
        vp = LivingHingesViewProvider(living_hinge_part.ViewObject)
        vp.setEdit(LivingHingesViewProvider)
        return


Gui.addCommand('livinghinge', LivingHingeCommand())



