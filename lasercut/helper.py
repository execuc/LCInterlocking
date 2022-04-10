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
from operator import itemgetter, attrgetter


# http://stackoverflow.com/questions/2535917/copy-kwargs-to-self
class ObjectProperties(object):
    def __init__(self, **kwargs):
        self.obj_class = str(type(self).__name__)
        for k, v in kwargs.items():
            if not hasattr(self, "_allowed") or str(k) in self._allowed:
                setattr(self, k, v)
            #else:
            #    FreeCAD.Console.PrintWarning(str(k) + " is not allowed for " + str(type(self)))

class Segment:
    def __init__(self, first=FreeCAD.Vector(0, 0, 0), second=FreeCAD.Vector(0, 0, 0)):
        self.A = first
        self.B = second

    def a(self):
        return self.A

    def b(self):
        return self.B * 1

    def clone_a(self):
        return self.A * 1

    def clone_b(self):
        return self.B * 1

    def vector(self):
        return self.B.sub(self.A)

    def length(self):
        return self.vector().Length

    def mid_point(self):
        mid_point_b = self.A.add(self.B)
        mid_point_b.scale(0.5, 0.5, 0.5)
        return mid_point_b

    def get_angle(self, segment):
        return self.vector().getAngle(segment.vector())

    def add(self, vector):
        return Segment(self.A.add(vector), self.B.add(vector))

    def rotate_z(self, angle):
        return Segment(rotate_vector_z(self.A, angle), rotate_vector_z(self.B, angle))

    def __repr__(self):
        return "Segment A: " + str(self.A) + ", B: " + str(self.B)


def rotate_vector_z(vector, angle):
        point = FreeCAD.Vector(vector.x, vector.y, vector.z)
        point.x = vector.x * math.cos(angle) - vector.y * math.sin(angle)
        point.y = vector.x * math.sin(angle) + vector.y * math.cos(angle)
        return point

# http://www.fairburyfastener.com/xdims_metric_nuts.htm
def get_screw_nut_spec(metric_diameter, metric_length):
    if metric_diameter == 1.6:
        return ObjectProperties(screw_diameter=metric_diameter, screw_length=metric_length,
                                screw_length_tol=0.1, nut_flat_flat=3.2, nut_height=1.3)
    elif metric_diameter == 2:
        return ObjectProperties(screw_diameter=metric_diameter, screw_length=metric_length,
                                screw_length_tol=0.1, nut_flat_flat=4., nut_height=1.6)
    elif metric_diameter == 2.5:
        return ObjectProperties(screw_diameter=metric_diameter, screw_length=metric_length,
                                screw_length_tol=0.1, nut_flat_flat=5., nut_height=2.)
    elif metric_diameter == 3:
        return ObjectProperties(screw_diameter=metric_diameter, screw_length=metric_length,
                                screw_length_tol=0.1,  nut_flat_flat=5.5, nut_height=2.4)
    elif metric_diameter == 4:
        return ObjectProperties(screw_diameter=metric_diameter, screw_length=metric_length,
                                screw_length_tol=0.1,  nut_flat_flat=7., nut_height=3.2)
    elif metric_diameter == 5:
        return ObjectProperties(screw_diameter=metric_diameter, screw_length=metric_length,
                                screw_length_tol=0.1, nut_flat_flat=8., nut_height=4.7)
    elif metric_diameter == 6:
        return ObjectProperties(screw_diameter=metric_diameter, screw_length=metric_length,
                                screw_length_tol=0.1, nut_flat_flat=10., nut_height=5.2)
    elif metric_diameter == 8:
        return ObjectProperties(screw_diameter=metric_diameter, screw_length=metric_length,
                                screw_length_tol=0.1, nut_flat_flat=13., nut_height=6.8)
    elif metric_diameter == 10:
        return ObjectProperties(screw_diameter=metric_diameter, screw_length=metric_length,
                                screw_length_tol=0.1, nut_flat_flat=16., nut_height=8.4)
    raise ValueError("Unknown screw diameter")


def transform_part(tab_to_add, face):
    y_invert = False
    if hasattr(face, 'y_invert'):
        y_invert = face.y_invert
    return transform(tab_to_add, face.freecad_face, face.transform_matrix, y_invert)


