
import io
import gzip
import zipfile
import numpy as np
from dive.mask import Mask
import nibabel as nib
from dive.tract import Tract
from dive.helper import  Colors
import trx.trx_file_memmap as tmm
class load:
    def __init__(self):
        self.index_mask = 0
        self.flag_multple = 0
        self.distinctpy_colormask = None
        self.mask = None

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

        
    def load_mask(self,mask_args,color_map_mask=[],color=None,color_map=None):
        
        self.flag_multple = 0
        self.index_mask= self.index_mask+1
        print(mask_args,color)
        if mask_args==None: actor_mask = None
        else:
            mask = nib.load(mask_args)
            self.mask = mask
            if len(np.unique(mask.get_fdata()))>2:
                self.flag_multple = 1
                if len(color_map_mask)>0:
                    mask_caller = Mask(mask,colormap=color_map_mask)
                    actor_mask,self.distinctpy_colormask = mask_caller.multi_label()
                else:
                    mask_caller = Mask(mask)
                    actor_mask,self.distinctpy_colormask = mask_caller.multi_label()
            else:
                if color:
                    mask_caller = Mask(mask,color)
                    actor_mask = mask_caller.one_label()
                else:
                    if color_map!=None: 
                        name = mask_args.split('/')[-1].split('.')[0]
                        dic_colors = Colors.load_colors()
                        if name in dic_colors:
                            mask_caller = Mask(mask,dic_colors[name])
                            actor_mask = mask_caller.one_label()
                    else: 
                        mask_caller = Mask(mask,Colors.get_tab20_color(index = self.index_mask, type_='vol'))
                        actor_mask = mask_caller.one_label()
        return actor_mask

    def load_tract(self,tract_args=None,tract_width = 1.0,tract_color = None,color_map_csv_tract=[],color_map_csv_mask=[]):

        if tract_args!=None:
            if str(tract_args).split('.')[-1] == 'gz' or str(tract_args).split('.')[-1] == 'zip':
                tract_image =  nib.streamlines.load(self.read_from_compressed(tract_args))
            elif str(tract_args).split('.')[-1] == 'trx':
                    tract_image =  tmm.load(tract_args)
            else: tract_image = nib.streamlines.load(tract_args)

            if not tract_image.header : print("The Track has no Header!") 

            if self.flag_multple == 1:
                tract_caller = Tract(bundle = tract_image.streamlines,tw=tract_width)
                if len(color_map_csv_tract)>0:
                    tract_caller.selt_colormap(instance=color_map_csv_tract)
                    
                elif len(color_map_csv_mask)>0:
                    tract_caller.selt_colormap(instance=color_map_csv_mask)
                
                else: tract_caller.selt_colormap(instance=self.distinctpy_colormask)
                actor_tract = tract_caller.with_colormap(mask=self.mask)

            elif tract_color!=None:
                tract_caller = Tract(bundle = tract_image.streamlines,tw=tract_width,color_list=tract_color)
                actor_tract = tract_caller.single_color()
            else:
                tract_caller = Tract(bundle = tract_image.streamlines,tw=tract_width)
                actor_tract = tract_caller.dirrection_color()
        return actor_tract
        
