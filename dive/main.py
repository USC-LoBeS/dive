import io
import sys
import gzip
import zipfile
import argparse
import numpy as np
import pyvista as pv
import nibabel as nib
from dive.mask import Mask
from dive.tract import Tract
from dive.showman import Show
import trx.trx_file_memmap as tmm
from dive.csv_tocolors import Colors_csv
from dive.helper import load_3dbrain, load_2dbrain, Colors, Mesh
import distinctipy
import random
random.seed(1)
# from dipy.io.image import load_nifti

def run_main():
    formatter = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(description='Diffusion Visualization Analytics (diVE) BY Siddharth Narula, Iyad Ba Gari', formatter_class=formatter)
    parser.add_argument('--mesh',nargs='+', help='Single or Multple VTK files')
    parser.add_argument('--tract',nargs='+', help='The corresponding tract file, if only tract is provided then Visualize it according to directions, if a multi labeled mask is given then loads it according to the same colors.')
    parser.add_argument('--mask',nargs='+',help='The corresponding mask/nii.gz file, if only 1 label is present then loads it as single color else multiple colors, each color according to the labels.')
    parser.add_argument('--output',help='Path for output, to save the screenshots, or direct output')
    parser.add_argument('--background',default=0,type=int, help='Choice either black or white')
    parser.add_argument('--zoom',default=0.5,type=float,help='Zooming Factor for a standard view')
    parser.add_argument('--inter',help = 'Have a window of interactive file or just save the screenshots at the path provided.',default=1,type=int)
    parser.add_argument('--stats_csv',type=str,help='Provide path of a csv to visualize Mask')
    parser.add_argument('--threshold',type=float,default=0.05)
    parser.add_argument('--log_p_value',default=False,type=bool)
    parser.add_argument('--range_value',help='Min and Max values for the value range',nargs=2,type=float,default=None)
    parser.add_argument('--map',help='Colormap name from matplotlib',type=str, default = 'RdBu')
    parser.add_argument('--colors_tract',type=str,help='List of Colors for Tract')
    parser.add_argument('--colors_mask',type=str,help='List of Colors for Mask')
    parser.add_argument('--colors_mesh',type=str,help='List of Colors for Mesh')
    parser.add_argument('--width_tract',type=int,help='Specify the width of stremline', default=1)
    parser.add_argument('--brain_2d',nargs='+',help='A nifti.gz file for the brain you want to put at the back of tracts.')
    parser.add_argument('--glass_brain',help = 'A nifti.gz for the brain file to be loaded as a 3d brain.')
    parser.add_argument('--color_map',default=None,help='A text file with colors for each ROI')   
    parser.add_argument('--tracts_paint',default=False,type=bool,help='Run with tracts_paint')
   
    if len(sys.argv) == 1:
        parser.print_help()
        return
    args = parser.parse_args()
    if args.inter == 0:
        interactive = False
    else: interactive = True

    rois = {}

    def read_from_compressed(file = None):
        """
        Args:
            file: path to the compressed file

        Returns:
            img: file object to be read by nibabel
        This function reads compressed (zip or gz) TRK or TCK files and returns an object 
        that can be read using nibabel
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
        print(list_csvs[0])

    numb = max(len(args.mask), len(args.mesh), len(args.tract))
    slice_actor = None
    glass_brain_actor = None
    ui_caller = Show(background=args.background)
    main_scene = ui_caller.define_scene()
    dict_disp = {}
    dict_disp['Mask'] = get_file_name(args.mask)
    dict_disp['Tract'] = get_file_name(args.tract)
    dict_disp['Mesh'] = get_file_name(args.mesh)
    if args.brain_2d ==None:
        dict_disp['Brain'] = get_file_name([args.glass_brain])
    else:
        dict_disp['Brain'] = get_file_name([args.glass_brain,args.brain_2d[0]] )

    for i in range(numb):
        flag_multple =0
        actor_tract = actor_vtk = actor_mask = None
        if args.stats_csv:
            if args.stats_csv[i]!=None and len(list_csvs)>i:
                cc = Colors_csv(list_csvs[i])
                color_map_mask = cc.assign_colors(map=args.map,range_value=args.range_value,log_p_value=args.log_p_value,threshold=args.threshold, output=args.output)
        if len(args.mask)<=i: actor_mask = None
        else:
            if args.mask[i]!=None:
                mask = nib.load(args.mask[i])
            if len(np.unique(mask.get_fdata()))>2:
                flag_multple = 1
                if (args.stats_csv!=None and len(list_csvs)>i):

                    mask_caller = Mask(mask,colormap=color_map_mask)
                    actor_mask,distinctpy_colormask = mask_caller.multi_label()
                else:
                    mask_caller = Mask(mask)
                    actor_mask,distinctpy_colormask = mask_caller.multi_label()
            elif len(mask_color_list)>i:
                mask_caller = Mask(mask,mask_color_list[i])
                actor_mask = mask_caller.one_label()
            else:
                if args.color_map!=None: 
                    name = args.mask[i].split('/')[-1].split('.')[0]
                    dic_colors = Colors.load_colors()
                    if name in dic_colors:
                        mask_caller = Mask(mask,mask_color_list[i])
                        actor_mask = mask_caller.one_label()
                else: 
                    mask_caller = Mask(mask,Colors.get_tab20_color(index = i, type_='vol'))
                    actor_mask = mask_caller.one_label()
        
        if len(args.tract)<=i:actor_tract = None
        else:
            if args.tract[i]!=None:
                if str(args.tract[i]).split('.')[-1] == 'gz' or str(args.tract[i]).split('.')[-1] == 'zip':
                    tract_image =  nib.streamlines.load(read_from_compressed(args.tract[i]))
                elif str(args.tract[i]).split('.')[-1] == 'trx':
                    tract_image =  tmm.load(args.tract[i])
                else: tract_image = nib.streamlines.load(args.tract[i])
                if not tract_image.header : print("The Track has no Header!") 
                if flag_multple ==1 and args.tracts_paint==False:
                    tract_caller = Tract(bundle = tract_image.streamlines,tw=args.width_tract)
                    if args.stats_csv!=None and args.stats_csv[i]!=None:
                        tract_caller.selt_colormap(instance=color_map_mask)
                    
                    else: tract_caller.selt_colormap(instance=distinctpy_colormask)
                    actor_tract = tract_caller.with_colormap(mask=mask)

                elif len(tract_color_list)>i:
                    tract_caller = Tract(bundle = tract_image.streamlines,tw=args.width_tract,color_list=tract_color_list[i])
                    actor_tract = tract_caller.single_color()
                elif args.tracts_paint==True:
                    if args.stats_csv:
                        color_map_mask_tracts_paint = color_map_mask
                    else:
                        color_map_mask = distinctipy.get_colors(15)
                    tract_caller = Tract(bundle = tract_image.streamlines,tw=args.width_tract)
                    tract_caller.selt_colormap(instance=color_map_mask_tracts_paint)
                    actor_tract = tract_caller.tracts_paint()
                else:
                    tract_caller = Tract(bundle = tract_image.streamlines,tw=args.width_tract)
                    actor_tract = tract_caller.dirrection_color()

        if args.mesh!=None:
            if len(args.mesh)<=i:
                actor_vtk = None
            else:
                print(len(args.mesh),i)
                if flag_multple==1:
                    mesh_caller = Mesh(pv.PolyData(args.mesh[i]))
                    actor_vtk = mesh_caller.load_mesh_with_colors(mask = mask,color_map = distinctpy_colormask)
                else:
                    if args.colors_mesh and args.colors_mesh[i]:
                        mesh_caller = Mesh(pv.PolyData(args.mesh[i]),vtk_color_list[i])
                        actor_vtk = mesh_caller.load_mesh()
                    else:
                        mesh_caller = Mesh(pv.PolyData(args.mesh[i]),color_list=Colors.get_tab20_color(index = i, type_='vtk'))
                        actor_vtk = mesh_caller.load_mesh()

        if actor_mask!= None:
            main_scene.add(actor_mask)
            rois[dict_disp['Mask'][i]] = actor_mask 
        if actor_tract!= None:
            main_scene.add(actor_tract)
            rois[dict_disp['Tract'][i]] = actor_tract 
        if actor_vtk!= None:
            main_scene.add(actor_vtk)
            rois[dict_disp['Mesh'][i]] = actor_vtk 
            
        if args.glass_brain and glass_brain_actor==None:
            glass_brain_caller = load_3dbrain(nib.load(args.glass_brain))

            glass_brain_actor = glass_brain_caller.loading()
            main_scene.add(glass_brain_actor)
            rois[dict_disp['Brain'][i]] = glass_brain_actor
        if args.brain_2d and slice_actor==None:
            caller_2d = load_2dbrain(nib.load(args.brain_2d[0]))
            slice_actor = caller_2d.load_actor()
            value_min = min(nib.load(args.brain_2d[0]).get_fdata().shape)
            ui_caller.define_maxview(value_min,slice_actor = slice_actor)
            main_scene.add(slice_actor)
            rois[dict_disp['Brain'][i]] = slice_actor

    if args.brain_2d and len(args.brain_2d)>1:
        ui_caller.slice_actorvalues(args.brain_2d[1:])

    ui_caller.Showmanger_init(di=dict_disp,rois=rois,interactive=interactive,output_path=args.output)


