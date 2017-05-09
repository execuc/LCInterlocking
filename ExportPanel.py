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
import os
import math
import Draft
from lasercut.helper import biggest_area_faces

__dir__ = os.path.dirname(__file__)
iconPath = os.path.join(__dir__, 'icons')


def get_freecad_object():
    if len(FreeCADGui.Selection.getSelectionEx()) < 1:
            raise ValueError("No selection")

    obj_list = []
    for selection in FreeCADGui.Selection.getSelectionEx():
        obj_list.append(selection.Object)
    return obj_list


def transform_shape(part_feature, new_part_feature, freecad_document):
    new_part_feature.Shape = part_feature.Shape.removeSplitter()
    freecad_document.recompute()
    normal_face_prop = biggest_area_faces(part_feature.Shape)
    normal_ref = normal_face_prop[0]
    rotation_to_apply = FreeCAD.Rotation(normal_ref, FreeCAD.Vector(0, 0, 1))
    current_rotation = new_part_feature.Placement.Rotation
    new_rotation = rotation_to_apply.multiply(current_rotation)
    new_part_feature.Placement.Rotation = new_rotation
    freecad_document.recompute()

    return True


class ExportCommand:

    def __init__(self):
        return

    def GetResources(self):
        return {'Pixmap': os.path.join(iconPath, 'export.xpm'),  # the name of a svg file available in the resources
                'MenuText': "Export",
                'ToolTip': "Export"}

    def IsActive(self):
        return len(FreeCADGui.Selection.getSelection()) > 0

    def Activated(self):
        parts_list = get_freecad_object()
        new_doc = FreeCAD.newDocument("export_shape")
        self.export_list(parts_list, new_doc)
        FreeCADGui.getDocument(new_doc.Name).ActiveView.fitAll()
        return

    def export_list(self, parts_list, freecad_document):
        x_pos = 0.
        y_pos = 0.
        margin = 10.
        max_line_y = 0
        z_fix = 30
        new_parts_list = []
        per_line = int(math.sqrt(len(parts_list)))
        for i in range(len(parts_list)):
            part = parts_list[i]
            new_part = freecad_document.addObject("Part::Feature", "test")

            transform_shape(part, new_part, freecad_document)
            bound_box = new_part.Shape.BoundBox
            shift_vector = FreeCAD.Vector(-bound_box.XMin + x_pos, -bound_box.YMin + y_pos, z_fix - bound_box.ZMin)
            x_pos += bound_box.XLength + margin
            new_part.Placement.Base = new_part.Placement.Base.add(shift_vector)
            bound_box = new_part.Shape.BoundBox
            freecad_document.recompute()

            if (bound_box.YLength + y_pos) > max_line_y:
                max_line_y = bound_box.YLength + y_pos

            if (i+1) % per_line == 0:
                y_pos = max_line_y + margin
                x_pos = 0

            new_parts_list.append(new_part)

        for tmppart in new_parts_list:
            Draft.makeShape2DView(tmppart)

        freecad_document.recompute()

        return new_parts_list


Gui.addCommand('export_command', ExportCommand())
