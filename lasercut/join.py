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
import helper


def assemble_list_element(el_list):
    if len(el_list) == 0:
        return None

    part = el_list[0]
    for el in el_list[1:]:
        part = part.fuse(el)

    return part


class MaterialElement:
    def __init__(self, properties):
        self.properties = properties
        self.toAdd = []
        self.toRemove = []

    def reset_add_remove(self):
        self.toAdd = []
        self.toRemove = []

    def get_name(self):
        return self.properties.freecad_object.Name

    def get_new_name(self):
        return self.properties.new_name

    def get_shape(self):
        part = assemble_list_element(self.toAdd)
        new_shape = self.properties.freecad_object.Shape
        if part is not None:
            new_shape = new_shape.fuse(part)
        part = assemble_list_element(self.toRemove)
        if part is not None:
            new_shape = new_shape.cut(part)
        return new_shape


def get_slot_positions(tab_properties):
    slots_list = []
    interval_length = tab_properties.y_length / float(tab_properties.tabs_number)
    half_tab_number = int(float(tab_properties.tabs_number) / 2.0)
    if tab_properties.tabs_number % 2 == 1:
        slots_list.append(0.0 + tab_properties.tabs_shift)
        for i in range(half_tab_number):
            left = float(i+1) * interval_length * tab_properties.interval_ratio
            right = float(-i-1) * interval_length * tab_properties.interval_ratio
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

    if tab_properties.y_invert:
        invert_list = []
        for slot in slots_list:
            invert_list.append(-slot)
        slots_list = invert_list

    return slots_list


def make_dog_bone_on_xy(pos_x, pos_y, height, radius):
    cylinder = Part.makeCylinder(radius, height, FreeCAD.Vector(0, 0, -height / 2.0))
    cylinder.translate(FreeCAD.Vector(pos_x, pos_y, 0.))
    return cylinder


def make_dog_bone_on_xz(pos_y, pos_z, height, radius):
    cylinder = Part.makeCylinder(radius, height, FreeCAD.Vector(0, 0, -height / 2.0))
    cylinder.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 1, 0), 90)
    cylinder.translate(FreeCAD.Vector(0., pos_y, pos_z))
    return cylinder


def make_dog_bone_on_limits_on_yz(shape, length,
                                  y_min_z_min=True, y_max_z_min=True, y_min_z_max=True, y_max_z_max=True):
    bound_box = shape.BoundBox
    if y_min_z_min:
        shape = shape.fuse(make_dog_bone_on_xz(bound_box.YMin + 0.1, bound_box.ZMin + 0.1, length, 0.2))
    if y_max_z_min:
        shape = shape.fuse(make_dog_bone_on_xz(bound_box.YMax - 0.1, bound_box.ZMin + 0.1, length, 0.2))
    if y_min_z_max:
        shape = shape.fuse(make_dog_bone_on_xz(bound_box.YMin + 0.1, bound_box.ZMax - 0.1, length, 0.2))
    if y_max_z_max:
        shape = shape.fuse(make_dog_bone_on_xz(bound_box.YMax - 0.1, bound_box.ZMax - 0.1, length, 0.2))
    return shape


def make_dog_bone_on_limits_on_xy(shape, length):
    bound_box = shape.BoundBox
    shape = shape.fuse(make_dog_bone_on_xy(bound_box.XMin + 0.1, bound_box.YMin + 0.1, length, 0.2))
    shape = shape.fuse(make_dog_bone_on_xy(bound_box.XMax - 0.1, bound_box.YMin + 0.1, length, 0.2))
    shape = shape.fuse(make_dog_bone_on_xy(bound_box.XMin + 0.1, bound_box.YMax - 0.1, length, 0.2))
    shape = shape.fuse(make_dog_bone_on_xy(bound_box.XMax - 0.1, bound_box.YMax - 0.1, length, 0.2))
    return shape


