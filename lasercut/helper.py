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

import Part
import FreeCAD

import math


# http://stackoverflow.com/questions/2535917/copy-kwargs-to-self
class ObjectProperties(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)


# http://www.fairburyfastener.com/xdims_metric_nuts.htm
def get_screw_nut_spec(metric_diameter, metric_length):
    if metric_diameter == 1.6:
        return ObjectProperties(screw_diameter=metric_diameter, screw_length=metric_length,
                                nut_flat_flat=3.2, nut_height=1.3)
    elif metric_diameter == 2:
        return ObjectProperties(screw_diameter=metric_diameter, screw_length=metric_length,
                                nut_flat_flat=4., nut_height=1.6)
    elif metric_diameter == 2.5:
        return ObjectProperties(screw_diameter=metric_diameter, screw_length=metric_length,
                                nut_flat_flat=5., nut_height=2.)
    elif metric_diameter == 3:
        return ObjectProperties(screw_diameter=metric_diameter, screw_length=metric_length,
                                nut_flat_flat=5.5, nut_height=2.4)
    elif metric_diameter == 4:
        return ObjectProperties(screw_diameter=metric_diameter, screw_length=metric_length,
                                nut_flat_flat=7., nut_height=3.2)
    elif metric_diameter == 5:
        return ObjectProperties(screw_diameter=metric_diameter, screw_length=metric_length,
                                nut_flat_flat=8., nut_height=4.7)
    elif metric_diameter == 6:
        return ObjectProperties(screw_diameter=metric_diameter, screw_length=metric_length,
                                nut_flat_flat=10., nut_height=5.2)
    elif metric_diameter == 8:
        return ObjectProperties(screw_diameter=metric_diameter, screw_length=metric_length,
                                nut_flat_flat=13., nut_height=6.8)
    elif metric_diameter == 10:
        return ObjectProperties(screw_diameter=metric_diameter, screw_length=metric_length,
                                nut_flat_flat=16., nut_height=8.4)
    raise ValueError("Unknown screw diameter")


def transform(part, referentiel_face, x_origin, transform_matrix=None):
    normal_face = referentiel_face.normalAt(0, 0)
    # original center is (0,0,0)
    transformed_center = referentiel_face.CenterOfMass + normal_face.normalize() * x_origin
    if transform_matrix is None:
        transform_matrix = get_matrix_transform(referentiel_face)
    part.Placement = FreeCAD.Placement(transform_matrix).multiply(part.Placement)
    part.translate(transformed_center)
    return part

# http://gamedev.stackexchange.com/questions/20097/how-to-calculate-a-3x3-rotation-matrix-from-2-direction-vectors
# http://www.freecadweb.org/api/Vector.html
def get_matrix_transform(face):
    x_local, y_local_not_normalized, z_local_not_normalized = get_local_axis(face)
    y_local = y_local_not_normalized.normalize()
    z_local = z_local_not_normalized.normalize()

    m = FreeCAD.Matrix()
    if z_local is not None:
        m.A11 = x_local.x
        m.A12 = y_local.x
        m.A13 = z_local.x
        m.A21 = x_local.y
        m.A22 = y_local.y
        m.A23 = z_local.y
        m.A31 = x_local.z
        m.A32 = y_local.z
        m.A33 = z_local.z

    return m


def get_local_axis(face):
    list_edges = Part.__sortEdges__(face.Edges)
    list_points = sort_quad_vertex(list_edges, False)
    if list_points is None:
        list_points = sort_quad_vertex(list_edges, True)
    if list_points is None:
        raise ValueError("Error sorting vertex")

    normal_face = face.normalAt(0, 0)
    y_local = None
    z_local = None
    x_local = normal_face.negative()
    z_local_not_normalized = None
    y_local_not_normalized = None
    for x in range(0, 4):
        vector1 = list_points[(x + 1) % 4] - list_points[x]
        vector2 = list_points[(x - 1) % 4] - list_points[x]
        y_local = None
        z_local = None
        if vector1.Length >= vector2.Length:
            z_local_not_normalized = vector2 * 1
            y_local_not_normalized = vector1 * 1
            y_local = vector1.normalize()
            z_local = vector2.normalize()

        else:
            z_local_not_normalized = vector1 * 1
            y_local_not_normalized = vector2 * 1
            y_local = vector2.normalize()
            z_local = vector1.normalize()

        computed_x_local = y_local.cross(z_local)

        if compare_freecad_vector(computed_x_local, x_local):
            # FreeCAD.Console.PrintMessage("\nFound\n")
            # FreeCAD.Console.PrintMessage(x_local)
            # FreeCAD.Console.PrintMessage(y_local)
            # FreeCAD.Console.PrintMessage(z_local)
            # FreeCAD.Console.PrintMessage("\n\n")
            return x_local, y_local_not_normalized, z_local_not_normalized

    return None, None, None


def compare_freecad_vector(vector1, vector2, epsilon=10e-6):
    vector = vector1.sub(vector2)
    if math.fabs(vector.x) < epsilon and math.fabs(vector.y) < epsilon and math.fabs(vector.z) < epsilon:
        return True
    return False


def compare_freecad_vector_direction(vector1, vector2, epsilon=10e-6):
    return math.fabs(vector1.cross(vector2).Length) < epsilon


def sort_quad_vertex(list_edges, reverse):
    list_points = []
    if not reverse:
        list_points = [list_edges[0].Vertexes[0].Point, list_edges[0].Vertexes[1].Point]
    else:
        list_points = [list_edges[0].Vertexes[1].Point, list_edges[0].Vertexes[0].Point]
    for edge in list_edges[1:-1]:
        vertex1 = edge.Vertexes[0].Point
        vertex2 = edge.Vertexes[1].Point

        if vertex1 == list_points[-1]:
            list_points.append(vertex2)
        elif vertex2 == list_points[-1]:
            list_points.append(vertex1)
        else:
            return None

    return list_points


# TODO : not clean
def get_value(item):
    return item[1]


#   Returns face grouping by normal,sorted by the amount of surface (descending)
def biggest_area_faces(freecad_object):
    normal_area_list = []
    for face in freecad_object.Shape.Faces:
        # print face
        normal = face.normalAt(0, 0)
        # print normal
        found = False
        for i in range(len(normal_area_list)):
            normal_test = normal_area_list[i][0]
            if compare_freecad_vector_direction(normal, normal_test):  # inverse to test
                found = True
                normal_area_list[i][1] += face.Area
                normal_area_list[i][2].append(face)
                break
        if not found:
            normal_area_list.append([normal, face.Area, [face]])
    # print normal_area_list
    sorted_list = sorted(normal_area_list, key=get_value)
    # print sorted_list
    biggest_area_face = sorted_list[-1]
#       contains : 0:normal, 1:area mm2, 2; list of faces
    return biggest_area_face
