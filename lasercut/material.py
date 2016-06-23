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
import Part
import collections
from helper import ObjectProperties, sort_quad_vertex, biggest_area_faces


class MaterialProperties(ObjectProperties):

    _allowed = ('type', 'thickness', 'thickness_tolerance', 'laser_beam_diameter', 'freecad_object')
    TYPE_LASER_CUT = 1

    def __init__(self, **kwargs):
        super(MaterialProperties, self).__init__(**kwargs)
        if not hasattr(self, 'freecad_object'):
            raise ValueError("Must defined freecad object")
        if not hasattr(self, 'type'):
            self.type = self.TYPE_LASER_CUT
        if not hasattr(self, 'thickness'):
            self.thickness = 5.0
            try:
                self.thickness = retrieve_thickness_from_biggest_face(self.freecad_object)
                # FreeCAD.Console.PrintMessage("found : %f\n" % self.thickness)
            except ValueError as e:
                FreeCAD.Console.PrintMessage(e)
        if not hasattr(self, 'thickness_tolerance'):
            self.thickness_tolerance = 0.1 * self.thickness
        if not hasattr(self, 'laser_beam_diameter'):
            self.laser_beam_diameter = self.thickness / 15.0
        if not hasattr(self, 'new_name'):
            self.new_name = "%s_tab" % self.freecad_object.Label


# Prendre la normal la plus présente en terme de surface (biggest_area_faces)
# appliquer  une transformation pour orienter la normal vers Z
# l'éppaiseur et le Zlength du boundedbox (ce sera donc l'éppaisseur max)
def retrieve_thickness_from_bounded_box():
    return None


# Prend les deux premiere faces ayant la même normal (géré exception !! si une seule face)
# Pour chaque face recupere les points et calcule la plus petite distance entre chaque point
# de la premiere face et ceux de la deuxième face. La distance la plus petite est l'éppaisseur estimé.
def retrieve_thickness_from_biggest_face(freecad_object):
    area_faces = biggest_area_faces(freecad_object)
    list_edges_face1 = Part.__sortEdges__(area_faces[2][0].Edges)
    list_edges_face2 = Part.__sortEdges__(area_faces[2][1].Edges)

    list_pts_face1 = sort_quad_vertex(list_edges_face1, False)
    if list_pts_face1 is None:
        list_pts_face1 = sort_quad_vertex(list_edges_face1, True)
    if list_pts_face1 is None:
        raise ValueError("Error sorting vertex")

    list_pts_face2 = sort_quad_vertex(list_edges_face2, False)
    if list_pts_face2 is None:
        list_pts_face2 = sort_quad_vertex(list_edges_face2, True)
    if list_pts_face2 is None:
        raise ValueError("Error sorting vertex")

    min_array = []
    for vec1 in list_pts_face1:
        tab_diff = []
        for vec2 in list_pts_face2:
            tab_diff.append(vec1.sub(vec2).Length)
        min_array.append(min(tab_diff))

    counter_list = collections.Counter(min_array)
    thickness_occ = counter_list.most_common(1)

    return thickness_occ[0][0]
