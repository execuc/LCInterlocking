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

from PySide import QtGui
from lasercut.tabproperties import TabProperties
from toolwidget import ParamWidget, WidgetValue
import copy


class BaseTabWidget(ParamWidget):

    def __init__(self, cad_face, cad_object, name, t_type):
        self.name = "%s.%s" % (cad_object.Name, name)
        self.description = "%s.%s (%s)" % (cad_object.Name, name, t_type)
        self.real_name = name
        tab_properties = TabProperties(freecad_object=cad_object, freecad_face=cad_face, tab_type=t_type,
                                       name=self.name, real_name=self.real_name)
        ParamWidget.__init__(self, tab_properties)
        self.widget_list.extend([WidgetValue(type=float, name="y_length", show_name="Width", widget=None),
                                 WidgetValue(type=float, name="thickness", show_name="Thickness", widget=None),
                                WidgetValue(type=float, name="tabs_number", show_name="Number of tabs",
                                            widget=None, interval_value=[1., 300.], step=1., decimals=0),
                                WidgetValue(type=float, name="tabs_width", show_name="Width of tabs", widget=None,
                                            interval_value=[1., 300.], step=1., decimals=2),
                                WidgetValue(type=float, name="tabs_shift", show_name="Shift", widget=None,
                                            interval_value=[-300, 300.], step=1., decimals=2),
                                WidgetValue(type=float, name="interval_ratio", show_name="Interval ratio",
                                            widget=None, interval_value=[0.1, 5.], step=0.1, decimals=2),
                                WidgetValue(type=bool, name="dog_bone", show_name="Dog bone hole", widget=None),
                                WidgetValue(type=bool, name="tab_dog_bone", show_name="Tab dog bone hole", widget=None)
                                 ])

    def get_tab_type(self):
        return self.object_property.tab_type


class TabWidget(BaseTabWidget):

    def __init__(self, cad_face, cad_object, name, t_type):
        BaseTabWidget.__init__(self, cad_face, cad_object, name, t_type)


class TSlotWidget(BaseTabWidget):

    def __init__(self, cad_face, cad_object, name, t_type):
        BaseTabWidget.__init__(self, cad_face, cad_object, name, t_type)

        self.widget_list.extend([WidgetValue(type=float, name="half_tab_ratio", show_name="Half tab ratio",
                                             widget=None, interval_value=[0.1, 5.], step=0.1, decimals=2),
                                WidgetValue(type=float, name="screw_diameter", show_name="Screw diameter",
                                            widget=None, interval_value=[1., 30.], step=1., decimals=2.),
                                WidgetValue(type=float, name="screw_length", show_name="Screw length",
                                            widget=None, interval_value=[5., 300.], step=1., decimals=2.),
                                WidgetValue(type=float, name="screw_length_tol", show_name="Screw length tol.",
                                            widget=None, interval_value=[0, 300.], step=1., decimals=2.)])


class TabContinuousWidget(BaseTabWidget):

    def __init__(self, cad_face, cad_object, name, t_type):
        BaseTabWidget.__init__(self, cad_face, cad_object, name, t_type)

        self.widget_list = [WidgetValue(type=float, name="y_length", show_name="Width", widget=None),
                            WidgetValue(type=float, name="thickness", show_name="Thickness", widget=None),
                            WidgetValue(type=float, name="tabs_number", show_name="Number of elements",
                                            widget=None, interval_value=[2., 300.], step=1., decimals=0),
                            WidgetValue(type=bool, name="y_invert", show_name="Invert Y", widget=None),
                            WidgetValue(type=bool, name="dog_bone", show_name="Dog bone hole", widget=None),
                            WidgetValue(type=bool, name="tab_dog_bone", show_name="Tab dog bone hole", widget=None)]


class TabFlexWidget(BaseTabWidget):

    def __init__(self, cad_face, cad_object, name, t_type):
        BaseTabWidget.__init__(self, cad_face, cad_object, name, t_type)

        self.widget_list = [WidgetValue(type=float, name="tabs_width", show_name="Width of tabs", widget=None,
                                            interval_value=[1., 300.], step=1., decimals=2),
                            WidgetValue(type=bool, name="y_invert", show_name="Invert Y", widget=None),
                            WidgetValue(type=bool, name="dog_bone", show_name="Dog bone hole", widget=None)]


