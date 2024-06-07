import numpy as np
import nibabel as nib
from fury import actor, colormap
import trx.trx_file_memmap as tmm
from dive.csv_tocolors import Colors_csv
class Tract(Colors_csv):

    def __init__(self,bundle,color_list=None, tw=1):
        super().__init__()
        self.colors = color_list
        self.bundle = bundle
        self.tract_width = tw

    def selt_colormap(self,instance):
        self.colors_from_csv = instance

    def with_colormap(self,mask):
        self.pts = [item for sublist in self.bundle for item in sublist]
        nifti_data = mask.get_fdata()
        voxels = np.round(nib.affines.apply_affine(np.linalg.inv(mask.affine), self.pts))
        nifti_dict = {(i, j, k): val for (i, j, k), val in np.ndenumerate(nifti_data)}
        master_color = list(map(lambda vox: nifti_dict[vox[0], vox[1], vox[2]], voxels))
        master_color = np.asarray(master_color).astype(int)
        nb_streams = len(np.unique(self.pts))
        disks_color = [] 
        for i in range(len(master_color)):
            if master_color[i]==0:
                disks_color.append(tuple([0.0,0.0,0.0]))
            else:
                disks_color.append(tuple(self.colors_from_csv[master_color[i]-1]))
        stream_actor = actor.line(self.bundle, fake_tube=True, colors=disks_color,linewidth=self.tract_width)
        return stream_actor
    
    def single_color(self):
        stream_actor = actor.line(self.bundle,colors=self.colors,lod=False,fake_tube = True,linewidth=self.tract_width)
        return stream_actor
    
    def dirrection_color(self):
        
        diff = [np.diff(list(s), axis=0) for s in self.bundle]
        diff = [[d[0]] + list(d) for d in diff]
        orientations = np.asarray([o for d in diff for o in d])
        colorsz_tract = colormap.orient2rgb(orientations)
        stream_actor = actor.line(self.bundle,colors=colorsz_tract,lod=False,fake_tube = True,linewidth=self.tract_width)
        return stream_actor