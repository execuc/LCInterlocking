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

"""Bind numeric part/tab parameters to FreeCAD expressions.

Parameters live in a JSON blob (App::PropertyPythonObject), which FreeCAD's
expression engine can't reach. For each parameter bound to an expression we
add a hidden property to the feature ("mirror property") and set the
expression on it. FreeCAD then tracks the dependency on the spreadsheet or
VarSet, keeps the expression up to date when aliases are renamed, and
recomputes the feature when a referenced value changes.

The feature's ExpressionEngine is the only record of which parameters are
bound; the blob only keeps the last evaluated values.
"""

import math
import re

PREFIX = "lcx_"
GROUP = "LCInterlocking expressions"

KIND_PART = "part"
KIND_TAB = "tab"

# Fields that must be whole numbers once evaluated, with their minimum value.
INTEGER_FIELDS = {"tabs_number": 1}

# Fields measured in mm. Their mirror property is a distance, so the panel
# shows "mm" and expressions such as "Params.kerf" (0.2 mm) match the unit.
# Other fields (ratios, counts) are plain numbers.
LENGTH_FIELDS = {"thickness", "thickness_tolerance", "hole_width_tolerance", "laser_beam_diameter",
                 "node_thickness", "tabs_width", "tabs_shift", "screw_diameter", "screw_length",
                 "screw_length_tol"}

_SEPARATOR = "__"


def _sanitize(text):
    return re.sub(r"[^A-Za-z0-9_]", "_", str(text))


def property_name(kind, key, field):
    """Name of the mirror property for one parameter of one part or tab."""
    return "%s%s_%s%s%s" % (PREFIX, kind, _sanitize(key), _SEPARATOR, field)


def _split_property_name(name):
    """Return (kind, sanitized key, field) for a mirror property name, or None."""
    if not name.startswith(PREFIX) or _SEPARATOR not in name:
        return None
    head, field = name[len(PREFIX):].rsplit(_SEPARATOR, 1)
    if "_" not in head:
        return None
    kind, key = head.split("_", 1)
    return kind, key, field


def item_kind_key(item):
    """Kind and key used to name the mirror properties of a part or tab.

    Linked parts/tabs share the parameters of their source, so they use the
    source's key.
    """
    if hasattr(item, "tab_name"):
        return KIND_TAB, (item.link_name or item.tab_name)
    return KIND_PART, (item.link_name or item.name)


def _engine(fp):
    try:
        return dict(fp.ExpressionEngine)
    except AttributeError:
        return {}


def get_expression(fp, kind, key, field):
    return _engine(fp).get(property_name(kind, key, field))


def strip_expression(expr):
    if expr is None:
        return ""
    expr = expr.strip()
    if expr.startswith("="):
        expr = expr[1:].strip()
    return expr


def evaluate(fp, expr, field=None):
    """Evaluate an expression in the context of the feature and return a float.

    Quantities are returned in FreeCAD's internal unit (mm for lengths).
    Raises ValueError with a readable message on failure.
    """
    expr = strip_expression(expr)
    if not expr:
        raise ValueError("Empty expression")
    try:
        result = fp.evalExpression(expr)
    except Exception as e:
        raise ValueError(str(e))
    value = getattr(result, "Value", result)
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError("'%s' does not give a number" % expr)
    if math.isnan(value) or math.isinf(value):
        raise ValueError("'%s' does not give a finite number" % expr)
    if field in INTEGER_FIELDS:
        value = float(max(INTEGER_FIELDS[field], int(round(value))))
    return value


def set_expression(fp, kind, key, field, expr):
    """Bind (or unbind, when expr is empty) one parameter.

    The expression is checked first, because FreeCAD accepts broken
    expressions silently. Raises ValueError if it can't be evaluated.
    """
    expr = strip_expression(expr)
    name = property_name(kind, key, field)
    if not expr:
        _remove_property(fp, name)
        return
    value = evaluate(fp, expr, field)
    ensure_property(fp, kind, key, field)
    if _engine(fp).get(name) != expr:
        fp.setExpression(name, expr)
    setattr(fp, name, value)


def ensure_property(fp, kind, key, field):
    """Create the mirror property if needed and return (name, created)."""
    name = property_name(kind, key, field)
    if hasattr(fp, name):
        return name, False
    prop_type = "App::PropertyDistance" if field in LENGTH_FIELDS else "App::PropertyFloat"
    fp.addProperty(prop_type, name, GROUP, "Expression for %s of %s" % (field, key), 0, False, True)
    return name, True


def mirror_properties(fp):
    return [name for name in fp.PropertiesList if _split_property_name(name) is not None]


def _remove_property(fp, name):
    if not hasattr(fp, name):
        return
    if name in _engine(fp):
        fp.setExpression(name, None)
    fp.removeProperty(name)


def remove_stale(fp, items):
    """Remove mirror properties of parts/tabs that are no longer in the feature."""
    valid = set()
    for item in items:
        kind, key = item_kind_key(item)
        valid.add((kind, _sanitize(key)))
    for name in list(fp.PropertiesList):
        parsed = _split_property_name(name)
        if parsed is None:
            continue
        kind, key, field = parsed
        if (kind, key) not in valid:
            _remove_property(fp, name)


def apply_values(fp, items, report_error=None):
    """Evaluate every bound parameter and write the result into the items.

    Expressions are evaluated directly instead of reading the mirror
    property, so this also works right after set_expression(), before the
    document has been recomputed. Returns True if any value changed.
    """
    engine = _engine(fp)
    bound = {}
    for name, expr in engine.items():
        parsed = _split_property_name(name)
        if parsed is not None:
            bound.setdefault(parsed[:2], []).append((parsed[2], expr))

    changed = False
    for item in items:
        kind, key = item_kind_key(item)
        for field, expr in bound.get((kind, _sanitize(key)), []):
            try:
                value = evaluate(fp, expr, field)
            except ValueError as e:
                if report_error is not None:
                    report_error("%s: expression for %s '%s' failed: %s\n" % (key, field, expr, e))
                continue
            current = getattr(item, field, None)
            if current is None or abs(float(current) - value) > 1e-9:
                setattr(item, field, value)
                changed = True
    return changed


class ExpressionSession(object):
    """Tracks expression changes made while a task panel is open.

    The panel binds its spin boxes to the mirror properties, and FreeCAD's
    expression editor (the f(x) button) writes to them immediately. So the
    session remembers the expressions present when the panel opened, puts
    them back on Cancel, and removes the mirror properties that ended up
    without an expression when the panel closes.
    """

    def __init__(self, fp):
        self.fp = fp
        engine = _engine(fp)
        self.original = dict((name, engine[name]) for name in mirror_properties(fp) if name in engine)

    def ensure_property(self, kind, key, field):
        return ensure_property(self.fp, kind, key, field)[0]

    def get_expression(self, name):
        return _engine(self.fp).get(name)

    def evaluate(self, expr, field=None):
        return evaluate(self.fp, expr, field)

    def _remove_unbound(self):
        engine = _engine(self.fp)
        for name in mirror_properties(self.fp):
            if name not in engine:
                self.fp.removeProperty(name)

    def commit(self, items):
        """OK: keep the expressions, drop unused and stale mirror properties."""
        self._remove_unbound()
        remove_stale(self.fp, items)

    def rollback(self):
        """Cancel: restore the expressions present when the panel opened."""
        engine = _engine(self.fp)
        for name in mirror_properties(self.fp):
            original = self.original.get(name)
            if engine.get(name) != original:
                self.fp.setExpression(name, original)
        self._remove_unbound()
