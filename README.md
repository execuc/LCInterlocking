LCInterlocking
==========

**2019/01: all tools can now be reedited.**

**2019/01: add support to Python 3 of Freecad 0.18.** 

Experimental module for FreeCAD 0.16 and 0.17.

It is not reliable, you have to check parts before doing the laser cut, don't trust it !

Interlocking demonstration : https://youtu.be/YGFIdLpdWXE

![Illustration](https://github.com/execuc/LCInterlocking/blob/master/test/Illustration.png)



Goal
--------------------
This experimental FreeCAD module is used to create interlocking laser cut parts.
For example, a box created by a conventional method of FreeCAD PartDesign. A first feature creates connections
between parts (simple tabs/holes or T-Slots).
A second feature rotate every pieces that belong to the same plane and uses the projection of the Draft module.
The contours of parts may be exported to svg format.


Install Notes
--------------------
Download the repository as zip via the button on this website or clone via the command line using #git clone https://github.com/execuc/LCInterlocking .
After download the module must be moved to subfolder mod of the Freecad install directory. On Ubuntu 16.04 move the module to /usr/share/freecad-daily/Mod/. In Windows it will probably be something like C:\Program Files\FreeCAD\Mod. 
If you now restart Freecad, the program will detect the installed module.

Box generator
--------------------
This tool allows to create 6 faces of box without connection. Each dimensions can be defined. Then connections have to
be defined with the interlocking tool.

Demonstration : https://www.youtube.com/watch?v=wuu_lRsXGd0

Description: The user creates a new document and herafter selects the new work bench "laser cut interlocking".
A box is created by clicking the button with tooltip "create a box without tab". The final box is created with the default dimensions. The exceptions are; width is 53 mm and not 50 mm, outside measure checkbox is unchecked instead checked and the thickness is 4 mm instead of 3 mm. The box is used in some other tutorials.


Rounded box generator
--------------------
This tool allows to create a box from a polygon which has a circumscribed circle. Each dimensions can be defined.
Then connections have to be defined with the interlocking and living hinges tool.

Demonstration : https://www.youtube.com/watch?v=lEOgZ6k9Vxw



Interlocking
--------------------
Each involved part have to be configured (thickness, laser cut beam diameter...). Select part(s) by selected each entire
parts or just a face and click on "Add parts" or "Add same parts". The second button allows to share the same
properties between selected parts avoiding to set manually same properties for each part.
Then, select face(s), kind of join (tab, T-slot or continuous) and click on "Add face(s)" or "Add same faces". "Same
faces" is used to share same tab properties between selected faces.
Click on preview to view result on an other document. Click OK to create new parts in the current document.

Demonstration : https://youtu.be/YGFIdLpdWXE

Test file : LCInterlocking/test/simple_box.fcstd



Crosspiece :
--------------------
Simply select the parts that intersect at 90 degree to create a crosspiece between parts. 

Demonstration : https://www.youtube.com/watch?v=tIchogx5BLE
Test files : LCInterlocking/test/crosspiece.fcstd and LCInterlocking/test/crosspiece2.fcstd



Living hinges
--------------------
This tool is used to make curved laser bend surface. Faces of oriented part which follow are flatened and linked 
with living hinges. Actually curved part must have its radius center equidistant from faces.

Demonstration : https://www.youtube.com/watch?v=KSnMxqjA_-Q

Test file : LCInterlocking/test/simple_hinges.fcstd



SVG export
--------------------
Parts to be exported have to be selected before clicking to this feature. A new document is created with copied parts
and projections on XY plan. Select projections and export it to the Flattened SVG format. You can use inkscape to
remove some unwanted lines (if exist) as line between tab and its parts. To do it, ungroup all, object to path, remove unwanted lines, join
curves with very little tolerance and you can regroup all if you want.

Some details are not correctly drawn with Inkscape (i.e. "circle) in contrary to Corel Draw for example.
**NEW :** Thanks to arkhnchul, ".removeSplitter()" method is used on shape to remove these unwanted lines. If it leads to error,
remove this call in exportPanel.py.


TODO
----
 * Add new interlocking.
 * Optimize.
 * ...
