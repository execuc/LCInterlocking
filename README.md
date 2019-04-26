LCInterlocking
==========

![Illustration](docs/imgs/illustration.png)<br>

Goal
--------------------
This experimental FreeCAD module is used to create interlocking cut parts from 3D to 2D SVG. It was created for laser cutting but can work with CNC router.<br>

**It is not reliable, you have to check parts before doing the laser cut, don't trust it !**

Panel
--------------------
This panel appears when "Laser cut Interlocking" module is selected :
![Illustration](docs/imgs/panel.png)

Tools
--------------------
 * ![Illustration](docs/imgs/box_generator.png) : [Generate box without connection.](docs/box_generator.md)
 * ![Illustration](docs/imgs/interlocking.png) : [Create tabs/slots connection.](docs/interlocking.md) (Interlocking tool)
 * ![Illustration](docs/imgs/crosspiece.png) : [Create node for cross connection.](docs/crosspiece.md) (Crosspiece tool)
 * ![Illustration](docs/imgs/roundedboxgenerator.png) : [Generate rounded box without connection.](docs/rounded_box_generator.md)
 * ![Illustration](docs/imgs/living_hinges.png) : [Create bend surface with living hinges.](docs/living_hinges.md)
 * ![Illustration](docs/imgs/export.png) : [Project parts to 2D plan in order to export in SVG format.](docs/export.md) (Export tool)

Install Notes
--------------------
Download the repository as zip via the button on this website or clone via the command line using #git clone https://github.com/execuc/LCInterlocking .

After download the module must be moved to subfolder mod of the Freecad install directory. 
On Ubuntu 16.04 move the module to /usr/share/freecad-daily/Mod/. In Windows it will probably be something like C:\Program Files\FreeCAD\Mod. 
On Debian 9, the Mod directory is in Home directory/.FreeCAD

If you now restart Freecad, the program will detect the installed module.

Note
--------------------
It is advisable to show the report view and to redirect the python errors on to show module warning/error.

Some videos on older module version
-----------------------------------------
 * Box generator/interlocking/inkscape: https://youtu.be/YGFIdLpdWXE
 * Box tool: https://www.youtube.com/watch?v=wuu_lRsXGd0
 * Rounded box tool:  https://www.youtube.com/watch?v=lEOgZ6k9Vxw
 * Crosspiece: https://www.youtube.com/watch?v=tIchogx5BLE
 * Rounded corner: https://www.youtube.com/watch?v=KSnMxqjA_-Q
 
 Change notes
--------------------
**v1.2: In progress**
 * Fix float entry max value(99.99) bug.
 
**v1.1:**
 * Restore crosspiece dog bones and node options.
 * Add fast preview option for interlocking tool.

**v1.0:**
 * Add a preview button to interlocking and crosspiece tool.
 * All tools can now be reedited.
 * Add support to Python 3 of Freecad 0.18.
 
 Gallery
--------------------
![Illustration](docs/imgs/illustration2.png)<br>
![Illustration](docs/imgs/illustration3.png)<br>
