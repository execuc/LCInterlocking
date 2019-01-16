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
import FreeCAD

class TreeItem(object):

    PART = 1
    PART_LINK = 2
    TAB = 3
    TAB_LINK = 4
    ROOT = 5

    def __init__(self, t_type, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []
        self.type = t_type

    def append_child(self, item):
        self.childItems.append(item)

    def remove_child(self, row):
        value = self.childItems[row]
        self.childItems.remove(value)

        return True

    def child(self, row):
        return self.childItems[row]

    def child_count(self):
        return len(self.childItems)

    def column_count(self):
        return len(self.itemData)

    def data(self, column):
        if self.type == TreeItem.TAB or self.type == TreeItem.TAB_LINK:
            if column == 0:
                return self.itemData[1]
            else:
                return ""
        try:
            return self.itemData[column]
        except IndexError:
            return None

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)
        return 0

    def get_name(self):
        return self.itemData[0]


class TreeModel(QtCore.QAbstractItemModel):
    def __init__(self, parent=None):
        super(TreeModel, self).__init__(parent)
        self.rootItem = TreeItem(TreeItem.ROOT, ["Name", "Label"])

    def append_part(self, name, label, is_link=False):
        row = self.rootItem.child_count() - 1
        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        part_type = TreeItem.PART_LINK if is_link else TreeItem.PART
        self.rootItem.append_child(TreeItem(part_type, [name, label], self.rootItem))
        self.endInsertRows()
        self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())
        return self.index(self.rootItem.child_count()-1, 0, QtCore.QModelIndex())

    def append_tab(self, part_name, tab_name, show_name, is_link=False):
        index_inserted = None
        for part_item in self.rootItem.childItems:
            if part_item.get_name() == part_name:
                for tab_item in part_item.childItems:
                    if tab_item.get_name() == tab_name:
                        raise ValueError("%s already managed" % tab_name)
                parent_index = self.createIndex(part_item.row(), 0, part_item)
                row = part_item.child_count() - 1
                self.beginInsertRows(parent_index, row, row)
                tab_type = TreeItem.TAB_LINK if is_link else TreeItem.TAB
                tab_item = TreeItem(tab_type, [tab_name, show_name], part_item)
                part_item.append_child(tab_item)
                self.endInsertRows()
                self.dataChanged.emit(parent_index, parent_index)
                index_inserted = self.index(part_item.child_count()-1, 0, parent_index)
                break
        return index_inserted

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().column_count()
        else:
            return self.rootItem.column_count()

    def data(self, index, role):
        if not index.isValid():
            return None

        if role == QtCore.Qt.ForegroundRole:
            item = index.internalPointer()
            if item.type == TreeItem.PART_LINK or item.type == TreeItem.TAB_LINK:
                return QtGui.QColor(190, 190, 190)

        if role != QtCore.Qt.DisplayRole:
            return None

        item = index.internalPointer()
        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags

        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.rootItem.data(section)

        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parent_item = self.rootItem
        else:
            parent_item = parent.internalPointer()

        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent()

        if parent_item == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def rowCount(self, parent):
        node = self.node_from_index(parent)
        if node is None:
            return 0
        return node.child_count()

    def removeRows(self, row, count, parent_index):
        self.beginRemoveRows(parent_index, row, row)
        node = self.node_from_index(parent_index)
        node.remove_child(row)
        self.endRemoveRows()

        return True

    def node_from_index(self, index):
        return index.internalPointer() if index.isValid() else self.rootItem

    def insertRow(self, row, parent):
        return self.insertRows(row, 1, parent)

    def insertRows(self, row, count, parent):
        self.beginInsertRows(parent, row, (row + (count - 1)))
        self.endInsertRows()
        return True
