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
from lasercut.roundedboxproperties import RoundedBoxProperties, TopBottomRoundedProperties


class DimensionRoundedBoxParam(ParamWidget):

    def __init__(self, properties = None):
        self.name = "Dimension"
        if properties is None:
            properties = RoundedBoxProperties()
        ParamWidget.__init__(self, properties)
        self.widget_list.extend([WidgetValue(type=float, name="nb_face", show_name="Number of faces", widget=None,
                                             interval_value=[5, 15], decimals=0, step=1),
                                 WidgetValue(type=float, name="inradius", show_name="Inner radius", widget=None,
                                             interval_value=[0.5, 3000.], decimals=2, step=1),
                                 WidgetValue(type=float, name="max_side_length", show_name="Max side length", widget=None),
                                 WidgetValue(type=float, name="side_length", show_name="Side length", widget=None,
                                             interval_value=[0.5, 3000.], decimals=2, step=1),
                                 WidgetValue(type=float, name="height", show_name="Side height", widget=None,
                                             interval_value=[0.5, 3000.], decimals=2, step=1),
                                 WidgetValue(type=float, name="thickness", show_name="Thickness", widget=None,
                                             interval_value=[0.5, 3000.], decimals=2, step=1),
                                 WidgetValue(type=float, name="cut", show_name="Nb cut", widget=None,
                                             interval_value=[0, 1000], decimals=0, step=1)
                                 ])

    def update_information(self):
        widget = self.get_widget("max_side_length")
        if widget is not None:
            widget.setText("%f" % self.get_property_value("max_side_length"))
        widget = self.get_widget("side_length")
        if widget is not None:
            widget.setValue(self.get_property_value("side_length"))
        widget = self.get_widget("cut")
        if widget is not None:
            widget.setValue(self.get_property_value("cut"))



class BottomRoundedBoxParam(ParamWidget):

    def __init__(self, properties = None):
        self.name = "Bottom"
        if properties is None:
            properties = TopBottomRoundedProperties()
        ParamWidget.__init__(self, properties)
        self.widget_list.extend([WidgetValue(type=list, name="position", show_name="Position", widget=None,
                                             interval_value=[TopBottomRoundedProperties.POSITION_OUTSIDE,
                                                             TopBottomRoundedProperties.POSITION_INSIDE]),
                                 WidgetValue(type=float, name="height_shift", show_name="Height shift", widget=None,
                                             interval_value=[0, 3000.], decimals=2, step=1,
                                             parent_name="position",
                                             parent_value=TopBottomRoundedProperties.POSITION_INSIDE),
                                 WidgetValue(type=float, name="radius_outside", show_name="Radius oustide", widget=None,
                                             interval_value=[0, 3000.], decimals=2, step=1,
                                             parent_name="position",
                                             parent_value=TopBottomRoundedProperties.POSITION_OUTSIDE)
                                 ])


class TopBoxRoundedParam(ParamWidget):

    def __init__(self, properties = None):
        self.name = "Top"
        if properties is None:
            properties = TopBottomRoundedProperties()
        ParamWidget.__init__(self, properties)
        self.widget_list.extend([WidgetValue(type=list, name="position", show_name="Position", widget=None,
                                             interval_value=[TopBottomRoundedProperties.POSITION_OUTSIDE,
                                                             TopBottomRoundedProperties.POSITION_INSIDE]),
                                 WidgetValue(type=float, name="height_shift", show_name="Height shift", widget=None,
                                             interval_value=[0, 3000.], decimals=2, step=1,
                                             parent_name="position",
                                             parent_value=TopBottomRoundedProperties.POSITION_INSIDE),
                                 WidgetValue(type=float, name="radius_outside", show_name="Radius oustide", widget=None,
                                             interval_value=[0, 3000.], decimals=2, step=1,
                                             parent_name="position",
                                             parent_value=TopBottomRoundedProperties.POSITION_OUTSIDE)
                                 ])
