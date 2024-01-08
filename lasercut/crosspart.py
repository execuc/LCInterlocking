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
import lasercut.helper as helper
from lasercut.material import MaterialProperties


def is_inside(face, shape_to_test):
    normal = face.normalAt(0, 0)
    point = face.CenterOfMass + normal.normalize() * 0.1
    sphere = Part.makeSphere(0.04, point)
    #Part.show(sphere)
    return sphere.common(shape_to_test).Volume > 0.00001


def make_dog_bone_on_xz(pos_x, pos_z, width, radius):
    cylinder = Part.makeCylinder(radius, width, FreeCAD.Vector(pos_x, -width/2.0, pos_z), FreeCAD.Vector(0, 1, 0))
    return cylinder


def make_dog_bone_on_yz(pos_y, pos_z, length, radius):
    cylinder = Part.makeCylinder(radius, length, FreeCAD.Vector(-length / 2.0, pos_y, pos_z), FreeCAD.Vector(1, 0, 0))
    return cylinder


def make_cross_box(length, width, height, node_type, node_thickness):
    half_length = length / 2.0

    p1 = FreeCAD.Vector(half_length, 0, 0)
    p2 = FreeCAD.Vector(-half_length, 0, 0)
    p3 = FreeCAD.Vector(-half_length, 0, -height)
    p4 = FreeCAD.Vector(half_length, 0, -height)

    l1 = Part.makeLine(p1, p2)
    l2 = Part.makeLine(p2, p3)
    l3 = Part.makeLine(p3, p4)
    l4 = Part.makeLine(p4, p1)
    wire = Part.Wire([l1,l2,l3,l4])
    face = Part.Face(wire)
    face.translate(FreeCAD.Vector(0, -width / 2.0, 0))
    part = face.extrude(FreeCAD.Vector(0, width, 0))
    return part


def make_dog_bones_xz(part, length, width, height, dog_bone_radius, up=True):
    half_length = length / 2.0
    shift_dog_bone = dog_bone_radius / 2.0
    if up:
        dog_bones = make_dog_bone_on_xz(half_length - shift_dog_bone, -shift_dog_bone, width, dog_bone_radius)
        dog_bones = dog_bones.fuse(make_dog_bone_on_xz(-half_length + shift_dog_bone, -shift_dog_bone, width, dog_bone_radius))
    else:
        dog_bones = make_dog_bone_on_xz(-half_length + shift_dog_bone, -height + shift_dog_bone, width, dog_bone_radius)
        dog_bones = dog_bones.fuse(make_dog_bone_on_xz(half_length - shift_dog_bone, -height + shift_dog_bone, width, dog_bone_radius))

    part = part.fuse(dog_bones)
    return part


def make_dog_bones_yz(part, length, width, height, dog_bone_radius, up=True):
    half_width = width / 2.0
    shift_dog_bone = dog_bone_radius / 2.0
    if up:
        dog_bones = make_dog_bone_on_yz(-half_width + shift_dog_bone, -shift_dog_bone, length, dog_bone_radius)
        dog_bones = dog_bones.fuse(make_dog_bone_on_yz(half_width - shift_dog_bone, -shift_dog_bone, length, dog_bone_radius))
    else:
        dog_bones = make_dog_bone_on_yz(-half_width + shift_dog_bone, -height + shift_dog_bone, length, dog_bone_radius)
        dog_bones = dog_bones.fuse(make_dog_bone_on_yz(half_width - shift_dog_bone, -height + shift_dog_bone, length, dog_bone_radius))

    part = part.fuse(dog_bones)
    return part


def make_node_xz(width, height, thickness,  x_positive = True):

    p1 = FreeCAD.Vector(0., -thickness/2.0, height / 2.0)
    p2 = FreeCAD.Vector(0., -thickness/2.0, -height / 2.0)
    if x_positive is True:
        pa = FreeCAD.Vector(width, -thickness/2.0, 0.)
    else:
        pa = FreeCAD.Vector(-width, -thickness/2.0, 0.)

    l1 = Part.makeLine(p1, p2)
    a2 = Part.Arc(p2, pa, p1).toShape()
    wire = Part.Wire([l1, a2])
    face = Part.Face(wire)
    node = face.extrude(FreeCAD.Vector(0, thickness, 0))

    return node


def make_node_yz(width, height, thickness,  x_positive = True):

    p1 = FreeCAD.Vector(-thickness/2.0, 0, height / 2.0)
    p2 = FreeCAD.Vector(-thickness/2.0, 0, -height / 2.0)
    if x_positive is True:
        pa = FreeCAD.Vector(-thickness/2.0, width, 0.)
    else:
        pa = FreeCAD.Vector(-thickness/2.0, -width, 0.)

    l1 = Part.makeLine(p1, p2)
    a2 = Part.Arc(p2, pa, p1).toShape()
    wire = Part.Wire([l1, a2])
    face = Part.Face(wire)
    node = face.extrude(FreeCAD.Vector(thickness, 0, 0))

    return node

