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

import FreeCADGui


def get_freecad_objects_list():
    objs_sel = []
    for selection in FreeCADGui.Selection.getSelectionEx():
        objs_sel.append(selection.Object)
    return objs_sel


def get_freecad_faces_objects_list():
    face_obj_list = []
    for selection_obj in FreeCADGui.Selection.getSelectionEx():
        index = 0
        for face in selection_obj.SubObjects:
            face_obj_list.append({'freecad_object': selection_obj.Object, 'face': face,
                                  'name': selection_obj.SubElementNames[index]})
            index += 1
    return face_obj_list
