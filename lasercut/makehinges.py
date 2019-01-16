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
from lasercut.helper import transform, compare_freecad_vector, compare_value, Segment, assemble_list_element


def complete_hinges_properties(hinge, face_1, face_2, storeAll = False):
    edge1, edge2, extrusion_vector = get_coplanar_edge(face_1, face_2)
    seg_face_1, seg_face_2 = get_segment_from_edge(edge1, edge2)
    intersection_point = do_intersection(seg_face_1,seg_face_2)

    #print "intersection point : => " + str(intersection_point)
    #print "seg1 " +str(seg_face_1)
    #print "seg2 " +str(seg_face_2)

    diff_length_test = compare_value(intersection_point.sub(seg_face_1.B).Length,
                                     intersection_point.sub(seg_face_2.B).Length,
                                     10e-3)
    if diff_length_test is False :
        raise ValueError("Not an arc %f %f" %(intersection_point.sub(seg_face_1.B).Length, intersection_point.sub(seg_face_2.B).Length))
    inner_arc_radius = intersection_point.sub(seg_face_1.B).Length
    outer_arc_radius = intersection_point.sub(seg_face_1.A).Length
    mid_arc_radius = intersection_point.sub(seg_face_1.mid_point()).Length

    mid_point_b = seg_face_1.B.add(seg_face_2.B)
    mid_point_b.scale(0.5, 0.5, 0.5)
    dir_mid_point = mid_point_b.sub(intersection_point)
    dir_mid_point.normalize()

    inner_arc_point = dir_mid_point * inner_arc_radius
    outter_arc_point = dir_mid_point * outer_arc_radius
    if hinge.reversed_angle:
        inner_arc_point = intersection_point.sub(inner_arc_point)
        outter_arc_point = intersection_point.sub(outter_arc_point)
    else:    
        inner_arc_point = inner_arc_point.add(intersection_point)
        outter_arc_point = outter_arc_point.add(intersection_point)
    arc_middle_segment = Segment(outter_arc_point, inner_arc_point)
    
    hinge.seg_face_1 = seg_face_1
    hinge.seg_face_2 = seg_face_2
    hinge.arc_middle_segment = arc_middle_segment
    hinge.extrustion_vector = extrusion_vector
    hinge.rad_angle = seg_face_1.get_angle(seg_face_2)
    if hinge.reversed_angle:
        hinge.rad_angle= math.pi*2 - hinge.rad_angle
    hinge.deg_angle = hinge.rad_angle * 180. / math.pi 
    hinge.rotation_vector = seg_face_1.vector().cross(seg_face_2.vector())
    if hinge.reversed_angle:
        hinge.rotation_vector*=-1
    hinge.arc_length = mid_arc_radius * hinge.rad_angle
    hinge.arc_inner_radius = inner_arc_radius
    hinge.arc_outer_radius = outer_arc_radius
    hinge.thickness = seg_face_1.length()

    if storeAll is False:
        hinge.arc_middle_segment = None
        hinge.extrustion_vector = None
        hinge.seg_face_1 = None
        hinge.seg_face_2 = None
        hinge.rotation_vector = None

    return True


def create_solid_corner(hinge):
    inner_arc_point = hinge.arc_middle_segment.B
    outter_arc_point = hinge.arc_middle_segment.A

    l1 = Part.makeLine(hinge.seg_face_1.A, hinge.seg_face_1.B)
    a2 = Part.Arc(hinge.seg_face_1.B, inner_arc_point, hinge.seg_face_2.B).toShape()
    l3 = Part.makeLine(hinge.seg_face_2.B, hinge.seg_face_2.A)
    a4 = Part.Arc(hinge.seg_face_2.A, outter_arc_point, hinge.seg_face_1.A).toShape()
    wire = Part.Wire([l1, a2, l3, a4])
    face = Part.Face(wire)

    hinge.solid = face.extrude(hinge.extrustion_vector)
    #Part.show(hinge.solid)
    return


