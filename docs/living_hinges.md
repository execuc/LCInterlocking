Living hinges
===========

This tool is used to make curved laser bend surface. Faces of oriented part which follow are flattened and linked with living hinges. Actually curved part must have its radius center equidistant from faces.

Procedure
-------------

For the example we will start from a rounded box created from th corresponding tool :
![Illustration](imgs/livinghinges/makeroundedbox.png)
<br>

 * Select the right face of the first part and then the left face of the second and click on "Add connexion"
![Illustration](imgs/livinghinges/hinge1.png)
<br>

 * Select the right face of the second and then the left face of the third and "Add connexion". Continue with all corners you want in the same order of selection.
![Illustration](imgs/livinghinges/hinge2.png)
<br>

 * Adjust parameters and click on OK. A "living_hinges" group is created with the flatten part and part with solid corner (for visualization). The flatten part can be exported via the export tool.
![Illustration](imgs/livinghinges/final.png)
<br>

Note:

 * Properties can be edited again by clicking to the group.
 * In this example, first part will be added twice because it is referenced as first and as last item in connections. To make it works, first part has to be cut in two parts. Rounded bow generator can do it with  "NB cut" parameter to >= 1.
