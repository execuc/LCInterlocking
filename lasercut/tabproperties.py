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

    _allowed = ('name', 'real_name', 'y_length', 'thickness', 'tabs_width', 'tabs_number', 'tabs_shift',
                'dog_bone', 'screw_diameter', 'screw_length', 'makeScrew', 'y_invert'
                'half_tab_ratio', 'interval_ratio', 'freecad_face', 'freecad_object', 'tab_type')

    def __init__(self, **kwargs):
        super(TabProperties, self).__init__(**kwargs)
        if not hasattr(self, 'freecad_object') or not hasattr(self, 'freecad_face'):
            raise ValueError("Must defined freecad face/object")
        if not hasattr(self, 'tab_type'):
            raise ValueError("no type of tab defined")
        if not hasattr(self, 'y_length') or not hasattr(self, 'thickness') or not hasattr(self, 'transform_matrix'):
            try:
                x_local, y_length, thickness = helper.get_local_axis(self.freecad_face)
                self.thickness = thickness.Length
                self.y_length = y_length.Length
                self.transform_matrix = helper.get_matrix_transform(self.freecad_face)
#                FreeCAD.Console.PrintMessage("y_length : %f, thickness: %f\n" %(self.thickness, self.y_length))
            except ValueError as e:
                FreeCAD.Console.PrintMessage(e)
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
        if not hasattr(self, 'dog_bone'):
            self.dog_bone = True
        if not hasattr(self, 'y_invert'):
            self.y_invert = False

