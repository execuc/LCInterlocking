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
    
    def _convert_invert_states(self, invert_states_dict):
        """Convert string keys to tuples for make_cross_parts"""
        if not invert_states_dict:
            return {}
        result = {}
        for key, value in invert_states_dict.items():
            if isinstance(key, str) and '|' in key:
                part1_name, part2_name = key.split('|', 1)
                result[(part1_name, part2_name)] = value
            elif isinstance(key, tuple):
                result[key] = value
        return result

    def onChanged(self, fp, prop):
        if prop == "need_recompute":
            self.execute(fp)
        elif prop == "preview":
            self.full_preview(fp)
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

    def full_preview(self, fp):
        if fp.preview != PREVIEW_NONE:
            fp.preview = PREVIEW_NONE

            document = fp.Document
            full_preview_doc_name = str(fp.Name) + "_preview_parts"
            new_doc = False
            try:
                full_preview_doc = FreeCAD.getDocument(full_preview_doc_name)
                objs = full_preview_doc.Objects
                for obj in objs:
                    full_preview_doc.removeObject(obj.Name)
            except:
                new_doc = True
                full_preview_doc = FreeCAD.newDocument(full_preview_doc_name)

            parts = []
            for part in fp.parts.lst:
                cp_part = copy.deepcopy(part)
                freecad_obj = document.getObject(cp_part.name)
                cp_part.recomputeInit(freecad_obj)
                parts.append(cp_part)

            # Convert string keys to tuples for make_cross_parts
            invert_states = self._convert_invert_states(
                fp.invertStates if hasattr(fp, 'invertStates') and fp.invertStates else {}
            )
            computed_parts = make_cross_parts(parts, dry_run=False, invert_states=invert_states)
            for part in computed_parts:
                new_shape = full_preview_doc.addObject("Part::Feature", part.get_new_name())
                new_shape.Shape = part.get_shape()
            full_preview_doc.recompute()
            if new_doc:
                FreeCADGui.getDocument(full_preview_doc.Name).ActiveView.fitAll()


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
            invert_states = self._convert_invert_states(
                fp.invertStates if hasattr(fp, 'invertStates') and fp.invertStates else {}
            )
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
        self.live_preview_objects = []  # Store temporary objects created for interaction preview
        
        super(CrossPiece, self).__init__("Crosspiece", obj_join)
        self.obj_join = obj_join
        self.parts_origin = copy.deepcopy(obj_join.parts)
        self.obj_join.edit = True

    def accept(self):
        # Clear temporary preview before accepting
        self.clear_live_preview()
        self.compute(False)
        FreeCADGui.ActiveDocument.resetEdit()
        return True

    def reject(self):
        # Clear temporary preview before rejecting
        self.clear_live_preview()
        self.obj_join.parts = self.parts_origin
        self.obj_join.edit = False
        FreeCADGui.ActiveDocument.resetEdit()
        return True

    def compute(self, full_preview):
        self.save_items_properties()
        self.save_link_properties()
        self.save_invert_states()  # Save invert checkbox states
        if not full_preview:
            self.obj_join.need_recompute = True
        else:
            self.obj_join.preview = PREVIEW_NORMAL

    def full_preview(self):
        # Clear temporary preview before full preview
        self.clear_live_preview()
        self.compute(True)
        self.selection_changed(None, None)
        return
    
    def selection_changed(self, selected, deselected):
        """Override to deselect interactions when tree selection changes"""
        # Clear live preview when selecting a part (deselecting interaction)
        self.clear_live_preview()
        self.selected_interaction = None
        
        # Deselect interactions when tree selection changes
        # Block signals to prevent recursive calls
        if hasattr(self, 'interactions_list_widget') and self.interactions_list_widget:
            self.save_invert_states()
            self.interactions_list_widget.blockSignals(True)
            self.interactions_list_widget.clearSelection()
            self.interactions_list_widget.blockSignals(False)
        
        # Call parent method
        super(CrossPiece, self).selection_changed(selected, deselected)

    def init_tree_widget(self):
        #Preview button
        v_box = QtGui.QVBoxLayout()
        preview_button = QtGui.QPushButton('Preview', self.tree_widget)
        preview_button.clicked.connect(self.full_preview)
        line = QtGui.QFrame(self.tree_widget)
        line.setFrameShape(QtGui.QFrame.HLine);
        line.setFrameShadow(QtGui.QFrame.Sunken);
        h_box = QtGui.QHBoxLayout()
        h_box.addWidget(preview_button)
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
        # Center-align column headers in tree view
        self.tree_view_widget.header().setDefaultAlignment(QtCore.Qt.AlignCenter)
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
        self.interactions_list_widget = QtGui.QTableWidget(self.tree_widget)
        # Set selection mode to single selection (only one interaction can be selected at a time)
        self.interactions_list_widget.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.interactions_list_widget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        # Set column headers
        self.interactions_list_widget.setColumnCount(2)
        # Set header labels - use setHorizontalHeaderLabels which is more reliable
        self.interactions_list_widget.setHorizontalHeaderLabels(['Interaction', 'Invert'])
        self.interactions_list_widget.setFixedHeight(250)
        # Style headers: center-aligned
        header = self.interactions_list_widget.horizontalHeader()
        header.setDefaultAlignment(QtCore.Qt.AlignCenter)
        self.interactions_list_widget.horizontalHeader().setStretchLastSection(False)
        # Use setSectionResizeMode instead of setResizeMode (newer PySide API)
        try:
            self.interactions_list_widget.horizontalHeader().setSectionResizeMode(0, QtGui.QHeaderView.Stretch)
        except AttributeError:
            # Fallback for older PySide versions
            self.interactions_list_widget.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.interactions_list_widget.setColumnWidth(1, 80)
        # Make sure headers are visible
        self.interactions_list_widget.horizontalHeader().setVisible(True)
        # Style the table to match the parts list appearance
        self.interactions_list_widget.setAlternatingRowColors(False)
        self.interactions_list_widget.setShowGrid(False)  # No grid lines between rows
        self.interactions_list_widget.verticalHeader().setVisible(False)
        self.interactions_list_widget.itemSelectionChanged.connect(self.on_interaction_selected)
        self.tree_vbox.addWidget(self.interactions_list_widget)
        
        # Calculate initial interactions
        self.update_interactions()
    
    def _convert_invert_states(self, invert_states_dict):
        """Convert string keys to tuples for make_cross_parts"""
        if not invert_states_dict:
            return {}
        result = {}
        for key, value in invert_states_dict.items():
            if isinstance(key, str) and '|' in key:
                part1_name, part2_name = key.split('|', 1)
                result[(part1_name, part2_name)] = value
            elif isinstance(key, tuple):
                result[key] = value
        return result
    
    def _get_part_object(self, part_name):
        """Helper to safely get a part object from document"""
        try:
            return self.active_document.getObject(part_name)
        except:
            return None
    
    def _show_all_parts(self):
        """Show all parts from parts list"""
        if hasattr(self.obj_join, 'parts'):
            for part in self.obj_join.parts.lst:
                part_obj = self._get_part_object(part.name)
                if part_obj and hasattr(part_obj, 'ViewObject'):
                    try:
                        part_obj.ViewObject.show()
                    except:
                        pass
    
    def update_interactions(self):
        """Calculate and display interactions between parts"""
        # Get invert states from obj_join and convert string keys to tuples
        invert_states = self._convert_invert_states(
            self.obj_join.invertStates if hasattr(self.obj_join, 'invertStates') and self.obj_join.invertStates else {}
        )
        
        # Calculate interactions
        parts = []
        for part in self.obj_join.parts.lst:
            cp_part = copy.deepcopy(part)
            freecad_obj = self._get_part_object(cp_part.name)
            if freecad_obj is None:
                continue
            cp_part.recomputeInit(freecad_obj)
            parts.append(cp_part)
        
        if len(parts) < 2:
            self.interactions = []
            if hasattr(self, 'interactions_list_widget') and self.interactions_list_widget:
                self.interactions_list_widget.setRowCount(0)
            if hasattr(self, 'interaction_checkboxes'):
                self.interaction_checkboxes.clear()
            return
        
        try:
            _, interactions = make_cross_parts(parts, dry_run=True, invert_states=invert_states)
            self.interactions = interactions
            
            # Update UI
            if hasattr(self, 'interactions_list_widget') and self.interactions_list_widget:
                self.interactions_list_widget.setRowCount(0)
            if hasattr(self, 'interaction_checkboxes'):
                self.interaction_checkboxes.clear()
            
            for interaction in interactions:
                interaction_key = (interaction['part1_name'], interaction['part2_name'])
                
                # Get labels for both parts
                part1_label = interaction['part1_name']
                part2_label = interaction['part2_name']
                try:
                    part1_obj, _ = self.partsList.get(interaction['part1_name'])
                    if part1_obj:
                        part1_label = part1_obj.label
                except:
                    pass
                try:
                    part2_obj, _ = self.partsList.get(interaction['part2_name'])
                    if part2_obj:
                        part2_label = part2_obj.label
                except:
                    pass
                
                # Create interaction display text: "Name1 (label1) -> Name2 (label2)"
                interaction_text = "%s (%s) -> %s (%s)" % (
                    interaction['part1_name'], part1_label,
                    interaction['part2_name'], part2_label
                )
                
                # Add error indicator if needed
                if interaction['type'] == 'error' or interaction['type'] == 'not_managed':
                    error_text = " [ERROR: " + interaction.get('error', 'Unknown error') + "]"
                    interaction_text += error_text
                
                # Add row to table
                row = self.interactions_list_widget.rowCount()
                self.interactions_list_widget.insertRow(row)
                
                # Column 0: Interaction text
                interaction_item = QtGui.QTableWidgetItem(interaction_text)
                interaction_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                interaction_item.setData(QtCore.Qt.UserRole, interaction)
                self.interactions_list_widget.setItem(row, 0, interaction_item)
                
                # Column 1: Invert checkbox (if parametrable) or empty
                if interaction.get('parametrable', False):
                    checkbox = QtGui.QCheckBox("", self.tree_widget)  # No text, just checkbox
                    # Get the actual state from invertStates (may differ from interaction['invert_y'])
                    key_str = "%s|%s" % (interaction_key[0], interaction_key[1])
                    actual_state = False
                    if hasattr(self.obj_join, 'invertStates') and self.obj_join.invertStates:
                        actual_state = self.obj_join.invertStates.get(key_str, interaction['invert_y'])
                    else:
                        actual_state = interaction['invert_y']
                    
                    # Set initial state
                    checkbox.setChecked(actual_state)
                    self.interaction_checkboxes[interaction_key] = checkbox
                    # Connect checkbox to update preview when clicked
                    checkbox.stateChanged.connect(lambda state, key=interaction_key: self.on_invert_changed(key, state))
                    # Center the checkbox in the cell
                    checkbox_widget = QtGui.QWidget()
                    checkbox_layout = QtGui.QHBoxLayout(checkbox_widget)
                    checkbox_layout.setAlignment(QtCore.Qt.AlignCenter)
                    checkbox_layout.setContentsMargins(0, 0, 0, 0)
                    checkbox_layout.addWidget(checkbox)
                    self.interactions_list_widget.setCellWidget(row, 1, checkbox_widget)
                else:
                    # Empty cell for non-parametrable interactions
                    empty_item = QtGui.QTableWidgetItem("")
                    empty_item.setFlags(QtCore.Qt.NoItemFlags)
                    self.interactions_list_widget.setItem(row, 1, empty_item)
        except Exception as e:
            FreeCAD.Console.PrintError("Error calculating interactions: %s\n" % str(e))
            self.interactions = []
            if hasattr(self, 'interactions_list_widget') and self.interactions_list_widget:
                self.interactions_list_widget.setRowCount(0)
            if hasattr(self, 'interaction_checkboxes'):
                self.interaction_checkboxes.clear()
    
    def clear_live_preview(self):
        """Clear temporary preview objects created for interaction preview and restore original parts"""
        # Remove temporary objects
        if hasattr(self, 'live_preview_objects'):
            for obj in self.live_preview_objects:
                try:
                    if obj and obj in self.active_document.Objects:
                        self.active_document.removeObject(obj.Name)
                except:
                    pass
            self.live_preview_objects = []
        # Restore original parts visibility
        self._show_all_parts()
        
        # Also restore parts from fromParts
        if hasattr(self.obj_join, 'fromParts') and self.obj_join.fromParts:
            for obj in self.obj_join.fromParts:
                try:
                    if obj and hasattr(obj, 'ViewObject'):
                        obj.ViewObject.show()
                except:
                    pass
    
    def generate_live_preview(self, interaction):
        """Generate temporary preview objects for the selected interaction"""
        if not interaction:
            return
        try:
            # Clear any existing live preview first
            if hasattr(self, 'live_preview_objects') and len(self.live_preview_objects) > 0:
                # Remove temporary objects
                for obj in self.live_preview_objects:
                    try:
                        if obj and obj in self.active_document.Objects:
                            self.active_document.removeObject(obj.Name)
                    except:
                        pass
                self.live_preview_objects = []
            
            # Restore visibility of ALL parts first (in case some were hidden from previous interaction)
            self._show_all_parts()
            
            # Get the two parts for this interaction
            part1_name = interaction['part1_name']
            part2_name = interaction['part2_name']
            
            # Hide only the two parts involved in this interaction (not all parts)
            part1_obj = self._get_part_object(part1_name)
            if part1_obj and hasattr(part1_obj, 'ViewObject'):
                try:
                    part1_obj.ViewObject.hide()
                except:
                    pass
            
            part2_obj = self._get_part_object(part2_name)
            if part2_obj and hasattr(part2_obj, 'ViewObject'):
                try:
                    part2_obj.ViewObject.hide()
                except:
                    pass
            
            # Find the parts in the parts list
            part1 = None
            part2 = None
            for part in self.obj_join.parts.lst:
                if part.name == part1_name:
                    part1 = part
                elif part.name == part2_name:
                    part2 = part
            
            if part1 and part2:
                # Create deep copies and initialize
                cp_part1 = copy.deepcopy(part1)
                cp_part2 = copy.deepcopy(part2)
                part1_obj = self._get_part_object(part1_name)
                part2_obj = self._get_part_object(part2_name)
                if part1_obj:
                    cp_part1.recomputeInit(part1_obj)
                if part2_obj:
                    cp_part2.recomputeInit(part2_obj)
                
                # Get invert state for this interaction
                interaction_key = (part1_name, part2_name)
                key_str = "%s|%s" % (part1_name, part2_name)
                invert_states = {}
                # Get invert state from checkbox if available (most up-to-date)
                invert_y = False
                if hasattr(self, 'interaction_checkboxes') and interaction_key in self.interaction_checkboxes:
                    # Get current state directly from checkbox
                    invert_y = self.interaction_checkboxes[interaction_key].isChecked()
                elif hasattr(self.obj_join, 'invertStates') and self.obj_join.invertStates:
                    # Fallback to saved state
                    invert_y = self.obj_join.invertStates.get(key_str, False)
                invert_states[interaction_key] = invert_y
                
                # Generate cross parts for just these two parts
                parts_list = [cp_part1, cp_part2]
                computed_parts = make_cross_parts(parts_list, dry_run=False, invert_states=invert_states)
                
                # Create temporary objects in the document
                for part in computed_parts:
                    temp_obj = self.active_document.addObject("Part::Feature", "temp_" + part.get_new_name())
                    temp_obj.Shape = part.get_shape()
                    temp_obj.ViewObject.show()
                    self.live_preview_objects.append(temp_obj)
                
                self.active_document.recompute()
                
                # Select the temporary preview objects in 3D view
                FreeCADGui.Selection.clearSelection()
                for temp_obj in self.live_preview_objects:
                    try:
                        FreeCADGui.Selection.addSelection(temp_obj)
                    except:
                        pass
                
        except Exception as e:
            FreeCAD.Console.PrintError("Error creating temporary preview: %s\n" % str(e))
            # Restore original parts on error
            if hasattr(self.obj_join, 'fromParts'):
                for obj in self.obj_join.fromParts:
                    try:
                        obj.ViewObject.show()
                    except:
                        pass
    
    def on_interaction_selected(self):
        """Handle interaction selection to show temporary crosspiece preview"""
        if not hasattr(self, 'interactions_list_widget') or not self.interactions_list_widget:
            return
        selected_ranges = self.interactions_list_widget.selectedRanges()
        
        # Deselect tree view when interaction is selected
        # Block signals to prevent recursive calls
        if len(selected_ranges) > 0:
            if hasattr(self, 'selection_model') and self.selection_model:
                # clearSelection() deselects all items in the tree view (parts list)
                self.selection_model.blockSignals(True)
                self.selection_model.clearSelection()
                self.selection_model.blockSignals(False)
                self.clear_parameter_widgets()
        
        FreeCADGui.Selection.clearSelection()
        
        if len(selected_ranges) == 0:
            # Deselection: clear temporary preview and restore original parts
            self.clear_live_preview()
            self.selected_interaction = None
            return
        
        # Get the first selected row
        selected_row = selected_ranges[0].topRow()
        # Get interaction data from first column (Name 1)
        item = self.interactions_list_widget.item(selected_row, 0)
        if item is None:
            self.selected_interaction = None
            return
        
        interaction = item.data(QtCore.Qt.UserRole)
        
        if interaction:
            self.selected_interaction = interaction
            self.generate_live_preview(interaction)
    
    def on_invert_changed(self, interaction_key, state):
        """Called when an invert checkbox is changed - update state and regenerate preview if needed"""
        # Save the state immediately
        key_str = "%s|%s" % (interaction_key[0], interaction_key[1])
        if not hasattr(self.obj_join, 'invertStates'):
            self.obj_join.invertStates = {}
        self.obj_join.invertStates[key_str] = (state == QtCore.Qt.Checked)
        
        # If this interaction is currently selected, regenerate the preview
        if hasattr(self, 'selected_interaction') and self.selected_interaction:
            current_key = (self.selected_interaction['part1_name'], self.selected_interaction['part2_name'])
            if current_key == interaction_key:
                # Clear and regenerate preview with new invert state
                self.clear_live_preview()
                self.generate_live_preview(self.selected_interaction)
    
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
