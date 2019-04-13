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
from lasercut.boxproperties import BoxProperties, TopBottomProperties


def make_box(dimension_properties, top_properties, bottom_properties):
    part_list = []

    if dimension_properties.outside_measure is True:
        make_box_outside_measure(dimension_properties, top_properties, bottom_properties, part_list)
    else:
        make_box_inside_measure(dimension_properties, top_properties, bottom_properties, part_list)

    return part_list


def make_box_outside_measure(dimension_properties, top_properties, bottom_properties, part_list):
    thickness = dimension_properties.thickness
    height = dimension_properties.height
    shift_height = 0.

    exceeding_length = 0.
    exceeding_width = 0.

    if dimension_properties.length_width_priority == BoxProperties.LENGTH_PRIORTY:
        length = dimension_properties.length
        length_spacing = dimension_properties.width - 2. * thickness
        width = dimension_properties.width - 2. * thickness
        width_spacing = dimension_properties.length - 2. * thickness - 2. * dimension_properties.width_shift
    elif dimension_properties.length_width_priority == BoxProperties.WIDTH_PRIORTY:
        length = dimension_properties.length - 2. * thickness
        length_spacing = dimension_properties.width - 2. * thickness - 2. * dimension_properties.length_shift
        width = dimension_properties.width
        width_spacing = dimension_properties.length - 2. * thickness
    elif dimension_properties.length_width_priority == BoxProperties.CROSS_PRIORTY:
        length = dimension_properties.length
        length_spacing = dimension_properties.width - 2. * thickness - dimension_properties.width_outside
        width = dimension_properties.width
        width_spacing = dimension_properties.length - 2. * thickness - dimension_properties.length_outside
    elif dimension_properties.length_width_priority == BoxProperties.ROUND_PRIORTY:
        length = dimension_properties.length - dimension_properties.inner_radius
        length_spacing = dimension_properties.width - 2. * thickness
        width = dimension_properties.width - dimension_properties.inner_radius
        width_spacing = dimension_properties.length - 2. * thickness
    else:
        raise ValueError("Length/Width priority not defined")

    if bottom_properties.position == TopBottomProperties.POSITION_OUTSIDE:
        height -= thickness
        shift_height -= -thickness / 2.0
        exceeding_length = max(exceeding_length, bottom_properties.length_outside)
        exceeding_width = max(exceeding_width, bottom_properties.width_outside)

    if top_properties.position == TopBottomProperties.POSITION_OUTSIDE:
        height -= thickness
        shift_height -= thickness / 2.0
        exceeding_length = max(exceeding_length, top_properties.length_outside)
        exceeding_width = max(exceeding_width, top_properties.width_outside)

    if exceeding_length > 0.:
        length -= exceeding_length
        width_spacing -= exceeding_length

    if exceeding_width > 0.:
        width -= exceeding_width
        length_spacing -= exceeding_width

    down_z_ref = -height / 2.0
    up_z_ref = height / 2.0
    face_panel, behind_panel = make_front_panels(length, height, thickness, length_spacing)
    if dimension_properties.length_width_priority == BoxProperties.ROUND_PRIORTY:
        face_panel = None
        face_panel_1, face_panel_2 = make_twice_half_front_panel(length, height, thickness, length_spacing)
    left_panel, right_panel = make_side_panels(width, height, thickness, width_spacing)
    if bottom_properties.position == TopBottomProperties.POSITION_INSIDE:
        bottom_panel = make_z_panel(width_spacing,
                                    length_spacing,
                                    thickness, down_z_ref + bottom_properties.height_shift)
    else:
        bottom_panel = make_z_panel(dimension_properties.length + bottom_properties.length_outside - exceeding_length,
                                    dimension_properties.width + bottom_properties.width_outside - exceeding_width,
                                    thickness, down_z_ref - thickness)

    if top_properties.top_type != TopBottomProperties.TOP_TYPE_NORMAL:
            raise ValueError("Top type not implemented")
    if top_properties.position == TopBottomProperties.POSITION_INSIDE:
        top_panel = make_z_panel(width_spacing,
                                 length_spacing,
                                 thickness, up_z_ref - thickness - top_properties.height_shift)
    else:
        top_panel = make_z_panel(dimension_properties.length + top_properties.length_outside - exceeding_length,
                                dimension_properties.width + top_properties.width_outside - exceeding_width,
                                thickness, up_z_ref)

    if face_panel is not None :
        face_panel.translate(FreeCAD.Vector(0, 0, shift_height))
    else :
        face_panel_1.translate(FreeCAD.Vector(0, 0, shift_height))
        face_panel_2.translate(FreeCAD.Vector(0, 0, shift_height))
    behind_panel.translate(FreeCAD.Vector(0, 0, shift_height))
    left_panel.translate(FreeCAD.Vector(0, 0, shift_height))
    right_panel.translate(FreeCAD.Vector(0, 0, shift_height))
    bottom_panel.translate(FreeCAD.Vector(0, 0, shift_height))
    top_panel.translate(FreeCAD.Vector(0, 0, shift_height))

    if face_panel is not None :
        part_list.append({'shape': face_panel, 'name': "face_panel"})
    else:
        part_list.append({'shape': face_panel_1, 'name': "face_panel_1"})
        part_list.append({'shape': face_panel_2, 'name': "face_panel_2"})
    part_list.append({'shape': behind_panel, 'name': "behind_panel"})
    part_list.append({'shape': left_panel, 'name': "left_panel"})
    part_list.append({'shape': right_panel, 'name': "right_panel"})
    part_list.append({'shape': bottom_panel, 'name': "bottom_panel"})
    part_list.append({'shape': top_panel, 'name': "top_panel"})


