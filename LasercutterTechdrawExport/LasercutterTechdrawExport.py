# -*- coding: utf-8 -*-

__title__ = "LasercutterTechdrawExport"
__author__ = "Christian Bergmann"
__license__ = "LGPL 2.1"
__doc__ = "Creates contour lines with for all selected objects and arranges them on a TechDraw page. An offset for the laser beam width will be added."

import os
import FreeCADGui
import FreeCAD
from FreeCAD import Vector
import Part
import Draft

__dir__ = os.path.dirname(__file__)
iconPath = os.path.join(__dir__, '../icons')
    
class LasercutterTechdrawExportWorker:
    def __init__(self, 
                 fp,    # an instance of Part::FeaturePython
                 TechdrawPage = None,
                 Parts = [],
                 BeamWidth = 0.2):
        fp.addProperty("App::PropertyLink", "TechdrawPage",  "LasercutterTechdrawExport",  "Selected parts").TechdrawPage = TechdrawPage
        fp.addProperty("App::PropertyLinkList", "Parts",  "LasercutterTechdrawExport",  "Selected parts").Parts = Parts
        fp.addProperty("App::PropertyFloat", "BeamWidth", "LasercutterTechdrawExport",  "Laser beam width in mm").BeamWidth = BeamWidth
        fp.Proxy = self
#        if len(Parts) == 0:
#            panel = LCTaskPanel(fp)
#            FreeCADGui.Control.showDialog(panel)
    
    def execute(self, fp):
        '''Do something when doing a recomputation, this method is mandatory'''
        selected_to_techdraw(fp.Parts, fp.TechdrawPage, fp.BeamWidth)
        
    def onChanged(self, fp, prop):
        '''Do something when a property has changed'''
        if prop == "Parts" or prop == "BeamWidth":
            selected_to_techdraw(fp.Parts, fp.TechdrawPage, fp.BeamWidth)


class LasercutterTechdrawExportViewProvider:
    def __init__(self, vobj):
        '''Set this object to the proxy object of the actual view provider'''
        vobj.Proxy = self
        self.Object = vobj.Object
            
    def getIcon(self):
        '''Return the icon which will FreeCADear in the tree view. This method is optional and if not defined a default icon is shown.'''
        return (os.path.join(iconPath, "LasercutterTechdrawExport.svg"))

    def attach(self, vobj):
        '''Setup the scene sub-graph of the view provider, this method is mandatory'''
        self.Object = vobj.Object
        self.onChanged(vobj, "Base")
 
    def updateData(self, fp, prop):
        '''If a property of the handled feature has changed we have the chance to handle this here'''
        pass
    
    def claimChildren(self):
        '''Return a list of objects that will be modified by this feature'''
        return self.Object.Parts + [self.Object.TechdrawPage]
        
    def onDelete(self, feature, subelements):
        '''Here we can do something when the feature will be deleted'''
        return True
    
    def onChanged(self, fp, prop):
        '''Here we can do something when a single property got changed'''
        pass
        
    def setEdit(self, vobj=None, mode=0):
#        if mode == 0:
#            self.panel = LCTaskPanel(self.Object)
#            FreeCADGui.Control.showDialog(self.panel)
        return False
        
    def __getstate__(self):
        '''When saving the document this object gets stored using Python's json module.\
                Since we have some un-serializable parts here -- the Coin stuff -- we must define this method\
                to return a tuple of all serializable objects or None.'''
        return None
 
    def __setstate__(self,state):
        '''When restoring the serialized object from document we have the chance to set some internals here.\
                Since no data were serialized nothing needs to be done here.'''
        return None
        
        
class LCTaskPanel:
    def __init__(self, fp):
        self.fp = fp
        # this will create a Qt widget from our ui file
        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(__dir__, 'lasercuttersvg.ui'))
        self.form.pushButtonAdd.pressed.connect(self.selectPart)
        self.form.pushButtonRemove.pressed.connect(self.removePart)
        self.form.pushButtonCreate.pressed.connect(self.action)
 
    def accept(self):
        selected_to_techdraw(fp.Parts, fp.TechdrawPage, fp.BeamWidth)
        FreeCADGui.Control.closeDialog()
       
    def selectPart(self):
        selection = FreeCADGui.Selection.getSelectionEx()
               
    def removePart(self):
        pass
    
    def action(self):
        pass
        
class LasercutterTechdrawExport():
    '''This class will be loaded when the workbench is activated in FreeCAD. You must restart FreeCAD to FreeCADly changes in this class'''  
      
    def Activated(self):
        '''Will be called when the feature is executed.'''
        # Generate commands in the FreeCAD python console to create LasercutterTechdrawExport
        FreeCADGui.doCommand("from LasercutterTechdrawExport import LasercutterTechdrawExport")
        
        FreeCADGui.doCommand("parts = []")
        selection = FreeCADGui.Selection.getSelectionEx()
        for sel in selection:
            FreeCADGui.doCommand("parts.append(FreeCAD.ActiveDocument.getObject('%s'))"%(sel.ObjectName))
            
        FreeCADGui.doCommand("LasercutterTechdrawExport.makeLasercutterTechdrawExport(parts)")
                  

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        if FreeCAD.ActiveDocument:
            return(True)
        else:
            return(False)
        
    def GetResources(self):
        '''Return the icon which will FreeCADear in the tree view. This method is optional and if not defined a default icon is shown.'''
        return {'Pixmap'  : os.path.join(iconPath, "LasercutterTechdrawExport.svg"),
                'Accel' : "", # a default shortcut (optional)
                'MenuText': "Lasercutter Techdraw Export",
                'ToolTip' : __doc__ }