def get_coplanar_edge(face1, face2):
    face1_edges = get_thickness_edge(face1)
    face2_edges = get_thickness_edge(face2)

    midpoint1_a = face1_edges[0].CenterOfMass
    midpoint2_a = face2_edges[0].CenterOfMass
    midpoint2_b = face2_edges[1].CenterOfMass

    edge2 = face2_edges[0]
    distance = midpoint1_a.sub(midpoint2_a).Length
    if midpoint1_a.sub(midpoint2_b).Length < distance:
        edge2 = face2_edges[1]

    return face1_edges[0], edge2, face1_edges[1].CenterOfMass.sub(face1_edges[0].CenterOfMass)


def get_segment_from_edge(edge1, edge2):
    length = edge1.Vertexes[0].Point.sub(edge2.Vertexes[0].Point).Length
    case = 1

    test_length = edge1.Vertexes[0].Point.sub(edge2.Vertexes[1].Point).Length
    if test_length < length:
        case = 2
        length = test_length

    test_length = edge1.Vertexes[1].Point.sub(edge2.Vertexes[0].Point).Length
    if test_length < length:
        case = 3
        length = test_length

    test_length =  edge1.Vertexes[1].Point.sub(edge2.Vertexes[1].Point).Length
    if test_length < length:
        case = 4
        length = test_length

    if case == 1:
        first = Segment(edge1.Vertexes[1].Point, edge1.Vertexes[0].Point)
        second = Segment(edge2.Vertexes[1].Point, edge2.Vertexes[0].Point)
    elif case == 2:
        first = Segment(edge1.Vertexes[1].Point, edge1.Vertexes[0].Point)
        second = Segment(edge2.Vertexes[0].Point, edge2.Vertexes[1].Point)
    elif case == 3:
        first = Segment(edge1.Vertexes[0].Point, edge1.Vertexes[1].Point)
        second = Segment(edge2.Vertexes[1].Point, edge2.Vertexes[0].Point)
    elif case == 4:
        first = Segment(edge1.Vertexes[0].Point, edge1.Vertexes[1].Point)
        second = Segment(edge2.Vertexes[0].Point, edge2.Vertexes[1].Point)
    else:
        raise ValueError("Impossible exception")
    return first, second


def get_thickness_edge(face):
    list_edges = Part.__sortEdges__(face.Edges)
    small_edge_list = [list_edges[0]]

    for edge in list_edges[1:]:
        if edge.Length == small_edge_list[0].Length:
            small_edge_list.append(edge)
        elif edge.Length < small_edge_list[0].Length:
            small_edge_list = [edge]

    return small_edge_list


def get_width_edge(face):
    list_edges = Part.__sortEdges__(face.Edges)
    long_edge_list = [list_edges[0]]

    for edge in list_edges[1:]:
        if edge.Length == long_edge_list[0].Length:
            long_edge_list.append(edge)
        elif edge.Length > long_edge_list[0].Length:
            long_edge_list = [edge]

    return long_edge_list


#http# s://gist.github.com/hanigamal/6556506
def do_intersection(seg1, seg2):
    da = seg1.B - seg1.A
    db = seg2.B - seg2.A
    dc = seg2.A - seg1.A

    coplanar_val = dc.dot(da.cross(db))
    if not compare_value(coplanar_val, 0.):
        raise ValueError("Not coplanar (seg1: %s, seg2: %s) => res: %s" %(str(seg1), str(seg2), str(coplanar_val)))

    a = dc.cross(db).dot(da.cross(db))
    s = dc.cross(db).dot(da.cross(db)) / da.cross(db).dot(da.cross(db))
    if s >= 10e-6:
        da.scale(s, s, s)
        ip = seg1.A.add(da)
        return ip
    else:
        raise ValueError("Wrong scale")


# http://www.deferredprocrastination.co.uk/blog/2012/minimum-bend-radius/
def estimate_min_link(rad_angle, thickness, clearance_width):
    tmp = (clearance_width + thickness) / (2. * math.sqrt(thickness * thickness / 2.))
    min_link = rad_angle / (math.pi / 4.0 - math.acos(tmp))
    return math.ceil(min_link)


