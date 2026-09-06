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

from PySide import QtGui

from lasercut.tabproperties import TabProperties
from panel.toolwidget import ParamWidget, WidgetValue
import copy
import FreeCAD

class BaseTabWidget(ParamWidget):

    def __init__(self, tab_properties):
        self.name = tab_properties.face_name
        self.description = tab_properties.description # a supprimer ?
        self.tab_name = tab_properties.tab_name
        self.obj_name = tab_properties.freecad_obj_name
        self.link_name = None
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

    def __init__(self, tab_properties):
        BaseTabWidget.__init__(self, tab_properties)


class TSlotWidget(BaseTabWidget):

    def __init__(self, tab_properties):
        BaseTabWidget.__init__(self, tab_properties)

        self.widget_list.extend([WidgetValue(type=float, name="half_tab_ratio", show_name="Half tab ratio",
                                             widget=None, interval_value=[0.1, 5.], step=0.1, decimals=2),
                                WidgetValue(type=float, name="screw_diameter", show_name="Screw diameter",
                                            widget=None, interval_value=[1., 30.], step=1., decimals=2.),
                                WidgetValue(type=float, name="screw_length", show_name="Screw length",
                                            widget=None, interval_value=[5., 300.], step=1., decimals=2.),
                                WidgetValue(type=float, name="screw_length_tol", show_name="Screw length tol.",
                                            widget=None, interval_value=[0, 300.], step=1., decimals=2.)])


class TabContinuousWidget(BaseTabWidget):

    def __init__(self, tab_properties):
        BaseTabWidget.__init__(self, tab_properties)

        self.widget_list = [WidgetValue(type=float, name="y_length", show_name="Width", widget=None),
                            WidgetValue(type=float, name="thickness", show_name="Thickness", widget=None),
                            WidgetValue(type=float, name="tabs_number", show_name="Number of elements",
                                            widget=None, interval_value=[2., 300.], step=1., decimals=0),
                            WidgetValue(type=bool, name="y_invert", show_name="Invert Y", widget=None),
                            WidgetValue(type=bool, name="dog_bone", show_name="Dog bone hole", widget=None),
                            WidgetValue(type=bool, name="tab_dog_bone", show_name="Tab dog bone hole", widget=None)]


class TabFlexWidget(BaseTabWidget):

    def __init__(self, tab_properties):
        BaseTabWidget.__init__(self, tab_properties)

        self.widget_list = [WidgetValue(type=float, name="tabs_width", show_name="Width of tabs", widget=None,
                                            interval_value=[1., 300.], step=1., decimals=2),
                            WidgetValue(type=bool, name="y_invert", show_name="Invert Y", widget=None),
                            WidgetValue(type=bool, name="dog_bone", show_name="Dog bone hole", widget=None)]


class TabLink(ParamWidget):

    def __init__(self, tab_properties):
        self.name = tab_properties.face_name
        self.description = tab_properties.description
        self.tab_name = tab_properties.tab_name
        self.obj_name = tab_properties.freecad_obj_name
        self.link_name =  tab_properties.link_name

        ParamWidget.__init__(self, tab_properties)
        self.widget_list.extend([WidgetValue(type=bool, name="y_invert", show_name="Invert Y", widget=None)])

    def get_group_box(self, widget):
        group_box = QtGui.QGroupBox(widget)
        group_box.setFlat(False)
        self.form = widget
        grid = self.get_grid()
        title = QtGui.QLabel(self.form)
        title.setText("Linked tab to : %s" % self.link_name)
        grid.addWidget(title, 1, 0, 1, 2)
        group_box.setLayout(grid)
        group_box.setTitle(self.name)
        return group_box, grid