# noeud court = 1/4 hauteur
# noeud long = 1/2 hauteur
# 2 neouds court = 2 * 1/4 hauteur espace de 16 % de la hateur au centre

def make_nodes_xz(shape, x_length, thickness, z_length, node_type, node_thickness):

    if node_type == MaterialProperties.NODE_NO:
        return shape

    nodes_list = []
    if node_type == MaterialProperties.NODE_SINGLE_SHORT:
        node_left = make_node_xz(node_thickness, z_length / 4.0, thickness, True)
        node_right = make_node_xz(node_thickness, z_length / 4.0, thickness, False)
        node_left.translate(FreeCAD.Vector(-x_length/2.0, 0, -z_length / 2.0))
        node_right.translate(FreeCAD.Vector(x_length/2.0, 0, -z_length / 2.0))
        nodes_list.append(node_left)
        nodes_list.append(node_right)
    elif node_type == MaterialProperties.NODE_SINGLE_LONG:
        node_left = make_node_xz(node_thickness, z_length / 2.0, thickness, True)
        node_right = make_node_xz(node_thickness, z_length / 2.0, thickness, False)
        node_left.translate(FreeCAD.Vector(-x_length/2.0, 0, -z_length / 2.0))
        node_right.translate(FreeCAD.Vector(x_length/2.0, 0, -z_length / 2.0))
        nodes_list.append(node_left)
        nodes_list.append(node_right)
    elif node_type == MaterialProperties.NODE_DUAL_SHORT:
        node_left_up = make_node_xz(node_thickness, z_length / 4.0, thickness, True)
        node_right_up = make_node_xz(node_thickness, z_length / 4.0, thickness, False)
        node_left_up.translate(FreeCAD.Vector(-x_length/2.0, 0, -z_length / 2.0 + (0.08 + 0.125) * z_length))
        node_right_up.translate(FreeCAD.Vector(x_length/2.0, 0, -z_length / 2.0 + (0.08 + 0.125) * z_length))

        node_left_down = make_node_xz(node_thickness, z_length / 4.0, thickness, True)
        node_right_down = make_node_xz(node_thickness, z_length / 4.0, thickness, False)
        node_left_down.translate(FreeCAD.Vector(-x_length/2.0, 0, -z_length / 2.0 - (0.08 + 0.125) * z_length))
        node_right_down.translate(FreeCAD.Vector(x_length/2.0, 0, -z_length / 2.0 - (0.08 + 0.125) * z_length))

        nodes_list.append(node_left_up)
        nodes_list.append(node_right_up)
        nodes_list.append(node_left_down)
        nodes_list.append(node_right_down)
    else:
        raise ValueError("Not implemented")

    for node in nodes_list:
        shape = shape.cut(node)

    return shape