def create_linked_part(hinges_list, material_properties):
    if len(hinges_list) == 0:
        raise ValueError("No hinge defined")

    if material_properties.laser_beam_diameter > material_properties.link_clearance:
        raise ValueError("Laser beam diameter is greater than clearance width")
    elif material_properties.link_clearance < 2. * material_properties.laser_beam_diameter:
        FreeCAD.Console.PrintMessage( \
              "Caution : link clearance is less than twice the laser beam diameter. Exported svg " + \
              "will contains lines too close and the laser will almost go twice in the same position.\n" + \
              "It is advisable to choose a clearance at least twice the kerf. You could also set clearance " + \
              "equals to kerf if you want laser have one passage. But in the exported SVG, hinges apertures " + \
              "are in fact square with 10e-3 width, so you have to remove manually the three others sides " + \
              "for all square to avoid laser returning to same place.")

    parts_to_fuse = [hinges_list[0].freecad_object_1.Shape.copy()]
    hinges_to_removes = []
    last_face = hinges_list[0].freecad_face_1
    sum_angle = 0.
    rotation_vector = None
    for index, hinge in enumerate(hinges_list):
        if hinge.nb_link < hinge.min_links_nb:
            FreeCAD.Console.PrintError("Min. link is not respected for living hinges named " + str(hinge.name))

        flat_connection = create_flat_connection(hinge, last_face)
        parts_to_fuse.append(flat_connection)
        hinges_to_removes.append(make_hinges(hinge, material_properties, last_face))
        last_face = find_same_normal_face(flat_connection, last_face)

        sum_angle += hinge.deg_angle
        if rotation_vector is None:
            rotation_vector = hinge.rotation_vector

        second_shape_transformed = assemble_shape(last_face, hinge.freecad_object_2.Shape, hinge.freecad_face_2,
                                                  rotation_vector, -sum_angle)
        parts_to_fuse.append(second_shape_transformed)
        if index < (len(hinges_list) - 1):
            last_face = find_same_normal_face(second_shape_transformed, last_face)

    flat_part = assemble_list_element(parts_to_fuse)
    for hinge_to_remove in hinges_to_removes:
        flat_part = flat_part.cut(hinge_to_remove)

    solid = hinges_list[0].solid.copy()
    for hinge in hinges_list[1:]:
        solid = solid.fuse(hinge.solid)

    return flat_part, solid


def create_flat_connection(hinge_properties, referentiel_face):
    box_x_size = hinge_properties.arc_length
    box_y_size = hinge_properties.extrustion_vector.Length
    box_z_size = hinge_properties.thickness
    box = Part.makeBox(box_x_size, box_y_size, box_z_size, FreeCAD.Vector(0., -box_y_size/2.0, -box_z_size/2.0))

    flat_connection = transform(box, referentiel_face)

    return flat_connection


def get_hinges_x_positions(nb_hinges, x_length):
    hinges_list = []
    interval_length = x_length / float(nb_hinges - 1)

    for i in range(int(nb_hinges)):
        hinges_list.append(float(i) * interval_length)

    return hinges_list


def get_hinges_y_positions(nb_holes_by_column, hole_length, hole_space):
    y_pos_list = []
    half_hole_number = int(float(nb_holes_by_column) / 2.0)
    interval_length = hole_length + hole_space

    if nb_holes_by_column % 2 == 1:
        y_pos_list.append(0.0)
        for i in range(half_hole_number):
            y_pos_list.append(float(i+1) * interval_length)
            y_pos_list.append(float(-i-1) * interval_length)
    else:
        for i in range(half_hole_number):
            y_pos_list.append(float(i) * interval_length + interval_length / 2.0)
            y_pos_list.append(float(-i) * interval_length - interval_length / 2.0)

    return y_pos_list


