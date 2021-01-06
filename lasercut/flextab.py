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
import lasercut.helper as helper
import math


def make_flex_tab_join(tab, tab_part, other_parts):
    make_round_tab(tab, tab_part, other_parts)
    return


def make_round_tab(tab, tab_part, other_parts):
    for part_interactor in other_parts:
        y = tab.y_length / 2.0 - part_interactor.properties.thickness - tab.tabs_width / 2.0
        tab_to_add = make_rounded_shape(tab_part.properties, part_interactor.properties,
                                        tab.tabs_width, y)

        intersect_test, tab_to_add_transformed = helper.check_intersect(tab_to_add, tab,
                                                                        part_interactor.properties)
        if intersect_test:
            tab_part.toAdd.append(tab_to_add_transformed)
            #print "tab " + str(tab.dog_bone)
            hole = helper.tab_join_create_hole_on_plane(tab, tab.tabs_width, y, tab_part.properties,
                                                        part_interactor.properties)
            part_interactor.toRemove.append(helper.transform_part(hole, tab))
            break

    for part_interactor in other_parts:
        y = -(tab.y_length / 2.0 - part_interactor.properties.thickness - tab.tabs_width / 2.0)

        tab_to_add = make_rounded_shape_for_groove(tab_part.properties, part_interactor.properties,
                                                   tab.tabs_width, y)

        intersect_test, tab_to_add_transformed = helper.check_intersect(tab_to_add, tab,
                                                                        part_interactor.properties)
        if intersect_test:
            tab_part.toAdd.append(tab_to_add_transformed)
            groove = make_flex_slot(tab_part.properties, part_interactor.properties,
                                    tab.tabs_width, y)
            tab_part.toRemove.append(helper.transform_part(groove, tab))
            hole = helper.tab_join_create_hole_on_plane(tab, tab.tabs_width, y, tab_part.properties,
                                                        part_interactor.properties)
            part_interactor.toRemove.append(helper.transform_part(hole, tab))
            break
    return


def make_rounded_shape(material_face, material_plane, width, pos_y, use_laser_kerf = True):
    part_thickness = material_face.thickness
    other_part_thickness_with_tolerance = material_plane.thickness + material_plane.thickness_tolerance

    corrected_width = width
    if use_laser_kerf:
        corrected_width = corrected_width + material_face.laser_beam_diameter

    half_width = corrected_width / 2.0
    z = part_thickness/2.0
    th = other_part_thickness_with_tolerance

    p1 = FreeCAD.Vector(0., -half_width, z)
    p2 = FreeCAD.Vector(0.3 * th, -half_width, z)
    cp2_1 = FreeCAD.Vector(0.9 * th, -half_width, z)
    p3 = FreeCAD.Vector(0.9 * th, 0, z)
    cp3_1 = FreeCAD.Vector(0.9 * th, half_width / 4.0, z)
    cp3_2 = FreeCAD.Vector(1.6 * th, half_width / 4.0, z)
    p4 = FreeCAD.Vector(1.6 * th, half_width / 2.0, z)
    p5 = FreeCAD.Vector(1.6 * th, half_width, z)
    cp5_1 = FreeCAD.Vector(1.6 * th, 1.2 * half_width, z)
    p6 = FreeCAD.Vector(1.04 * th, 1.2 * half_width, z)
    p7 = FreeCAD.Vector(th, half_width, z)
    p8 = FreeCAD.Vector(0, half_width, z)

    l1 = Part.Line(p1, p2)
    c2 = make_bezier_curve([p2, cp2_1, p3])
    c3 = make_bezier_curve([p3, cp3_1, cp3_2, p4])
    l4 = Part.Line(p4, p5)
    c5 = make_bezier_curve([p5, cp5_1, p6])
    l6 = Part.Line(p6, p7)
    l7 = Part.Line(p7, p8)
    l8 = Part.Line(p8, p1)

    shape = Part.Shape([l1, c2, c3, l4, c5, l6, l7, l8])
    wire = Part.Wire(shape.Edges)
    face = Part.Face(wire)
    part = face.extrude(FreeCAD.Vector(0, 0, -part_thickness))
    part.translate(FreeCAD.Vector(0, pos_y, 0))
    #Part.show(part)
    return part


