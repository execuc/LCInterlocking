# Plan: parameters as variables (expressions)

**Goal:** let users bind parameters such as Thickness, Thickness tolerance, Slot width tolerance and Width of tabs to variables (Spreadsheet aliases, VarSet properties, or formulas like `=2*t`) instead of fixed numbers.

**Status:** phases 1–4 and 6 done for Interlocking and Crosspiece. Phase 5 (Box, Rounded box, Living hinges) not started.

**Changes from the original plan:**
- The feature's ExpressionEngine is the only record of expressions; nothing is added to the JSON blob. FreeCAD rewrites expressions when an alias is renamed, so a copy in the blob would go stale.
- First version used a plain text box next to each spinbox. After testing, it was replaced by FreeCAD's `Gui::QuantitySpinBox` + `FreeCADGui.ExpressionBinding` (the standard f(x) button), as in FreeCAD's FEM task panels. The binding needs the property to exist, so mirror properties are created when a field is shown, and the ones left without an expression are removed on OK or Cancel. The expression editor writes to the object immediately, so `ExpressionSession` snapshots the expressions when the panel opens and restores them on Cancel.
- Length fields use `App::PropertyDistance` mirror properties and the `mm` unit on the spin box, so quantities like `0.2 mm` match. They display in the user's unit schema.
- Expressions are evaluated with `evalExpression` when values are applied, so they work right after OK without waiting for a recompute. `setExpression` silently accepts broken expressions, so each is checked before saving.

**Branch:** `expression-parameters`, created from `crosspiece-slot-side` so it includes the per-part slot side work (`slot_side` on `MaterialProperties`, the "Slot side" field in `CrossPartWidget`). The new crosspiece fields must keep working alongside the expression support.

## Why this isn't a small change

Every parameter is currently kept inside a single opaque blob on the feature: `parts`, `faces`, `box_properties` and so on are `App::PropertyPythonObject`, serialized to JSON by `panel/propertieslist.py`. FreeCAD's expression engine only attaches to real typed properties, so nothing in the blob can be bound to a variable.

Second, each feature's `execute()` only rebuilds when the panel sets `need_recompute` (`panel/multiplejoins.py`, `panel/crosspiece.py`). Even if values could be bound, editing a spreadsheet wouldn't regenerate the parts.

## Approach: mirror properties

Keep the JSON blob as the main storage. For each numeric parameter that has an expression, add a hidden real property to the feature (e.g. `p_Part001_thickness_tolerance`) and call `setExpression()` on it. FreeCAD then handles evaluation, the dependency on the spreadsheet or VarSet, renames and recompute. At recompute time, the evaluated values are copied back into the blob before the geometry is built.

- **Pros:** old `.FCStd` files load unchanged. The geometry code in `lasercut/*` doesn't change. Spreadsheets, VarSets and plain formulas all work, because they're all expressions.
- **Rejected alternative:** turn every parameter into a native property and drop the JSON. Cleaner in the long run, but it's a rewrite of every panel and breaks old documents.

## Phases

### 1. Shared plumbing (`lasercut/helper.py`, new `lasercut/expressions.py`)

- Add an `expressions` dict to `ObjectProperties` (field name → expression string), saved with the existing JSON. Old files simply have none.
- Helpers to:
  - build a safe property name from a part/face name plus a field
  - create, update and remove the mirror property
  - copy the evaluated values back into the blob

### 2. Recompute (`panel/multiplejoins.py`, `panel/crosspiece.py`)

- Make `execute()` rebuild when any mirror property has changed, not only when `need_recompute` is set.
- Clean up mirror properties when a part or tab is removed from the feature.

### 3. Panel UI (`panel/toolwidget.py`)

- Swap `QDoubleSpinBox` for FreeCAD's `Gui::QuantitySpinBox` together with `FreeCADGui.ExpressionBinding`. This gives the standard **f(x)** button, the expression editor with autocomplete, and the field turning blue when bound.
- Fallback if the binding misbehaves in a non-modal task panel: a small "=" field next to each spinbox, with the expression checked live using `evalExpression`.
- Edits stay inside a document transaction, so **Cancel** also undoes expression changes. Today Cancel only restores the deep-copied blob (`MultipleJoins.reject`).
- All panels build their fields through `ParamWidget`, so this adds expression support to every float field in one place.

### 4. Fields covered first: Interlocking and Crosspiece

- **Part** (`panel/partmat.py`): Thickness, Thickness tolerance, Slot width tolerance, Laser beam diameter, Node thickness
- **Tab** (`panel/tab.py`): Number of tabs, Width of tabs, Shift, Interval ratio, Half tab ratio, Screw diameter/length/tol., plus the Continuous and Flexible fields
- Tab "Width" and "Thickness" stay read-only, because they're measured from the face.
- Thickness is auto-detected from geometry, and `recomputeInit` only warns on a mismatch. If bound to a variable, the variable wins and the mismatch is still shown as a warning.

### 5. Later: Box, Rounded box, Living hinges

Same plumbing applied to `MakeBoxPanel.py`, `MakeRoundedBoxPanel.py` and `panel/livinghinge.py`.

### 6. Docs and testing

- Update `docs/interlocking.md` and `docs/crosspiece.md`; add a CHANGELOG entry.
- Manual checks against the files in `test/`:
  - old files open unchanged
  - changing a spreadsheet cell rebuilds the parts
  - Cancel undoes expression changes
  - renaming a spreadsheet alias carries through
  - a bad expression shows an error instead of crashing

## Risks

- `execute()` already calls `document.recompute()` from inside a recompute. Fine when pressing OK, but spreadsheet-driven rebuilds may expose it, so it may need restructuring.
- `ExpressionBinding` and `QuantitySpinBox` should be available from Python but are untested in this panel. Prototype them first (phase 3) before building on top.

## Open decisions

1. **Minimum FreeCAD version:** VarSets need FreeCAD 1.0+. Spreadsheets and formulas work on older versions. The plan supports all three either way.
2. **Scope of the first PR:** recommended Interlocking and Crosspiece first (phases 1–4), box and hinge tools in a follow-up.
3. **Property view:** expose the mirror properties in FreeCAD's property editor, or keep them hidden and edit only through the panel? Recommended: hidden at first.
