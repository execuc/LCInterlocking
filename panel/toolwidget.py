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

from PySide import QtCore, QtGui
from lasercut import helper


class WidgetValue(helper.ObjectProperties):

    _allowed = ('widget', 'show_name', 'name', 'type', 'interval_value', 'decimals', 'step')

    def __init__(self, **kwargs):
        super(WidgetValue, self).__init__(**kwargs)


class ParamWidget(object):

    def __init__(self, object_property):
        self.object_property = object_property
        self.widget_list = []
        self.form = None
        return

    def get_grid(self):
        row_index = 0
        widgets_grid = QtGui.QGridLayout(self.form)
        for widget in self.widget_list:
            self.create_item(widget, widgets_grid, row_index)
            row_index += 1
        return widgets_grid

    def create_item(self, widget_config, grid, row_index):
        title = QtGui.QLabel(self.form)
        title.setText("%s : " % widget_config.show_name)
        grid.addWidget(title, row_index, 0)
        if widget_config.type == float and not hasattr(widget_config, 'step'):
            widget_config.widget = QtGui.QLabel(self.form)
            widget_config.widget.setText("%f" % self.get_property_value(widget_config.name))
            grid.addWidget(widget_config.widget, row_index, 1)
        elif widget_config.type == float:
            widget_config.widget = QtGui.QDoubleSpinBox(self.form)
            widget_config.widget.setDecimals(widget_config.decimals)
            widget_config.widget.setSingleStep(widget_config.step)
            widget_config.widget.setMinimum(widget_config.interval_value[0])
            widget_config.widget.setValue(self.get_property_value(widget_config.name))
            widget_config.widget.setMaximum(widget_config.interval_value[-1])
            grid.addWidget(widget_config.widget, row_index, 1)
        elif widget_config.type == bool:
            widget_config.widget = QtGui.QCheckBox("", self.form)
            state = QtCore.Qt.Checked if self.get_property_value(widget_config.name) == True else QtCore.Qt.Unchecked
            widget_config.widget.setCheckState(state)
            grid.addWidget(widget_config.widget, row_index, 1)
        elif widget_config.type == list:
            widget_config.widget = QtGui.QComboBox(self.form)
            widget_config.widget.addItems(widget_config.interval_value)
            grid.addWidget(widget_config.widget, row_index, 1)
        elif widget_config.type == str:
            widget_config.widget = QtGui.QLineEdit(self.form)
            widget_config.widget.setText(self.get_property_value(widget_config.name))
            grid.addWidget(widget_config.widget, row_index, 1)
        else:
            raise ValueError("Undefined widget type")

    def get_properties(self):
        for widget_config in self.widget_list:
            if widget_config.type == float and not hasattr(widget_config, 'step'):
                continue
            elif widget_config.type == float:
                self.set_property_value(widget_config.name, widget_config.widget.value())
            elif widget_config.type == bool:
                if widget_config.widget.checkState() == QtCore.Qt.Checked:
                    self.set_property_value(widget_config.name, True)
                else:
                    self.set_property_value(widget_config.name, False)
            elif widget_config.type == str:
                self.set_property_value(widget_config.name, widget_config.widget.text())
            elif widget_config.type == list:
                raise ValueError("Unsupported widget type")
            else:
                raise ValueError("Undefined widget type")
        return self.object_property

    def set_property_value(self, name, value):
        return setattr(self.object_property, name, value)

    def get_property_value(self, name):
        return getattr(self.object_property, name)

    # NEW
    def get_group_box(self, widget):
        group_box = QtGui.QGroupBox(widget)
        group_box.setFlat(False)
        self.form = widget
        grid = self.get_grid()
        group_box.setLayout(grid)
        group_box.setTitle(self.name)
        return group_box, grid

    def properties(self):
        return self.object_property