def make_rounded_shape_for_groove(material_face, material_plane, width, pos_y, use_laser_kerf = True):
    part_thickness = material_face.thickness
    other_part_thickness_with_tolerance = material_plane.thickness + material_plane.thickness_tolerance

    corrected_width = width
    if use_laser_kerf:
        corrected_width = corrected_width + material_face.laser_beam_diameter

    half_width = corrected_width / 2.0
    z = part_thickness/2.0
    th = other_part_thickness_with_tolerance

    p1 = FreeCAD.Vector(0., -half_width, z)
    p2 = FreeCAD.Vector(th, -half_width, z)
    p3 = FreeCAD.Vector(1.04 * th, -1.15 * half_width, z)
    p4 = FreeCAD.Vector(1.4 * th, -1.15 * half_width, z)
    cp4_1 = FreeCAD.Vector(1.6 * th, -half_width / 4.0, z)
    p5 = FreeCAD.Vector(th, half_width / 4.0, z)
    p6 = FreeCAD.Vector(th, 0.7 * half_width, z)
    cp6_1 = FreeCAD.Vector(th, half_width, z)
    p7 = FreeCAD.Vector(0.7 * th, half_width, z)
    p8 = FreeCAD.Vector(0, half_width, z)

    l1 = Part.Line(p1, p2)
    l2 = Part.Line(p2, p3)
    l3 = Part.Line(p3, p4)
    c4 = make_bezier_curve([p4, cp4_1, p5])
    l5 = Part.Line(p5, p6)
    c6 = make_bezier_curve([p6, cp6_1, p7])
    p7 = Part.Line(p7, p8)
    p8 = Part.Line(p8, p1)

    shape = Part.Shape([l1, l2, l3, c4, l5, c6, p7, p8])
    wire = Part.Wire(shape.Edges)
    face = Part.Face(wire)
    part = face.extrude(FreeCAD.Vector(0, 0, -part_thickness))
    part.translate(FreeCAD.Vector(0, pos_y, 0))
    #Part.show(part)

    part = helper.make_dog_bone_on_limits_on_xz(part, part_thickness)

    return part


def make_flex_slot(material_face, material_plane, width, pos_y, use_laser_kerf = True):
    part_thickness = material_face.thickness
    corrected_width = width
    if use_laser_kerf:
        corrected_width = corrected_width + material_face.laser_beam_diameter

    x_start = (material_plane.thickness + material_plane.thickness_tolerance) * 2.0 # 2.0 is arbitrary
    y_start = width / 5.0
    x_length = 1.8 * corrected_width
    y_length = 0.6 * corrected_width
    groove_thickness = 0.15 * corrected_width

    z = part_thickness / 2.0
    p1 = FreeCAD.Vector(x_start, y_start, z)
    p2 = FreeCAD.Vector(-x_length / 12.0, y_start, z)
    cp2_1 = FreeCAD.Vector(-x_length / 6.0, y_start, z)
    cp2_2 = FreeCAD.Vector(-x_length / 2.0, y_start - y_length, z)
    p3 = FreeCAD.Vector(FreeCAD.Vector(-x_length, y_start - (y_length / 2.0) , z))

    half_groove = groove_thickness / 2.0
    lp1 = p1 + FreeCAD.Vector(0., -half_groove, 0)
    rp1 = p1 + FreeCAD.Vector(0., half_groove, 0)
    lp2 = p2 + FreeCAD.Vector(0., -half_groove, 0)
    rp2 = p2 + FreeCAD.Vector(0., half_groove, 0)
    lcp2_1 = cp2_1 + FreeCAD.Vector(0., -half_groove, 0)
    rcp2_1 = cp2_1 + FreeCAD.Vector(0., half_groove, 0)
    lcp2_2 = cp2_2 + FreeCAD.Vector(0., -half_groove, 0)
    rcp2_2 = cp2_2 + FreeCAD.Vector(0., half_groove, 0)
    lp3 = p3 + FreeCAD.Vector(0., -half_groove, 0)
    rp3 = p3 + FreeCAD.Vector(0., half_groove, 0)

    local_axe_tmp = rp3.sub(lp3)
    local_axe_tmp.normalize()
    arc_dir_vector = FreeCAD.Vector(0,0,1).cross(local_axe_tmp)
    arc_dir_vector.normalize()
    arc_cp = (rp3 + lp3) * 0.5 + arc_dir_vector * local_axe_tmp.Length * 0.5

    l1 = Part.Line(lp1, lp2)
    c2 = make_bezier_curve([lp2, lcp2_1, lcp2_2, lp3])
    a3 = Part.Arc(lp3, arc_cp, rp3)
    c4 = make_bezier_curve([rp2, rcp2_1, rcp2_2, rp3])
    l5 = Part.Line(rp1, rp2)
    l6 = Part.Line(rp1, lp1)

    shape = Part.Shape([l1, c2, a3, c4, l5, l6])
    wire = Part.Wire(shape.Edges)
    face = Part.Face(wire)
    part = face.extrude(FreeCAD.Vector(0, 0, -part_thickness))
    #Part.show(part)
    part.translate(FreeCAD.Vector(0, pos_y, 0))

    return part


