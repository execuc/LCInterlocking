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
from FreeCAD import Gui, Matrix
import os
from lasercut.crosspart import make_cross_parts
from panel.treepanel import TreePanel, PREVIEW_NONE, PREVIEW_NORMAL, PREVIEW_FAST
from panel.propertieslist import PropertiesList
import json
import copy
from PySide import QtCore, QtGui

__dir__ = os.path.dirname(__file__)
iconPath = os.path.join(__dir__, '../icons')


class CrossPieceGroup:
    def __init__(self, obj):
        obj.addProperty('App::PropertyPythonObject', 'parts').parts = PropertiesList()
        obj.addProperty('App::PropertyPythonObject', 'need_recompute').need_recompute = False
        obj.addProperty('App::PropertyPythonObject', 'preview').preview = PREVIEW_NONE
        obj.addProperty('App::PropertyLinkList', 'generatedParts').generatedParts = []
        obj.addProperty('App::PropertyLinkList', 'fromParts').fromParts = []
        obj.addProperty('App::PropertyPythonObject', 'edit').edit = False
        obj.addProperty('App::PropertyPythonObject', 'namesMapping').namesMapping = {}
        obj.Proxy = self

    def onChanged(self, fp, prop):
        if prop == "need_recompute":
            self.execute(fp)
        elif prop == "preview":
            self.preview(fp)
        elif prop == "edit":
            self.editMode(fp)

    def editMode(self, fp):
        if fp.edit:
            if not hasattr(fp, "fromParts"):
                return
            for obj in fp.fromParts:
                obj.ViewObject.show()
            for obj in fp.generatedParts:
                obj.ViewObject.hide()
        else:
            if not hasattr(fp, "fromParts"):
                return
            for obj in fp.fromParts:
                obj.ViewObject.hide()
            for obj in fp.generatedParts:
                obj.ViewObject.show()

    def preview(self, fp):
        if fp.preview != PREVIEW_NONE:
            fp.preview = PREVIEW_NONE

            document = fp.Document
            preview_doc_name = str(fp.Name) + "_preview_parts"
            new_doc = False
            try:
                preview_doc = FreeCAD.getDocument(preview_doc_name)
                objs = preview_doc.Objects
                for obj in objs:
                    preview_doc.removeObject(obj.Name)
            except:
                new_doc = True
                preview_doc = FreeCAD.newDocument(preview_doc_name)

            parts = []
            tabs = []
            for part in fp.parts.lst:
                cp_part = copy.deepcopy(part)
                freecad_obj = document.getObject(cp_part.name)
                cp_part.recomputeInit(freecad_obj)
                parts.append(cp_part)

            computed_parts = make_cross_parts(parts)
            for part in computed_parts:
                new_shape = preview_doc.addObject("Part::Feature", part.get_new_name())
                new_shape.Shape = part.get_shape()
            preview_doc.recompute()
            if new_doc:
                FreeCADGui.getDocument(preview_doc.Name).ActiveView.fitAll()


    def execute(self, fp):
        if fp.need_recompute:
            fp.need_recompute = False

            document = fp.Document
            if len(fp.fromParts) > 0:
                groupObj = fp.fromParts[0]
            else:
                groupObj = document.addObject("App::DocumentObjectGroup", str(fp.Name) + "_origin_parts")

            subObjectList = groupObj.Group
            for subObj in subObjectList:
                groupObj.removeObject(subObj)

            fp.fromParts = []
            parts = []
            freedac_origin_obj = []
            freedac_origin_obj.append(groupObj)
            for part in fp.parts.lst:
                cp_part = copy.deepcopy(part)
                freecad_obj = document.getObject(cp_part.name)
                freedac_origin_obj.append(freecad_obj)
                cp_part.recomputeInit(freecad_obj)
                groupObj.addObject(freecad_obj)
                parts.append(cp_part)

            fp.fromParts = freedac_origin_obj
            computed_parts = make_cross_parts(parts)

            previous_nameMapping = copy.copy(fp.namesMapping)
            fp.namesMapping.clear()

            freecad_obj_generated = []
            freecad_objname_tokeep = []
            for part in computed_parts:
                if part.get_new_name() in previous_nameMapping:
                    freecad_obj = document.getObject(previous_nameMapping[part.get_new_name()])
                else:
                    freecad_obj = document.addObject("Part::Feature", part.get_new_name())
                fp.namesMapping[part.get_new_name()] = freecad_obj.Name
                freecad_obj.Shape = part.get_shape()
                freecad_objname_tokeep.append(freecad_obj.Name)
                freecad_obj_generated.append(freecad_obj)

            for part in fp.generatedParts:
                if part.Name not in freecad_objname_tokeep:
                    document.removeObject(part.Name)

            fp.generatedParts = freecad_obj_generated
            fp.edit = False

            FreeCADGui.getDocument(document.Name).ActiveView.fitAll()
            document.recompute()


class CrossPieceViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self

    def setEdit(self, vobj=None, mode=0):
        if mode == 0:
            FreeCADGui.Control.showDialog(CrossPiece(self.Object))
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
        if len(self.Object.fromParts) > 0:
            return [self.Object.fromParts[0]] + self.Object.generatedParts
        else:
            return []


class CrossPiece(TreePanel):
    def __init__(self, obj_join):
        super(CrossPiece, self).__init__("Crosspiece", obj_join)
        self.obj_join = obj_join
        self.parts_origin = copy.deepcopy(obj_join.parts)
        self.obj_join.edit = True

    def accept(self):
        self.compute(False)
        return True

    def reject(self):
        self.obj_join.parts = self.parts_origin
        self.obj_join.edit = False
        return True

    def compute(self, preview):
        self.save_items_properties()
        self.save_link_properties()
        if not preview:
            self.obj_join.need_recompute = True
        else:
            self.obj_join.preview = PREVIEW_NORMAL

    def preview(self):
        self.compute(True)
        self.selection_changed(None, None)
        return

    def init_tree_widget(self):
        #Preview button
        v_box = QtGui.QVBoxLayout(self.tree_widget)
        preview_button = QtGui.QPushButton('Preview', self.tree_widget)
        preview_button.clicked.connect(self.preview)
        #self.fast_preview = QtGui.QCheckBox("Fast preview", self.tree_widget)
        line = QtGui.QFrame(self.tree_widget)
        line.setFrameShape(QtGui.QFrame.HLine);
        line.setFrameShadow(QtGui.QFrame.Sunken);
        h_box = QtGui.QHBoxLayout(self.tree_widget)
        h_box.addWidget(preview_button)
        #h_box.addWidget(self.fast_preview)
        v_box.addLayout(h_box)
        v_box.addWidget(line)
        self.tree_vbox.addLayout(v_box)
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
        return True

    def Activated(self):
        groupCross = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "CrossPiece")
        CrossPieceGroup(groupCross)
        vp = CrossPieceViewProvider(groupCross.ViewObject)
        vp.setEdit(CrossPieceViewProvider)
        return

Gui.addCommand('crosspiece', CrossPieceCommand())
