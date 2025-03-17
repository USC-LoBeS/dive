import re
import vtk
import webcolors
import matplotlib
import numpy as np
from tqdm import tqdm
import nibabel as nib
from fury import actor,utils
from tslearn.metrics import dtw_path
from scipy.ndimage import gaussian_filter
from dipy.tracking.streamline import length
# from dipy.io.streamline import load_tractogram
from dipy.segment.clustering import QuickBundles
from vtkmodules.vtkRenderingCore import vtkProperty
from dipy.segment.featurespeed import ResampleFeature
from dipy.segment.metric import AveragePointwiseEuclideanMetric
from dipy.tracking.streamline import length, transform_streamlines


class load_3dbrain:
    def __init__(self,nifti) -> None:
        self.data = nifti.get_fdata()
        self.threshold = 45
        self.sigma = 0.5
        self.affine = nifti.affine
        self.glass_brain_actor = actor

    def loading(self):
        self.data[self.data<self.threshold] = 0
        smooth_data = gaussian_filter(self.data,sigma=self.sigma)
        self.glass_brain_actor = actor.contour_from_roi(self.data,affine = self.affine,color=[0,0,0],opacity=0.08)
        # self.set_property()
        return self.glass_brain_actor

class load_2dbrain:
    def __init__(self,nifti) -> None:
        self.data = nifti.get_fdata()
        self.affine = nifti.affine
        self.mean, self.std = self.data[self.data > 0].mean(), self.data[self.data > 0].std()
        self.value_range = (self.mean - 0.1* self.std, self.mean + 3 * self.std)

    def load_actor(self):
        slice_actor = actor.slicer(self.data,affine = self.affine,value_range=self.value_range,opacity=0.9)
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
        for index in voxels:
            array_3d[int(index[0]),int(index[1]),int(index[2])] = mask.get_fdata()[index[0],index[1],index[2]]
        roi_dict = np.delete(np.unique(array_3d), 0)
        unique_roi_surfaces = vtk.vtkAssembly()
        color_map = np.asarray(color_map)
        for i, roi in enumerate(roi_dict):
            roi_data = np.isin(array_3d,roi).astype(int)
            roi_surfaces = actor.contour_from_roi(roi_data,affine=mask.affine,color=color_map[i],opacity=1)
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

## The following functions copied from Medial Tractography Analysis (MeTA) repository: https://github.com/bagari/meta
def reorient_streamlines(m_centroid, s_centroids):
    """
    Reorients the subject centroids based on the model centroid.
    Args:
        m_centroid (np.ndarray): Model centroid
        s_centroids (list): List of subject centroids
    Returns:
        oriented_s_centroids (list): List of reoriented subject centroids
    """

    def is_flipped(m_centroid, s_centroid):
        """
        checks if subjects centroid is flipped compared to the model centroid.
        """
        start_distance = np.linalg.norm(m_centroid[0] - s_centroid[-1])
        start = np.linalg.norm(m_centroid[-1] - s_centroid[0])

        end_distance = np.linalg.norm(m_centroid[-1] - s_centroid[-1])
        end = np.linalg.norm(m_centroid[0] - s_centroid[0])

        if (start_distance < end_distance) and (start < end):
            return True
        return False

    oriented_s_centroids = []
    for s_centroid in s_centroids:
        if is_flipped(m_centroid, s_centroid):
            oriented_s_centroids.append(s_centroid[::-1])
        else:
            oriented_s_centroids.append(s_centroid)

    return oriented_s_centroids

