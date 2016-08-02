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
import itertools
import helper


def is_inside(face, shape_to_test):
    normal = face.normalAt(0, 0)
    point = face.CenterOfMass + normal.normalize() * 0.1
    sphere = Part.makeSphere(0.04, point)
    #Part.show(sphere)
    return sphere.common(shape_to_test).Volume > 0.00001


def make_box(length, width, height):
    origin = FreeCAD.Vector(-length/2.0, -width / 2.0, -height)
    box = Part.makeBox(length, width, height, origin)
    return box


def get_transformation_matrix_from_vectors(x, y, z):
    x_local = x.normalize()
    y_local = y.normalize()
    z_local = z.normalize()

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


def transform(part, referential_face, transform_matrix):
    transformed_center = referential_face.CenterOfMass
    part.Placement = FreeCAD.Placement(transform_matrix).multiply(part.Placement)
    part.translate(transformed_center)
    return part


def retrieve_face_axis(sorted_areas_by_normals, shape):
    test_face = sorted_areas_by_normals[2][2][0] # get medium faces -> list of faces -> first face
    z_axis = sorted_areas_by_normals[0][2][0].normalAt(0, 0) # get smallest faces -> list of faces -> first face
    x_axis = None
    y_axis = None
    if is_inside(test_face, shape):
        #print "inside"
        x_axis = test_face.normalAt(0, 0)
        y_axis = z_axis.cross(x_axis)
    else:
        #print "outside"
        y_axis = test_face.normalAt(0, 0)
        x_axis = y_axis.cross(z_axis)

    #print "x_axis: " + str(x_axis) + ", y_axis: " + str(y_axis) + ", z_axis: " + str(z_axis)
    return x_axis, y_axis, z_axis


def remove_intersections(first_part, second_part, referential_faces, axis, invert_y = False):
    length = (referential_faces[0].CenterOfMass - referential_faces[1].CenterOfMass).Length / 2.0
    first_box_x = second_part.properties.thickness + second_part.properties.thickness_tolerance - second_part.properties.laser_beam_diameter + second_part.properties.hole_width_tolerance
    first_box = make_box(first_box_x, first_part.properties.thickness, length)
    if invert_y:
        first_box.translate(FreeCAD.Vector(0, 0, -length))
    transform_matrix = get_transformation_matrix_from_vectors(axis[0], axis[1], axis[2])
    transform(first_box, referential_faces[0], transform_matrix)

    second_box_x = first_part.properties.thickness + first_part.properties.thickness_tolerance - first_part.properties.laser_beam_diameter + first_part.properties.hole_width_tolerance
    second_box = make_box(second_part.properties.thickness, second_box_x, length)
    if not invert_y:
        second_box.translate(FreeCAD.Vector(0, 0, -length))
    transform(second_box, referential_faces[0], transform_matrix)

    #Part.show(first_box)
    #Part.show(second_box)
    first_part.toRemove.append(first_box)
    second_part.toRemove.append(second_box)


#            Y
#            |
#            |
#            |
#            |Z
#            ---------------------------> X
# X is the width of part 2(correspond à la longueur de la piece 1)
# Y is the width of part 1.
# Z is the heigt of the intersection
def make_cross_parts(parts):
    parts_element = []
    for part in parts:
        mat_element = helper.MaterialElement(part)
        parts_element.append(mat_element)

    for subset in itertools.combinations(parts_element, 2):
        first_part = subset[0]
        second_part = subset[1]
        if parts_element.index(subset[0]) > parts_element.index(subset[1]):
            first_part = subset[1]
            second_part = subset[0]

        first_shape = first_part.properties.freecad_object.Shape
        second_shape = second_part.properties.freecad_object.Shape
        intersect_shape = first_shape.common(second_shape)
        if intersect_shape.Volume > 0.001:
            sorted_areas_by_normals = helper.sort_area_faces(intersect_shape)
            str_parts_name = first_part.get_name() + " -> " + second_part.get_name()
            if len(sorted_areas_by_normals) != 3:
                raise ValueError(str_parts_name + " : intersection is not rectangular box")
            smallest_area = helper.sort_area_faces(intersect_shape)[0]
            referential_faces = smallest_area[2]
            first_face = referential_faces[0]
            second_face = referential_faces[1]
            axis = retrieve_face_axis(sorted_areas_by_normals, first_shape)
            # Examine box border to determine shapes configuration
            first_face_first_shape = is_inside(first_face, first_shape)
            second_face_first_shape = is_inside(second_face, first_shape)
            first_face_second_shape = is_inside(first_face, second_shape)
            second_face_second_shape = is_inside(second_face, second_shape)
            #print "first_face_first_shape: " + str(first_face_first_shape) + " second_face_first_shape:" + str(second_face_first_shape) + " first_face_second_shape: " + str(first_face_second_shape) + " second_face_second_shape:" + str(second_face_second_shape)
            if not first_face_first_shape and not second_face_first_shape \
                    and first_face_second_shape and second_face_second_shape:
                raise ValueError(str_parts_name + " : a part is included in the other.")
            elif first_face_first_shape and second_face_first_shape \
                    and not first_face_second_shape and not second_face_second_shape:
                raise ValueError(str_parts_name + " : a part is included in the other.")
            elif not first_face_first_shape and not second_face_first_shape \
                    and not first_face_second_shape and not second_face_second_shape:
                #print str_parts_name + " : same height parts"
                remove_intersections(first_part, second_part, referential_faces, axis)
            elif not first_face_first_shape and second_face_first_shape \
                    and first_face_second_shape and not second_face_second_shape:
                #print str_parts_name + " : a part is above the other (1)"
                remove_intersections(first_part, second_part, referential_faces, axis)
            elif first_face_first_shape and not second_face_first_shape \
                    and not first_face_second_shape and second_face_second_shape:
                #print str_parts_name + " : a part is above the other (2)"
                remove_intersections(first_part, second_part, referential_faces, axis, True)
            else:
                raise ValueError("Not managed")

    return parts_element
