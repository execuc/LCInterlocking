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

from lasercut.helper import ObjectProperties


class BoxProperties(ObjectProperties):

    _allowed = ('length', 'width', 'height', 'thickness', 'outside_measure',
                'length_width_priority', 'length_outside', 'width_outside',
                'bottom_position', 'bottom_shift', 'inner_radius',
                'length_shift', 'width_shift')

    LENGTH_PRIORTY = "Length"
    WIDTH_PRIORTY = "Width"
    CROSS_PRIORTY = "No - Cross"
    ROUND_PRIORTY = "No - For rounding"

    BOTTOM_OUTSIDE = "Outside"
    BOTTOM_INSIDE = "Inside"

    def __init__(self, **kwargs):
        super(BoxProperties, self).__init__(**kwargs)
        if not hasattr(self, 'length'):
            self.length = 90.
        if not hasattr(self, 'width'):
            self.width = 50.
        if not hasattr(self, 'height'):
            self.height = 30.
        if not hasattr(self, 'thickness'):
            self.thickness = 3.
        if not hasattr(self, 'outside_measure'):
            self.outside_measure = True
        # Length/width
        if not hasattr(self, 'length_width_priority'):
            self.length_width_priority = self.LENGTH_PRIORTY
        if not hasattr(self, 'length_outside'):
            self.length_outside = 0.
        if not hasattr(self, 'width_outside'):
            self.width_outside = 0.
        if not hasattr(self, 'inner_radius'):
            self.inner_radius = 0.
        if not hasattr(self, 'length_shift'):
            self.length_shift = 0.
        if not hasattr(self, 'width_shift'):
            self.width_shift = 0.


class TopBottomProperties(ObjectProperties):
    _allowed = ('position', 'height_shis notift', 'length_outside', 'width_outside', 'top_type', 'cover_length_tolerance')

    POSITION_OUTSIDE = "Outside"
    POSITION_INSIDE = "Inside"
    TOP_TYPE_NORMAL = "Normal"
    TOP_TYPE_COVER = "Openable"

    def __init__(self, **kwargs):
        super(TopBottomProperties, self).__init__(**kwargs)
        if not hasattr(self, 'position'):
            self.position = self.POSITION_OUTSIDE
        if not hasattr(self, 'height_shift'):
            self.height_shift = 0.
        if not hasattr(self, 'length_outside'):
            self.length_outside = 0.
        if not hasattr(self, 'width_outside'):
            self.width_outside = 0.
        if not hasattr(self, 'top_type'):
            self.top_type = self.TOP_TYPE_NORMAL
        if not hasattr(self, 'cover_length_tolerance'):
            self.cover_length_tolerance = 3.
