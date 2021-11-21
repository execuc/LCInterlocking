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
from panel.tab import TabProperties
import lasercut.flextab as flextab
import lasercut.helper as helper


def get_slot_positions(tab_properties):
    slots_list = []
    interval_length = tab_properties.y_length / float(tab_properties.tabs_number)
    half_tab_number = int(float(tab_properties.tabs_number) / 2.0)
    if tab_properties.tabs_number % 2 == 1:
        slots_list.append(0.0 + tab_properties.tabs_shift)
        for i in range(half_tab_number):
            left = float(i+1) * interval_length
            right = float(-i-1) * interval_length
            if tab_properties.interval_ratio != 1.0:
                left *= tab_properties.interval_ratio
                right *= tab_properties.interval_ratio
            slots_list.append(left + tab_properties.tabs_shift)
            slots_list.append(right + tab_properties.tabs_shift)
    else:
        for i in range(half_tab_number):
            left = float(i) * interval_length + interval_length / 2.0
            right = float(-i) * interval_length - interval_length / 2.0
            if tab_properties.interval_ratio != 1.0:
                left *= tab_properties.interval_ratio
                right *= tab_properties.interval_ratio
            slots_list.append(left + tab_properties.tabs_shift)
            slots_list.append(right + tab_properties.tabs_shift)

    # if tab_properties.y_invert:
    #     invert_list = []
    #     for slot in slots_list:
    #         invert_list.append(-slot)
    #     slots_list = invert_list

    return slots_list


def screw_way_on_plane(material_plane, screw_nut_spec, pos_y):
    # horizontal hole
    radius = (screw_nut_spec.screw_diameter * 1.2 - material_plane.laser_beam_diameter) / 2.0
    cylinder = Part.makeCylinder(radius, material_plane.thickness, FreeCAD.Vector(0, 0, -material_plane.thickness / 2.))
    cylinder.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 1, 0), 90)
    cylinder.translate(FreeCAD.Vector(material_plane.thickness / 2.0, pos_y, 0.))
    return cylinder


def screw_way_on_face(material_face, material_plane, screw_nut_spec, pos_y, dog_bone=False):
    # horizontal hole
    vert_corrected_length = screw_nut_spec.screw_length - material_plane.thickness \
                            + material_plane.thickness_tolerance + screw_nut_spec.screw_length_tol
    corrected_width = screw_nut_spec.screw_diameter * 1.2 - material_face.laser_beam_diameter
    corrected_height = material_face.thickness  # + materialFace.tolerance
    screw_hole = Part.makeBox(vert_corrected_length, corrected_width, corrected_height,
                              FreeCAD.Vector(0.,
                                             -corrected_width / 2.0, -corrected_height / 2.0))
    if dog_bone:
        screw_hole = helper.make_dog_bone_on_limits_on_xy(screw_hole, corrected_height, True)
    x_pos = -vert_corrected_length
    screw_hole.translate(FreeCAD.Vector(x_pos, pos_y, 0))
    # Nut hole
    corrected_length = screw_nut_spec.nut_height - material_face.laser_beam_diameter + 0.1
    corrected_width = screw_nut_spec.nut_flat_flat - material_face.laser_beam_diameter + 0.1
    nut_hole = Part.makeBox(corrected_length, corrected_width, corrected_height,
                            FreeCAD.Vector(0,
                                           -corrected_width / 2.0, -corrected_height / 2.0))
    x_pos = -vert_corrected_length + screw_nut_spec.nut_height + screw_nut_spec.screw_length_tol
    nut_hole.translate(FreeCAD.Vector(x_pos, pos_y, 0))
    if dog_bone:
        nut_hole = helper.make_dog_bone_on_limits_on_xy(nut_hole, corrected_height)
    hole = screw_hole.fuse(nut_hole)
    return hole


