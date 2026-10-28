Crosspiece
===========

This tool allow to create slot on parts in order to fit together.

Procedure
-----------
 * Select all the involved part and click on "Add same parts" if they share the same material properties, else click on "Add parts"
 ![Illustration](imgs/crosspiece/addparts.png)
 * Configure material properties on black font item from the tree view as thickness, laser cut beam diameter....
 * Optionally choose the **Slot side** of each part: *Top* or *Bottom* to pick which side its slots open on, or *Auto* (default) to let the tool decide. When one part of a joint is set and the other is on *Auto*, the other part gets the opposite side.
   * *Top* is the +Z side of the joint. If the joint is horizontal, it is +Y, then +X.
   * Two crossing parts can't both use the same side. If one part sticks out above or below the other, the geometry decides the sides, and a conflicting choice shows an error.
 * Click on OK to create a "Crosspiece" group. Interlocking parts are below this group. Origin parts are represented inside a sub group.
 ![Illustration](imgs/crosspiece/final.png)
  
 Additional Information
----------------------------
  * Crosspiece properties can be edited again clicking on "Crosspiece" group item.
  * In editing mode, parts can be visualized by selecting the treview of the tools. Then they can be displayed/hidden by tapping in the key "space".
  * Preview button allows to create a new document with crosspiece parts without exiting tool. It's convenient to adjust connection parameters.

  