def screw_way_on_plane(material_plane, screw_nut_spec, pos_y):
    # horizontal hole
    radius = (screw_nut_spec.screw_diameter * 1.2 - material_plane.laser_beam_diameter) / 2.0
    cylinder = Part.makeCylinder(radius, material_plane.thickness, FreeCAD.Vector(0, 0, -material_plane.thickness / 2.))
    cylinder.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 1, 0), 90)
    cylinder.translate(FreeCAD.Vector(0., pos_y, 0.))
    return cylinder


def screw_way_on_face(material_face, material_plane, screw_nut_spec, pos_y, dog_bone=False):
    # horizontal hole
    vert_corrected_length = screw_nut_spec.screw_length - material_plane.thickness + material_plane.thickness_tolerance
    corrected_width = screw_nut_spec.screw_diameter * 1.2 - material_face.laser_beam_diameter
    corrected_height = material_face.thickness  # + materialFace.tolerance
    screw_hole = Part.makeBox(vert_corrected_length, corrected_width, corrected_height,
                              FreeCAD.Vector(material_plane.thickness / 2.0,
                                             -corrected_width / 2.0, -corrected_height / 2.0))
    screw_hole.translate(FreeCAD.Vector(0, pos_y, 0))
    corrected_length = screw_nut_spec.nut_height - material_face.laser_beam_diameter + 0.1
    corrected_width = screw_nut_spec.nut_flat_flat - material_face.laser_beam_diameter + 0.1
    nut_hole = Part.makeBox(corrected_length, corrected_width, corrected_height,
                            FreeCAD.Vector(material_plane.thickness / 2.0,
                                           -corrected_width / 2.0, -corrected_height / 2.0))
    x_pos = vert_corrected_length - corrected_length - screw_nut_spec.nut_height
    nut_hole.translate(FreeCAD.Vector(x_pos, pos_y, 0))
    if dog_bone:
        nut_hole = make_dog_bone_on_limits_on_xy(nut_hole, corrected_height)
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
def tab_join_create_tab_on_face(material_face, material_plane, width, pos_y, left_kerf=True, right_kerf=True,
                                use_mat_tol=True):
    # X Rien pr l'instant, mais on peut prendre en compte l'epaiseur variante de la piece opposé => length
    # Y Ajout d'un Kerf => width
    # Z Rien => height
    corrected_length = material_plane.thickness
    # corrected_width = width + materialFace.laser_beam_diameter
    corrected_height = material_face.thickness

    corrected_width = width  # - materialPlane.laser_beam_diameter
    corrected_width_center = corrected_width / 2.0
    if left_kerf and right_kerf:
        corrected_width += material_face.laser_beam_diameter
        corrected_width_center = corrected_width / 2.0
    elif left_kerf:
        corrected_width += material_face.laser_beam_diameter / 2.0
        corrected_width_center = (corrected_width + material_face.laser_beam_diameter / 2.0) / 2.0
    elif right_kerf:
        corrected_width += material_face.laser_beam_diameter / 2.0
        corrected_width_center = (corrected_width - material_face.laser_beam_diameter / 2.0) / 2.0

    origin = FreeCAD.Vector(-corrected_length / 2.0, -corrected_width_center, -corrected_height / 2.0)
    tab = Part.makeBox(corrected_length, corrected_width, corrected_height, origin)
    tab.translate(FreeCAD.Vector(0, pos_y, 0))

    return tab


# def tab_join_create_hole_on_plane(material_face, material_plane, width, pos_y, left_kerf=True, right_kerf=True,
#                                   use_mat_tol=True, dog_bone=False):
#     # X Rien pour l'instant
#     # Y Enlever un kerf
#     # Z Ajout de la tolérance de l'éppaisseur et enlever le kerf
#     corrected_length = material_plane.thickness  # OK
#     corrected_height = material_face.thickness + material_face.thickness_tolerance - material_plane.laser_beam_diameter
#
#     corrected_width = width  # - materialPlane.laser_beam_diameter
#     corrected_width_center = corrected_width / 2.0
#     if left_kerf and right_kerf:
#         corrected_width -= material_plane.laser_beam_diameter
#         corrected_width_center = corrected_width / 2.0
#     elif left_kerf:
#         corrected_width -= material_plane.laser_beam_diameter / 2.0
#         corrected_width_center = (corrected_width - material_plane.laser_beam_diameter / 2.0) / 2.0
#     elif right_kerf:
#         corrected_width -= material_plane.laser_beam_diameter / 2.0
#         corrected_width_center = (corrected_width + material_plane.laser_beam_diameter / 2.0) / 2.0
#
#     origin = FreeCAD.Vector(-corrected_length / 2.0, - corrected_width_center, -corrected_height / 2.0)
#     hole = Part.makeBox(corrected_length, corrected_width, corrected_height, origin)
#     hole.translate(FreeCAD.Vector(0, pos_y, 0))
#
#     if dog_bone:
#         hole = make_dog_bone_on_limits_on_yz(hole, corrected_length)
#
#     return hole


