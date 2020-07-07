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
import os, copy
from PySide import QtCore, QtGui
try:
    from PySide.QtGui import QItemSelectionModel
except ImportError:
    from PySide.QtCore import QItemSelectionModel

from panel.partmat import PartsList, CrossPartWidget, Part
from panel.tab import TabsList
from panel import selection
from lasercut.tabproperties import TabProperties
from panel.treeview import TreeModel, TreeItem
from panel.propertieslist import PropertiesList


PREVIEW_NONE = 0
PREVIEW_NORMAL = 1
PREVIEW_FAST = 2


class TreePanel(object):

    def __init__(self, title, obj_join = None): #none to be removed
        self.form = []
        self.obj_join = obj_join
        self.parts = self.obj_join.parts
        if hasattr(self.obj_join, "faces"):
            self.faces = self.obj_join.faces
        else:
            self.faces = PropertiesList()

        if title != "Crosspiece":
            self.partsList = PartsList(Part, self.parts)
        else:
            self.partsList = PartsList(CrossPartWidget, self.parts)
        self.tabsList = TabsList(self.faces)

        self.params_widget = None
        if self.params_widget:
            self.form.append(self.params_widget)
        self.hide_button = None
        self.show_button = None
        self.reset_transparency_button = None
        self.set_transparency_button = None
        self.active_document = self.obj_join.Document#FreeCAD.ActiveDocument
        self.tree_widget = QtGui.QWidget()
        self.tree_widget.setObjectName("TreePanel")
        self.tree_widget.setWindowTitle(title)
        self.tree_vbox = QtGui.QVBoxLayout(self.tree_widget)
        self.form.append(self.tree_widget)
        self.model = TreeModel()
        self.tree_view_widget = QtGui.QTreeView()
        self.tree_view_widget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tree_view_widget.setModel(self.model)
        self.tree_view_widget.setFixedHeight(250)
        self.selection_model = None
        self.tab_type_box = None
        self.edited_items = []
        self.edit_items_layout = None
        self.init_tree_widget()
        self.preview_doc = None
        self.show_other_state_checkbox = None
        self.other_object_list = []
        self.save_initial_objects()

        for item in self.parts:
            self.model.append_part(item.name, item.label, bool(item.link_name))

        for item in self.faces:
            self.model.append_tab(item.freecad_obj_name, item.tab_name, item.face_name, bool(item.link_name))

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)

    def accept(self):
        raise ValueError("Must overloaded")

    def reject(self):
        raise ValueError("Must overloaded")

    def init_tree_widget(self):
        v_box = QtGui.QVBoxLayout(self.tree_widget)
        preview_button = QtGui.QPushButton('Preview', self.tree_widget)
        preview_button.clicked.connect(self.abs_preview)
        self.fast_preview = QtGui.QCheckBox("Fast preview", self.tree_widget)
        line = QtGui.QFrame(self.tree_widget)
        line.setFrameShape(QtGui.QFrame.HLine);
        line.setFrameShadow(QtGui.QFrame.Sunken);
        h_box = QtGui.QHBoxLayout(self.tree_widget)
        h_box.addWidget(preview_button)
        h_box.addWidget(self.fast_preview)
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
        # Add faces buttons
        h_box = QtGui.QHBoxLayout(self.tree_widget)
        self.tab_type_box = QtGui.QComboBox(self.tree_widget)
        self.tab_type_box.addItems([TabProperties.TYPE_TAB, TabProperties.TYPE_T_SLOT,
                                    TabProperties.TYPE_CONTINUOUS])#, TabProperties.TYPE_FLEX])
        h_box.addWidget(self.tab_type_box)
        add_faces_button = QtGui.QPushButton('Add faces', self.tree_widget)
        add_faces_button.clicked.connect(self.add_tabs)
        add_same_faces_button = QtGui.QPushButton('Add same faces', self.tree_widget)
        add_same_faces_button.clicked.connect(self.add_same_tabs)
        h_box.addWidget(add_faces_button)
        h_box.addWidget(add_same_faces_button)
        self.tree_vbox.addLayout(h_box)
        # tree
        self.selection_model = self.tree_view_widget.selectionModel()
        self.selection_model.selectionChanged.connect(self.selection_changed)
        self.tree_vbox.addWidget(self.tree_view_widget)
        remove_item_button = QtGui.QPushButton('Remove item', self.tree_widget)
        remove_item_button.clicked.connect(self.remove_items)
        self.tree_vbox.addWidget(remove_item_button)
        line = QtGui.QFrame(self.tree_widget)
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Sunken)
        self.tree_vbox.addWidget(line)
        # test layout
        self.edit_items_layout = QtGui.QVBoxLayout(self.tree_widget)
        self.tree_vbox.addLayout(self.edit_items_layout)

    def check_parts(self, parts):
        for part in parts:
            if self.partsList.exist(part.Name):
                FreeCAD.Console.PrintError("Part %s is already configured" % part.Name)
                return False
        return True

    def add_parts(self):
        self.check_is_in_active_view()
        parts = selection.get_freecad_objects_list()
        last_index = None
        if not self.check_parts(parts):
            return
        for part in parts:
            try:
                item = self.partsList.append(part)
                last_index = self.model.append_part(item.name, item.label)
            except ValueError as e:
                FreeCAD.Console.PrintError(e)
                return
        self.force_selection(last_index)

    def add_same_parts(self):
        self.check_is_in_active_view()
        freecad_parts = selection.get_freecad_objects_list()
        index = None
        if len(freecad_parts) == 0 or not self.check_parts(freecad_parts):
            return
        try:
            item = self.partsList.append(freecad_parts[0])
            index = self.model.append_part(item.name, item.label)
            for part in freecad_parts[1:]:
                sub_item = self.partsList.append_link(part, freecad_parts[0])
                self.model.append_part(sub_item.name, sub_item.label, True)
        except ValueError as e:
            FreeCAD.Console.PrintError(e)
            return
        self.force_selection(index)
        return

    def remove_items(self):
        indexes = self.tree_view_widget.selectionModel().selectedIndexes()
        if len(indexes) == 0:
            FreeCAD.Console.PrintWarning("Nothing to remove\n")
            return
        parent_test_name = indexes[0].internalPointer().parent().get_name()
        for index in indexes:#[1:]:
            if index.internalPointer().parent().get_name() != parent_test_name:
                FreeCAD.Console.PrintError("No same level delete")
                return False
            elif index.internalPointer().child_count() > 0:
                FreeCAD.Console.PrintError("%s has children" % index.internalPointer().get_name())
                return False
        for index in indexes:
            item = index.internalPointer()
            if item.type == TreeItem.PART and len(self.partsList.get_linked_parts(item.get_name())) > 0:
                FreeCAD.Console.PrintError('Some parts are linked to this part %s\n' % item.get_name())
                return False
            elif item.type == TreeItem.TAB and len(self.tabsList.get_linked_tabs(item.get_name())) > 0:
                FreeCAD.Console.PrintError('Some tabs are linked to this tab %s\n' % item.get_name())
                return False

        for index in indexes:
            item = index.internalPointer()
            if item.type == TreeItem.PART or item.type == TreeItem.PART_LINK:
                self.partsList.remove(item.get_name())
            elif item.type == TreeItem.TAB or item.type == TreeItem.TAB_LINK:
                self.tabsList.remove(item.get_name())
            else:
                FreeCAD.Console.PrintError("Unknown deleter item")
        rows = sorted(set(index.row() for index in indexes))
        for row in reversed(rows):
            self.model.removeRow(row, indexes[0].parent())

        return

    def check_faces(self, faces):
        for face in faces:
            if not self.partsList.exist(face['freecad_object'].Name):
                FreeCAD.Console.PrintError("Part of face %s is not configured" % face['name'])
                return False
            elif self.tabsList.exist(face['name']):
                FreeCAD.Console.PrintError("Face %s already present" % face['name'])
                return False
        return True

    def add_tabs(self):
        self.check_is_in_active_view()
        faces = selection.get_freecad_faces_objects_list()
        last_index = None
        if self.check_faces(faces) is False:
            return
        for face in faces:
            try:
                item = self.tabsList.append(face, self.tab_type_box.currentText())
                last_index = self.model.append_tab(item.freecad_obj_name, item.tab_name, item.face_name)
            except ValueError as e:
                FreeCAD.Console.PrintError(e)
                return
        self.force_selection(last_index)
        return

    def add_same_tabs(self):
        self.check_is_in_active_view()
        faces = selection.get_freecad_faces_objects_list()
        index = None
        if self.check_faces(faces) is False or len(faces) == 0:
            return
        try:
            face = faces[0]
            item = self.tabsList.append(face, self.tab_type_box.currentText())
            index = self.model.append_tab(item.freecad_obj_name, item.tab_name, item.face_name)
            for face in faces[1:]:
                sub_item = self.tabsList.append_link(face, item.tab_name)
                self.model.append_tab(sub_item.freecad_obj_name, sub_item.tab_name, sub_item.face_name, True)

        except ValueError as e:
            FreeCAD.Console.PrintError(e)
            return
        self.force_selection(index)
        return

    def force_selection(self, index):
        self.selection_model.clearSelection()
        self.selection_model.select(index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)

    def selection_changed(self, selected, deselected):
        FreeCADGui.Selection.clearSelection()
        self.save_items_properties()
        self.edited_items = []
        self.remove_items_widgets()
        indexes = self.tree_view_widget.selectedIndexes()
        tab_indexes = []
        for index in indexes:
            if index.column() > 0:
                continue
            item = index.internalPointer()
            if item.type == TreeItem.TAB or item.type == TreeItem.TAB_LINK:
                tab_indexes.append(index)
                continue
            elif item.type == TreeItem.PART or item.type == TreeItem.PART_LINK :
                part, widget = self.partsList.get(item.get_name())
                fobj = self.active_document.getObject(part.name)
                FreeCADGui.Selection.addSelection(fobj)

                self.edited_items.append(widget)
                groupx_box, grid = widget.get_group_box(self.tree_widget)
                self.edit_items_layout.addWidget(groupx_box)

        for index in tab_indexes:
            if index.column() > 0:
                continue
            item = index.internalPointer()
            tab, widget = self.tabsList.get(item.get_name())
            if tab is None:
                raise ValueError("No tab named %s", item.get_name())
            if widget is None:
                raise ValueError("No widget named %s", item.get_name())
            fobj = self.active_document.getObject(tab.freecad_obj_name)
            FreeCADGui.Selection.addSelection(fobj, tab.face_name)

            self.edited_items.append(widget)
            groupx_box, grid = widget.get_group_box(self.tree_widget)
            self.edit_items_layout.addWidget(groupx_box)

        for index in tab_indexes:
            parent_index = index.parent()
            if parent_index.isValid():
                self.tree_view_widget.setExpanded(parent_index, True)

    def remove_items_widgets(self):
        for cnt in reversed(range(self.edit_items_layout.count())):
            # takeAt does both the jobs of itemAt and removeWidget
            # namely it removes an item and returns it
            widget = self.edit_items_layout.takeAt(cnt).widget()

            if widget is not None:
                # widget will be None if the item is a layout
                widget.deleteLater()

    def save_items_properties(self):
        for item in self.edited_items:
            item.get_properties()

    def init_params(self):
        self.params_widget = QtGui.QWidget()
        self.params_widget.setObjectName("ParamsPanel")
        self.params_widget.setWindowTitle("Parameters")
        self.params_vbox = QtGui.QVBoxLayout(self.params_widget)
        QtGui.QWidget().setLayout(self.params_vbox)
        parts_vbox = QtGui.QGridLayout(self.params_widget)
        self.hide_button = QtGui.QPushButton('Hide others', self.params_widget)
        parts_vbox.addWidget(self.hide_button, 0, 0)
        self.hide_button.clicked.connect(self.hide_others)
        self.show_button = QtGui.QPushButton('Show all', self.params_widget)
        parts_vbox.addWidget(self.show_button, 0, 1)
        self.show_button.clicked.connect(self.show_initial_objects)

        self.set_transparency_button = QtGui.QPushButton('Set transparent', self.params_widget)
        parts_vbox.addWidget(self.set_transparency_button, 1, 0)
        self.set_transparency_button.clicked.connect(self.set_transparency)
        self.reset_transparency_button = QtGui.QPushButton('Restore transparent', self.params_widget)
        parts_vbox.addWidget(self.reset_transparency_button, 1, 1)
        self.reset_transparency_button.clicked.connect(self.restore_transparency)

        preview_button = QtGui.QPushButton('Preview', self.params_widget)
        parts_vbox.addWidget(preview_button,2,0,1,2)
        preview_button.clicked.connect(self.preview)

    def abs_preview(self):
        self.preview(self.fast_preview.isChecked())

    def compute_parts(self):
        raise ValueError("Must overloaded")

    def preview(self, fast=False):
        raise ValueError("Must overloaded")

    def save_initial_objects(self):
        self.other_object_list = []
        objs = self.active_document.Objects
        for obj in objs:
            if obj.ViewObject.isVisible() and hasattr(obj.ViewObject,"Transparency"):
                self.other_object_list.append({'obj':obj, 'transparency':copy.copy(obj.ViewObject.Transparency)})

    def show_initial_objects(self):
        for obj in self.other_object_list:
            freecad_object = obj['obj']
            freecad_object.ViewObject.show()
        return

    def hide_others(self):
        current_obj_list = selection.get_freecad_objects_list()
        object_list = []
        if current_obj_list is None or len(current_obj_list) == 0:
            FreeCAD.Console.PrintError("No object selectionned\n")
            return
        objects = self.active_document.Objects
        for obj in objects:
            freecad_object = obj
            if freecad_object.ViewObject.isVisible() and freecad_object not in current_obj_list:
                freecad_object.ViewObject.hide()

    def restore_transparency(self):
        for obj in self.other_object_list:
            freecad_object = obj['obj']
            freecad_object.ViewObject.Transparency = obj['transparency']

    def set_transparency(self):
        for obj in self.other_object_list:
            freecad_object = obj['obj']
            freecad_object.ViewObject.Transparency = 90

    def check_is_in_active_view(self):
        if self.active_document != FreeCAD.ActiveDocument:
            raise ValueError("You have to select original document")
        return True

    def save_link_properties(self):
        self.partsList.get_parts_properties()
        self.tabsList.get_tabs_properties()
