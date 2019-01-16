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
from lasercut.helper import ObjectProperties, sort_quad_vertex, biggest_area_faces, sort_area_shape_list, compare_value


class MaterialProperties(ObjectProperties):

    _allowed = ('type', 'thickness', 'thickness_tolerance', 'hole_width_tolerance',
                'laser_beam_diameter', 'name', 'label', 'link_name',
                # For cross Part
                'dog_bone', 'node_type', 'node_thickness') #'freecad_object_index'
    TYPE_LASER_CUT = 1
    NODE_NO = "No node"
    NODE_SINGLE_SHORT = 'Single short'
    NODE_SINGLE_LONG = 'Single long'
    NODE_DUAL_SHORT = 'Dual short'

    def __init__(self, **kwargs):
        super(MaterialProperties, self).__init__(**kwargs)
        self.freecad_object = None
        #if not hasattr(self, 'freecad_object_index'):
        #    raise ValueError("Must defined freecad object")
        if not hasattr(self, 'type'):
            self.type = self.TYPE_LASER_CUT
        if not hasattr(self, 'thickness'):
            self.thickness = 5.0
            try:
                #self.thickness = retrieve_thickness_from_biggest_face(self.freecad_object)
                self.thickness = retrieve_thickness_from_biggest_face(kwargs['freecad_object'])
                # FreeCAD.Console.PrintError("found : %f\n" % self.thickness)
            except ValueError as e:
                FreeCAD.Console.PrintError(e)
        if not hasattr(self, 'thickness_tolerance'):
            self.thickness_tolerance = 0.1 * self.thickness
        if not hasattr(self, 'laser_beam_diameter'):
            self.laser_beam_diameter = self.thickness / 15.0
        if not hasattr(self, 'new_name'):
            self.new_name = "%s_tab" % kwargs['freecad_object'].Label
        if not hasattr(self, 'hole_width_tolerance'):
            self.hole_width_tolerance = 0.0
        # For cross part
        if not hasattr(self, 'dog_bone'):
            self.dog_bone = True
        if not hasattr(self, 'node_type'):
            self.node_type = self.NODE_NO
        if not hasattr(self, 'node_thickness'):
            self.node_thickness = 0.05 * self.thickness
        if not hasattr(self, 'link_name'):
            self.link_name = ""

    def recomputeInit(self, freecad_obj):
        self.freecad_object = freecad_obj
        thickness = retrieve_thickness_from_biggest_face(freecad_obj)
        if compare_value(thickness, self.thickness) is False:
            FreeCAD.Console.PrintError("Recomputed thickness for %s is different (%f != %f)\n" % (self.name, thickness, self.thickness))


# Prendre la normal la plus présente en terme de surface (biggest_area_faces)
# appliquer  une transformation pour orienter la normal vers Z
# l'éppaiseur et le Zlength du boundedbox (ce sera donc l'éppaisseur max)
def retrieve_thickness_from_bounded_box():
    return None


# Prend les deux premiere faces ayant la même normal (géré exception !! si une seule face)
# Pour chaque face recupere les points et calcule la plus petite distance entre chaque point
# de la premiere face et ceux de la deuxième face. La distance la plus petite est l'éppaisseur estimé.
def retrieve_thickness_from_biggest_face(freecad_object):
    area_faces = biggest_area_faces(freecad_object.Shape)
    # order faces by normals
    sub_areas_face = sort_area_shape_list(area_faces[2])
    # TODO : check if normals at opposite
    #list_edges_face1 = Part.__sortEdges__(area_faces[2][0].Edges)
    #list_edges_face2 = Part.__sortEdges__(area_faces[2][1].Edges)
    list_edges_face1 = Part.__sortEdges__(sub_areas_face[0][2][0].Edges)
    list_edges_face2 = Part.__sortEdges__(sub_areas_face[1][2][0].Edges)

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
    # print "min_array " + str(min_array)
    counter_list = collections.Counter(min_array)
    thickness_occ = counter_list.most_common(1)

    return thickness_occ[0][0]