class TabsList(object):

    def __init__(self, faces):
        self.faces = faces
        self.faces_widget_list = []
        return

    # def resumeWidget(self):
    #     for face in self.faces:
    #         if not face.link_name:
    #             self.faces_widget_list.append(self.createWidgetFromTabProperties(face))
    #         else:
    #             self.faces_widget_list.append(TabLink(face))
    #     return self.faces_widget_list

    def createWidgetFromTabProperties(self, tab_properties):
        widget = None
        tab_type = tab_properties.tab_type

        if tab_type == TabProperties.TYPE_TAB:
            widget = TabWidget(tab_properties)
        elif tab_type == TabProperties.TYPE_T_SLOT:
            widget = TSlotWidget(tab_properties)
        elif tab_type == TabProperties.TYPE_CONTINUOUS:
            widget = TabContinuousWidget(tab_properties)
        #elif tab_type == TabProperties.TYPE_FLEX:
        #    widget = TabFlexWidget(tab_properties)
        else:
            raise ValueError("Unknown type of tab")

        return widget

    def append(self, face, tab_type):
        name = face["name"]
        tab_properties = TabProperties(freecad_face=face['face'],
                                       freecad_obj_name=face['freecad_object'].Name,
                                       face_name=name,
                                       tab_type=tab_type)

        if self.exist(tab_properties.tab_name):
            raise ValueError(tab_properties.tab_name + " already in interactor tabs list")

        #widget = self.createWidgetFromTabProperties(tab_properties)
        self.faces.append(tab_properties)
        #self.faces_widget_list.append(widget)
        return self.faces[-1]#, self.faces_widget_list[-1]

    def append_link(self, face, src_tab_name):
        src_tab_element, widget = self.get(src_tab_name)
        if src_tab_element is None:
            raise ValueError("No original part found (%s)" % src_tab_name)
        name = face["name"]
        tab_properties = TabProperties(freecad_face=face['face'],
                                       freecad_obj_name=face['freecad_object'].Name,
                                       face_name=name,
                                       tab_type=TabProperties.TYPE_NOT_DEFINED,
                                       link_name=src_tab_name)

        if self.exist(tab_properties.tab_name):
            raise ValueError(tab_properties.tab_name + " already in interactor tabs list")

        self.faces.append(tab_properties)
        #self.faces_widget_list.append(TabLink(tab_properties))
        return self.faces[-1]#, self.faces_widget_list[-1]

    def remove(self, name, batch_names=frozenset()):
        self._promote_link(name, batch_names)
        found_index = None
        for index in range(len(self.faces)):
            if self.faces[index].tab_name == name:
                found_index = index
                break

        if found_index is not None:
            self.faces.pop(found_index)

    def _merged_from_origin(self, origin, link_tab):
        new_tab = copy.deepcopy(origin)
        new_tab.link_name = link_tab.link_name
        new_tab.tab_name = link_tab.tab_name
        new_tab.face_name = link_tab.face_name
        new_tab.description = link_tab.description
        new_tab.freecad_obj_name = link_tab.freecad_obj_name
        new_tab.y_invert = link_tab.y_invert
        new_tab.transform_matrix = link_tab.transform_matrix
        new_tab.thickness = link_tab.thickness
        new_tab.y_length = link_tab.y_length
        return new_tab

    def _promote_link(self, name, batch_names):
        linked = [tab for tab in self.get_linked_tabs(name) if tab.tab_name not in batch_names]
        if len(linked) == 0:
            return
        origin, widget = self.get(name)
        promoted_tab_name = linked[0].tab_name
        for index in range(len(self.faces.lst)):
            if self.faces.lst[index].tab_name == promoted_tab_name:
                promoted = self._merged_from_origin(origin, self.faces.lst[index])
                promoted.link_name = ""
                self.faces.lst[index] = promoted
                break
        for other in linked[1:]:
            for index in range(len(self.faces.lst)):
                if self.faces.lst[index].tab_name == other.tab_name:
                    self.faces.lst[index].link_name = promoted_tab_name
                    break
        FreeCAD.Console.PrintMessage("%s promoted to origin of the linked faces group\n" % promoted_tab_name)

    def exist(self, name):
        for part in self.faces:
            if part.tab_name == name:
                return True
        return False

    def get(self, name):
        #FreeCAD.Console.PrintMessage("get " + name + "\n")
        for index in range(len(self.faces)):
            if self.faces[index].tab_name == name:
                #FreeCAD.Console.PrintMessage("found " + name + "\n")
                face = self.faces[index]
                if not face.link_name:
                    widget = self.createWidgetFromTabProperties(face)
                else:
                    widget = TabLink(face)
                return face, widget


        return None, None

    def get_linked_tabs(self, name):
        el_list = []
        for tab in self.faces:
            if tab.link_name == name:
                el_list.append(tab)
        return el_list

    def __iter__(self):
        return iter(self.faces)

    def get_tabs_properties(self):
        tabs_properties = []
        for tab in self.faces.lst:
            if tab.link_name:
                tab_link, widget = self.get(tab.link_name)
                tabs_properties.append(self._merged_from_origin(tab_link, tab))
            else:
                tabs_properties.append(copy.deepcopy(tab))

        self.faces.lst = tabs_properties

        return tabs_properties




