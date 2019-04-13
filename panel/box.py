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

from panel.toolwidget import ParamWidget, WidgetValue
from lasercut.boxproperties import BoxProperties, TopBottomProperties


class DimensionBoxParam(ParamWidget):

    def __init__(self, properties = None):
        self.name = "Dimension"
        if properties is None:
            properties = BoxProperties()
        ParamWidget.__init__(self, properties)
        self.widget_list.extend([WidgetValue(type=float, name="length", show_name="Length", widget=None,
                                             interval_value=[0.5, 3000.], decimals=2, step=1),
                                 WidgetValue(type=float, name="width", show_name="Width", widget=None,
                                             interval_value=[0.5, 3000.], decimals=2, step=1),
                                 WidgetValue(type=float, name="height", show_name="Height", widget=None,
                                             interval_value=[0.5, 3000.], decimals=2, step=1),
                                 WidgetValue(type=float, name="thickness", show_name="Thickness", widget=None,
                                             interval_value=[0.5, 3000.], decimals=2, step=1),
                                 WidgetValue(type=bool, name="outside_measure", show_name="Outside measure", widget=None)

                                 ])


class LengthWidthBoxParam(ParamWidget):

    def __init__(self, properties = None):
        self.name = "Length and width"
        if properties is None:
            properties = BoxProperties()
        ParamWidget.__init__(self, properties)
        self.widget_list.extend([WidgetValue(type=list, name="length_width_priority", show_name="Priority", widget=None,
                                             interval_value=[BoxProperties.LENGTH_PRIORTY, BoxProperties.WIDTH_PRIORTY,
                                                             BoxProperties.CROSS_PRIORTY, BoxProperties.ROUND_PRIORTY]),
                                 WidgetValue(type=float, name="width_shift", show_name="Width shift", widget=None,
                                             interval_value=[0, 3000.], decimals=2, step=1,
                                             parent_name="length_width_priority",
                                             parent_value=[BoxProperties.LENGTH_PRIORTY]),
                                 WidgetValue(type=float, name="length_shift", show_name="Length shift", widget=None,
                                             interval_value=[0, 3000.], decimals=2, step=1,
                                             parent_name="length_width_priority",
                                             parent_value=[BoxProperties.WIDTH_PRIORTY]),
                                 WidgetValue(type=float, name="length_outside", show_name="Diff. length", widget=None,
                                             interval_value=[0, 3000.], decimals=2, step=1,
                                             parent_name="length_width_priority",
                                             parent_value=[BoxProperties.CROSS_PRIORTY]),
                                 WidgetValue(type=float, name="width_outside", show_name="Diff. width", widget=None,
                                             interval_value=[0, 3000.], decimals=2, step=1,
                                             parent_name="length_width_priority",
                                             parent_value=[BoxProperties.CROSS_PRIORTY]),
                                 WidgetValue(type=float, name="inner_radius", show_name="Width/length", widget=None,
                                             interval_value=[0, 3000.], decimals=2, step=1,
                                             parent_name="length_width_priority",
                                             parent_value=[BoxProperties.ROUND_PRIORTY])
                                 ])


class BottomBoxParam(ParamWidget):

    def __init__(self, properties = None):
        self.name = "Bottom"
        if properties is None:
            properties = TopBottomProperties()
        ParamWidget.__init__(self, properties)
        self.widget_list.extend([WidgetValue(type=list, name="position", show_name="Position", widget=None,
                                             interval_value=[TopBottomProperties.POSITION_OUTSIDE, TopBottomProperties.POSITION_INSIDE]),
                                 WidgetValue(type=float, name="height_shift", show_name="Height shift", widget=None,
                                             interval_value=[0, 3000.], decimals=2, step=1,
                                             parent_name="position", parent_value=TopBottomProperties.POSITION_INSIDE),
                                 WidgetValue(type=float, name="length_outside", show_name="Length oustide", widget=None,
                                             interval_value=[0, 3000.], decimals=2, step=1,
                                             parent_name="position", parent_value=TopBottomProperties.POSITION_OUTSIDE),
                                 WidgetValue(type=float, name="width_outside", show_name="Width oustide", widget=None,
                                             interval_value=[0, 3000.], decimals=2, step=1,
                                             parent_name="position", parent_value=TopBottomProperties.POSITION_OUTSIDE)
                                 ])


class TopBoxParam(ParamWidget):

    def __init__(self, properties = None):
        self.name = "Top"
        if properties is None:
            properties = TopBottomProperties()
        ParamWidget.__init__(self, properties)
        self.widget_list.extend([WidgetValue(type=list, name="position", show_name="Position", widget=None,
                                             interval_value=[TopBottomProperties.POSITION_OUTSIDE, TopBottomProperties.POSITION_INSIDE]),
                                 WidgetValue(type=float, name="height_shift", show_name="Height shift", widget=None,
                                             interval_value=[0, 3000.], decimals=2, step=1,
                                             parent_name="position", parent_value=TopBottomProperties.POSITION_INSIDE),
                                 # WidgetValue(type=list, name="top_type", show_name="Top type", widget=None,
                                 #             interval_value=[TopBottomProperties.TOP_TYPE_NORMAL, TopBottomProperties.TOP_TYPE_COVER],
                                 #            parent_name="position", parent_value=TopBottomProperties.POSITION_INSIDE),
                                 WidgetValue(type=float, name="length_outside", show_name="Length outside", widget=None,
                                             interval_value=[0, 3000.], decimals=2, step=1,
                                             parent_name="position", parent_value=TopBottomProperties.POSITION_OUTSIDE),
                                 WidgetValue(type=float, name="width_outside", show_name="Width outside", widget=None,
                                             interval_value=[0, 3000.], decimals=2, step=1,
                                             parent_name="position", parent_value=TopBottomProperties.POSITION_OUTSIDE)
                                 #WidgetValue(type=float, name="cover_length_tolerance", show_name="Cover length tol.",
                                 #            widget=None, interval_value=[0, 3000.], decimals=2, step=1,
                                 #            parent_name=["position", "top_type"],
                                 #            parent_value=[TopBottomProperties.POSITION_INSIDE, TopBottomProperties.TOP_TYPE_COVER])

                                 ])
