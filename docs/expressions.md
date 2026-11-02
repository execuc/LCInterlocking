Parameters as variables
===========

In the Interlocking and Crosspiece tools, every number field of a part or a face (thickness, thickness tolerance, slot width tolerance, laser beam diameter, node thickness, number of tabs, width of tabs, shift, screw dimensions...) can be bound to a FreeCAD expression instead of a fixed number.

This lets several parts and connections share one material definition, kept in a Spreadsheet or a VarSet.

Procedure
-------------
 * Create the variables, for example a Spreadsheet named `Params` with aliases `thk`, `tol` and `kerf`, or a VarSet (FreeCAD 1.0+).
 * Edit the "MultiJoin" or "Crosspiece" group and select a part or a face in the tool's tree view.
 * Type an expression in the field to the right of a value, for example:
   * `Params.kerf`
   * `=Params.thk * 0.1`
   * `VarSet.Kerf`
   * `2 * 0.15 mm`
 * The value on the left is greyed out and shows the result. An invalid expression is shown in red; hover over it to see why.
 * Clear the field to go back to a fixed number.
 * Click on OK to save. Cancel discards expression changes too.

Additional Information
----------------------------
  * When a variable changes, the generated parts are rebuilt on the next recompute.
  * Renaming a spreadsheet alias updates the expressions automatically.
  * Linked parts and faces (added with "Add same parts" / "Add same faces") use the expressions of the part or face they are linked to.
  * Lengths are in mm. "Number of tabs" is rounded to a whole number, with a minimum of 1.
  * Expressions are stored as hidden properties named `lcx_...` on the group object. Removing a part or face from the tool removes its expressions.
  * If the thickness of a part is bound to a variable that doesn't match the part's actual geometry, a warning is shown in the report view.
