#!/usr/bin/env python

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
from lasercut import expressions
import FreeCAD

EXPRESSION_HELP = ("Optional expression, e.g. Params.thickness, =2 * Params.tol or VarSet.Kerf.\n"
                   "Leave empty to use the number on the left.")

class WidgetValue(helper.ObjectProperties):

    _allowed = ('widget', 'show_name', 'name', 'type', 'interval_value', 'decimals', 'step',
                'parent_name', 'parent_value', 'widget_title')

    def __init__(self, **kwargs):
        super(WidgetValue, self).__init__(**kwargs)


class ParamWidget(object):

    def __init__(self, object_property):
        self.object_property = object_property
        self.widget_list = []
        self.form = None
        self.expression_session = None
        self.expression_kind = None
        self.expression_key = None
        return

    def set_expression_session(self, session):
        """Let numeric fields be bound to expressions (see lasercut.expressions)."""
        self.expression_session = session
        self.expression_kind, self.expression_key = expressions.item_kind_key(self.object_property)

    def get_grid(self):
        row_index = 0
        # Do not parent the layout to the form directly; the layout is set on the
        # group box later, and attaching it to the parent widget would conflict
        # with any existing layout on that widget.
        widgets_grid = QtGui.QGridLayout()
        for widget in self.widget_list:
            self.create_item(widget, widgets_grid, row_index)
            row_index += 1
        self.listchangeIndex(0)
        return widgets_grid

    def create_item(self, widget_config, grid, row_index):
        widget_config.widget_title = QtGui.QLabel(self.form)
        widget_config.widget_title.setText("%s : " % widget_config.show_name)

        if widget_config.type == float and not hasattr(widget_config, 'step'):
            widget_config.widget = QtGui.QLabel(self.form)
            widget_config.widget.setText("%f" % self.get_property_value(widget_config.name))
        elif widget_config.type == float:
            widget_config.widget = QtGui.QDoubleSpinBox(self.form)
            widget_config.widget.setDecimals(widget_config.decimals)
            widget_config.widget.setSingleStep(widget_config.step)
            widget_config.widget.setMinimum(widget_config.interval_value[0])
            widget_config.widget.setMaximum(widget_config.interval_value[-1])
            widget_config.widget.setValue(self.get_property_value(widget_config.name))
            if self.expression_session is not None:
                self.create_expression_edit(widget_config)
        elif widget_config.type == bool:
            widget_config.widget = QtGui.QCheckBox("", self.form)
            state = QtCore.Qt.Checked if self.get_property_value(widget_config.name) == True else QtCore.Qt.Unchecked
            widget_config.widget.setCheckState(state)
        elif widget_config.type == list:
            widget_config.widget = QtGui.QComboBox(self.form)
            widget_config.widget.addItems(widget_config.interval_value)
            default_value_index = 0
            for str_value in widget_config.interval_value:
                if self.get_property_value(widget_config.name) == str_value:
                    break
                default_value_index += 1
            if default_value_index == len(widget_config.interval_value):
                raise ValueError("Default value not found for list" + widget_config.name)
            widget_config.widget.setCurrentIndex(default_value_index)
            widget_config.widget.currentIndexChanged.connect(self.listchangeIndex)
        elif widget_config.type == str:
            widget_config.widget = QtGui.QLineEdit(self.form)
            widget_config.widget.setText(self.get_property_value(widget_config.name))
        else:
            raise ValueError("Undefined widget type")

        grid.addWidget(widget_config.widget_title, row_index, 0)
        grid.addWidget(widget_config.widget, row_index, 1)
        if self.get_expression_edit(widget_config) is not None:
            grid.addWidget(widget_config.expression_widget, row_index, 2)

    @staticmethod
    def get_expression_edit(widget_config):
        return getattr(widget_config, 'expression_widget', None)

    def create_expression_edit(self, widget_config):
        edit = QtGui.QLineEdit(self.form)
        edit.setPlaceholderText("= expression")
        edit.setText(self.expression_session.get(self.expression_kind, self.expression_key, widget_config.name))
        widget_config.expression_widget = edit
        widget_config.expression_value = None
        edit.textChanged.connect(lambda text, config=widget_config: self.expression_changed(config))
        self.expression_changed(widget_config)

    def expression_changed(self, widget_config):
        edit = widget_config.expression_widget
        spin_box = widget_config.widget
        text = expressions.strip_expression(edit.text())
        widget_config.expression_value = None
        if not text:
            spin_box.setEnabled(True)
            edit.setStyleSheet("")
            edit.setToolTip(EXPRESSION_HELP)
            return
        try:
            value = self.expression_session.evaluate(text, widget_config.name)
        except ValueError as e:
            spin_box.setEnabled(True)
            edit.setStyleSheet("QLineEdit { color: #d32f2f; }")
            edit.setToolTip("Invalid expression: %s" % e)
            return
        widget_config.expression_value = value
        # The spin box only shows the result; the value itself isn't clamped to its range.
        spin_box.setValue(value)
        spin_box.setEnabled(False)
        edit.setStyleSheet("")
        edit.setToolTip("= %s" % ("%.6g" % value))

    def get_properties(self):
        for widget_config in self.widget_list:
            if widget_config.type == float and not hasattr(widget_config, 'step'):
                continue
            elif widget_config.type == float:
                edit = self.get_expression_edit(widget_config)
                if edit is not None:
                    self.expression_session.set(self.expression_kind, self.expression_key,
                                                widget_config.name, edit.text())
                    if widget_config.expression_value is not None:
                        self.set_property_value(widget_config.name, widget_config.expression_value)
                        continue
                self.set_property_value(widget_config.name, widget_config.widget.value())
            elif widget_config.type == bool:
                if widget_config.widget.checkState() == QtCore.Qt.Checked:
                    self.set_property_value(widget_config.name, True)
                else:
                    self.set_property_value(widget_config.name, False)
            elif widget_config.type == str:
                self.set_property_value(widget_config.name, widget_config.widget.text())
            elif widget_config.type == list:
                self.set_property_value(widget_config.name, widget_config.widget.currentText())
            else:
                raise ValueError("Undefined widget type")
        return self.object_property

    def set_property_value(self, name, value):
        return setattr(self.object_property, name, value)

    def get_property_value(self, name):
        return getattr(self.object_property, name)

    def get_group_box(self, widget):
        group_box = QtGui.QGroupBox(widget)
        group_box.setFlat(False)
        if hasattr(self, 'description'):
            group_box.setTitle("%s" % self.description)
        else:
            group_box.setTitle("%s" % self.name)
        self.form = widget
        grid = self.get_grid()
        group_box.setLayout(grid)
        return group_box, grid

    def properties(self):
        return self.object_property

    def get_widget(self, name):
        widget = None
        for widget_config in self.widget_list:
            if widget_config.name == name:
                widget = widget_config.widget
                break

        if widget is None:
            raise ValueError("Widget " + str(name) + " not found")
        return widget

    def listchangeIndex(self, index):
        self.get_properties()
        for widget_config in self.widget_list:
            if hasattr(widget_config, 'parent_name') and hasattr(widget_config, 'parent_value'):
                if isinstance(widget_config.parent_name, list):
                    parents_list = widget_config.parent_name
                    parents_values = widget_config.parent_value
                else:
                    parents_list = [widget_config.parent_name]
                    parents_values = [widget_config.parent_value]

                if len(parents_list) != len(parents_values):
                    raise ValueError("Not well formatted widget")

                widget_config.widget_title.show()
                widget_config.widget.show()
                if self.get_expression_edit(widget_config) is not None:
                    widget_config.expression_widget.show()

                for index in range(len(parents_list)):
                    parent = parents_list[index]
                    list_value = parents_values[index]
                    if not isinstance(list_value, list):
                        list_value = [parents_values[index]]
                    found = False
                    for value in list_value:
                        if self.get_property_value(parent) == value:
                            found = True
                            break
                    if found is False:
                        widget_config.widget_title.hide()
                        widget_config.widget.hide()
                        if self.get_expression_edit(widget_config) is not None:
                            widget_config.expression_widget.hide()
                        break