class TabLink(ParamWidget):

    def __init__(self, cad_face, cad_object, name, tab_link):
        self.tab_link = tab_link
        self.name = "%s.%s" % (cad_object.Name, name)
        self.real_name = name
        tab_properties = TabProperties(freecad_object=cad_object, freecad_face=cad_face,
                                       tab_type=str(self.tab_link.properties().tab_type),
                                       name=self.name, real_name=self.real_name)
        ParamWidget.__init__(self, tab_properties)
        self.widget_list.extend([WidgetValue(type=bool, name="y_invert", show_name="Invert Y", widget=None)])

    def get_group_box(self, widget):
        group_box = QtGui.QGroupBox(widget)
        group_box.setFlat(False)
        self.form = widget
        grid = self.get_grid()
        title = QtGui.QLabel(self.form)
        title.setText("Linked tab to : %s" % self.tab_link.description)
        grid.addWidget(title, 1, 0, 1, 2)
        group_box.setLayout(grid)
        group_box.setTitle(self.name)
        return group_box, grid


class TabsList(object):

    def __init__(self):
        self.tabs_list = []
        return

    def append(self, freecad_face, freecad_object, name, tab_type):
        if self.exist(name):
            raise ValueError(name + " already in interactor tabs list")
        else:
            tab = None
            if tab_type == TabProperties.TYPE_TAB:
                tab = TabWidget(freecad_face, freecad_object, name, tab_type)
            elif tab_type == TabProperties.TYPE_T_SLOT:
                tab = TSlotWidget(freecad_face, freecad_object, name, tab_type)
            elif tab_type == TabProperties.TYPE_CONTINUOUS:
                tab = TabContinuousWidget(freecad_face, freecad_object, name, tab_type)
            elif tab_type == TabProperties.TYPE_FLEX:
                tab = TabFlexWidget(freecad_face, freecad_object, name, tab_type)
            else:
                raise ValueError(name + " unkonwn type of tab")
            self.tabs_list.append(tab)
        return self.tabs_list[-1]

    def append_link(self, freecad_face, freecad_object, name, part_src_name):
        if self.exist(name):
            raise ValueError(name + " already in interactor tabs list")
        else:
            src_tab_element = self.get(part_src_name)
            if src_tab_element is None:
                raise ValueError("No original part found (%s)" % part_src_name)
            self.tabs_list.append(TabLink(freecad_face, freecad_object, name, src_tab_element))
        return self.tabs_list[-1]

    def remove(self, name):
        found = None
        linked_tabs = self.get_linked_tabs(name)
        if len(linked_tabs) > 0:
            raise ValueError('Some tabs are linked to this part %s' % name)

        for part in self.tabs_list:
            if part.name == name:
                found = part
                break
        if found is not None:
            self.tabs_list.remove(found)

    def exist(self, name):
        for part in self.tabs_list:
            if part.name == name:
                return True
        return False

    def get(self, name):
        for tab in self.tabs_list:
            if tab.name == name:
                return tab
        return None

    def get_linked_tabs(self, name):
        el_list = []
        for tab in self.tabs_list:
            if isinstance(tab, TabLink) and tab.tab_link.name == name:
                el_list.append(tab)
        return el_list

    def __iter__(self):
        return iter(self.tabs_list)

    def get_tabs_properties(self):
        tabs_properties = []
        for tab in self.tabs_list:
            if isinstance(tab, TabLink):
                linked_properties = copy.copy(tab.tab_link.properties())
                linked_properties.freecad_object = tab.properties().freecad_object
                linked_properties.freecad_face = tab.properties().freecad_face
                linked_properties.name = tab.properties().name
                linked_properties.real_name = tab.properties().real_name
                linked_properties.y_invert = tab.properties().y_invert
                linked_properties.transform_matrix = tab.properties().transform_matrix
                linked_properties.thickness = tab.properties().thickness
                linked_properties.y_length = tab.properties().y_length
                tabs_properties.append(linked_properties)
            else:
                tabs_properties.append(tab.properties())
        return tabs_properties




