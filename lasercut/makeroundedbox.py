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

from FreeCAD import Gui
import FreeCAD
import FreeCADGui
import Part
import math
from lasercut.roundedboxproperties import RoundedBoxProperties, TopBottomRoundedProperties
import lasercut.helper as helper
from lasercut.makehinges import do_intersection


def make_rounded_box(dimension_properties, top_properties, bottom_properties):
    height = dimension_properties.height
    part_list = []

    if dimension_properties.side_length >= dimension_properties.max_side_length:
        raise ValueError("Side length is bigger than its maximum")
    if dimension_properties.cut > dimension_properties.nb_face:
        raise ValueError("Number of cut is bigger than number of face")

    bottom_part = create_plane_part(dimension_properties, bottom_properties)
    if bottom_properties.position == TopBottomRoundedProperties.POSITION_INSIDE:
        bottom_part.translate(FreeCAD.Vector(0, 0, -dimension_properties.height / 2.0 + bottom_properties.height_shift))
    else:
        bottom_part.translate(FreeCAD.Vector(0, 0, -dimension_properties.height/2.0 - dimension_properties.thickness))
        #height -= dimension_properties.thickness
    part_list.append({'shape': bottom_part, 'name': "bottom_face_"})

    top_part = create_plane_part(dimension_properties, top_properties)
    if top_properties.position == TopBottomRoundedProperties.POSITION_INSIDE:
        top_part.translate(FreeCAD.Vector(0, 0, dimension_properties.height / 2.0 - dimension_properties.thickness -
                                          top_properties.height_shift))
    else:
        top_part.translate(FreeCAD.Vector(0, 0, dimension_properties.height/2.0))
        #height -= dimension_properties.thickness
    part_list.append({'shape': top_part, 'name': "top_face_"})

    edge = create_contours(dimension_properties.inradius, dimension_properties.nb_face,
                           dimension_properties.side_length, dimension_properties.thickness)
    part_list += create_sides(edge, height, dimension_properties.cut)

    return part_list


def create_contours(radius, nb_face, side_length, thickness):
    rel_angle = 2.0 * math.pi / float(nb_face)
    polygon_segment = []

    for face_index in range(int(nb_face)):
        seg_a = helper.Segment(FreeCAD.Vector(thickness, -side_length / 2.0, 0.),
                               FreeCAD.Vector(0., -side_length / 2.0, 0.))
        seg_b = helper.Segment(FreeCAD.Vector(thickness, side_length / 2.0, 0.),
                               FreeCAD.Vector(0., side_length / 2.0, 0.))
        current_angle = rel_angle * face_index
        translation = helper.rotate_vector_z(FreeCAD.Vector(radius, 0., 0), current_angle)
        transformed_seg_a = seg_a.rotate_z(current_angle).add(translation)
        transformed_seg_b = seg_b.rotate_z(current_angle).add(translation)

        polygon_segment.append([transformed_seg_a, transformed_seg_b])


    return polygon_segment


# Split a list into roughly equal-sized pieces :
# http://stackoverflow.com/questions/2130016/splitting-a-list-of-arbitrary-size-into-only-roughly-n-equal-parts
def chunkIt(seq, num):
    if num == 0:
        return []
    avg = len(seq) / float(num)
    out = []
    last = 0.0

    while last < len(seq):
        out.append(seq[int(last):int(last + avg)])
        last += avg

    return out