def check_intersect(tab_to_add, face, part_interactor_properties):
    tab_to_add_transformed = transform_part(tab_to_add, face)
    part_shape_transformed = part_interactor_properties.freecad_object.Shape
    #print "volume %f" % part_shape_transformed.common(tab_to_add_transformed).Volume
    return part_shape_transformed.common(tab_to_add_transformed).Volume > 0.001, tab_to_add_transformed


def transform(part, referentiel_face, transform_matrix=None, y_invert = False):
    normal_face = referentiel_face.normalAt(0, 0)
    # original center is (0,0,0)
    transformed_center = referentiel_face.CenterOfMass #+ normal_face.normalize() * x_origin
    if transform_matrix is None:
        transform_matrix = get_matrix_transform(referentiel_face)
    part.Placement = FreeCAD.Placement(transform_matrix).multiply(part.Placement)
    part.translate(transformed_center)
    if y_invert:
        part.rotate(transformed_center, normal_face, 180.)
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

def normaliseEdge(edge):
    sizeX = edge.BoundBox.XMax - edge.BoundBox.XMin
    sizeY = edge.BoundBox.YMax - edge.BoundBox.YMin
    sizeZ = edge.BoundBox.ZMax - edge.BoundBox.ZMin
    
    return FreeCAD.Vector(sizeX / edge.Length, sizeY / edge.Length, sizeZ / edge.Length )

def get_local_axis(face):
    list_edges = Part.__sortEdges__(face.Edges)
    
    coalescedEdges = []
    previousEdge = None
    previousEdgeGradient = None
    for edge in list_edges:
        edgeGradient = normaliseEdge(edge)

        if previousEdge is not None:
            # If this edge is the same direction as the previous edge, then we can merge the two edges together.
            if edgeGradient == previousEdgeGradient:
                ls = Part.LineSegment( coalescedEdges[-1].Vertexes[0].Point, FreeCAD.Vector(edge.Vertexes[1].X, edge.Vertexes[1].Y, edge.Vertexes[1].Z) )
                coalescedEdges[-1] = Part.Edge(ls)
            else:
                coalescedEdges.append(edge)
        else:
            coalescedEdges.append(edge)

        previousEdgeGradient = edgeGradient
        previousEdge = edge

    # And check in case the last edge is an extension of the first.
    lastGradient = normaliseEdge(coalescedEdges[-1])
    firstGradient = normaliseEdge(coalescedEdges[0])

    if lastGradient == firstGradient:
        ls = Part.LineSegment( coalescedEdges[-1].Vertexes[0].Point, FreeCAD.Vector(coalescedEdges[0].Vertexes[1].X, coalescedEdges[0].Vertexes[1].Y, coalescedEdges[0].Vertexes[1].Z) )
        coalescedEdges[-1] = Part.Edge(ls)
        
        coalescedEdges.remove(coalescedEdges[0])

    list_edges = coalescedEdges

    list_points = sort_quad_vertex(list_edges, False)
    if list_points is None:
        list_points = sort_quad_vertex(list_edges, True)
    if list_points is None:
        raise ValueError("Error sorting vertex")

    normal_face = face.normalAt(0, 0)
    y_local = None
    z_local = None
    #x_local = normal_face.negative()
    x_local = normal_face.normalize()
    z_local_not_normalized = None
    y_local_not_normalized = None
    for x in range(0, len(list_edges)):
        vector1 = list_points[(x + 1) % len(list_edges)] - list_points[x]
        vector2 = list_points[(x - 1) % len(list_edges)] - list_points[x]
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
            #FreeCAD.Console.PrintError("\nFound\n")
            #FreeCAD.Console.PrintError(x_local)
            #FreeCAD.Console.PrintError(y_local)
            #FreeCAD.Console.PrintError(z_local)
            #FreeCAD.Console.PrintError("\n\n")
            return x_local, y_local_not_normalized, z_local_not_normalized

    return None, None, None

def get_local_axis_normalized(face):
    x_local, y_local_not_normalized, z_local_not_normalized = get_local_axis(face)
    y_local_not_normalized.normalize()
    z_local_not_normalized.normalize()
    return x_local, y_local_not_normalized, z_local_not_normalized


