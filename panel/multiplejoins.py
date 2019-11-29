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
from lasercut.join import make_tabs_joins
from panel.treepanel import TreePanel, PREVIEW_NONE, PREVIEW_NORMAL, PREVIEW_FAST
from panel.propertieslist import PropertiesList
import json
import copy

__dir__ = os.path.dirname(__file__)
iconPath = os.path.join(__dir__, '../icons')


class MultipleJoinGroup:
    def __init__(self, obj):
        obj.addProperty('App::PropertyPythonObject', 'parts').parts = PropertiesList()
        obj.addProperty('App::PropertyPythonObject', 'faces').faces = PropertiesList()
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
            fast = False
            if fp.preview == PREVIEW_FAST:
                fast = True
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

            for tab in fp.faces.lst:
                cp_tab = copy.deepcopy(tab)
                freecad_obj = document.getObject(cp_tab.freecad_obj_name)
                freecad_face = document.getObject(cp_tab.freecad_obj_name).Shape.getElement(cp_tab.face_name)
                cp_tab.recomputeInit(freecad_obj, freecad_face)
                tabs.append(cp_tab)

            computed_parts = make_tabs_joins(parts, tabs)
            for part in computed_parts:
                new_shape = preview_doc.addObject("Part::Feature", part.get_new_name())
                new_shape.Shape = part.get_shape(fast)
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

            tabs = []
            for tab in fp.faces.lst:
                cp_tab = copy.deepcopy(tab)
                freecad_obj = document.getObject(cp_tab.freecad_obj_name)
                freecad_face = document.getObject(cp_tab.freecad_obj_name).Shape.getElement(cp_tab.face_name)
                cp_tab.recomputeInit(freecad_obj, freecad_face)
                tabs.append(cp_tab)

            computed_parts = make_tabs_joins(parts, tabs)

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


class MultipleJoinViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self

    def setEdit(self, vobj=None, mode=0):
        if mode == 0:
            FreeCADGui.Control.showDialog(MultipleJoins(self.Object))
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


class MultipleJoins(TreePanel):
    def __init__(self, obj_join):
        super(MultipleJoins, self).__init__("Parts and tabs", obj_join)
        self.obj_join = obj_join
        self.parts_origin = copy.deepcopy(obj_join.parts)
        self.faces_origin = copy.deepcopy(obj_join.faces)
        self.obj_join.edit = True

    def accept(self):
        self.compute(False)
        return True

    def reject(self):
        self.obj_join.parts = self.parts_origin
        self.obj_join.faces = self.faces_origin
        self.obj_join.edit = False
        return True

    def preview(self, fast=False):
        self.compute(True, fast)
        self.selection_changed(None, None)
        return

    def compute(self, preview, fast=False):
        self.save_items_properties()
        self.save_link_properties()
        if not preview:
            self.obj_join.need_recompute = True
        elif not fast:
            self.obj_join.preview = PREVIEW_NORMAL
        else:
            self.obj_join.preview = PREVIEW_FAST

class MultipleCommand:

    def __init__(self):
        return

    def GetResources(self):
        return {'Pixmap': os.path.join(iconPath, 'one_tab.xpm'),  # the name of a svg file available in the resources
                'MenuText': "Slots",
                'ToolTip': "Interlocking"}

    def IsActive(self):
        return True

    def Activated(self):
        groupJoin = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "MultiJoin")
        MultipleJoinGroup(groupJoin)
        vp = MultipleJoinViewProvider(groupJoin.ViewObject)
        vp.setEdit(MultipleJoinViewProvider)
        return

Gui.addCommand('multiple_tabs_command', MultipleCommand())
