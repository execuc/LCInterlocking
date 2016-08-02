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


class LCInterlockingWorkbench (Workbench):
    MenuText = "Laser Cut Interlocking"
    ToolTip = "Laser cut interlocking assistant"
    Icon = """
/* XPM */
static char * laser_xpm[] = {
"16 16 2 1",
" 	c None",
".	c #FF0036",
"                ",
"                ",
"     .        . ",
"      .      .  ",
"       .    .   ",
"         ..     ",
"        ....    ",
".............   ",
".............   ",
"        ....    ",
"         ..     ",
"       .    .   ",
"      .      .  ",
"     .        . ",
"                ",
"                "};
"""
 
    def Initialize(self):
        import ExportPanel
        from panel import multiplejoins, crosspiece
        cmd_list = ["multiple_tabs_command", "export_crosspiece", "export_command"]  # A list of command names created in the line above
        self.appendToolbar("Laser Cut Commands", cmd_list)  # creates a new toolbar with your commands
 
    def Activated(self):
        return
 
    def Deactivated(self):
        return
 
    def ContextMenu(self, recipient):
        self.appendContextMenu("My commands", self.list)
 
    def GetClassName(self):
        return "Gui::PythonWorkbench"
 
Gui.addWorkbench(LCInterlockingWorkbench())