def perform_dtw(model_bundle, subject_bundle, num_segments, affine=None):
    """
    This function performs Dynamic Time Warping (DTW) on two tractogram (.trk)
    files in same space.

    Args:
        tbundle (str): path to a template .trk file
        sbundle (str): Path to a subject .trk file
        num_segments (int): number of points (N+1) of template centroid to segment the bundle (N)

    Returns:
        dict: dictionary containing the corresponding points.
    """

    # reference_image = nib.load(mask_img)

    ## Trasform the Template bundle to the subject space world cordinates and then to the subject voxel space cordinates:
    ##load_tractogram(model_bundle, "same", bbox_valid_check=False)
    model_streamlines = model_bundle.streamlines
    transformed_model_bundles = transform_streamlines(model_streamlines, np.linalg.inv(affine))

    m_feature = ResampleFeature(nb_points=num_segments)
    m_metric = AveragePointwiseEuclideanMetric(m_feature)
    m_qb = QuickBundles(threshold=np.inf, metric=m_metric)
    m_centroid = m_qb.cluster(transformed_model_bundles).centroids
    print('Model: Centroid length... ', np.mean([length(streamline) for streamline in m_centroid]))

    ## Trasform the Subject bundle to the subject voxel cordinates:
    subject_streamlines = subject_bundle.streamlines
    transformed_subject_bundles = transform_streamlines(subject_streamlines, np.linalg.inv(affine))
    s_feature = ResampleFeature(nb_points=500)
    s_metric = AveragePointwiseEuclideanMetric(s_feature)
    s_qb = QuickBundles(threshold=np.inf, metric=s_metric)
    s_centroid = s_qb.cluster(transformed_subject_bundles).centroids
    print('Subject: Centroid length... ', np.mean([length(streamline) for streamline in s_centroid]))

    ## Create multiple centroids from subject bundle using QuickBundles
    num_clusters = 10
    feature = ResampleFeature(nb_points=500)
    metric = AveragePointwiseEuclideanMetric(feature)
    qb = QuickBundles(threshold=2., metric=metric, max_nb_clusters=num_clusters)
    centroids = qb.cluster(transformed_subject_bundles).centroids

    ## Check if the centroids are flipped compared to the model centroid
    s_centroid = reorient_streamlines(m_centroid, s_centroid)
    centroids = reorient_streamlines(m_centroid, centroids)

    ## Compute the correspondence between the model and the subject centroids using DTW
    dtw_corres = []
    for idx, (m_centroid, s_centroid) in enumerate(zip(m_centroid, s_centroid)):
        pathDTW, similarityScore = dtw_path(m_centroid, s_centroid)
        x1, y1, z1 = m_centroid[:, 0], m_centroid[:, 1], m_centroid[:, 2]
        x2, y2, z2 = s_centroid[:, 0], s_centroid[:, 1], s_centroid[:, 2]
        corres = dict()
        for (i, j) in pathDTW:
            key = (x1[i], y1[i], z1[i])
            value = (x2[j], y2[j], z2[j])
            if key in corres:
                corres[key].append(value)
            else:
                corres[key] = [value]
        centroid_corres = []
        for key in corres.keys():
            t = len(corres[key]) // 2
            centroid_corres.append(corres[key][t])
        dtw_corres.append(np.array(centroid_corres))

    ## Establish correspondence between dtw_corres and centroids of the subject bundle
    s_corres = []
    for idx, centroid in enumerate(centroids):

        s_centroid = np.squeeze(centroid)
        s_ref  = np.squeeze(dtw_corres)
        pathDTW, similarityScore = dtw_path(s_ref, s_centroid)
        x1, y1, z1 = s_ref[:, 0], s_ref[:, 1], s_ref[:, 2]
        x2, y2, z2 = s_centroid[:, 0], s_centroid[:, 1], s_centroid[:, 2]
        corres = dict()
        for (i, j) in pathDTW:
            key = (x1[i], y1[i], z1[i])
            value = (x2[j], y2[j], z2[j])
            if key in corres:
                corres[key].append(value)
            else:
                corres[key] = [value]

        centroid_corres = []
        for key in corres.keys():
            t = len(corres[key]) // 2
            centroid_corres.append(corres[key][t])
        s_corres.append(np.array(centroid_corres))

    ## combine correspondences
    combined_corres = dtw_corres + s_corres

    ## Remove centroids that are shorter than the threshold
    data = []
    for streamline in combined_corres:
        data.append(length(streamline))
    mean_length = np.mean(data)
    std_length = np.std(data)
    print("Average streamlines length", np.mean(data))
    print("Standard deviation", std_length)
    threshold = mean_length - 1 * std_length
    indices = np.where(data < threshold)
    final_corres = [sl for idx, sl in enumerate(combined_corres) if idx not in indices[0]]

    ## Compute pairwise distances between corresponding points of the final centroids
    corresponding_points = np.array(final_corres)
    pairwise_distances = np.zeros((corresponding_points.shape[1], corresponding_points.shape[0], corresponding_points.shape[0]))
    for i in range(corresponding_points.shape[1]):
        for j in range(corresponding_points.shape[0]):
            for k in range(j + 1, corresponding_points.shape[0]):
                pairwise_distances[i, j, k] = np.linalg.norm(corresponding_points[j, i] - corresponding_points[k, i])
    pairwise_distances[pairwise_distances == 0] = np.nan
    mean_distances = np.nanmean(pairwise_distances, axis=(1, 2))
    std_distances = np.nanstd(pairwise_distances, axis=(1, 2))
    excluded_idx = np.where(std_distances <= 3.5)[0]

    ## Filter the final_corres based on pairwise distances that have std <= 3.5
    excluded_start = excluded_idx[0]
    excluded_end = excluded_idx[-1]

    filtered_arrays = []
    for idx, array in enumerate(final_corres):
        combined_array = []
        if excluded_start > 1:
            start_point = array[0]
            end_point = array[excluded_start]
            side_1_points = np.linspace(start_point, end_point, excluded_start + 1)[1:-1]
            combined_array.extend(array[0:1])
            combined_array.extend(side_1_points)
        elif excluded_start <= 1:
            combined_array.extend(array[0:excluded_start])
        combined_array.extend(array[excluded_start:excluded_end+1])
        if num_segments - excluded_end > 1:
            start_point = array[excluded_end]
            end_point = array[-1]
            side_2_points = np.linspace(start_point, end_point, num_segments - excluded_end)[1:-1]
            combined_array.extend(side_2_points)
            combined_array.extend(array[-1:])
        elif num_segments - excluded_end == 1:
            combined_array.extend(array[-1:])

        filtered_arrays.append(np.array(combined_array))
    print("Total number filtered centroids:", len(filtered_arrays))
    return filtered_arrays



