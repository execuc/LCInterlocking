Parameters as variables
===========

In the Interlocking and Crosspiece tools, every number field of a part or a face (thickness, thickness tolerance, slot width tolerance, laser beam diameter, node thickness, number of tabs, width of tabs, shift, screw dimensions...) can be bound to a FreeCAD expression instead of a fixed number, the same way as in other FreeCAD dialogs.

This lets several parts and connections share one material definition, kept in a Spreadsheet or a VarSet.

Procedure
-------------
 * Create the variables, for example a Spreadsheet named `Params` with aliases `thk`, `tol` and `kerf`, or a VarSet (FreeCAD 1.0+).
 * Edit the "MultiJoin" or "Crosspiece" group and select a part or a face in the tool's tree view.
 * Click the **f(x)** icon in a value field, or type `=` in it, and enter an expression in FreeCAD's expression editor, for example:
   * `Params.kerf`
   * `Params.thk * 0.1`
   * `VarSet.Kerf`
   * `2 * 0.15 mm`
 * The field then shows the result and is locked to the expression. To go back to a fixed number, open the expression editor again and remove the expression.
 * Click on OK to save. Cancel restores the expressions as they were when the tool was opened.

Additional Information
----------------------------
  * When a variable changes, the generated parts are rebuilt on the next recompute.
  * Renaming a spreadsheet alias updates the expressions automatically.
  * Linked parts and faces (added with "Add same parts" / "Add same faces") use the expressions of the part or face they are linked to.
  * Length fields use FreeCAD's unit settings (Preferences > General > Units), so they may show inches. Ratios and counts have no unit. "Number of tabs" is rounded to a whole number, with a minimum of 1.
  * Expressions are stored as hidden properties named `lcx_...` on the group object. They are created while the tool is open and only the ones with an expression are kept. Removing a part or face from the tool removes its expressions.
  * If the thickness of a part is bound to a variable that doesn't match the part's actual geometry, a warning is shown in the report view.
