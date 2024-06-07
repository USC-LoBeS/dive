import re
import vtk
import webcolors
import matplotlib
import numpy as np
import nibabel as nib
from fury import actor,utils
from scipy.ndimage import gaussian_filter
from fury.colormap import colormap_lookup_table
from vtkmodules.vtkRenderingCore import vtkProperty


class load_3dbrain:

    def __init__(self,nifti) -> None:
        self.data = nifti.get_fdata()
        self.threshold = 45
        self.sigma = 0.5
        self.affine = nifti.affine
        self.glass_brain_actor = actor

    # def set_property(self):
    #     self.glass_brain_actor.GetProperty().EdgeVisibilityOn()  
    #     self.glass_brain_actor.GetProperty().VertexVisibilityOff()
    #     self.glass_brain_actor.GetProperty().SetEdgeColor(0.5, 0.5, 0.5)  
    #     glass_material =  self.glass_brain_actor.GetProperty()
    #     glass_material.SetAmbient(1)
    #     glass_material.SetDiffuse(1)
    #     glass_material.SetSpecular(1.0)
    #     glass_material.SetSpecularPower(100.0)
    #     glass_material.SetOcclusionStrength(0.1)
    #     glass_material.SetRenderLinesAsTubes(True)
    #     glass_material.SetMetallic(1)
    #     self.glass_brain_actor.GetProperty().SetRoughness(0)
    #     self.glass_brain_actor.GetProperty().SetOpacity(0.05)

    def loading(self):
        self.data[self.data<self.threshold] = 0
        smooth_data = gaussian_filter(self.data,sigma=self.sigma)
        self.glass_brain_actor = actor.contour_from_roi(self.data,self.affine,color=[0,0,0],opacity=0.08)
        # self.set_property()
        return self.glass_brain_actor


class load_2dbrain:
    def __init__(self,nifti) -> None:
        self.data = nifti.get_fdata()
        # self.data[self.data == 0] = 1000
        self.max_v = min(self.data.shape)      ### not used yet
        self.affine = nifti.affine
        self.mean, self.std = self.data[self.data > 0].mean(), self.data[self.data > 0].std()
        self.value_range = (self.mean - 0.1* self.std, self.mean + 3 * self.std)

    def load_actor(self):
        slice_actor = actor.slicer(self.data,self.affine,self.value_range,opacity=0.9)
        return slice_actor


class Mesh:
    def __init__(self,vtk,color_list=[]) -> None:
        self.vtk = vtk
        self.color_list = color_list

    def property(self):
        property = vtkProperty()
        property.SetColor(self.color_list)
        property.SetOpacity(1.0)
        property.SetRoughness(0.0)
        return property

    def load_mesh(self):
        property = self.property()
        actor_2 = vtk.vtkActor()
        actor_2 = utils.get_actor_from_polydata(self.vtk)
        actor_2.SetProperty(property)
        return actor_2

    def load_mesh_with_colors(self,mask,color_map):
        voxels = nib.affines.apply_affine(np.linalg.inv(mask.affine), self.vtk.points).astype(int)
        shape = mask.get_fdata().shape
        array_3d = np.zeros(shape, dtype=float)
        nifti_dict = {(i, j, k): val for (i, j, k), val in np.ndenumerate(mask.get_fdata())}
        master_color = list(map(lambda vox: nifti_dict[vox[0], vox[1], vox[2]], voxels))
        for index in voxels:
            array_3d[int(index[0]),int(index[1]),int(index[2])] = mask.get_fdata()[index[0],index[1],index[2]]
        roi_dict = np.delete(np.unique(array_3d), 0)
        unique_roi_surfaces = vtk.vtkAssembly()
        color_map = np.asarray(color_map)
        for i, roi in enumerate(roi_dict):
            roi_data = np.isin(array_3d,roi).astype(int)
            roi_surfaces = actor.contour_from_roi(roi_data,mask.affine,color=color_map[i])
            unique_roi_surfaces.AddPart(roi_surfaces)
        return unique_roi_surfaces
        

class Colors:

    def __init__(self):
        self.rgb_decimal_tuple = None
    
    def get_rgb_from_color_name(self,color_name):
        try:
            rgb_tuple = webcolors.name_to_rgb(color_name)
            self.rgb_decimal_tuple = tuple(component / 255.0 for component in rgb_tuple)
            return self.rgb_decimal_tuple
        except ValueError:
            print("Invalid color name:",color_name)
            return None
    
    def hex_to_rgb(self,hex_value):
        rgb_tuple = webcolors.hex_to_rgb(hex_value) #Check Matplotlib
        self.rgb_decimal_tuple = tuple(component / 255.0 for component in rgb_tuple)
        return self.rgb_decimal_tuple

    def string_to_list(self,input_string):
        list_of_lists = []
        cleaned_string = input_string.replace('[', '').replace(']', '').replace('(','').replace(')','')  
        elements = cleaned_string.split(',')
        for element in elements:
            if element.startswith('#'):
                list_of_lists.append(self.hex_to_rgb(element))
            else:
                list_of_lists.append(self.get_rgb_from_color_name(element))
        return list_of_lists
    
    def get_tab20_color(index,type_):
        if type_=='vol':
            tab20_colors = matplotlib.cm.get_cmap('tab20')
        else:
            tab20_colors = matplotlib.cm.get_cmap('Pastel1_r')

        return matplotlib.colors.to_rgb(tab20_colors(index))

    def load_colors(self,colors_path=None):
        dic_colors = {}
        if colors_path==None: return
        with open(colors_path) as colors_file:
            lines = [line.rstrip() for line in colors_file if not line.rstrip().startswith('#')]
        for i in lines:
            match = re.search(r'[a-zA-Z]', i)
            first_alphabet_index = match.start() if match else None
            # Find the index of the last alphabetic character
            last_alphabet_index = None
            for match in re.finditer(r'[a-zA-Z]', i):
                last_alphabet_index = match.start()
            
            key = str(i[first_alphabet_index:last_alphabet_index+1])
            colors_str = i[last_alphabet_index+2:]
            colors_list = colors_str.split()
            colors_list = list(map(int, colors_list))
            rgb_tuple = colors_list[0:-1]
            rgb_decimal_tuple = tuple(component / 255.0 for component in rgb_tuple)
            dic_colors[key] = rgb_decimal_tuple

        return dic_colors
