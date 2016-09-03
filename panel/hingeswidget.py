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


from lasercut.hingesproperties import GlobalLivingMaterialProperties
from lasercut.hingesproperties import HingesProperties
from toolwidget import ParamWidget, WidgetValue


class GlobalLivingHingeWidget(ParamWidget):

    def __init__(self, cad_object):
        self.name = cad_object.Name
        self.label = cad_object.Label
        material = GlobalLivingMaterialProperties(freecad_object=cad_object)
        ParamWidget.__init__(self, material)
        self.widget_list.extend([WidgetValue(type=float, name="thickness", show_name="Thickness", widget=None),
                                 WidgetValue(type=str, name="new_name", show_name="Flat part name", widget=None),
                                 WidgetValue(type=list, name="hinge_type", show_name="Type", widget=None,
                                             interval_value=[GlobalLivingMaterialProperties.HINGE_TYPE_ALTERNATE_DOUBLE]),
                                 WidgetValue(type=float, name="alternate_nb_hinge", show_name="Nb hinge per column",
                                             widget=None, interval_value=[1, 30], decimals=0, step=1,
                                             parent_name="hinge_type",
                                             parent_value=[GlobalLivingMaterialProperties.HINGE_TYPE_ALTERNATE_DOUBLE]),
                                 WidgetValue(type=float, name="occupancy_ratio", show_name="Hinges occupancy ratio",
                                             widget=None, interval_value=[0.1, 1.], decimals=4, step=0.05,
                                             parent_name="hinge_type",
                                             parent_value=[GlobalLivingMaterialProperties.HINGE_TYPE_ALTERNATE_DOUBLE]),
                                 WidgetValue(type=float, name="link_clearance", show_name="Clearance width",
                                             widget=None, interval_value=[0., 30.], decimals=4, step=0.05),
                                 WidgetValue(type=float, name="laser_beam_diameter", show_name="Laser beam diameter",
                                             widget=None, interval_value=[0., 30.], decimals=4, step=0.05),
                                 WidgetValue(type=bool, name="generate_solid", show_name="Generate solid", widget=None)])


class LivingHingeWidget(ParamWidget):

    def __init__(self, first_freecad_face, first_freecad_object, second_freecad_face, second_freecad_object):
        material = HingesProperties(freecad_face_1 = first_freecad_face, freecad_object_1 = first_freecad_object,
                                    freecad_face_2 = second_freecad_face, freecad_object_2 = second_freecad_object)
        self.name = material.name
        ParamWidget.__init__(self, material)

        self.widget_list.extend([WidgetValue(type=float, name="arc_inner_radius", show_name="Arc radius (inner)", widget=None),
                                 WidgetValue(type=float, name="arc_outer_radius", show_name="Arc radius (outer)", widget=None),
                                 WidgetValue(type=float, name="arc_length", show_name="Arc length", widget=None),
                                 WidgetValue(type=float, name="deg_angle", show_name="Angle (degree)", widget=None),
                                 WidgetValue(type=float, name="min_links_nb", show_name="Min. link", widget=None),
                                 WidgetValue(type=float, name="nb_link", show_name="Number link",
                                             widget=None, interval_value=[2, 300], decimals=0, step=1)
                                 ])