#            X (Length)
#            |
#            |
#            |
#            |Z (Height)
#            ---------------------------> Y (Width)
# X est vers le haut
# Y est aligné sur la face
# Z est devant la camera
def tab_join_create_tab_on_face(material_face, material_plane, width, pos_y, tab_face, dog_bone=False):

    y_plus_inside, y_minus_inside = helper.check_limit_y_on_for_tab(tab_face, material_face.thickness, pos_y, width,
                                                                    material_plane.thickness, material_face)
    # X Rien pr l'instant, mais on peut prendre en compte l'epaiseur variante de la piece opposé => length
    # Y Ajout d'un Kerf => width
    # Z Rien => height
    corrected_length = material_plane.thickness
    # corrected_width = width + materialFace.laser_beam_diameter
    corrected_height = material_face.thickness

    corrected_width = width  # - materialPlane.laser_beam_diameter
    corrected_width_center = corrected_width / 2.0
    if y_minus_inside and y_plus_inside:
        corrected_width += material_face.laser_beam_diameter
        corrected_width_center = corrected_width / 2.0
    elif y_minus_inside:
        corrected_width += material_face.laser_beam_diameter / 2.0
        corrected_width_center = (corrected_width + material_face.laser_beam_diameter / 2.0) / 2.0
    elif y_plus_inside:
        corrected_width += material_face.laser_beam_diameter / 2.0
        corrected_width_center = (corrected_width - material_face.laser_beam_diameter / 2.0) / 2.0

    #origin = FreeCAD.Vector(-corrected_length / 2.0, -corrected_width_center, -corrected_height / 2.0)
    origin = FreeCAD.Vector(0., -corrected_width_center, -corrected_height / 2.0)
    tab = Part.makeBox(corrected_length, corrected_width, corrected_height, origin)
    tab.translate(FreeCAD.Vector(0, pos_y, 0))

    hole = None
    left_hole = None
    right_hole = None

    if dog_bone:
        radius = min(corrected_width, corrected_length) * 2 / 30.
        if y_minus_inside:
            left_hole = Part.makeCylinder(radius, corrected_height,
                                          FreeCAD.Vector(0, -corrected_width_center + pos_y, -corrected_height / 2.0),
                                          FreeCAD.Vector(0, 0, 1.))
        if y_plus_inside:
            right_hole = Part.makeCylinder(radius, corrected_height,
                                           FreeCAD.Vector(0, -corrected_width_center + corrected_width + pos_y,
                                           -corrected_height / 2.0),
                                           FreeCAD.Vector(0, 0, 1.))
        hole = left_hole
        if hole and right_hole:
            hole = hole.fuse(right_hole)
        elif right_hole:
            hole = right_hole

    return tab, hole


def make_tab_join(tab, tab_part, other_parts):
    slots_pos = get_slot_positions(tab)
    for i, y in enumerate(slots_pos):
        for part_interactor in other_parts:
            tab_to_add, tab_dog_bone = tab_join_create_tab_on_face(tab_part.properties, part_interactor.properties,
                                                                   tab.tabs_width, y, tab, tab.tab_dog_bone)
            intersect_test, tab_to_add_transformed = helper.check_intersect(tab_to_add, tab,
                                                                            part_interactor.properties)

            if intersect_test:
                tab_part.toAdd.append(tab_to_add_transformed)
                if tab_dog_bone:
                    tab_part.toRemove.append(helper.transform_part(tab_dog_bone, tab))
                hole = helper.tab_join_create_hole_on_plane(tab, tab.tabs_width, y, tab_part.properties,
                                                            part_interactor.properties, tab.dog_bone)
                part_interactor.toRemove.append(helper.transform_part(hole, tab))
                break
    return


def make_continuous_tab_joins(tab, tab_part, other_parts):
    tabs_number = int(tab.tabs_number - 1)
    virtual_tab_length = float(tab.y_length / float(int(tabs_number + 1)))
    y_pos = - tab.y_length / 2.0
    for tab_id in range(int(tabs_number + 1)):
        y_pos_center = y_pos + virtual_tab_length / 2.0
        # if tab.y_invert:
        #     y_pos_center = - y_pos_center
        left_kerf = False if tab_id == 0 else True
        right_kerf = False if tab_id == tabs_number else True
        if tab_id % 2 == 0:
            for part_interactor in other_parts:
                tab_to_add, tab_dog_bone = tab_join_create_tab_on_face(tab_part.properties, part_interactor.properties,
                                                                       virtual_tab_length, y_pos_center, tab,
                                                                       tab.tab_dog_bone)
                intersect_test, tab_to_add_transformed = helper.check_intersect(tab_to_add, tab,
                                                                                part_interactor.properties)
                if intersect_test:
                    tab_part.toAdd.append(tab_to_add_transformed)
                    if tab_dog_bone:
                        tab_part.toRemove.append(helper.transform_part(tab_dog_bone, tab))
                    hole = helper.tab_join_create_hole_on_plane(tab, virtual_tab_length, y_pos_center,
                                                                tab_part.properties, part_interactor.properties,
                                                                tab.dog_bone)
                    part_interactor.toRemove.append(helper.transform_part(hole, tab))
                    break
        y_pos += virtual_tab_length
    return


