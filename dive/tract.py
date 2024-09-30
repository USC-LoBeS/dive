import distinctipy
import random
import numpy as np
import nibabel as nib
from fury import actor, colormap
from scipy import stats
from scipy.spatial import cKDTree
import trx.trx_file_memmap as tmm
from dive.csv_tocolors import Colors_csv
from dipy.segment.clustering import QuickBundles
from dipy.segment.metric import AveragePointwiseEuclideanMetric
from dipy.tracking.streamline import (Streamlines,set_number_of_points)
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
            
    def assignment_map_(self,target_bundle, model_bundle, no_disks,threshold=None,method=None):
        """
        Calculates assignment maps of the target bundle with reference to
        model bundle centroids.
        Parameters
        ----------
        target_bundle : streamlines
            target bundle extracted from subject data in common space
        model_bundle : streamlines
            atlas bundle used as reference
        no_disks : integer, optional
            Number of disks used for dividing bundle into disks.

        Returns
        -------
        indx : ndarray
            Assignment map of the target bundle streamline point indices to the
            model bundle centroid points.

        """

        mbundle_streamlines = set_number_of_points(model_bundle, nb_points=no_disks)

        metric = AveragePointwiseEuclideanMetric()
        if method=="Center":
            qb = QuickBundles(threshold=threshold, metric=metric)
            k=1
        clusters = qb.cluster(mbundle_streamlines)
        centroids = Streamlines(clusters.centroids)

        _, indx = cKDTree(centroids.get_data(), 1, copy_data=True).query(
            target_bundle.get_data(), k=k
        )


        return indx
    
    def tracts_paint(self,method,number_of_streams):
        # print("AT TractPaint")

        if len(self.colors_from_csv)>1: nb_streams = len(self.colors_from_csv)
        else: nb_streams = number_of_streams
        if method=="Center": 
            indx = self.assignment_map_(self.bundle, self.bundle, nb_streams,threshold=np.inf,method="Center")  
        indx = np.array(indx)
        # print(np.unique(indx))
        if len(self.colors_from_csv)<1:
            colors = distinctipy.get_colors(nb_streams)
        else:
            colors = self.colors_from_csv
        disks_color = []
        if method=="Center":
            for i in range(len(indx)):
                disks_color.append(tuple(colors[indx[i]]))
        # print(disks_color)
        stream_actor = actor.line(self.bundle, fake_tube=True, colors=disks_color,linewidth=self.tract_width)
        return stream_actor