def segment_bundle(bundle_data, dtw_points_sets, num_segments):
    """
    Parcellate white matter bundle into num_segments based on DTW points.

    Parameters:
    -----------
    bundle_data: A bundle mask as a NumPy array.
    dtw_points_sets: list of ndarrays of shape (num_segments, 3) which are the corresponding DTW points.
    num_segments (int): required number of segments.

    Returns:
    --------
    segments: A list of labels, where each label corresponds to a segment.
    """
    segments = [np.zeros_like(bundle_data, dtype=bool) for _ in range(num_segments+1)]

    for dtw_points in tqdm(dtw_points_sets):
        for i in range(num_segments):
            if i == 0:
                plane_normal = (dtw_points[i+1] - dtw_points[i]).astype(float)
                for x, y, z in np.argwhere(bundle_data):
                    point = np.array([x, y, z])
                    if np.dot(point - dtw_points[i], -plane_normal) >= 0:
                        segments[i][x, y, z] = True

            ## 1st plane >>>
            if i < num_segments - 2 and i >= 0:
                plane_normal = (dtw_points[i+1] - dtw_points[i]).astype(float)
                next_plane_normal = (dtw_points[i+1 + 1] - dtw_points[i+1]).astype(float)
                for x, y, z in np.argwhere(bundle_data):
                    point = np.array([x, y, z])
                    if np.dot(point - dtw_points[i], plane_normal) >= 0 and np.dot(point - dtw_points[i+1], -next_plane_normal) >= 0:
                        segments[i+1][x, y, z] = True

            ## 2nd plane - end
            elif i == num_segments - 2:
                plane_normal = (dtw_points[i] - dtw_points[i-1]).astype(float)
                for x, y, z in np.argwhere(bundle_data):
                    point = np.array([x, y, z])
                    if np.dot(point - dtw_points[i-1], plane_normal) >= 0:
                        segments[i+1][x, y, z] = True

            ## end plane >>>
            elif i == num_segments - 1:
                plane_normal = (dtw_points[i] - dtw_points[i-1]).astype(float)
                for x, y, z in np.argwhere(bundle_data):
                    point = np.array([x, y, z])
                    if np.dot(point - dtw_points[i], plane_normal) >= 0:
                        segments[i+1][x, y, z] = True

    ######## catching remaining voxels ########
    arrays = np.array(segments)
    sum_array = np.sum(arrays, axis=0)
    remaining_voxels = sum_array.copy()
    if np.any(remaining_voxels):
        for x, y, z in np.argwhere(sum_array >= 2):
            for seg in segments:
                seg[x, y, z] = False
            point = np.array([x, y, z])
            min_distance = float('inf')
            closest_segment_idx = None
            for dtw_points in dtw_points_sets:
                for i in range(num_segments):
                    distance_to_start = np.linalg.norm(point - dtw_points[i])
                    if distance_to_start < min_distance:
                        min_distance = distance_to_start
                        closest_segment_idx = i
            if closest_segment_idx is not None:
                segments[closest_segment_idx][x, y, z] = True
    return segments

def create_mask_from_trk(streams, shape):
    # Load TRK file
    # streams, header = trackvis.read(trk_file)

    # Create an empty mask
    transformed_streamlines = transform_streamlines(streams.streamlines, np.linalg.inv(streams.affine))
    mask = np.zeros(shape, dtype=np.uint8)

    # Iterate through each stream in the tractography data
    for stream in transformed_streamlines:
        # Convert stream coordinates to integer indices
        for point in stream:
            x, y, z = np.round(point).astype(int)
            # Check if the point is within the mask dimensions
            if 0 <= x < shape[0] and 0 <= y < shape[1] and 0 <= z < shape[2]:
                mask[x, y, z] = 1  # Mark this voxel in the mask
    return mask

from dipy.tracking import utils

def bundle_density(streams,ref_shape,ref_affine):

    streamlines = streams.streamlines
    
    # Upsample Streamlines
    max_seq_len = abs(ref_affine[0, 0] / 4)
    streamlines = list(utils.subsegment(streamlines, max_seq_len))
    # Create Density Map
    dm = utils.density_map(streamlines, vol_dims=ref_shape, affine=ref_affine)
    # Create Binary Map
    dm_binary = dm > 0

    dm_binary_img = nib.Nifti1Image(dm_binary.astype("uint8"), ref_affine)
    return dm_binary_img