def make_nodes_yz(shape, thickness, y_length, z_length, node_type, node_thickness):

    if node_type == MaterialProperties.NODE_NO:
        return shape

    nodes_list = []
    if node_type == MaterialProperties.NODE_SINGLE_SHORT:
        node_left = make_node_yz(node_thickness, z_length / 4.0, thickness, True)
        node_right = make_node_yz(node_thickness, z_length / 4.0, thickness, False)
        node_left.translate(FreeCAD.Vector(0, -y_length/2.0, -z_length / 2.0))
        node_right.translate(FreeCAD.Vector(0, y_length/2.0, -z_length / 2.0))
        nodes_list.append(node_left)
        nodes_list.append(node_right)
    elif node_type == MaterialProperties.NODE_SINGLE_LONG:
        node_left = make_node_yz(node_thickness, z_length / 2.0, thickness, True)
        node_right = make_node_yz(node_thickness, z_length / 2.0, thickness, False)
        node_left.translate(FreeCAD.Vector(0, -y_length/2.0, -z_length / 2.0))
        node_right.translate(FreeCAD.Vector(0, y_length/2.0, -z_length / 2.0))
        nodes_list.append(node_left)
        nodes_list.append(node_right)
    elif node_type == MaterialProperties.NODE_DUAL_SHORT:
        node_left_up = make_node_yz(node_thickness, z_length / 4.0, thickness, True)
        node_right_up = make_node_yz(node_thickness, z_length / 4.0, thickness, False)
        node_left_up.translate(FreeCAD.Vector(0, -y_length/2.0, -z_length / 2.0 + (0.08 + 0.125) * z_length))
        node_right_up.translate(FreeCAD.Vector(0, y_length/2.0, -z_length / 2.0 + (0.08 + 0.125) * z_length))

        node_left_down = make_node_yz(node_thickness, z_length / 4.0, thickness, True)
        node_right_down = make_node_yz(node_thickness, z_length / 4.0, thickness, False)
        node_left_down.translate(FreeCAD.Vector(0, -y_length/2.0, -z_length / 2.0 - (0.08 + 0.125) * z_length))
        node_right_down.translate(FreeCAD.Vector(0, y_length/2.0, -z_length / 2.0 - (0.08 + 0.125) * z_length))

        nodes_list.append(node_left_up)
        nodes_list.append(node_right_up)
        nodes_list.append(node_left_down)
        nodes_list.append(node_right_down)
    else:
        raise ValueError("Not implemented")

    for node in nodes_list:
        shape = shape.cut(node)

    return shape


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
    height = (referential_faces[0].CenterOfMass - referential_faces[1].CenterOfMass).Length / 2.0
    first_box_x = second_part.properties.thickness + second_part.properties.thickness_tolerance - second_part.properties.laser_beam_diameter + second_part.properties.hole_width_tolerance
    first_box = make_cross_box(first_box_x, first_part.properties.thickness, height,
                               first_part.properties.node_type, first_part.properties.node_thickness)
    first_box = make_nodes_xz(first_box, first_box_x, first_part.properties.thickness, height,
                              first_part.properties.node_type, first_part.properties.node_thickness)
    dog_bone_radius = min(first_box_x, height) * 2. / 30.

    if invert_y:
        if first_part.properties.dog_bone:
            first_box = make_dog_bones_xz(first_box, first_box_x, first_part.properties.thickness, height, dog_bone_radius, True)
        first_box.translate(FreeCAD.Vector(0, 0, -height))
    elif first_part.properties.dog_bone:
        first_box = make_dog_bones_xz(first_box, first_box_x, first_part.properties.thickness, height, dog_bone_radius, False)

    transform_matrix = get_transformation_matrix_from_vectors(axis[0], axis[1], axis[2])
    transform(first_box, referential_faces[0], transform_matrix)

    second_box_y = first_part.properties.thickness + first_part.properties.thickness_tolerance - first_part.properties.laser_beam_diameter + first_part.properties.hole_width_tolerance
    second_box = make_cross_box(second_part.properties.thickness, second_box_y, height,
                                second_part.properties.node_type, second_part.properties.node_thickness)
    second_box = make_nodes_yz(second_box, second_part.properties.thickness, second_box_y, height,
                               second_part.properties.node_type, second_part.properties.node_thickness)

    dog_bone_radius = min(second_box_y, height) * 2. / 30.

    if not invert_y:
        if second_part.properties.dog_bone:
            second_box = make_dog_bones_yz(second_box, second_part.properties.thickness, second_box_y,height, dog_bone_radius, True)
        second_box.translate(FreeCAD.Vector(0, 0, -height))
    elif second_part.properties.dog_bone:
        second_box = make_dog_bones_yz(second_box, second_part.properties.thickness, second_box_y, height, dog_bone_radius, False)
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
# X is the width of part 2.
# Y is the width of part 1.
# Z is the height of the intersection
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
            #Part.show(intersect_shape)
            sorted_areas_by_normals = helper.sort_area_shape_faces(intersect_shape)
            str_parts_name = first_part.get_name() + " -> " + second_part.get_name()
            if len(sorted_areas_by_normals) != 3:
                raise ValueError(str_parts_name + " : intersection is not rectangular box")
            smallest_area = helper.sort_area_shape_faces(intersect_shape)[0]
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
            elif not first_face_first_shape and not second_face_first_shape \
                    and first_face_second_shape and not second_face_second_shape:
                # Case where face 2 is common base and shape 2 is higher
                remove_intersections(first_part, second_part, referential_faces, axis)
            elif first_face_first_shape and not second_face_first_shape \
                    and not first_face_second_shape and not second_face_second_shape:
                # Case where face 2 is common base and shape 1 is higher
                remove_intersections(first_part, second_part, referential_faces, axis, True)
            elif not first_face_first_shape and second_face_first_shape \
                    and not first_face_second_shape and not second_face_second_shape:
                # Case where face 1 is common base and shape 1 is higher
                remove_intersections(first_part, second_part, referential_faces, axis)
            elif not first_face_first_shape and not second_face_first_shape \
                    and not first_face_second_shape and second_face_second_shape:
                # Case where face 1 is common and shape 2 is higher
                remove_intersections(first_part, second_part, referential_faces, axis, True)
            else:
                raise ValueError("Not managed")

    return parts_element
