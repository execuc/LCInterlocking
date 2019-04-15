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


from PySide import QtCore, QtGui
from lasercut.material import MaterialProperties
from lasercut.helper import compare_value
from panel.toolwidget import ParamWidget, WidgetValue
import copy
import FreeCAD # todo : remove import

class Part(ParamWidget):

    def __init__(self, material):
        self.name = material.name
        self.label = material.label
        self.link_name = None

        ParamWidget.__init__(self, material)
        self.widget_list.extend([WidgetValue(type=str, name="new_name", show_name="New part name", widget=None),
                                 WidgetValue(type=float, name="thickness", show_name="Thickness", widget=None,
                                             interval_value=[0.5, 3000.], decimals=2, step=0.5),
                                 WidgetValue(type=float, name="thickness_tolerance", show_name="Thickness tolerance",
                                             widget=None, interval_value=[0., 30.], decimals=4, step=0.05),
                                 WidgetValue(type=float, name="hole_width_tolerance", show_name="Slot width tolerance",
                                             widget=None, interval_value=[0., 30.], decimals=4, step=0.05),
                                 WidgetValue(type=float, name="laser_beam_diameter", show_name="Laser beam diameter",
                                             widget=None, interval_value=[0., 30.], decimals=4, step=0.05)])


class CrossPartWidget(Part):

    def __init__(self, cad_object):
        Part.__init__(self, cad_object)
        self.widget_list.extend([WidgetValue(type=list, name="node_type", show_name="Node type", widget=None,
                                             interval_value=[MaterialProperties.NODE_NO,
                                                             MaterialProperties.NODE_SINGLE_SHORT,
                                                             MaterialProperties.NODE_SINGLE_LONG,
                                                             MaterialProperties.NODE_DUAL_SHORT]),
                                 WidgetValue(type=float, name="node_thickness", show_name="Node thickness",
                                             widget=None, interval_value=[0., 30.], decimals=4, step=0.05,
                                             parent_name="node_type",
                                             parent_value=[MaterialProperties.NODE_SINGLE_SHORT,
                                                           MaterialProperties.NODE_SINGLE_LONG,
                                                           MaterialProperties.NODE_DUAL_SHORT]),
                                 WidgetValue(type=bool, name="dog_bone", show_name="Dog bone hole", widget=None)])


class PartLink(ParamWidget):

    def __init__(self, material):
        self.name = material.name
        self.label = material.label
        self.link_name = material.link_name
        ParamWidget.__init__(self, material)
        self.widget_list.extend([WidgetValue(type=str, name="new_name", show_name="New part name", widget=None)])

    def get_group_box(self, widget):
        group_box = QtGui.QGroupBox(widget)
        group_box.setFlat(False)
        self.form = widget
        grid = self.get_grid()
        title = QtGui.QLabel(self.form)
        title.setText("Linked part to : %s" % self.link_name)
        grid.addWidget(title, 1, 0, 1, 2)
        group_box.setLayout(grid)
        group_box.setTitle(self.name)
        return group_box, grid


class PartsList(object):

    def __init__(self, object_type, parts):
        self.part_list = parts
        self.object_type = object_type
        return

    def append(self, freecad_object):
        if self.exist(freecad_object.Name):
            raise ValueError(freecad_object.Name + " already in interactor parts list")
        else:
            material = MaterialProperties(type=MaterialProperties.TYPE_LASER_CUT,
                                          name=freecad_object.Name, label=freecad_object.Label,
                                          freecad_object=freecad_object)
            self.part_list.append(material)
        return self.part_list[-1]

    def append_link(self, freecad_object, freecad_object_src):
        if self.exist(freecad_object.Name):
            raise ValueError(freecad_object.Name + " already in interactor parts list")
        else:
            src_part_element, widget = self.get(freecad_object_src.Name)
            if src_part_element is None:
                raise ValueError("No original part found")

            material = MaterialProperties(type=MaterialProperties.TYPE_LASER_CUT,
                                          name=freecad_object.Name, label=freecad_object.Label,
                                          freecad_object=freecad_object, link_name=freecad_object_src.Name)
            if not compare_value(material.thickness, src_part_element.thickness):
                raise ValueError(freecad_object.Name + " does not have the same thickness")

            self.part_list.append(material)

        return self.part_list[-1]

    def remove(self, name):
        found_index = None
        linked_parts = self.get_linked_parts(name)
        if len(linked_parts) > 0:
            FreeCAD.Console.PrintError('Some parts are linked to this part %s\n' % name)
            raise ValueError('Some parts are linked to this part %s' % name)

        for index in range(len(self.part_list)):
            if self.part_list[index].name == name:
                found_index = index
                break
        if found_index is not None:
            self.part_list.pop(found_index)

    def get_linked_parts(self, name):
        el_list = []
        part_lst = self.part_list.lst
        for part in part_lst:
            if part.link_name == name:
                el_list.append(part.name)
        return el_list

    def exist(self, name):
        for part in self.part_list:
            if part.name == name:
                return True
        return False

    def get(self, name):
        for index in range(len(self.part_list)):
            if self.part_list[index].name == name:
                material = self.part_list[index]
                if not material.link_name:
                    widget = self.object_type(material)
                else:
                    widget = PartLink(material)
                return material, widget

        return None, None

    def __iter__(self):
        return iter(self.part_list)

    def get_parts_properties(self):
        part_properties = []
        for part in self.part_list.lst:
            if part.link_name:
                part_link, widget = self.get(part.link_name)
                new_part = copy.deepcopy(part_link)
                new_part.new_name = part.new_name
                new_part.name = part.name
                new_part.link_name = part.link_name

                part_properties.append(new_part)
            else:
                part_properties.append(copy.deepcopy(part))

        self.part_list.lst = part_properties

        return part_properties