def compare_freecad_vector(vector1, vector2, epsilon=10e-6):
    vector = vector1.sub(vector2)
    if math.fabs(vector.x) < epsilon and math.fabs(vector.y) < epsilon and math.fabs(vector.z) < epsilon:
        return True
    return False


def compare_value(value1, value2, epsilon=10e-6):
    value = value1 - value2
    if math.fabs(value) < epsilon:
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

        if compare_freecad_vector(vertex1, list_points[-1]):
            list_points.append(vertex2)
        elif compare_freecad_vector(vertex2, list_points[-1]):
            list_points.append(vertex1)
        else:
            return None

    return list_points


def biggest_area_faces(freecad_shape):
    sorted_list = sort_area_shape_faces(freecad_shape)
    biggest_area_face = sorted_list[-1]
#       contains : 0:normal, 1:area mm2, 2; list of faces
    return biggest_area_face


def smallest_area_faces(freecad_shape):
    sorted_list = sort_area_shape_faces(freecad_shape)
    smallest_area_face = sorted_list[0]
#       contains : 0:normal, 1:area mm2, 2; list of faces
    return smallest_area_face


#   Returns face grouping by normal,sorted by the amount of surface (descending)
def sort_area_shape_faces(shape):
    return sort_area_face_common(shape.Faces, compare_freecad_vector_direction)


def sort_area_shape_list(faces_list):
    return sort_area_face_common(faces_list, compare_freecad_vector)


def sort_area_face_common(faces, test_function=compare_freecad_vector_direction):
    normal_area_list = []
    for face in faces:
        try:
            # print face
            normal = face.normalAt(0, 0)
            # print normal
            found = False
            for i in range(len(normal_area_list)):
                normal_test = normal_area_list[i][0]
                if test_function(normal, normal_test):
                    found = True
                    normal_area_list[i][1] += face.Area
                    normal_area_list[i][2].append(face)
                    tmp = sorted(normal_area_list[i][2], key=attrgetter('Area'),  reverse=True)
                    normal_area_list[i][2] = tmp
                    break
            if not found:
                normal_area_list.append([normal, face.Area, [face]])
        except Exception as ex:
            FreeCAD.Console.PrintError("Something wrong with face ", face, " : ", ex)
    # print normal_area_list
    sorted_list = sorted(normal_area_list, key=itemgetter(1))
    return sorted_list

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

    box_z_plus = Part.makeBox(box_x_size, box_y_size, box_z_size)
    box_z_plus.translate(FreeCAD.Vector(0.005, pos_y - box_y_size/2.0, material_face.thickness / 2.0))

    box_z_minus = Part.makeBox(box_x_size, box_y_size, box_z_size)
    box_z_minus.translate(FreeCAD.Vector(0.005, pos_y - box_y_size/2.0, -box_z_size - material_face.thickness / 2.0))

    z_plus_inside, toto1 = check_intersect(box_z_plus, tab_face, material_plane)
    z_minus_inside, toto2 = check_intersect(box_z_minus, tab_face, material_plane)

    #shapeobj = FreeCAD.ActiveDocument.addObject("Part::Feature","tstupdds_plus")
    #shapeobj.Shape = toto1
    #FreeCAD.ActiveDocument.recompute()

    #shapeobj = FreeCAD.ActiveDocument.addObject("Part::Feature","tstupddsd_minus")
    #shapeobj.Shape = toto2
    #FreeCAD.ActiveDocument.recompute()
    #print("z plus %r, minus %r" % (z_plus_inside, z_minus_inside))

    return z_plus_inside, z_minus_inside