def make_bezier_curve(points):
    geomCurve = Part.BezierCurve()
    geomCurve.setPoles(points)
    return geomCurve


#
#
# #            X (Length)
#  #            |
#  #            |
#  #            |
#  #            |Z (Height)
#  #            ---------------------------> Y (Width)
# def tab_join_create_rounded_tab(material_face, material_plane, width, pos_y, use_laser_kerf = True):
#
#     corrected_length = material_plane.thickness
#     corrected_width = width / 2.0 #+ materialFace.laser_beam_diameter
#     corrected_height = material_face.thickness
#
#     if use_laser_kerf:
#         corrected_width += material_face.laser_beam_diameter
#
#     #origin = FreeCAD.Vector(-corrected_length / 2.0, -corrected_width / 2.0, -corrected_height / 2.0)
#     origin = FreeCAD.Vector(0., 0., -corrected_height / 2.0)
#     tab = Part.makeBox(corrected_length, corrected_width, corrected_height, origin)
#
#     #Part.show(tab)
#
#     small_corrected_length = corrected_length /2.0
#     origin = FreeCAD.Vector(0., -corrected_width, -corrected_height / 2.0)
#     tab2 = Part.makeBox(small_corrected_length, corrected_width, corrected_height, origin)
#     #Part.show(tab2)
#     new_tab = tab.fuse(tab2)
#     #print "" + str(dir(new_tab))
#
#     print "a : " + str(corrected_length) + ", " + str(corrected_width)
#     new_tab = make_fillet_z(new_tab, corrected_length, corrected_width, 1)
#     new_tab.translate(FreeCAD.Vector(0, pos_y, 0))
#     Part.show(new_tab)
#     return new_tab
#
# def make_fillet_z_test(shape):
#     i = 0
#     edges_list = []
#     for edge in shape.Edges:
#         v1 = edge.Vertexes[0]
#         v2 = edge.Vertexes[1]
#
#         if v1.X == v2.X and v1.Y == v2.Y:
#             if v1.X > 0.1:
#                 #print "" + str(i) + " : fillet"
#                 edges_list.append(edge)
#         i+=1
#     if len(edges_list):
#         shape = shape.makeFillet(0.5, edges_list)
#     return shape
#
#
# def make_fillet_z(shape, x, y, radius, epsilon=10e-6):
#
#     for edge in shape.Edges:
#         v1 = edge.Vertexes[0]
#         v2 = edge.Vertexes[1]
#
#         if v1.X == v2.X and v1.Y == v2.Y and \
#             math.fabs(v1.X - x) < epsilon and math.fabs(v1.Y - y) < epsilon :
#                 shape = shape.makeFillet(radius, [edge])
#                 break
#
#     return shape
