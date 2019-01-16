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
from lasercut.material import retrieve_thickness_from_biggest_face
from lasercut.makehinges import complete_hinges_properties, create_solid_corner, estimate_min_link
import copy


class HingesProperties(helper.ObjectProperties):

    _allowed = ('freecad_face_1_name', 'freecad_object_1_name', 'freecad_face_2_name', 'freecad_object_2_name', 'name',
                'seg_face_1', 'seg_face_2', 'extrustion_vector', 'rad_angle', 'deg_angle', 'rotation_vector'
                'arc_length', 'arc_inner_radius', 'arc_outer_radius',
                'min_links_nb', 'nb_link', 'thickness', 'reversed_angle')

    def __init__(self, **kwargs):
        super(HingesProperties, self).__init__(**kwargs)
        self.freecad_object_1 = None
        self.freecad_face_1 = None
        self.freecad_object_2 = None
        self.freecad_face_2 = None
        if not kwargs['freecad_object_1'] or not kwargs['freecad_face_1']:
            raise ValueError("Must defined freecad face/object")
        if not kwargs['freecad_object_2'] or not kwargs['freecad_face_2']:
            raise ValueError("Must defined freecad face/object")
        self.freecad_object_1_name = kwargs['freecad_object_1'].Name
        self.freecad_object_2_name = kwargs['freecad_object_2'].Name

        if not hasattr(self, 'name'):
            self.name = kwargs['freecad_object_1'].Label + " -> " + kwargs['freecad_object_2'].Label
        self.arc_length = None
        self.extrustion_vector = None
        self.solid = None
        self.seg_face_1 = None
        self.seg_face_2 = None
        self.arc_middle_segment = None
        self.deg_angle = None
        self.rad_angle = None
        self.rotation_vector = None
        self.thickness = None
        self.min_links_nb = None
        self.arc_inner_radius = None
        self.arc_outer_radius = None
        self.nb_link = 5

        complete_hinges_properties(self, kwargs['freecad_face_1'], kwargs['freecad_face_2'], False)
        #create_solid_corner(self)
        self.compute_min_link(0.20)

    def compute_min_link(self, clearance_width):
        self.min_links_nb = estimate_min_link(self.rad_angle, self.thickness, clearance_width)
        self.nb_link = self.min_links_nb + 1

    def recomputeInit(self, freecad_object_1, freecad_face_1, freecad_object_2, freecad_face_2):
        self.freecad_object_1 = freecad_object_1
        self.freecad_face_1 = freecad_face_1
        self.freecad_object_2 = freecad_object_2
        self.freecad_face_2 = freecad_face_2
        complete_hinges_properties(self, freecad_face_1, freecad_face_2, True)
        create_solid_corner(self)

class GlobalLivingMaterialProperties(helper.ObjectProperties):

    _allowed = ('new_name', 'thickness', 'laser_beam_diameter', 'freecad_object_name',
                'freecad_object_label'
                'generate_solid', 'dog_bone', 'link_clearance', 'solid_name',
                'hinge_type', "alternate_nb_hinge", "occupancy_ratio")

    HINGE_TYPE_ALTERNATE_DOUBLE = "Alternate"

    def __init__(self, **kwargs):
        super(GlobalLivingMaterialProperties, self).__init__(**kwargs)
        #if not hasattr(self, 'freecad_object'):
        #    raise ValueError("Must defined freecad object")
        if not hasattr(self, 'thickness'):
            self.thickness = 5.0
            try:
                self.thickness = retrieve_thickness_from_biggest_face(kwargs['freecad_object'])
                # FreeCAD.Console.PrintError("found : %f\n" % self.thickness)
            except ValueError as e:
                FreeCAD.Console.PrintError(e)

        if not hasattr(self, 'freecad_object_name'):
            self.freecad_object_name = kwargs['freecad_object'].Name
        if not hasattr(self, 'name'):
            self.name = kwargs['freecad_object'].Name
        if not hasattr(self, 'label'):
            self.label = kwargs['freecad_object'].Label

        if not hasattr(self, 'laser_beam_diameter'):
            self.laser_beam_diameter = self.thickness / 15.0
        if not hasattr(self, 'link_clearance'):
            self.link_clearance = self.laser_beam_diameter * 3.0
        if not hasattr(self, 'new_name'):
            self.new_name = "%s_flat" % kwargs['freecad_object'].Label
        if not hasattr(self, 'solid_name'): #
            self.solid_name = "%s_solid" % kwargs['freecad_object'].Label
        if not hasattr(self, 'dog_bone'):
            self.dog_bone = False
        if not hasattr(self, 'generate_solid'):
            self.generate_solid = True
        if not hasattr(self, 'hinge_type'):
            self.hinge_type = self.HINGE_TYPE_ALTERNATE_DOUBLE
        if not hasattr(self, 'alternate_nb_hinge'):
            self.alternate_nb_hinge = int(2)
        if not hasattr(self, 'occupancy_ratio'):
            self.occupancy_ratio = 0.8



