import vtk
import random
import distinctipy
import numpy as np
from fury import actor

random.seed(1)

class Mask:

    def __init__(self,mask,color_list=None,colormap=[]):
        self.mask = mask
        self.pts = self.mask.get_fdata()
        self.sys_affine = mask.affine
        self.colors = color_list
        self.colormap = colormap
    
    def one_label(self):
        if (np.delete(np.unique(self.pts), 0)==1):
            nifti_real = self.pts == 1
        else:
            nifti_real = self.pts > 1
        
        if self.colors:
            volume_actor = actor.contour_from_roi(nifti_real,affine=self.sys_affine,color=self.colors)
        else:
            volume_actor = actor.contour_from_roi(nifti_real,affine=self.sys_affine,color=[0.5,0.5,0.5])
        return volume_actor
    
    def multi_label(self):
        roi_dict = np.delete(np.unique(self.pts), 0)
        nb_surfaces = len(roi_dict)
        unique_roi_surfaces = vtk.vtkAssembly()
        if len(self.colormap)==0:
            self.colormap = distinctipy.get_colors(nb_surfaces)
        self.colormap = np.asarray(self.colormap)
        for i, roi in enumerate(roi_dict):
            roi_data = np.isin(self.pts,roi).astype(int)
            roi_surfaces = actor.contour_from_roi(roi_data,self.sys_affine,color=self.colormap[i])
            unique_roi_surfaces.AddPart(roi_surfaces)
        return unique_roi_surfaces,self.colormap