def transform_part(tab_to_add, face, part_interactor_properties):
    x_origin = part_interactor_properties.thickness / 2.0
    return helper.transform(tab_to_add, face.freecad_face, x_origin, face.transform_matrix)


def check_intersect(tab_to_add, face, part_interactor_properties):
    tab_to_add_transformed = transform_part(tab_to_add, face, part_interactor_properties)
    part_shape_transformed = part_interactor_properties.freecad_object.Shape
    #print "volume %f" % part_shape_transformed.common(tab_to_add_transformed).Volume
    return part_shape_transformed.common(tab_to_add_transformed).Volume > 0.001, tab_to_add_transformed



def make_tab_join(tab, tab_part, other_parts):
    slots_pos = get_slot_positions(tab)
    for i, y in enumerate(slots_pos):
        for part_interactor in other_parts:
            tab_to_add = tab_join_create_tab_on_face(tab_part.properties, part_interactor.properties,
                                                     tab.tabs_width, y)
            intersect_test, tab_to_add_transformed = check_intersect(tab_to_add, tab,
                                                                     part_interactor.properties)

            if intersect_test:
                tab_part.toAdd.append(tab_to_add_transformed)
                hole = tab_join_create_hole_on_plane(tab, tab.tabs_width, y, tab_part.properties,
                                                       part_interactor.properties, True, True, True, tab.dog_bone)
                transformed_hole = transform_part(hole, tab, part_interactor.properties)
                part_interactor.toRemove.append(transformed_hole)
                break
    return


def make_continuous_tab_joins(tab, tab_part, other_parts):
    virtual_tab_length = float(tab.y_length / float(int(tab.tabs_number + 1)))
    y_pos = - tab.y_length / 2.0
    for tab_id in range(int(tab.tabs_number + 1)):
        y_pos_center = y_pos + virtual_tab_length / 2.0
        if tab.y_invert:
            y_pos_center = - y_pos_center
        left_kerf = False if tab_id == 0 else True
        right_kerf = False if tab_id == tab.tabs_number else True
        if tab_id % 2 == 0:
            for part_interactor in other_parts:
                tab_to_add = tab_join_create_tab_on_face(tab_part.properties, part_interactor.properties,
                                                         virtual_tab_length, y_pos_center, left_kerf, right_kerf)
                intersect_test, tab_to_add_transformed = check_intersect(tab_to_add, tab,
                                                                         part_interactor.properties)
                if intersect_test:
                    tab_part.toAdd.append(tab_to_add_transformed)
                    hole = tab_join_create_hole_on_plane(tab, virtual_tab_length, y_pos_center, tab_part.properties,
                                                         part_interactor.properties, left_kerf, right_kerf,
                                                         True, tab.dog_bone)
                    transformed_hole = transform_part(hole, tab, part_interactor.properties)
                    part_interactor.toRemove.append(transformed_hole)
                    break
        y_pos += virtual_tab_length
    return