def create_sides(polygon_segment, height, nb_cut):
    part_list = []
    index = 0
    nb_face = len(polygon_segment)

    cut_index_list = []
    for chunk_list in chunkIt(range(nb_face), nb_cut):
        cut_index_list.append(chunk_list[0])

    for index in range(nb_face):
        seg_a, seg_b = polygon_segment[index]

        if index not in cut_index_list:
            face = create_shape(seg_a.A, seg_b.A, seg_b.B, seg_a.B)
            part = face.extrude(FreeCAD.Vector(0, 0, height))
            part.translate(FreeCAD.Vector(0, 0., -height/2))
            part_list.append({'shape': part, 'name': "side_face_%d" % index})
        else:
            mid_point_a = seg_a.A.add(seg_b.A)
            mid_point_a.scale(0.5, 0.5, 0.5)
            mid_point_b = seg_a.B.add(seg_b.B)
            mid_point_b.scale(0.5, 0.5, 0.5)

            face_1 = create_shape(seg_a.A, mid_point_a, mid_point_b, seg_a.B)
            part_1 = face_1.extrude(FreeCAD.Vector(0, 0, height))
            part_1.translate(FreeCAD.Vector(0, 0., -height/2))

            face_2 = create_shape(mid_point_a, seg_b.A, seg_b.B, mid_point_b)
            part_2 = face_2.extrude(FreeCAD.Vector(0, 0, height))
            part_2.translate(FreeCAD.Vector(0, 0., -height/2))

            part_list.append({'shape': part_1, 'name': "side_face_%d_a" % index})
            part_list.append({'shape': part_2, 'name': "side_face_%d_b" % index})
        index += 1

    return part_list


def create_shape(p1, p2, p3, p4):
    l1 = Part.makeLine(p1, p2)
    l2 = Part.makeLine(p2, p3)
    l3 = Part.makeLine(p3, p4)
    l4 = Part.makeLine(p4, p1)

    wire = Part.Wire([l1, l2, l3, l4])
    face = Part.Face(wire)
    return face


def retrieve_segments_arc(polygon_segment):
    arcs_segment_list = []

    nb_face = len(polygon_segment)
    for index in range(nb_face):
        first_segment = polygon_segment[index][1]
        second_segment = polygon_segment[(index + 1) % nb_face][0]

        intersection_point = do_intersection(first_segment, second_segment)
        inner_arc_radius = intersection_point.sub(first_segment.B).Length
        outer_arc_radius = intersection_point.sub(first_segment.A).Length
        mid_point_b = first_segment.B.add(second_segment.B)
        mid_point_b.scale(0.5, 0.5, 0.5)
        dir_mid_point = mid_point_b.sub(intersection_point)
        dir_mid_point.normalize()

        inner_arc_point = dir_mid_point * inner_arc_radius
        inner_arc_point = inner_arc_point.add(intersection_point)
        outer_arc_point = dir_mid_point * outer_arc_radius
        outer_arc_point = outer_arc_point.add(intersection_point)
        arcs_segment_list.append(helper.Segment(outer_arc_point, inner_arc_point))

    #FreeCAD.Console.PrintMessage("Computed arc radius : inner = %f, outer = %f" % (inner_arc_radius, outer_arc_radius))
    return arcs_segment_list


def get_contours_with_arc(edge, arcs_segment_list):
    nb_face = len(edge)

    outer_contours = []
    inner_contours = []
    for index in range(nb_face):
        first_segment = edge[index][0]
        second_segment = edge[index][1]
        last_segment = edge[(index + 1) % nb_face][0]

        outer_contours.append(Part.makeLine(first_segment.A, second_segment.A))
        inner_contours.append(Part.makeLine(first_segment.B, second_segment.B))

        outer_contours.append(Part.Arc(second_segment.A, arcs_segment_list[index].A, last_segment.A).toShape())
        inner_contours.append(Part.Arc(second_segment.B, arcs_segment_list[index].B, last_segment.B).toShape())

    return inner_contours, outer_contours


def create_plane_part(dimension_properties, plane_properties):
    if plane_properties.position == TopBottomRoundedProperties.POSITION_INSIDE:
        radius = dimension_properties.inradius
        side_length = dimension_properties.side_length
    else:
        radius = dimension_properties.inradius + plane_properties.radius_outside
        side_length = dimension_properties.side_length * radius / dimension_properties.inradius

    edge = create_contours(radius, dimension_properties.nb_face, side_length, dimension_properties.thickness)
    arcs_segment_list = retrieve_segments_arc(edge)
    inner_contours, outer_contours = get_contours_with_arc(edge, arcs_segment_list)

    if plane_properties.position == TopBottomRoundedProperties.POSITION_INSIDE:
        wire=Part.Wire(inner_contours)
    else:
        wire=Part.Wire(outer_contours)

    face = Part.Face(wire)
    part = face.extrude(FreeCAD.Vector(0, 0, dimension_properties.thickness))
    return part