def check_limit_y(tab_face, height, pos_y, width, material_plane):
    box_x_size = material_plane.thickness / 2.0 # OK
    box_y_size = 0.1
    box_z_size = height / 2.0

    box_y_minus = Part.makeBox(box_x_size, box_y_size, box_z_size)
    box_y_minus.translate(FreeCAD.Vector(0.005, pos_y - width/2.0 - box_y_size, -box_z_size / 2.0))

    box_y_plus = Part.makeBox(box_x_size, box_y_size, box_z_size)
    box_y_plus.translate(FreeCAD.Vector(0.005, pos_y + width/2.0, -box_z_size / 2.0))

    y_plus_inside, toto1 = check_intersect(box_y_plus, tab_face, material_plane)
    y_minus_inside, toto2 = check_intersect(box_y_minus, tab_face, material_plane)

    #shapeobj = FreeCAD.ActiveDocument.addObject("Part::Feature","y_plus_inside")
    #shapeobj.Shape = toto1
    #FreeCAD.ActiveDocument.recompute()

    #shapeobj = FreeCAD.ActiveDocument.addObject("Part::Feature","y_minus_inside")
    #shapeobj.Shape = toto2
    #FreeCAD.ActiveDocument.recompute()
    #print("y plus %r, minus %r" % (y_plus_inside, y_minus_inside))

    return y_plus_inside, y_minus_inside


def check_limit_y_on_for_tab(tab_face, height, pos_y, width, thickness, material_face):
    box_x_size = thickness / 2.0 # OK
    box_y_size = 0.1
    box_z_size = height / 2.0

    box_y_minus = Part.makeBox(box_x_size, box_y_size, box_z_size)
    box_y_minus.translate(FreeCAD.Vector(-0.005 - box_x_size, pos_y - width/2.0 - box_y_size, -box_z_size / 2.0))

    box_y_plus = Part.makeBox(box_x_size, box_y_size, box_z_size)
    box_y_plus.translate(FreeCAD.Vector(-0.005 - box_x_size, pos_y + width/2.0, -box_z_size / 2.0))

    y_plus_inside, toto1 = check_intersect(box_y_plus, tab_face, material_face)
    y_minus_inside, toto2 = check_intersect(box_y_minus, tab_face, material_face)

    #shapeobj = FreeCAD.ActiveDocument.addObject("Part::Feature","y_plus_inside")
    #shapeobj.Shape = toto1
    #FreeCAD.ActiveDocument.recompute()

    #shapeobj = FreeCAD.ActiveDocument.addObject("Part::Feature","y_minus_inside")
    #shapeobj.Shape = toto2
    #FreeCAD.ActiveDocument.recompute()
    #print("y plus %r, minus %r" % (y_plus_inside, y_minus_inside))

    return y_plus_inside, y_minus_inside


def tab_join_create_hole_on_plane(tab_face, width, pos_y, material_face, material_plane, dog_bone=False):

    z_plus_inside, z_minus_inside = check_limit_z(tab_face, width, pos_y, material_face, material_plane)
    y_plus_inside, y_minus_inside = check_limit_y(tab_face, material_face.thickness, pos_y, width, material_plane)
    #print("z_plus_inside %r, z_minus_inside %r" % (z_plus_inside, z_minus_inside))
    corrected_length = material_plane.thickness  # OK

    corrected_width = width + material_plane.hole_width_tolerance # - materialPlane.laser_beam_diameter
    corrected_width_center = corrected_width / 2.0
    width_to_remove = material_plane.laser_beam_diameter #+ material_plane.hole_width_tolerance
    if y_minus_inside and y_plus_inside:
        corrected_width -= width_to_remove
        corrected_width_center = corrected_width / 2.0
    elif y_minus_inside:
        corrected_width -= width_to_remove / 2.0
        corrected_width_center = (corrected_width - width_to_remove / 2.0) / 2.0
    elif y_plus_inside:
        corrected_width -= width_to_remove / 2.0
        corrected_width_center = (corrected_width + width_to_remove / 2.0) / 2.0

    corrected_height = material_face.thickness + material_face.thickness_tolerance #- material_plane.laser_beam_diameter
    corrected_height_center = corrected_height / 2.0
    if z_plus_inside and z_minus_inside:
        corrected_height -= material_plane.laser_beam_diameter
        corrected_height_center = corrected_height / 2.0
    elif z_minus_inside:
        corrected_height -= material_plane.laser_beam_diameter / 2.0
        corrected_height_center = (corrected_height - material_plane.laser_beam_diameter / 2.0) / 2.0
    elif z_plus_inside:
        corrected_height -= material_plane.laser_beam_diameter / 2.0
        corrected_height_center = (corrected_height + material_plane.laser_beam_diameter / 2.0) / 2.0

    origin = FreeCAD.Vector(0., - corrected_width_center, -corrected_height_center)
    hole = Part.makeBox(corrected_length, corrected_width, corrected_height, origin)
    hole.translate(FreeCAD.Vector(0, pos_y, 0))

    if dog_bone:
        hole = make_dog_bone_on_limits_on_yz(hole, corrected_length,
                                             z_minus_inside and y_minus_inside,
                                             z_minus_inside and y_plus_inside,
                                             z_plus_inside and y_minus_inside,
                                             z_plus_inside and y_plus_inside)
    return hole


