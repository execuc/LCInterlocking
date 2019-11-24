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
from lasercut import helper


class TabProperties(helper.ObjectProperties):

    TYPE_TAB = 'Tab'
    TYPE_T_SLOT = 'Screw'
    TYPE_CONTINUOUS = 'Continuous'
    TYPE_FLEX = 'Flexible'
    TYPE_NOT_DEFINED = 'Not Defined'

    _allowed = ('face_name', 'y_length', 'thickness', 'tabs_width', 'tabs_number', 'tabs_shift',
                'dog_bone', 'tab_dog_bone', 'screw_diameter', 'screw_length', 'screw_length_tol', 'makeScrew',
                'y_invert', 'half_tab_ratio', 'interval_ratio', 'freecad_obj_name',
                'tab_type', 'group_id', 'description', 'link_name', 'tab_name', 'transform_matrix')

    __count = 0

    @classmethod
    def _count(cls):
        TabProperties.__count += 1
        return TabProperties.__count

    def __init__(self, **kwargs):
        super(TabProperties, self).__init__(**kwargs)
        self.freecad_object = None
        self.freecad_face = None
        self.transform_matrix = None
        if not kwargs['freecad_face']:
            raise ValueError("Must init with freecad face")
        if not hasattr(self, 'freecad_obj_name') :#or not hasattr(self, 'freecad_face'):
            raise ValueError("Must defined freecad face/object")
        if not hasattr(self, 'tab_type'):
            raise ValueError("no type of tab defined")
        if not hasattr(self, 'face_name'):
            #self.face_name = self.freecad_face['name']
            raise ValueError("name not defined")
        if not hasattr(self, 'tab_name'):
            self.tab_name = "%s.%s" % (self.freecad_obj_name, self.face_name)
        if not hasattr(self, 'description'):
            self.description = "%s.%s (%s)" % (self.freecad_obj_name, self.face_name, self.tab_type)
        if not hasattr(self, 'y_length') or not hasattr(self, 'thickness') or not hasattr(self, 'transform_matrix'):
            try:
                x_local, y_length, thickness = helper.get_local_axis(kwargs['freecad_face'])
                self.thickness = thickness.Length
                self.y_length = y_length.Length
            except ValueError as e:
                FreeCAD.Console.PrintError(e)
        if not hasattr(self, 'tabs_number'):
            self.tabs_number = 1
        if not hasattr(self, 'tabs_width'):
            self.tabs_width = 10
        if not hasattr(self, 'tabs_shift'):
            self.tabs_shift = 0.
        if not hasattr(self, 'interval_ratio'):
            self.interval_ratio = 1.
        if not hasattr(self, 'half_tab_ratio'):
            self.half_tab_ratio = 1.
        if not hasattr(self, 'screw_diameter'):
            self.screw_diameter = 3.
        if not hasattr(self, 'screw_length'):
            self.screw_length = 15.
        if not hasattr(self, 'screw_length_tol'):
            self.screw_length_tol = 0.5
        if not hasattr(self, 'dog_bone'):
            self.dog_bone = True
        if not hasattr(self, 'tab_dog_bone'):
            self.tab_dog_bone = False
        if not hasattr(self, 'y_invert'):
            self.y_invert = False
        self.group_id = self._count()
        if not hasattr(self, 'link_name'):
            self.link_name = ""

    def recomputeInit(self, freecad_obj, freecad_face):
        self.freecad_object = freecad_obj
        self.freecad_face = freecad_face
        x_local, y_length, thickness = helper.get_local_axis(freecad_face)
        self.thickness = thickness.Length
        self.y_length = y_length.Length
        self.transform_matrix = helper.get_matrix_transform(freecad_face)

        transform_group = freecad_obj.getParentGeoFeatureGroup()
        while transform_group is not None:
            self.transform_matrix = transform_group.Placement.toMatrix() * self.transform_matrix
            transform_group = transform_group.getParentGeoFeatureGroup()