def make_box_inside_measure(dimension_properties, top_properties, bottom_properties, part_list):

    thickness = dimension_properties.thickness
    height = dimension_properties.height
    shift_height = 0.
    add_outside_cover_length = 0.
    add_outside_cover_width = 0.

    if dimension_properties.length_width_priority == BoxProperties.LENGTH_PRIORTY:
        length = dimension_properties.length + 2. * thickness + 2. * dimension_properties.width_shift
        length_spacing = dimension_properties.width
        width = dimension_properties.width
        width_spacing = dimension_properties.length
        add_outside_cover_length =  2. * dimension_properties.width_shift
    elif dimension_properties.length_width_priority == BoxProperties.WIDTH_PRIORTY:
        length = dimension_properties.length
        length_spacing = dimension_properties.width
        width = dimension_properties.width + 2. * thickness + 2. * dimension_properties.length_shift
        width_spacing = dimension_properties.length
        add_outside_cover_width = 2. * dimension_properties.length_shift
    elif dimension_properties.length_width_priority == BoxProperties.CROSS_PRIORTY:
        length = dimension_properties.length + 2. * thickness + dimension_properties.length_outside
        length_spacing = dimension_properties.width
        width = dimension_properties.width + 2. * thickness + dimension_properties.width_outside
        width_spacing = dimension_properties.length
    elif dimension_properties.length_width_priority == BoxProperties.ROUND_PRIORTY:
        length = dimension_properties.length + 2. * thickness - dimension_properties.inner_radius
        length_spacing = dimension_properties.width
        width = dimension_properties.width + 2. * thickness - dimension_properties.inner_radius
        width_spacing = dimension_properties.length
    else:
        raise ValueError("Length/Width priority not defined")

    if bottom_properties.position == TopBottomProperties.POSITION_INSIDE:
        height += thickness + bottom_properties.height_shift
        shift_height += (-thickness - bottom_properties.height_shift) / 2.0

    if top_properties.position == TopBottomProperties.POSITION_INSIDE:
        height += thickness + top_properties.height_shift
        shift_height += (thickness + bottom_properties.height_shift) / 2.0

    down_z_ref = -height / 2.0
    up_z_ref = height / 2.0
    face_panel, behind_panel = make_front_panels(length, height, thickness, length_spacing)
    if dimension_properties.length_width_priority == BoxProperties.ROUND_PRIORTY:
        face_panel = None
        face_panel_1, face_panel_2 = make_twice_half_front_panel(length, height, thickness, length_spacing)
    left_panel, right_panel = make_side_panels(width, height, thickness, width_spacing)
    #bottom_panel = make_bottom_panel(dimension_properties, bottom_properties, down_z_ref, False)
    if bottom_properties.position == TopBottomProperties.POSITION_INSIDE:
        bottom_panel = make_z_panel(dimension_properties.length, dimension_properties.width, thickness,
                                       down_z_ref + bottom_properties.height_shift)
    else:
        bottom_panel = make_z_panel(dimension_properties.length + 2. * thickness + bottom_properties.length_outside + add_outside_cover_length,
                                       dimension_properties.width + 2. * thickness + bottom_properties.width_outside + add_outside_cover_width,
                                       thickness, down_z_ref - thickness)

    #top_panel = make_top_panel(dimension_properties, top_properties, up_z_ref, False)
    if top_properties.top_type != TopBottomProperties.TOP_TYPE_NORMAL:
            raise ValueError("Top type not implemented")
    if top_properties.position == TopBottomProperties.POSITION_INSIDE:
        top_panel = make_z_panel(dimension_properties.length, dimension_properties.width, thickness,
                                    up_z_ref - thickness - top_properties.height_shift)
    else:
        top_panel = make_z_panel(dimension_properties.length + 2. * thickness + top_properties.length_outside + add_outside_cover_length,
                                    dimension_properties.width + 2. * thickness + top_properties.width_outside + add_outside_cover_width,
                                    thickness, up_z_ref)

    if face_panel is not None :
        face_panel.translate(FreeCAD.Vector(0, 0, shift_height))
    else :
        face_panel_1.translate(FreeCAD.Vector(0, 0, shift_height))
        face_panel_2.translate(FreeCAD.Vector(0, 0, shift_height))
    behind_panel.translate(FreeCAD.Vector(0, 0, shift_height))
    left_panel.translate(FreeCAD.Vector(0, 0, shift_height))
    right_panel.translate(FreeCAD.Vector(0, 0, shift_height))
    bottom_panel.translate(FreeCAD.Vector(0, 0, shift_height))
    top_panel.translate(FreeCAD.Vector(0, 0, shift_height))

    if face_panel is not None :
        part_list.append({'shape': face_panel, 'name': "face_panel"})
    else:
        part_list.append({'shape': face_panel_1, 'name': "face_panel_1"})
        part_list.append({'shape': face_panel_2, 'name': "face_panel_2"})
    part_list.append({'shape': behind_panel, 'name': "behind_panel"})
    part_list.append({'shape': left_panel, 'name': "left_panel"})
    part_list.append({'shape': right_panel, 'name': "right_panel"})
    part_list.append({'shape': bottom_panel, 'name': "bottom_panel"})
    part_list.append({'shape': top_panel, 'name': "top_panel"})


