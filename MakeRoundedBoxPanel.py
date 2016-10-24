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
from panel.roundedbox import DimensionRoundedBoxParam, BottomRoundedBoxParam, TopBoxRoundedParam
from lasercut import makeroundedbox

__dir__ = os.path.dirname(__file__)
iconPath = os.path.join(__dir__, 'icons')
from PySide import QtCore, QtGui


class MakeRoundedBox:

    def __init__(self):
        self.form = []
        self.main_widget = QtGui.QWidget()
        self.main_widget.setWindowTitle("Make rounded box")
        self.parts_vbox = QtGui.QGridLayout(self.main_widget)
        self.form.append(self.main_widget)

        self.preview_button = QtGui.QPushButton('Preview', self.main_widget)
        self.parts_vbox.addWidget(self.preview_button, 0, 0, 1, 2)
        self.preview_button.clicked.connect(self.preview)

        self.box_properties = DimensionRoundedBoxParam()
        self.bottom_box_param = BottomRoundedBoxParam()
        self.top_box_param = TopBoxRoundedParam()

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
        radius_widget.valueChanged.connect(self.update_parameters)
        nb_face_widget = self.box_properties.get_widget("nb_face")
        nb_face_widget.valueChanged.connect(self.update_parameters)

        self.actual_parts = []
        self.document = FreeCAD.ActiveDocument
        return

    def accept(self):
        try:
            self.preview()
        except ValueError as e:
            FreeCAD.Console.PrintError(e)
        return True

    def reject(self):
        return True

    def update_parameters(self, value):
        self.box_properties.get_properties().compute_information()
        self.box_properties.update_information()
        return

    def create_new_parts(self, document, computed_parts):
        for part in computed_parts:
            new_shape = document.addObject("Part::Feature", part['name'])
            new_shape.Shape = part['shape']
            self.actual_parts.append(new_shape)
        document.recompute()

    def compute_parts(self):
        dimension_properties = self.box_properties.get_properties()
        top_properties = self.top_box_param.get_properties()
        bottom_properties = self.bottom_box_param.get_properties()
        parts_list = makeroundedbox.make_rounded_box(dimension_properties, top_properties, bottom_properties)
        return parts_list

    # Faire plutot un rendu dans le fenetre actuel, ne pas en creer une autre
    #self.active_document != FreeCAD.ActiveDocument:
    def preview(self):
        first_preview = len(self.actual_parts) == 0

        for part in self.actual_parts:
            self.document.removeObject(part.Name)

        self.actual_parts = []

        computed_parts = self.compute_parts()
        self.create_new_parts(self.document, computed_parts)
        if first_preview:
            FreeCADGui.getDocument(self.document.Name).ActiveView.fitAll()

        def init_widget():
            return


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
        panel = MakeRoundedBox()
        FreeCADGui.Control.showDialog(panel)
        return


Gui.addCommand('make_rounded_box_command', MakeRoundedBoxCommand())
