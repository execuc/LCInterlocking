#!/usr/bin/env python

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
        obj.addProperty('App::PropertyPythonObject', 'invertStates').invertStates = {}
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

            # Convert string keys to tuples for make_cross_parts
            invert_states = {}
            if hasattr(fp, 'invertStates') and fp.invertStates:
                for key, value in fp.invertStates.items():
                    if isinstance(key, str) and '|' in key:
                        part1_name, part2_name = key.split('|', 1)
                        invert_states[(part1_name, part2_name)] = value
                    elif isinstance(key, tuple):
                        invert_states[key] = value
            computed_parts = make_cross_parts(parts, dry_run=False, invert_states=invert_states)
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
            # Convert string keys to tuples for make_cross_parts
            invert_states = {}
            if hasattr(fp, 'invertStates') and fp.invertStates:
                for key, value in fp.invertStates.items():
                    if isinstance(key, str) and '|' in key:
                        part1_name, part2_name = key.split('|', 1)
                        invert_states[(part1_name, part2_name)] = value
                    elif isinstance(key, tuple):
                        invert_states[key] = value
            computed_parts = make_cross_parts(parts, dry_run=False, invert_states=invert_states)

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
    
    def unsetEdit(self, vobj, mode=0):
        FreeCADGui.Control.closeDialog()
        return

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
        # Initialize attributes before super().__init__() because init_tree_widget is called during parent init
        self.interactions = []
        self.interactions_list_widget = None
        self.interaction_checkboxes = {}  # Store checkboxes by interaction key
        self.selected_interaction = None
        
        super(CrossPiece, self).__init__("Crosspiece", obj_join)
        self.obj_join = obj_join
        self.parts_origin = copy.deepcopy(obj_join.parts)
        self.obj_join.edit = True

    def accept(self):
        self.compute(False)
        FreeCADGui.ActiveDocument.resetEdit()
        return True

    def reject(self):
        self.obj_join.parts = self.parts_origin
        self.obj_join.edit = False
        FreeCADGui.ActiveDocument.resetEdit()
        return True

    def compute(self, preview):
        self.save_items_properties()
        self.save_link_properties()
        self.save_invert_states()  # Save invert checkbox states
        if not preview:
            self.obj_join.need_recompute = True
        else:
            self.obj_join.preview = PREVIEW_NORMAL

    def preview(self):
        self.compute(True)
        self.selection_changed(None, None)
        return
    
    def selection_changed(self, selected, deselected):
        """Override to deselect interactions when tree selection changes"""
        # Deselect interactions when tree selection changes
        # Block signals to prevent recursive calls
        if hasattr(self, 'interactions_list_widget') and self.interactions_list_widget:
            self.interactions_list_widget.blockSignals(True)
            self.interactions_list_widget.clearSelection()
            self.interactions_list_widget.blockSignals(False)
        
        # Call parent method
        super(CrossPiece, self).selection_changed(selected, deselected)

    def init_tree_widget(self):
        #Preview button
        v_box = QtGui.QVBoxLayout()
        preview_button = QtGui.QPushButton('Preview', self.tree_widget)
        preview_button.clicked.connect(self.preview)
        #self.fast_preview = QtGui.QCheckBox("Fast preview", self.tree_widget)
        line = QtGui.QFrame(self.tree_widget)
        line.setFrameShape(QtGui.QFrame.HLine);
        line.setFrameShadow(QtGui.QFrame.Sunken);
        h_box = QtGui.QHBoxLayout()
        h_box.addWidget(preview_button)
        #h_box.addWidget(self.fast_preview)
        v_box.addLayout(h_box)
        v_box.addWidget(line)
        self.tree_vbox.addLayout(v_box)
        # Add part buttons
        h_box = QtGui.QHBoxLayout()
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
        # Parameters layout (where part properties are displayed)
        self.edit_items_layout = QtGui.QVBoxLayout()
        self.tree_vbox.addLayout(self.edit_items_layout)
        # Separator line before interactions
        line = QtGui.QFrame(self.tree_widget)
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Sunken)
        self.tree_vbox.addWidget(line)
        # Interactions section (after parameters)
        interactions_label = QtGui.QLabel('Interactions:', self.tree_widget)
        self.tree_vbox.addWidget(interactions_label)
        self.interactions_list_widget = QtGui.QListWidget(self.tree_widget)
        self.interactions_list_widget.setFixedHeight(150)
        # Set selection mode to single selection (only one interaction can be selected at a time)
        self.interactions_list_widget.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.interactions_list_widget.itemSelectionChanged.connect(self.on_interaction_selected)
        self.tree_vbox.addWidget(self.interactions_list_widget)
        
        # Calculate initial interactions
        self.update_interactions()
    
    def update_interactions(self):
        """Calculate and display interactions between parts"""
        # Get invert states from obj_join and convert string keys to tuples
        invert_states = {}
        if hasattr(self.obj_join, 'invertStates') and self.obj_join.invertStates:
            for key, value in self.obj_join.invertStates.items():
                if isinstance(key, str) and '|' in key:
                    part1_name, part2_name = key.split('|', 1)
                    invert_states[(part1_name, part2_name)] = value
                elif isinstance(key, tuple):
                    invert_states[key] = value
        
        # Calculate interactions
        parts = []
        for part in self.obj_join.parts.lst:
            cp_part = copy.deepcopy(part)
            freecad_obj = self.active_document.getObject(cp_part.name)
            if freecad_obj is None:
                continue
            cp_part.recomputeInit(freecad_obj)
            parts.append(cp_part)
        
        if len(parts) < 2:
            self.interactions = []
            if hasattr(self, 'interactions_list_widget') and self.interactions_list_widget:
                self.interactions_list_widget.clear()
            if hasattr(self, 'interaction_checkboxes'):
                self.interaction_checkboxes.clear()
            return
        
        try:
            _, interactions = make_cross_parts(parts, dry_run=True, invert_states=invert_states)
            self.interactions = interactions
            
            # Update UI
            if hasattr(self, 'interactions_list_widget') and self.interactions_list_widget:
                self.interactions_list_widget.clear()
            if hasattr(self, 'interaction_checkboxes'):
                self.interaction_checkboxes.clear()
            
            for interaction in interactions:
                interaction_key = (interaction['part1_name'], interaction['part2_name'])
                
                # Create display text
                display_text = interaction['display_name']
                if interaction['type'] == 'error' or interaction['type'] == 'not_managed':
                    display_text += " [ERROR: " + interaction.get('error', 'Unknown error') + "]"
                
                # Create item widget with label and optional checkbox
                item_widget = QtGui.QWidget()
                item_layout = QtGui.QHBoxLayout(item_widget)
                item_layout.setContentsMargins(4, 2, 4, 2)
                
                label = QtGui.QLabel(display_text)
                item_layout.addWidget(label)
                
                # Add checkbox for parametrable interactions
                if interaction.get('parametrable', False):
                    checkbox = QtGui.QCheckBox("Invert", self.tree_widget)
                    # Get the actual state from invertStates (may differ from interaction['invert_y'])
                    key_str = "%s|%s" % (interaction_key[0], interaction_key[1])
                    actual_state = False
                    if hasattr(self.obj_join, 'invertStates') and self.obj_join.invertStates:
                        actual_state = self.obj_join.invertStates.get(key_str, interaction['invert_y'])
                    else:
                        actual_state = interaction['invert_y']
                    
                    # Set initial state (no signal connection - state will be saved on OK/Preview/Add/Remove)
                    checkbox.setChecked(actual_state)
                    self.interaction_checkboxes[interaction_key] = checkbox
                    item_layout.addWidget(checkbox)
                
                item_layout.addStretch()
                
                item = QtGui.QListWidgetItem()
                item.setData(QtCore.Qt.UserRole, interaction)
                item.setSizeHint(item_widget.sizeHint())
                if hasattr(self, 'interactions_list_widget') and self.interactions_list_widget:
                    self.interactions_list_widget.addItem(item)
                    self.interactions_list_widget.setItemWidget(item, item_widget)
        except Exception as e:
            FreeCAD.Console.PrintError("Error calculating interactions: %s\n" % str(e))
            self.interactions = []
            if hasattr(self, 'interactions_list_widget') and self.interactions_list_widget:
                self.interactions_list_widget.clear()
            if hasattr(self, 'interaction_checkboxes'):
                self.interaction_checkboxes.clear()
    
    def on_interaction_selected(self):
        """Handle interaction selection to highlight parts in 3D view"""
        if not hasattr(self, 'interactions_list_widget') or not self.interactions_list_widget:
            return
        selected_items = self.interactions_list_widget.selectedItems()
        
        # Deselect tree view when interaction is selected
        # Block signals to prevent recursive calls
        if len(selected_items) > 0:
            if hasattr(self, 'selection_model') and self.selection_model:
                # clearSelection() deselects all items in the tree view (parts list)
                self.selection_model.blockSignals(True)
                self.selection_model.clearSelection()
                self.selection_model.blockSignals(False)
                self.clear_parameter_widgets()
                
        
        FreeCADGui.Selection.clearSelection()
        
        if len(selected_items) == 0:
            self.selected_interaction = None
            return
        
        item = selected_items[0]
        interaction = item.data(QtCore.Qt.UserRole)
        
        if interaction:
            self.selected_interaction = interaction
            # Highlight the two parts
            try:
                part1_obj = self.active_document.getObject(interaction['part1_name'])
                part2_obj = self.active_document.getObject(interaction['part2_name'])
                if part1_obj:
                    FreeCADGui.Selection.addSelection(part1_obj)
                if part2_obj:
                    FreeCADGui.Selection.addSelection(part2_obj)
            except Exception as e:
                FreeCAD.Console.PrintError("Error highlighting parts: %s\n" % str(e))
    
    def save_invert_states(self):
        """Save the current state of all invert checkboxes to obj_join.invertStates"""
        if not hasattr(self.obj_join, 'invertStates'):
            self.obj_join.invertStates = {}
        
        # Save all checkbox states
        for interaction_key, checkbox in self.interaction_checkboxes.items():
            checked = checkbox.isChecked()
            # Convert tuple key to string for FreeCAD property storage
            key_str = "%s|%s" % (interaction_key[0], interaction_key[1])
            self.obj_join.invertStates[key_str] = checked
    
    def add_parts(self):
        """Override to recalculate interactions after adding parts"""
        self.save_invert_states()  # Save invert checkbox states before updating
        super(CrossPiece, self).add_parts()
        self.update_interactions()
    
    def add_same_parts(self):
        """Override to recalculate interactions after adding same parts"""
        self.save_invert_states()  # Save invert checkbox states before updating
        super(CrossPiece, self).add_same_parts()
        self.update_interactions()
    
    def remove_items(self):
        """Override to recalculate interactions after removing items"""
        self.save_invert_states()  # Save invert checkbox states before updating
        result = super(CrossPiece, self).remove_items()
        if result is not False:
            self.update_interactions()
        return result

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
        CrossPieceViewProvider(groupCross.ViewObject)
        FreeCADGui.ActiveDocument.setEdit(groupCross.Name)
        return

Gui.addCommand('crosspiece', CrossPieceCommand())