def make_dog_bone_on_limits_on_yz(shape, length,
                                  y_min_z_min=True, y_max_z_min=True, y_min_z_max=True, y_max_z_max=True):
    bound_box = shape.BoundBox
    radius = min(bound_box.YMax - bound_box.YMin, bound_box.ZMax - bound_box.ZMin) * 2 / 30.
    shift = radius / 2.0
    if y_min_z_min:
        shape = shape.fuse(make_dog_bone_on_yz(bound_box.YMin + shift, bound_box.ZMin + shift, length, radius))
    if y_max_z_min:
        shape = shape.fuse(make_dog_bone_on_yz(bound_box.YMax - shift, bound_box.ZMin + shift, length, radius))
    if y_min_z_max:
        shape = shape.fuse(make_dog_bone_on_yz(bound_box.YMin + shift, bound_box.ZMax - shift, length, radius))
    if y_max_z_max:
        shape = shape.fuse(make_dog_bone_on_yz(bound_box.YMax - shift, bound_box.ZMax - shift, length, radius))
    return shape


def make_dog_bone_on_xy(pos_x, pos_y, height, radius):
    cylinder = Part.makeCylinder(radius, height, FreeCAD.Vector(pos_x, pos_y, -height / 2.0), FreeCAD.Vector(0, 0, 1))
    return cylinder


def make_dog_bone_on_yz(pos_y, pos_z, height, radius):
    cylinder = Part.makeCylinder(radius, height, FreeCAD.Vector(0, pos_y, pos_z), FreeCAD.Vector(1., 0, 0))
    return cylinder


def make_dog_bone_on_limits_on_xy(shape, length, x_min_only=False):
    bound_box = shape.BoundBox
    radius = min(bound_box.XMax - bound_box.XMin, bound_box.YMax - bound_box.YMin) * 2 / 30.
    shift = radius / 2.0
    shape = shape.fuse(make_dog_bone_on_xy(bound_box.XMin + shift, bound_box.YMin + shift, length, radius))
    if x_min_only is False:
        shape = shape.fuse(make_dog_bone_on_xy(bound_box.XMax - shift, bound_box.YMin + shift, length, radius))
    shape = shape.fuse(make_dog_bone_on_xy(bound_box.XMin + shift, bound_box.YMax - shift, length, radius))
    if x_min_only is False:
        shape = shape.fuse(make_dog_bone_on_xy(bound_box.XMax - shift, bound_box.YMax - shift, length, radius))
    return shape


def assemble_list_element(el_list):
    if len(el_list) == 0:
        return None

    part = el_list[0]
    for el in el_list[1:]:
        part = part.fuse(el)

    return part


#Use this function only for preview
# See Warning at https://www.freecadweb.org/wiki/Part_MakeCompound :
# "A compound containing pieces that intersect or touch is invalid
# for Boolean operations. Because of performance issues, checking
# if the pieces intersect is not done. Automatic geometry check
# (available for Boolean operations) is disabled for part compound as well."
def assemble_list_element_fast(el_list):
    if len(el_list) == 0:
        return None
    return Part.makeCompound(el_list)


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

    def get_shape(self, fast_assemble=False):
        if not fast_assemble:
            part = assemble_list_element(self.toAdd)
        else:
            part = assemble_list_element_fast(self.toAdd)
        new_shape = self.properties.freecad_object.Shape
        if part is not None:
            new_shape = new_shape.fuse(part)
        part = assemble_list_element(self.toRemove)
        if part is not None:
            new_shape = new_shape.cut(part)
        return new_shape