#XY plan
def make_z_panel(length, width, thickness, z_pos):
    half_length = length / 2.0
    half_width = width / 2.0
    p1 = FreeCAD.Vector(-half_length, -half_width, z_pos)
    p2 = FreeCAD.Vector(-half_length, half_width, z_pos)
    p3 = FreeCAD.Vector(half_length, half_width, z_pos)
    p4 = FreeCAD.Vector(half_length, -half_width, z_pos)

    wire = Part.makePolygon([p1,p2,p3,p4,p1])
    face = Part.Face(wire)
    part = face.extrude(FreeCAD.Vector(0, 0, thickness))
    return part


# XZ plan
def make_front_panels(length, height, thickness, spacing):
    half_length = length / 2.0
    down_height = -height / 2.0
    up_height = height / 2.0
    y = spacing / 2.0
    p1 = FreeCAD.Vector(-half_length, y, down_height)
    p2 = FreeCAD.Vector(-half_length, y, up_height)
    p3 = FreeCAD.Vector(half_length, y, up_height)
    p4 = FreeCAD.Vector(half_length, y, down_height)

    wire=Part.makePolygon([p1,p2,p3,p4,p1])
    face = Part.Face(wire)
    front_part = face.extrude(FreeCAD.Vector(0, thickness, 0))
    behind_part = front_part.copy()
    behind_part.translate(FreeCAD.Vector(0, -spacing - thickness, 0))

    return front_part, behind_part


def make_twice_half_front_panel(length, height, thickness, spacing):
    quarter_length = length / 4.0
    down_height = -height / 2.0
    up_height = height / 2.0
    y = spacing / 2.0
    p1 = FreeCAD.Vector(-quarter_length, y, down_height)
    p2 = FreeCAD.Vector(-quarter_length, y, up_height)
    p3 = FreeCAD.Vector(quarter_length, y, up_height)
    p4 = FreeCAD.Vector(quarter_length, y, down_height)

    wire = Part.makePolygon([p1,p2,p3,p4,p1])
    face = Part.Face(wire)
    front_part_1 = face.extrude(FreeCAD.Vector(0, thickness, 0))
    front_part_2 = front_part_1.copy()
    front_part_1.translate(FreeCAD.Vector(-quarter_length, 0, 0))
    front_part_2.translate(FreeCAD.Vector(quarter_length, 0, 0))

    return front_part_1, front_part_2

# YZ plan
def make_side_panels(width, height, thickness, spacing):
    half_width = width / 2.0
    down_height = -height / 2.0
    up_height = height / 2.0
    x = spacing / 2.0
    p1 = FreeCAD.Vector(x, -half_width, down_height)
    p2 = FreeCAD.Vector(x, -half_width, up_height)
    p3 = FreeCAD.Vector(x, half_width, up_height)
    p4 = FreeCAD.Vector(x, half_width, down_height)

    wire = Part.makePolygon([p1,p2,p3,p4,p1])
    face = Part.Face(wire)
    left_part = face.extrude(FreeCAD.Vector(thickness, 0, 0))
    right_part = left_part.copy()
    right_part.translate(FreeCAD.Vector(-spacing - thickness, 0, 0))

    return left_part, right_part