def make_tslot_tab_join(tab, tab_part, other_parts):
    half_tab_distance = (tab.screw_diameter * tab.half_tab_ratio) + tab.tabs_width / 2.0
    screw_nut_spec = helper.get_screw_nut_spec(tab.screw_diameter, tab.screw_length)
    screw_nut_spec.screw_length_tol = tab.screw_length_tol
    slots_pos = get_slot_positions(tab)
    for i, y in enumerate(slots_pos):
        for part_interactor in other_parts:
            left_tab_to_add, left_tab_dog_bone = tab_join_create_tab_on_face(tab_part.properties,
                                                                             part_interactor.properties,
                                                                             tab.tabs_width, y - half_tab_distance,
                                                                             tab, tab.tab_dog_bone)
            right_tab_to_add, right_tab_dog_bone = tab_join_create_tab_on_face(tab_part.properties,
                                                                               part_interactor.properties,
                                                                               tab.tabs_width, y + half_tab_distance,
                                                                               tab, tab.tab_dog_bone)

            right_intersect_test, right_tab_to_add_transformed = helper.check_intersect(right_tab_to_add, tab,
                                                                                 part_interactor.properties)
            left_intersect_test, left_tab_to_add_transformed = helper.check_intersect(left_tab_to_add, tab,
                                                                               part_interactor.properties)

            if right_intersect_test or left_intersect_test:
                tab_part.toAdd.append(left_tab_to_add_transformed)
                tab_part.toAdd.append(right_tab_to_add_transformed)
                if left_tab_dog_bone:
                    tab_part.toRemove.append(helper.transform_part(left_tab_dog_bone, tab))
                if right_tab_dog_bone:
                    tab_part.toRemove.append(helper.transform_part(right_tab_dog_bone, tab))

                left_hole = helper.tab_join_create_hole_on_plane(tab, tab.tabs_width, y - half_tab_distance,
                                                                 tab_part.properties, part_interactor.properties,
                                                                 tab.dog_bone)
                right_hole = helper.tab_join_create_hole_on_plane(tab, tab.tabs_width, y + half_tab_distance,
                                                                  tab_part.properties, part_interactor.properties,
                                                                  tab.dog_bone)

                part_interactor.toRemove.append(helper.transform_part(left_hole, tab))
                part_interactor.toRemove.append(helper.transform_part(right_hole, tab))

                screw_way_hole_face = screw_way_on_face(tab_part.properties, part_interactor.properties,
                                                        screw_nut_spec, y, tab.dog_bone)
                screw_way_hole_plane = screw_way_on_plane(part_interactor.properties, screw_nut_spec, y)

                tab_part.toRemove.append(helper.transform_part(screw_way_hole_face, tab))
                part_interactor.toRemove.append(helper.transform_part(screw_way_hole_plane, tab))

                break
    return


def make_tabs_joins(parts, tabs):
    parts_element = []
    for part in parts:
        mat_element = helper.MaterialElement(part)
        parts_element.append(mat_element)

    removeParts = {}
    #test to improve speed
    for tab in tabs:
        keyid = str(tab.group_id)
        if keyid not in removeParts:
            removeParts[keyid] = []
        removeParts[keyid].append(tab.freecad_object.Name)

    for tab in tabs:
        tab_part = None
        other_parts = []
        keyid = str(tab.group_id)
        for part in parts_element:
            if part.get_name() == tab.freecad_object.Name:
                tab_part = part
#            else:
            elif part.get_name() not in removeParts[keyid]:
                other_parts.append(part)
        if tab.tab_type == TabProperties.TYPE_TAB:
            make_tab_join(tab, tab_part, other_parts)
        elif tab.tab_type == TabProperties.TYPE_T_SLOT:
            make_tslot_tab_join(tab, tab_part, other_parts)
        elif tab.tab_type == TabProperties.TYPE_CONTINUOUS:
            make_continuous_tab_joins(tab, tab_part, other_parts)
        elif tab.tab_type == TabProperties.TYPE_FLEX:
            flextab.make_flex_tab_join(tab, tab_part, other_parts)
        else:
            raise ValueError("Unknown tab type")
    return parts_element