def make_tslot_tab_join(tab, tab_part, other_parts):
    half_tab_distance = (tab.screw_diameter * tab.half_tab_ratio) + tab.tabs_width / 2.0
    screw_nut_spec = helper.get_screw_nut_spec(tab.screw_diameter, tab.screw_length)
    slots_pos = get_slot_positions(tab)
    for i, y in enumerate(slots_pos):
        for part_interactor in other_parts:
            left_tab_to_add = tab_join_create_tab_on_face(tab_part.properties, part_interactor.properties,
                                                          tab.tabs_width, y - half_tab_distance)
            right_tab_to_add = tab_join_create_tab_on_face(tab_part.properties, part_interactor.properties,
                                                           tab.tabs_width, y + half_tab_distance)

            right_intersect_test, right_tab_to_add_transformed = check_intersect(right_tab_to_add, tab,
                                                                                 part_interactor.properties)
            left_intersect_test, left_tab_to_add_transformed = check_intersect(left_tab_to_add, tab,
                                                                               part_interactor.properties)

            if right_intersect_test or left_intersect_test:
                tab_part.toAdd.append(left_tab_to_add_transformed)
                tab_part.toAdd.append(right_tab_to_add_transformed)

                left_hole = tab_join_create_hole_on_plane(tab, tab.tabs_width, y - half_tab_distance,
                                                          tab_part.properties, part_interactor.properties,
                                                          True, True, True, tab.dog_bone)
                right_hole = tab_join_create_hole_on_plane(tab, tab.tabs_width, y + half_tab_distance,
                                                          tab_part.properties, part_interactor.properties,
                                                          True, True, True, tab.dog_bone)

                part_interactor.toRemove.append(transform_part(left_hole, tab,
                                                               part_interactor.properties))
                part_interactor.toRemove.append(transform_part(right_hole, tab,
                                                               part_interactor.properties))

                screw_way_hole_face = screw_way_on_face(tab_part.properties, part_interactor.properties,
                                                        screw_nut_spec, y, tab.dog_bone)
                screw_way_hole_plane = screw_way_on_plane(part_interactor.properties, screw_nut_spec, y)

                tab_part.toRemove.append(transform_part(screw_way_hole_face, tab,
                                                        part_interactor.properties))
                part_interactor.toRemove.append(transform_part(screw_way_hole_plane, tab,
                                                               part_interactor.properties))

                break
    return


def make_tabs_joins(parts, tabs):
    parts_element = []
    for part in parts:
        mat_element = MaterialElement(part)
        parts_element.append(mat_element)

    for tab in tabs:
        tab_part = None
        other_parts = []
        for part in parts_element:
            if part.get_name() == tab.freecad_object.Name:
                tab_part = part
            else:
                other_parts.append(part)
        if tab.tab_type == TabProperties.TYPE_TAB:
            make_tab_join(tab, tab_part, other_parts)
        elif tab.tab_type == TabProperties.TYPE_T_SLOT:
            make_tslot_tab_join(tab, tab_part, other_parts)
        elif tab.tab_type == TabProperties.TYPE_CONTINUOUS:
            make_continuous_tab_joins(tab, tab_part, other_parts)
        else:
            raise ValueError("Unknown tab type")
    return parts_element

# ################################# test

#            X (Length)
#            |
#            |
#            |
#            |Z (Height)
#            ---------------------------> Y (Width)
# X est vers le haut
# Y est aligné sur la face
# Z est devant la camera
def check_limit_z(tab_face, width, pos_y, material_face, material_plane):
    box_x_size = material_plane.thickness / 2.0 # OK
    box_y_size = width / 2.0
    box_z_size = 0.1

    box_z_minus = Part.makeBox(box_x_size, box_y_size, box_z_size)
    box_z_minus.translate(FreeCAD.Vector(-box_x_size - 0.005, pos_y - box_y_size/2.0, material_face.thickness / 2.0))

    box_z_plus = Part.makeBox(box_x_size, box_y_size, box_z_size)
    box_z_plus.translate(FreeCAD.Vector(-box_x_size - 0.005, pos_y - box_y_size/2.0, -box_z_size - material_face.thickness / 2.0))

    z_plus_inside, toto1 = check_intersect(box_z_plus, tab_face, material_plane)
    z_minus_inside, toto2 = check_intersect(box_z_minus, tab_face, material_plane)

    # shapeobj = FreeCAD.ActiveDocument.addObject("Part::Feature","tstupdds_plus")
    # shapeobj.Shape = toto1
    # FreeCAD.ActiveDocument.recompute()
    #
    # shapeobj = FreeCAD.ActiveDocument.addObject("Part::Feature","tstupddsd_minus")
    # shapeobj.Shape = toto2
    # FreeCAD.ActiveDocument.recompute()
    #print("z plus %r, minus %r" % (z_plus_inside, z_minus_inside))

    return z_plus_inside, z_minus_inside
