import io
import sys
import gzip
import json
import random
import zipfile
import argparse
import distinctipy
import numpy as np
import pyvista as pv
import nibabel as nib
from dive.mask import Mask
from dive.tract import Tract
from dive.showman import Show
import trx.trx_file_memmap as tmm
from dive.csv_tocolors import Colors_csv
from nibabel.streamlines import ArraySequence
from dive.helper import load_3dbrain, load_2dbrain, Colors, Mesh
random.seed(1)


def run_main():
    formatter = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(description='Diffusion Visualization Analytics (diVE)', formatter_class=formatter)
    parser.add_argument('--mesh', nargs='+', help='Single or Multple VTK files')
    parser.add_argument('--tract', nargs='+', help='A white matter bundle in TRK, TCK, or TRX format')
    parser.add_argument('--mask', nargs='+', help='A NIfTI binary file can be a single label or multiple labels') 
    parser.add_argument('--output', default=None, help='Path to save screenshots e.g., /home/file_name (--inter should be 0)')
    parser.add_argument('--background', type=int, default=0, help='Choice either black or white Background color choice: 0 for black, 1 for white')
    parser.add_argument('--zoom', type=float, default=0.5, help='Zooming factor for a standard view')
    parser.add_argument('--inter', type=int, default=1, help = 'Enable interactive mode (1) or save screenshots directly (0)')
    parser.add_argument('--stats_csv',type=str,help='Path to a CSV file for mask visualization')
    parser.add_argument('--threshold',type=float,default=0.05, help='Threshold value for visualization')
    parser.add_argument('--log_p_value', type=bool, default=False, help='Use logarithmic p-values (True/False)')
    parser.add_argument('--range_value', nargs=2, type=float, default=None, help='Minimum and maximum values for the value range')
    parser.add_argument('--map', help='Colormap name from Matplotlib', type=str, default = 'RdBu')
    parser.add_argument('--colors_tract', type=str, help='List of colors for tracts')
    parser.add_argument('--colors_mask', type=str, help='List of colors for masks')
    parser.add_argument('--colors_mesh', type=str, help='List of colors for meshes')
    parser.add_argument('--width_tract', type=int, default=1, help='Specify the width of the streamlines')
    parser.add_argument('--brain_2d', nargs='+', help='A NIfTI file for a 2D brain image')
    parser.add_argument('--glass_brain', help = 'A NIfTI binary file for a 3D brain visualization.')
    parser.add_argument('--color_map', default=None, help='A text file specifying colors for each ROI')   
    parser.add_argument('--segmentation_method', type=str, default=False, help="Segmentation method to use (e.g., 'centerline' or 'MeTA').")
    parser.add_argument('--segments', type=str, default=False, help='Number of segments for the segmented streamlines along the length')
    parser.add_argument('--cam_view',default=False,type=str,help='Path to JSON file with view specifications')

    if len(sys.argv) == 1:
        parser.print_help()
        return
    args = parser.parse_args()
    if args.inter == 0:
        interactive = False
    else: interactive = True

    def read_from_compressed(file = None):
        """
        This function reads compressed (zip or gz) TRK or TCK files and returns an object 
        that can be read using nibabel.
        Args:
            file: path to the compressed file
        Returns:
            img: file object to be read by nibabel
        """
        zip_type = file.split('.')[-1]
        if zip_type == 'gz':
            with gzip.open(file) as gf:
                data = gf.read()
                img = io.BytesIO(data)
        elif zip_type == 'zip':
            with zipfile.ZipFile(file, mode="r") as zf:
                f_name = zf.namelist()[0]
                img = zf.open(f_name)
        else:
            print("Wrong zip type. Either '.gz' or '.zip' ")
        return img

    def get_file_name(lst):
        result = []
        for item in lst:
            if item is not None:
                parts = item.split('/')[-1].split('.')[0]
                if parts:
                    result.append(parts)
        if not result:
            result.append(None)

        return result

    colors_caller = Colors()
    tract_color_list = colors_caller.string_to_list(input_string = args.colors_tract) if args.colors_tract else  []
    mask_color_list = colors_caller.string_to_list(input_string = args.colors_mask) if args.colors_mask else []
    vtk_color_list = colors_caller.string_to_list(input_string = args.colors_mesh) if args.colors_mesh else []

    if args.mask==None: args.mask = []
    if args.mesh ==None: args.mesh=[]
    if args.tract ==None: args.tract=[]
    if args.stats_csv:
        list_csvs = args.stats_csv.split(',')

    num_max = max(len(args.mask), len(args.mesh), len(args.tract))
    slice_actor = None
    glass_brain_actor = None
    ui_caller = Show(background=args.background)
    main_scene = ui_caller.define_scene()
    dict_disp = {}
    dict_disp['Mask'] = get_file_name(args.mask)
    dict_disp['Tract'] = get_file_name(args.tract)
    dict_disp['Mesh'] = get_file_name(args.mesh)

    if args.brain_2d is None:
        dict_disp['Brain'] = get_file_name([args.glass_brain])
    else:
        dict_disp['Brain'] = get_file_name([args.glass_brain,args.brain_2d[0]])

    if args.cam_view:
        with open(args.cam_view, 'r') as f:
            view_config = json.load(f)
    else:
        view_config = {}
    matching_keys = []
    for key in view_config:
        bundle_name = dict_disp['Tract'][0] if dict_disp['Tract'] else None
        if not bundle_name:
            bundle_name = dict_disp['Mask'][0] if dict_disp['Mask'] else None
        if key in bundle_name:
            matching_keys.append(key)
    if matching_keys:
        for mk in matching_keys:
            camera_view = view_config[mk]
            print(f"Using camera view: {camera_view}")
    else:
        camera_view = 'Coronal_A'
        print(f"Default camera view: {camera_view}")

    rois = {}
    for i in range(num_max):
        
        flag_multiple = 0
        actor_bundle = actor_vtk = actor_mask = None
        if args.stats_csv:
            if args.stats_csv[i]!=None and len(list_csvs)>i:
                cc = Colors_csv(list_csvs[i])
                color_map_mask = cc.assign_colors(map=args.map,range_value=args.range_value,log_p_value=args.log_p_value,threshold=args.threshold, output=args.output)
        
        ## Load masks
        if i < len(args.mask) and args.mask[i] is not None:
            mask = nib.load(args.mask[i])

            ## Load masks with multiple labels
            if len(np.unique(mask.get_fdata()))>2:
                flag_multiple = 1
                #Load based on stats_csv
                if (args.stats_csv!=None and len(list_csvs)>i):
                    mask_caller = Mask(mask,colormap=color_map_mask)
                    actor_mask,distinctpy_colormask = mask_caller.multi_label()
                    main_scene.add(actor_mask)
                    rois[dict_disp['Mask'][i]] = actor_mask
                else:
                    mask_caller = Mask(mask)
                    actor_mask,distinctpy_colormask = mask_caller.multi_label()
                    main_scene.add(actor_mask)
                    rois[dict_disp['Mask'][i]] = actor_mask

            ## Color masks based on --colors_mask are provided
            elif len(mask_color_list)>i:
                mask_caller = Mask(mask,mask_color_list[i])
                actor_mask = mask_caller.one_label()
                main_scene.add(actor_mask)
                rois[dict_disp['Mask'][i]] = actor_mask

            ## Multiple Colors based on color_map or random
            else:
                ## Color masks with multiple lables based on the color_map
                if args.color_map!=None: 
                    name = args.mask[i].split('/')[-1].split('.')[0]
                    dic_colors = Colors.load_colors()
                    if name in dic_colors:
                        mask_caller = Mask(mask,mask_color_list[i])
                        actor_mask = mask_caller.one_label()
                        main_scene.add(actor_mask)
                        rois[dict_disp['Mask'][i]] = actor_mask
                ## Color masks with multiple lables using random colors
                else: 
                    mask_caller = Mask(mask,Colors.get_tab20_color(index = i, type_='vol'))
                    actor_mask = mask_caller.one_label()
                    main_scene.add(actor_mask)
                    rois[dict_disp['Mask'][i]] = actor_mask
            
        ## Load tractography files:
        if i < len(args.tract) and args.tract[i] is not None:
            ## Load compressed tractography formats (TCK, TRK, etc.)
            if str(args.tract[i]).split('.')[-1] == 'gz' or str(args.tract[i]).split('.')[-1] == 'zip':
                tract_image =  nib.streamlines.load(read_from_compressed(args.tract[i]))
            ## Load TRX file

            if str(args.tract[i]).split('.')[-1] == 'trx':
                tract_image = tmm.load(args.tract[i])
                tract_image.streamlines._data = tract_image.streamlines._data.astype(np.float32)
            ## Load other tractography formats (TCK, TRK, etc.)
            else: tract_image = nib.streamlines.load(args.tract[i])

            ## Used for color N segments of the bundle along its length Based on the csv file (stats_csv) {Not tested/implemented for TRX}
            if flag_multiple ==1:
                bundle_caller = Tract(bundle = tract_image.streamlines,tw=args.width_tract)
                if args.stats_csv!=None and args.stats_csv[i]!=None:
                    bundle_caller.selt_colormap(instance=color_map_mask)
                else: 
                    bundle_caller.selt_colormap(instance=distinctpy_colormask)
                actor_bundle = bundle_caller.with_colormap(mask=mask)
                main_scene.add(actor_bundle)
                rois[dict_disp['Tract'][i]] = actor_bundle

            ## Used for color N segments of the bundle along its length {Not tested/implemented for TRX}
            elif (args.segmentation_method) =="MeTA" or (args.segmentation_method) =="centerline" :
                
                if (np.array_equal(tract_image.affine, np.eye(4))): 
                    print("A reference image is needed since the tract you provided has affine with no traslation will use brain_2d file as the affine")
                    aff = nib.load(args.brain_2d[0]).affine
                else: aff= tract_image.affine
                
                bundle_caller = Tract(bundle = tract_image,tw=args.width_tract,bundle_shape = tract_image.header['dimensions'],aff=aff)
                
                if args.stats_csv:
                    color_map_mask_tracts_paint = color_map_mask
                    bundle_caller.selt_colormap(instance=color_map_mask_tracts_paint)

                actor_bundle = bundle_caller.tracts_paint(method = args.segmentation_method,number_of_streams=int(args.segments))
                main_scene.add(actor_bundle)
                rois[dict_disp['Tract'][i]] = actor_bundle 

            elif len(tract_color_list) > i:
                ## Load bundles with single color if --colors_tract are provided
                bundle_caller = Tract(bundle = tract_image.streamlines,tw=args.width_tract,color_list=tract_color_list[i])
                actor_bundle = bundle_caller.single_color()
                main_scene.add(actor_bundle)
                rois[dict_disp['Tract'][i]] = actor_bundle 

            else:
                if not hasattr(tract_image, 'groups') or len(tract_image.groups) == 0:
                    ## Load the bundle with directional color (for TRX with only one bundle, no groups)
                    ## Support other tractography formats
                    bundle_caller = Tract(bundle = tract_image.streamlines,tw=args.width_tract)
                    actor_bundle = bundle_caller.dirrection_color()
                    main_scene.add(actor_bundle)
                    rois[dict_disp['Tract'][i]] = actor_bundle
                else:
                    ## Special case for multiple bundles in a TRX file 
                    if args.stats_csv==None:
                        color_map_mask = distinctipy.get_colors(len(tract_image.groups))

                    for index, (group_name, group_indices) in enumerate(tract_image.groups.items()):
                        group_streamlines = ArraySequence([tract_image.streamlines[idx] for idx in group_indices])
                       # need to test
                        if args.stats_csv:
                            color_map_mask = []
                            color_map_mask[index] = cc.assign_colors_grp(map=args.map,range_value=args.range_value,log_p_value=args.log_p_value,threshold=args.threshold, output=args.output,group=1)
                        group_tract_caller = Tract(bundle = group_streamlines,tw=args.width_tract,color_list=color_map_mask[index])
                        group_actor_tract = group_tract_caller.single_color()
                        ## Add the actor to the main scene and rois dictionary
                        updated_name = f"{dict_disp['Tract'][i]}_{group_name}"
                        prefix = f"{dict_disp['Tract'][i]}_"
                        if updated_name.startswith(prefix):
                            updated_name = updated_name[len(prefix):]
                        main_scene.add(group_actor_tract)
                        dict_disp['Tract'].append(updated_name)
                        rois[updated_name] = group_actor_tract
                    ## Remove the initial entry of Tract if there are multiple groups
                    if len(tract_image.groups) > 0 and len(dict_disp['Tract']) > len(tract_image.groups):
                        dict_disp['Tract'].pop(i)

        ## Load Mesh files:
        if i < len(args.mesh) and args.mesh[i] is not None:
            if flag_multiple==1:
                mesh_caller = Mesh(pv.PolyData(args.mesh[i]))
                actor_vtk = mesh_caller.load_mesh_with_colors(mask = mask,color_map = distinctpy_colormask)
                main_scene.add(actor_vtk)
                rois[dict_disp['Mesh'][i]] = actor_vtk
            else:
                if args.colors_mesh and args.colors_mesh[i]:
                    mesh_caller = Mesh(pv.PolyData(args.mesh[i]),vtk_color_list[i])
                else:
                    mesh_caller = Mesh(pv.PolyData(args.mesh[i]),color_list=Colors.get_tab20_color(index = i, type_='vtk'))
                actor_vtk = mesh_caller.load_mesh()
                main_scene.add(actor_vtk)
                rois[dict_disp['Mesh'][i]] = actor_vtk

        ## Load 3D glass brain:
        if args.glass_brain and glass_brain_actor is None:
            glass_brain_caller = load_3dbrain(nib.load(args.glass_brain))
            glass_brain_actor = glass_brain_caller.loading()
            main_scene.add(glass_brain_actor)
            rois[dict_disp['Brain'][i]] = glass_brain_actor

        ## Load 2D brain slice:
        if args.brain_2d and slice_actor is None:
            caller_2d = load_2dbrain(nib.load(args.brain_2d[0]))
            slice_actor = caller_2d.load_actor()
            value_min = min(nib.load(args.brain_2d[0]).get_fdata().shape)
            ui_caller.define_maxview(value_min,slice_actor = slice_actor)
            main_scene.add(slice_actor)
            rois[dict_disp['Brain'][i]] = slice_actor

        
    if args.brain_2d and len(args.brain_2d)>1:
        ui_caller.slice_actorvalues(args.brain_2d[1:])

    ui_caller.Showmanger_init(di=dict_disp,rois=rois,interactive=interactive,camera_view=camera_view,output_path=args.output)
