# -*- coding: utf-8 -*-

__title__ = "LasercutterTechdrawExport"
__author__ = "Christian Bergmann"
__license__ = "LGPL 2.1"
__doc__ = "Creates contour lines with for all selected objects and arranges them on a TechDraw page. An offset for the laser beam width will be added."

import os
import FreeCADGui
import FreeCAD as app
from FreeCAD import Vector, Rotation
import Part
import Draft

__dir__ = os.path.dirname(__file__)
iconPath = os.path.join(__dir__, '../icons')
        
class LasercutterTechdrawExportItem:
    def __init__(self, 
                 fp,    # an instance of Part::FeaturePython
                 Part = None,
                 BeamWidth = 0.2,
                 Normal = Vector(0, 0, 1)):
        self.updating = False
        fp.addProperty("App::PropertyLink", "Part",  "LasercutterTechdrawExport",  "Selected part").Part = Part
        fp.addProperty("App::PropertyVector", "Normal",  "LasercutterTechdrawExport",  "What the heck is normal ?").Normal = Normal
        fp.addProperty("App::PropertyFloat", "BeamWidth", "LasercutterTechdrawExport",  "Laser beam width in mm").BeamWidth = BeamWidth
        fp.Proxy = self
#        if len(Parts) == 0:
#            panel = LCTaskPanel(fp)
#            FreeCADGui.Control.showDialog(panel)
    
    def execute(self, fp):
        '''Do something when doing a recomputation, this method is mandatory'''
        if fp.Part and fp.Normal and (not self.updating):
            self.make_outline(fp)
        
    def onChanged(self, fp, prop):
        '''Do something when a property has changed'''
        if prop == "Part" or prop == "BeamWidth" or prop == "Normal":
            self.execute(fp)         
            
    def make_outline(self, fp): 
        self.updating = True 
        face = self.get_biggest_face(fp.Part)
        if face:
            outline = face.makeOffset2D(fp.BeamWidth / 2)
            if fp.Normal == Vector(0, 0, 1):
                fp.Normal = face.normalAt(0, 0)
        else:
            print("no face")
            outline = part.makeOffset(fp.BeamWidth / 2)       
            
        fp.Shape = Part.Compound(outline.Wires);
        fp.Label = fp.Part.Label + " offset"
        
        rotation_to_apply = Rotation(fp.Normal, Vector(0, 0, 1))
        new_rotation = rotation_to_apply.multiply(fp.Placement.Rotation)
        fp.Placement.Rotation = new_rotation
        self.rotate_biggest_side_up(fp)
        self.updating = False
        
    def get_biggest_face(self, part):
        max_area = 0
        for face in part.Shape.Faces:
            if face and face.Area > max_area:
                max_area = face.Area
                max_face = face
    
        if max_face:
            return max_face
        
    def rotate_biggest_side_up(self, fp):
        bbox = fp.Shape.BoundBox
        xmin = bbox.XLength
        angle = 0.0
        r = fp.Placement.Rotation
        while angle < 180:     
            angle = angle + 22.5       
            rotation_to_apply = Rotation(22.5, 0.0, 0.0)
            new_rotation = rotation_to_apply.multiply(fp.Placement.Rotation)
            fp.Placement.Rotation = new_rotation
    
            if xmin > fp.Shape.BoundBox.XLength:
                xmin = fp.Shape.BoundBox.XLength
                r = fp.Placement.Rotation
    
        fp.Placement.Rotation = r
        
        
class LasercutterTechdrawExportItemViewProvider:
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
        pass
        
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
            
        FreeCADGui.doCommand("LasercutterTechdrawExport.makeLasercutterTechdrawExport(parts, BeamWidth = 0.2, doc = App.activeDocument())")
                  

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        if app.activeDocument():
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


def selected_to_techdraw(doc, offsets, techdraw, BeamWidth):
    x = BeamWidth
    y = 0
    
    for offset in offsets:
        bbox = offset.Shape.BoundBox
        bsize = Vector(bbox.XLength, bbox.YLength, bbox.ZLength)
        
        # add a 2D view to the TechDraw page right of the last part
        maxheight = y + bsize.y + BeamWidth
        if maxheight > techdraw.Template.Height:
            techdraw.Template.Height = maxheight

        maxwidth = x + bsize.x + BeamWidth
        if maxwidth > techdraw.Template.Width:
            techdraw.Template.Width = maxwidth

        viewname = offset.Label.replace("offset", "contour")
        views = doc.getObjectsByLabel(viewname)
        if len(views) > 0:
            view = views[0]
        else:
            view = doc.addObject('TechDraw::DrawViewPart', viewname)
            techdraw.addView(view)
            
        view.CoarseView = False
        view.ViewObject.LineWidth = BeamWidth
        view.Source = offset
        view.Direction = Vector(0, 0, 1)
        view.ScaleType = u"Custom"
        view.Scale = 1.00
        view.X = x + bsize.x / 2
        view.Y = y + bsize.y - (bsize.y / 2)
        x = x + bsize.x + BeamWidth
              

def makeLasercutterTechdrawExport(parts, BeamWidth = 0.2, doc = app.activeDocument()):   
    techdraw = doc.addObject('TechDraw::DrawPage','LasercutterTechdraw')
    template = doc.addObject('TechDraw::DrawSVGTemplate','Template')
    techdraw.Template = template
    
    contours = []
    for p in parts:  
        ifp = doc.addObject("Part::FeaturePython", "LasercutterTechdrawExport")
        LasercutterTechdrawExportItem(ifp, p, BeamWidth)
        LasercutterTechdrawExportItemViewProvider(ifp.ViewObject)  
        contours.append(ifp)   
    
    LaserCutterExportObjects = doc.addObject('App::DocumentObjectGroup', 'LaserCutterExportObjects')
    LaserCutterExportObjects.Group = contours
    LaserCutterExportObjects.ViewObject.hide()
    doc.recompute()
    selected_to_techdraw(doc, contours, techdraw, BeamWidth)
    doc.recompute()
    techdraw.ViewObject.show()
