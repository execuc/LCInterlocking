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
from toolwidget import ParamWidget, WidgetValue
import copy


class Part(ParamWidget):

    def __init__(self, cad_object):
        self.name = cad_object.Name
        self.label = cad_object.Label
        material = MaterialProperties(freecad_object=cad_object, type=MaterialProperties.TYPE_LASER_CUT)
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

    def __init__(self, cad_object, part_link):
        self.name = cad_object.Name
        self.label = cad_object.Label
        self.part_link = part_link
        material = MaterialProperties(freecad_object=cad_object, type=MaterialProperties.TYPE_LASER_CUT)
        ParamWidget.__init__(self, material)
        self.widget_list.extend([WidgetValue(type=str, name="new_name", show_name="New part name", widget=None)])

    def get_group_box(self, widget):
        group_box = QtGui.QGroupBox(widget)
        group_box.setFlat(False)
        self.form = widget
        grid = self.get_grid()
        title = QtGui.QLabel(self.form)
        title.setText("Linked part to : %s" % self.part_link.name)
        grid.addWidget(title, 1, 0, 1, 2)
        group_box.setLayout(grid)
        group_box.setTitle(self.name)
        return group_box, grid


class PartsList(object):

    def __init__(self, object_type=Part):
        self.part_list = []
        self.object_type = object_type
        return

    def append(self, freecad_object):
        if self.exist(freecad_object.Name):
            raise ValueError(freecad_object.Name + " already in interactor parts list")
        else:
            self.part_list.append(self.object_type(freecad_object))
        return self.part_list[-1]

    def append_link(self, freecad_object, freecad_object_src):
        if self.exist(freecad_object.Name):
            raise ValueError(freecad_object.Name + " already in interactor parts list")
        else:
            src_part_element = self.get(freecad_object_src.Name)
            if src_part_element is None:
                raise ValueError("No original part found")
            self.part_list.append(PartLink(freecad_object, src_part_element))
            if self.part_list[-1].properties().thickness != src_part_element.properties().thickness:
                del self.part_list[-1]
                raise ValueError(freecad_object.Name + " does not have the same thickness")

        return self.part_list[-1]

    def remove(self, name):
        found = None
        linked_parts = self.get_linked_parts(name)
        if len(linked_parts) > 0:
            raise ValueError('Some parts are linked to this part %s' % name)

        for part in self.part_list:
            if part.name == name:
                found = part
                break
        if found is not None:
            self.part_list.remove(found)

    def get_linked_parts(self, name):
        el_list = []
        for part in self.part_list:
            if isinstance(part, PartLink) and part.part_link.name == name:
                el_list.append(part)
        return el_list

    def exist(self, name):
        for part in self.part_list:
            if part.name == name:
                return True
        return False

    def get(self, name):
        for part in self.part_list:
            if part.name == name:
                return part
        return None

    def __iter__(self):
        return iter(self.part_list)

    def get_parts_properties(self):
        part_properties = []
        for part in self.part_list:
            if isinstance(part, PartLink):
                linked_properties = copy.copy(part.part_link.properties())
                linked_properties.freecad_object = part.properties().freecad_object
                linked_properties.new_name = part.properties().new_name
                part_properties.append(linked_properties)
            else:
                part_properties.append(part.properties())

        return part_properties




