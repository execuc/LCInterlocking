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

import FreeCAD
import FreeCADGui
from FreeCAD import Gui
import os
from lasercut.join import make_tabs_joins
from treepanel import TreePanel

__dir__ = os.path.dirname(__file__)
iconPath = os.path.join(__dir__, '../icons')


class MultipleJoins(TreePanel):
    def __init__(self):
        super(MultipleJoins, self).__init__("Parts and tabs")

    def accept(self):
        try:
            computed_parts = self.compute_parts()
            self.create_new_parts(self.active_document, computed_parts)
            for part in self.partsList.get_parts_properties():
                part.freecad_object.ViewObject.hide()
        except ValueError as e:
            FreeCAD.Console.PrintError(e)
        return True

    def reject(self):
        return True

    def compute_parts(self):
        self.save_items_properties()
        parts = self.partsList.get_parts_properties()
        tabs = self.tabsList.get_tabs_properties()
        if len(parts) == 0 or len(tabs) == 0:
            raise ValueError("No pars or tabs defined")
        return make_tabs_joins(parts, tabs)

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
        if not preview_doc_exist :
            FreeCADGui.getDocument(self.preview_doc.Name).ActiveView.fitAll()
        return


class MultipleCommand:

    def __init__(self):
        return

    def GetResources(self):
        return {'Pixmap': os.path.join(iconPath, 'one_tab.xpm'),  # the name of a svg file available in the resources
                'MenuText': "Slots",
                'ToolTip': "Slots"}

    def IsActive(self):
        return True

    def Activated(self):
        panel = MultipleJoins()
        FreeCADGui.Control.showDialog(panel)
        return

Gui.addCommand('multiple_tabs_command', MultipleCommand())