#
#
# def check_yz_limit(box_dimensions, position):
#
#     box_z_plus = Part.makeBox(box_dimensions[0], ...
#
#
#
# def test_y_limit(tab_face, width, pos_y, material_face, material_plane):
#     box_x_size = material_plane.thickness / 2.0
#     box_y_size = 0.1
#     box_z_size = material_face.thickness / 2.0
#
#     box_y_plus = Part.makeBox(box_x_size, box_y_size, box_z_size)
#     box_y_plus.translate(FreeCAD.Vector(box_x_size / 2.0 + 0.005, pos_y + width /2.0, -(box_z_size / 2.0 + 0.005)))
#     box_y_minus = Part.makeBox(box_x_size, box_y_size, box_z_size)
#     box_y_minus.translate(FreeCAD.Vector(box_x_size / 2.0 + 0.005, pos_y - width /2.0, -(box_z_size / 2.0 + 0.005)))
#     y_plus_inside, toto1 = check_intersect(box_y_plus, tab_face.freecad_face, material_face)
#     y_minus_inside, toto2 = check_intersect(box_y_minus, tab_face.freecad_face, material_face)
#     shapeobj = FreeCAD.ActiveDocument.addObject("Part::Feature","tstupddsd")
#     shapeobj.Shape = toto1
#     FreeCAD.ActiveDocument.recompute()
#
#     # si intersect est null, ça veut dire qu'on est dehors (normallement on arrive a la tranche, on est pas supposé
#     # dépassé la tranche) => ne pas ajouter le laser kerf de ce coté
#
#     print(" test plus %r, minus %r" % (y_plus_inside, y_minus_inside))
#     return y_plus_inside, y_minus_inside
#
# #            X (Length)
# #            |
# #            |
# #            |
# #            |Z (Height)
# #            ---------------------------> Y (Width)
# # X est vers le haut
# # Y est aligné sur la face
# # Z est devant la camera
# def tab_join_create_tab_on_face_2(tab_face, width, pos_y, material_face, material_plane):
#
#     y_plus_inside, y_minus_inside = test_y_limit(tab_face, width+material_face.laser_beam, pos_y, material_face, material_plane)
#
#     corrected_length = material_plane.thickness
#     corrected_height = material_face.thickness
#
#     corrected_width = width
#     corrected_width_center = corrected_width / 2.0
#     if y_plus_inside and y_minus_inside:
#         corrected_width += material_face.laser_beam_diameter
#         corrected_width_center = corrected_width / 2.0
#     elif y_plus_inside:
#         corrected_width += material_face.laser_beam_diameter / 2.0
#         corrected_width_center = (corrected_width + material_face.laser_beam_diameter / 2.0) / 2.0
#     elif y_minus_inside:
#         corrected_width += material_face.laser_beam_diameter / 2.0
#         corrected_width_center = (corrected_width - material_face.laser_beam_diameter / 2.0) / 2.0
#
#     origin = FreeCAD.Vector(-corrected_length / 2.0, -corrected_width_center, -corrected_height / 2.0)
#     tab = Part.makeBox(corrected_length, corrected_width, corrected_height, origin)
#     tab.translate(FreeCAD.Vector(0, pos_y, 0))
#
#     return tab


