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

from treepanel import TreePanel
from lasercut.crosspart import make_cross_parts

__dir__ = os.path.dirname(__file__)
iconPath = os.path.join(__dir__, '../icons')

class CrossPiece(TreePanel):

    def __init__(self):
        super(CrossPiece, self).__init__("Crosspiece")

    def accept(self):
        try:
            computed_parts = self.compute_parts()
            self.create_new_parts(self.active_document, computed_parts)
            for part in self.partsList.get_parts_properties():
                part.freecad_object.ViewObject.hide()
        except ValueError as e:
            FreeCAD.Console.PrintMessage(e)
        return True

    def reject(self):
        return True

    def compute_parts(self):
        self.save_items_properties()
        parts = self.partsList.get_parts_properties()
        if len(parts) == 0:
            raise ValueError("No pars or tabs defined")
        return make_cross_parts(parts)

    def preview(self):
        FreeCAD.Console.PrintMessage("Preview Button\n")
        computed_parts = self.compute_parts()
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

        self.create_new_parts(self.preview_doc, computed_parts)
        if not preview_doc_exist:
            FreeCADGui.getDocument(self.preview_doc.Label).ActiveView.fitAll()
        return

    def init_tree_widget(self):
        # Add part buttons
        h_box = QtGui.QHBoxLayout(self.tree_widget)
        add_parts_button = QtGui.QPushButton('Add parts', self.tree_widget)
        add_parts_button.clicked.connect(self.add_parts)
        add_same_part_button = QtGui.QPushButton('Add same parts', self.tree_widget)
        add_same_part_button.clicked.connect(self.add_same_parts)
        h_box.addWidget(add_parts_button)
        h_box.addWidget(add_same_part_button)
        self.tree_vbox.addLayout(h_box)
        # tree
        self.selection_model = self.tree_view_widget.selectionModel()
        self.selection_model.selectionChanged.connect(self.selection_changed)
        self.tree_vbox.addWidget(self.tree_view_widget)
        remove_item_button = QtGui.QPushButton('Remove item', self.tree_widget)
        remove_item_button.clicked.connect(self.remove_items)
        self.tree_vbox.addWidget(remove_item_button)
        # test layout
        self.edit_items_layout = QtGui.QVBoxLayout(self.tree_widget)
        self.tree_vbox.addLayout(self.edit_items_layout)



class CrossPieceCommand:

    def __init__(self):
        return

    def GetResources(self):
        return {'Pixmap': os.path.join(iconPath, 'crosspiece.xpm'),  # the name of a svg file available in the resources
                'MenuText': "Crosspiece",
                'ToolTip': "Crosspiece"}

    def IsActive(self):
        #return len(FreeCADGui.Selection.getSelection()) > 0
        return True

    def Activated(self):
        panel = CrossPiece()
        FreeCADGui.Control.showDialog(panel)
        return




Gui.addCommand('crosspiece', CrossPieceCommand())
