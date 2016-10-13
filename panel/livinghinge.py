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

from hingeswidget import GlobalLivingHingeWidget, LivingHingeWidget
from panel import selection
from lasercut.makehinges import create_linked_part

__dir__ = os.path.dirname(__file__)
iconPath = os.path.join(__dir__, '../icons')


class LivingHinges:

    def __init__(self):
        self.form = []

        global_obj = selection.get_freecad_objects_list()[0]
        self.global_properties = GlobalLivingHingeWidget(global_obj)

        self.param_widget = QtGui.QWidget()
        self.param_widget.setWindowTitle("Global parameters")
        self.form.append(self.param_widget)
        self.params_vlayout = QtGui.QVBoxLayout(self.param_widget)

        global_box, grid = self.global_properties.get_group_box(self.param_widget)
        self.con_button = QtGui.QPushButton('Preview', self.param_widget)
        self.params_vlayout.addWidget(self.con_button)
        self.con_button.clicked.connect(self.preview)
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

        link_clearance_widget = self.global_properties.get_widget("link_clearance")
        link_clearance_widget.valueChanged.connect(self.update_connection_from_global_parameters)

        try:
            self.add_connection()
        except ValueError:
            pass

        return

    def accept(self):
        flat_part, solid_part = self.compute_parts()
        self.create_object(self.document, flat_part, solid_part)
        return True

    def reject(self):
        return True

    def compute_parts(self):
        connection_list = []
        for con_widget in self.connection_widget_list:
            connection_list.append(con_widget.get_properties())
        return create_linked_part(connection_list, self.global_properties.get_properties())

    def preview(self):
        FreeCAD.Console.PrintMessage("Preview Button\n")
        flat_part, solid_part = self.compute_parts()
        preview_doc_exist = True
        try:
            FreeCAD.getDocument("preview_parts")
        except:
            preview_doc_exist = False

        if not preview_doc_exist:
            self.preview_doc = FreeCAD.newDocument("preview_parts")
        else:
            objs = self.preview_doc.Objects
            for obj in objs:
                self.preview_doc.removeObject(obj.Name)

        self.create_object(self.preview_doc, flat_part, solid_part)
        if not preview_doc_exist :
            FreeCADGui.getDocument(self.preview_doc.Name).ActiveView.fitAll()
        return

    def create_object(self, document, flat_part, solid_part):
        if self.global_properties.get_properties().generate_solid is True:
            solid_obj = document.addObject("Part::Feature", self.global_properties.get_properties().solid_name)
            solid_obj.Shape = solid_part
        flat_part_obj = document.addObject("Part::Feature", self.global_properties.get_properties().new_name)
        flat_part_obj.Shape = flat_part
        document.recompute()

    def get_last_object(self):
        if len(self.connection_widget_list) == 0:
            return self.global_properties.properties().freecad_object
        else:
            return self.connection_widget_list[-1].properties().freecad_object_2

    def add_connection(self):
        faces_list = selection.get_freecad_faces_objects_list()
        if len(faces_list) == 0 or len(faces_list) % 2 == 1:
            raise ValueError("Please select at least two faces (multiple of two)")

        for index in range(0, len(faces_list)-1, 2):
            current_last_object = self.get_last_object()
            if faces_list[index]["freecad_object"] == current_last_object:
                face_1 = faces_list[index]
                face_2 = faces_list[index+1]
            else:
                raise ValueError("Please select a face belonging to the last part")

            widget = LivingHingeWidget(face_1['face'], face_1['freecad_object'],
                                       face_2['face'], face_2['freecad_object'])

            link_clearance = self.global_properties.get_properties().link_clearance
            if link_clearance != 0.:
                widget.properties().compute_min_link(link_clearance)
            self.connection_widget_list.append(widget)
        self.draw_connections()
        return

    def update_connection_from_global_parameters(self, value):
        self.draw_connections()

    def draw_connections(self):
        link_clearance = self.global_properties.get_properties().link_clearance
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
        panel = LivingHinges()
        FreeCADGui.Control.showDialog(panel)
        return


Gui.addCommand('livinghinge', LivingHingeCommand())