def tab_join_create_hole_on_plane(tab_face, width, pos_y, material_face, material_plane, left_kerf=True, right_kerf=True,
                                  use_mat_tol=True, dog_bone=False):

    z_plus_inside, z_minus_inside = check_limit_z(tab_face, width, pos_y, material_face, material_plane)
    #print("z_plus_inside %r, z_minus_inside %r" % (z_plus_inside, z_minus_inside))
    corrected_length = material_plane.thickness  # OK

    corrected_width = width  # - materialPlane.laser_beam_diameter
    corrected_width_center = corrected_width / 2.0
    if left_kerf and right_kerf:
        corrected_width -= material_plane.laser_beam_diameter
        corrected_width_center = corrected_width / 2.0
    elif left_kerf:
        corrected_width -= material_plane.laser_beam_diameter / 2.0
        corrected_width_center = (corrected_width - material_plane.laser_beam_diameter / 2.0) / 2.0
    elif right_kerf:
        corrected_width -= material_plane.laser_beam_diameter / 2.0
        corrected_width_center = (corrected_width + material_plane.laser_beam_diameter / 2.0) / 2.0

    corrected_height = material_face.thickness + material_face.thickness_tolerance #- material_plane.laser_beam_diameter
    corrected_height_center = corrected_height /2.0
    if z_plus_inside and z_minus_inside:
        corrected_height -= material_plane.laser_beam_diameter
        corrected_height_center = corrected_height / 2.0
    elif z_plus_inside:
        corrected_height -= material_plane.laser_beam_diameter / 2.0
        corrected_height_center = (corrected_height - material_plane.laser_beam_diameter / 2.0) / 2.0
    elif z_minus_inside:
        corrected_height -= material_plane.laser_beam_diameter / 2.0
        corrected_height_center = (corrected_height + material_plane.laser_beam_diameter / 2.0) / 2.0

    origin = FreeCAD.Vector(-corrected_length / 2.0, - corrected_width_center, -corrected_height_center)
    hole = Part.makeBox(corrected_length, corrected_width, corrected_height, origin)
    hole.translate(FreeCAD.Vector(0, pos_y, 0))

    if dog_bone:
        hole = make_dog_bone_on_limits_on_yz(hole, corrected_length, z_plus_inside, z_plus_inside, z_minus_inside, z_minus_inside)
    return hole


# def make_tab_join_2(tab, tab_part, other_parts):
#     slots_pos = get_slot_positions(tab)
#     for i, y in enumerate(slots_pos):
#         for part_interactor in other_parts:
#             tab_to_add = tab_join_create_tab_on_face_2(tab_part.properties, part_interactor.properties,
#                                                      tab.tabs_width, y)
#             intersect_test, tab_to_add_transformed = check_intersect(tab_to_add, tab.freecad_face,
#                                                                      part_interactor.properties)
#
#             if intersect_test:
#                 tab_part.toAdd.append(tab_to_add_transformed)
#
#                 # test pr pb quand le laser kerf est supérieur à la tolérance, car laisse une tranche de matière
#                 # si le tab est en bout de surface
#                 # hole_up, hole_down = check_limit_z(tab_part.properties, part_interactor.properties, tab.tabs_width, y)
#                 # intersect_test1, toto1 = check_intersect(hole_up, tab.freecad_face,
#                 #                                                      part_interactor.properties)
#                 # intersect_test2, toto2 = check_intersect(hole_down, tab.freecad_face,
#                 #                                                      part_interactor.properties)
#                 # #fin test
#                 # shapeobj = FreeCAD.ActiveDocument.addObject("Part::Feature","tstup")
#                 # shapeobj.Shape = toto1
#                 # FreeCAD.ActiveDocument.recompute()
#                 #
#                 # shapeobj2 = FreeCAD.ActiveDocument.addObject("Part::Feature","tstdown")
#                 # shapeobj2.Shape = toto2
#                 # FreeCAD.ActiveDocument.recompute()
#
#                 # print("test up %r, test down %r" % (intersect_test1, intersect_test2))
#                 #
#                 hole = tab_join_create_hole_on_plane(tab_part.properties, part_interactor.properties,
#                                                      tab.tabs_width, y, True, True, True, tab.dog_bone)
#                 transformed_hole = transform_part(hole, tab.freecad_face, part_interactor.properties)
#                 part_interactor.toRemove.append(transformed_hole)
#                 break
#     return
