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

from lasercut import helper
from lasercut.tabproperties import TabProperties

# Extra depth added past the neighboring part's own thickness when probing for
# a physical intersection, to absorb tiny numerical/zero-gap edge cases.
PROBE_MARGIN = 0.2
MIN_INTERSECT_VOLUME = 0.001


class CandidateFace:
    def __init__(self, freecad_obj, face_index, face, y_length, thickness):
        self.freecad_obj = freecad_obj
        self.face_index = face_index
        self.face = face
        self.face_name = "Face%d" % (face_index + 1)
        self.y_length = y_length
        self.thickness = thickness


def collect_candidate_faces(freecad_objects):
    candidates = []
    for obj in freecad_objects:
        for index, face in enumerate(obj.Shape.Faces):
            try:
                normal, y_local, z_local = helper.get_local_axis(face)
            except Exception:
                # get_local_axis assumes a planar quad face; skip anything else
                # (curved faces, fillets, holes, ...) rather than crashing the scan.
                continue
            if normal is None:
                continue
            candidates.append(CandidateFace(obj, index, face, y_local.Length, z_local.Length))
    return candidates


def _intersecting_parts(candidate, freecad_objects, thickness_by_name):
    normal = candidate.face.normalAt(0, 0).normalize()
    matches = []
    for obj in freecad_objects:
        if obj is candidate.freecad_obj:
            continue
        depth = thickness_by_name.get(obj.Name, candidate.thickness) + PROBE_MARGIN
        try:
            probe = candidate.face.extrude(normal * depth)
            volume = obj.Shape.common(probe).Volume
        except Exception:
            continue
        if volume > MIN_INTERSECT_VOLUME:
            matches.append(obj)
    return matches


def find_connections(freecad_objects, thickness_by_name):
    """For every candidate tab face, test (via the same boolean-intersection
    test the real cut algorithm uses) which other part it would actually cut
    into. A face connecting to exactly one other part is a confident match;
    each physical connection is only reported once (from whichever side is
    found first), since only one side needs a tab entry."""
    candidates = collect_candidate_faces(freecad_objects)

    connections = []
    ambiguous = []
    unmatched = []
    seen_pairs = set()
    for candidate in candidates:
        matches = _intersecting_parts(candidate, freecad_objects, thickness_by_name)
        if len(matches) == 0:
            unmatched.append(candidate)
        elif len(matches) > 1:
            ambiguous.append(candidate)
        else:
            target = matches[0]
            pair_key = frozenset([candidate.freecad_obj.Name, target.Name])
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)
            connections.append((candidate, target))
    return connections, ambiguous, unmatched


def compute_tab_sizing(y_length, desired_tab_width, tab_type):
    if tab_type == TabProperties.TYPE_CONTINUOUS:
        # tabs_number counts every alternating segment here, tab and gap alike.
        tabs_number = max(2, int(round(y_length / desired_tab_width)))
        return tabs_number, desired_tab_width

    # tabs_number counts only the solid tabs, so double the period to leave a gap of roughly the same size.
    tabs_number = max(1, int(round(y_length / (2. * desired_tab_width))))
    tabs_width = desired_tab_width
    while tabs_number > 1 and tabs_number * tabs_width > y_length:
        tabs_number -= 1
    return tabs_number, tabs_width
