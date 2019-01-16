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
import math


class RoundedBoxProperties(ObjectProperties):

    _allowed = ('nb_face', 'inradius', 'height', 'side_length', 'max_side_length', 'thickness', 'cut')

    def __init__(self, **kwargs):
        super(RoundedBoxProperties, self).__init__(**kwargs)
        if not hasattr(self, 'nb_face'):
            self.nb_face = int(5)
        if not hasattr(self, 'inradius'):
            self.inradius = 50.
        if not hasattr(self, 'height'):
            self.height = 30.
        if not hasattr(self, 'thickness'):
            self.thickness = 3.
        if not hasattr(self, 'cut_nb'):
            self.cut = int(0)

        self.side_length = 0.
        self.max_side_length = 0.
        self.compute_information(True)

    def compute_information(self, update_side_length = False):
        circumradius =  self.inradius / math.cos(math.pi / float(self.nb_face))
        self.max_side_length = 2 * circumradius * math.sin(math.pi / float(self.nb_face))
        self.max_side_length = round(self.max_side_length - 0.01, 2)

        if update_side_length is True or self.side_length >= self.max_side_length :
            self.side_length = math.floor(self.max_side_length * 0.75)

        if self.cut > self.nb_face:
            self.cut = int(self.nb_face)


class TopBottomRoundedProperties(ObjectProperties):
    _allowed = ('position', 'height_shift', 'radius_outside')

    POSITION_OUTSIDE = "Outside"
    POSITION_INSIDE = "Inside"

    def __init__(self, **kwargs):
        super(TopBottomRoundedProperties, self).__init__(**kwargs)
        if not hasattr(self, 'position'):
            self.position = self.POSITION_INSIDE
        if not hasattr(self, 'height_shift'):
            self.height_shift = 0.
        if not hasattr(self, 'radius_outside'):
            self.radius_outside = 0.