FreeCADGui.addCommand('LasercutterTechdrawExport', LasercutterTechdrawExport())



# creates contourlines for all selected objects to a TechDraw page
def make_offset_parts(doc, cutterDiameter):
    selection = FreeCADGui.Selection.getSelection()
    if not selection:
        print("nothing selected !")
        return

    if not selection[0].Shape:
        print("selected part has no shape !")
        return

    offsets = []
    for sel in selection:
        # create a contour line object for every selected object
        offset = doc.addObject("Part::Offset", sel.Label + "_offset")
        offset.Source = Draft.clone(sel)
        offset.Value = cutterDiameter / 2
        offset.Mode = 0
        offset.Join = 2
        offset.Intersection = False
        offset.SelfIntersection = False
        offset.ViewObject.Visibility=False
        doc.recompute()

        # rotate biggest face into xy-plane
        face = get_biggest_face(offset)
        if face is not None:
            rotate_face_up(offset, face)
            rotate_biggest_side_up(offset, face)

        offsets.append(offset)
     
    return offsets


def selected_to_techdraw(offsets, techdraw, BeamWidth):
    doc = FreeCAD.ActiveDocument
    x = BeamWidth
    y = 0
    
    for offset in offsets:
        bbox = offset.Shape.BoundBox
        # add a 2D view to the TechDraw page right of the last part
        maxheight = y + bbox.YLength + BeamWidth
        if maxheight > techdraw.Template.Height:
            techdraw.Template.Height = maxheight

        maxwidth = x + bbox.XLength + BeamWidth
        if maxwidth > techdraw.Template.Width:
            techdraw.Template.Width = maxwidth

        viewname = offset.Label.replace("offset", "contour")
        view = doc.getObject(viewname)
        if not view:
            view = doc.addObject('TechDraw::DrawViewPart', viewname)
            techdraw.addView(view)
            
        view.CoarseView = True
        view.ViewObject.LineWidth = BeamWidth
        view.Source = offset
        view.Direction = Vector(0, 0, 1)
        view.ScaleType = u"Custom"
        view.Scale = 1.00
        view.X = x + bbox.XLength / 2
        view.Y = y + bbox.YLength - (bbox.YLength / 2)
        x = x + bbox.XLength + BeamWidth
        

def get_biggest_face(part):
    max_area = 0
    max_face = None
    for face in part.Shape.Faces:
        if face.Area > max_area:
            max_area = face.Area
            max_face = face

    return max_face


# rotate face into xy-plane
def rotate_face_up(part_feature, face):
    normal_ref = face.normalAt(0, 0)
    rotation_to_FreeCADly = FreeCAD.Rotation(normal_ref, Vector(0, 0, 1))
    new_rotation = rotation_to_FreeCADly.multiply(part_feature.Placement.Rotation)
    part_feature.Placement.Rotation = new_rotation


def rotate_biggest_side_up(part_feature, face):
    bbox = part_feature.Shape.BoundBox
    xmin = bbox.XLength
    anglemax = 0.0
    angle = 0.0
    while angle < 180:
        Draft.rotate([part_feature], 22.5, Vector(bbox.XMin, bbox.YMin, bbox.ZMin), axis=Vector(0.0,0.0,1.0), copy=False)
        angle = angle + 22.5

        if xmin > part_feature.Shape.BoundBox.XLength:
            xmin = part_feature.Shape.BoundBox.XLength
            anglemax = angle

    Draft.rotate([part_feature], 180 + anglemax, Vector(0.0,0.0,0.0), axis=Vector(0.0,0.0,1.0), copy=False)


def makeLasercutterTechdrawExport(parts, BeamWidth = 0.2):   
    doc = FreeCAD.ActiveDocument
    techdraw = doc.addObject('TechDraw::DrawPage','LasercutterTechdraw')
    template = doc.addObject('TechDraw::DrawSVGTemplate','Template')
    techdraw.Template = template
    
    offset_parts = []
    if len(parts) > 0:       
        offset_parts = make_offset_parts(doc, BeamWidth)
        selected_to_techdraw(offset_parts, techdraw, BeamWidth)
    
    fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "LasercutterTechdrawExport")
    LasercutterTechdrawExportWorker(fp, techdraw, offset_parts, BeamWidth)
    LasercutterTechdrawExportViewProvider(fp.ViewObject)
    FreeCAD.ActiveDocument.recompute()
    techdraw.ViewObject.show()
    return fp