def create_hole_hinge(hinge_clearance, hinge_length, thickness, kerf_diameter):
    height = thickness * 2.0
    hinge_width = max(10e-3, hinge_clearance - kerf_diameter)
    if hinge_clearance < kerf_diameter:
        raise ValueError("Hinge clearance is less than kerf diameter")
    elif hinge_clearance < 2. * kerf_diameter:
        box_length = hinge_length - kerf_diameter
        hinge = Part.makeBox(hinge_width, box_length, height, FreeCAD.Vector(-hinge_width/2.0, -box_length/2.0, -height/2.0))
    else:
        box_length = hinge_length - hinge_width - kerf_diameter # hinge_width is for the two corner radius
        hinge = draw_rounded_hinge(hinge_width, box_length, height)

    return hinge


def draw_rounded_hinge(hinge_width, hinge_length, height):
    half_w = hinge_width/2.0
    half_l = hinge_length/2.0
    half_h = height / 2.0
    z_plane = -half_h
    v1 = FreeCAD.Vector(-half_w, -half_l, z_plane)
    v2 = FreeCAD.Vector(-half_w, half_l, z_plane)
    v3 = FreeCAD.Vector(half_w, half_l, z_plane)
    v4 = FreeCAD.Vector(half_w, -half_l, z_plane)
    vc1 = FreeCAD.Vector(0, -(half_l + half_w), z_plane)
    vc2 = FreeCAD.Vector(0, half_l+half_w, z_plane)
    c1 = Part.Arc(v1, vc1, v4).toShape()
    c2 = Part.Arc(v2, vc2, v3).toShape()
    l1 = Part.makeLine(v1, v2)
    l2 = Part.makeLine(v3, v4)
    wire = Part.Wire([c1, l1, c2, l2])
    hinge = wire.extrude(FreeCAD.Vector(0.0, 0.0, height))
    hinge_solid = Part.makeSolid(hinge)
    return hinge_solid


def make_hinges(hinge_properties, global_hinges_properties, referentiel_face):
    x_hinges_positions = get_hinges_x_positions(hinge_properties.nb_link, hinge_properties.arc_length)
    hinges_list = []
    y_length = hinge_properties.extrustion_vector.Length
    thickness = hinge_properties.thickness
    length_ratio = global_hinges_properties.occupancy_ratio

    nb_holes_by_column = int(global_hinges_properties.alternate_nb_hinge)
    hole_length = (y_length * length_ratio) / float(nb_holes_by_column)
    hole_space = y_length * (1. - length_ratio) /float(nb_holes_by_column + 1)
    y_pos_list = get_hinges_y_positions(nb_holes_by_column, hole_length, hole_space)
    nb_holes_by_column = int(nb_holes_by_column + 1)
    y_pos_list_2 = get_hinges_y_positions(nb_holes_by_column, hole_length, hole_space)

    index = 0
    for hinge_x in x_hinges_positions:

        if index % 2 == 0:
            pos_list = y_pos_list
        else:
            pos_list = y_pos_list_2

        for pos_y in pos_list:
            new_hinge = create_hole_hinge(global_hinges_properties.link_clearance, hole_length, thickness,
                                          global_hinges_properties.laser_beam_diameter)
            new_hinge.translate(FreeCAD.Vector(hinge_x, pos_y, 0))
            hinges_list.append(new_hinge)
        index += 1

    hinges_to_remove = assemble_list_element(hinges_list)
    hinges_to_remove_transformed = transform(hinges_to_remove, referentiel_face)
    return hinges_to_remove_transformed


def assemble_shape(face1, shape, face2, rotation_vector, rotation_angle):
    new_shape = shape.copy()
    new_shape.rotate(face2.CenterOfMass, rotation_vector, rotation_angle)
    new_shape.translate(face1.CenterOfMass.sub(face2.CenterOfMass))
    return new_shape


def find_same_normal_face(obj, ref_face):
    ref_normal = ref_face.normalAt(0, 0)
    found_face = None
    for face in obj.Faces:
        normal = face.normalAt(0, 0)

        if compare_freecad_vector(ref_normal, normal) is True and compare_value(ref_face.Area, face.Area) is True:
            found_face = face
            break
    if found_face is None:
        raise ValueError("Unable to find face with same normal")

    return found_face

