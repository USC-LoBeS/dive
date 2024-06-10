- [1] <strong>Rendering Mask :</strong> 
    To render a 3D mask of a given region of interest (ROI) in a specific color. First, load your MRI or NIfTI image highlighting the ROI. 
    Then specify the color that you want to apply. To load multiple files separate them by Space and colors by comma. To load a 3D glass brain use glass_brain argument. For Changing the background color from Black to white use background 1. For 2D brain images use brain_2d argument and specify the file name. Also use the view button to toggel them ON. If the user wants to take a Log of P-Values before thresholding then they can use the log_p_value argument

    <img src="https://raw.githubusercontent.com/USC-LoBeS/dive/main/example/images/Picture1.png" width="480">

    ```
    dive --mask /example/IFOF_R_global_all.nii.gz
    ```

    <img src="https://raw.githubusercontent.com/USC-LoBeS/dive/main/example/images/Picture2.png" width="480">

    ```
    dive --mask /example/IFOF_R_global_all.nii.gz --colors_mask red
    ```

    <img src="https://raw.githubusercontent.com/USC-LoBeS/dive/main/example/images/Picture2_2.png" width="480">

    ```
    dive --mask example/IFOF_R_global_all.nii.gz example/CST_R_global_all.nii.gz --glass_brain example/ICBM152_adult.WM.nii.gz --background 1 
    ```
    
    For Multi Labeled Mask use the same --mask argument, also user can specify a statistics file using a csv file.
    Having a Threshold for P-value, and range for the plotting value. The colors can be choosen using map.

    <img src="https://raw.githubusercontent.com/USC-LoBeS/dive/main/example/images/Picture1_1.png" width="480">

    ```
    dive --mask example/DSI_CST_R_local_all.nii.gz --brain_2d example/mni_icbm152_t1_tal_nlin_sym_09a.nii.gz

    ```
    <img src="https://raw.githubusercontent.com/USC-LoBeS/dive/main/example/images/Picture1_withcmap_stats.png" width="480">

    ```
    dive --mask example/DSI_CST_R_local_all.nii.gz --stats_csv example/stat_template.csv --brain_2d example/mni_icbm152_t1_tal_nlin_sym_09a.nii.gz --range_value -1 1 --threshold 0.5 --map viridis
    ```

- [2] <strong>Rendering Mesh :</strong> 
    To render a 3D mesh of a given region of interest (ROI) in a specific color. First, load your VTK image highlighting the ROI. 
    Then specify the color that you want to apply.

    <img src="https://raw.githubusercontent.com/USC-LoBeS/dive/main/example/images/Picture3.png" width="480">

    ```
    dive --mesh /example/IFOF_R_skeleton.vtk
    ```

    <img src="https://raw.githubusercontent.com/USC-LoBeS/dive/main/example/images/Picture4.png" width="480">

    ```
    dive --mask /example/IFOF_R_skeleton.vtk --colors_mesh red
    ```

- [3] <strong>Rendering Tract :</strong> 
    To render a 3D mesh of a given region of interest (ROI) in a specific color. First, load your Tract (trk,tck,trx), they are colored based on the directions, if you want to load them in a specific color then specify the color that you want to apply.

    <img src="https://raw.githubusercontent.com/USC-LoBeS/dive/main/example/images/Picture5.png" width="480">

    ```
    dive --tract example/CST_R.trk
    ```

    <img src="https://raw.githubusercontent.com/USC-LoBeS/dive/main/example/images/Picture6.png" width="480">

    ```
    dive --tract example/CST_R.trk --colors_tract red
    ```
    
- [4] <strong>Rendering Multiple File Types :</strong> 
    To render multiple files types tegether the user can specify the tracts and masks together if they are given with the same index and mask is a multi-labeled mask then the mask's colormap is applied to the Tracts.
    
    <img src="https://raw.githubusercontent.com/USC-LoBeS/dive/main/example/images/Picture7.png" width="480">

    ```
    dive --mask example/DSI_CST_R_local_all.nii.gz --stats_csv example/stat_template.csv --tract example/CST_R.trk --glass_brain example/ICBM152_adult.WM.nii.gz --background 1 --output example/test_op
    ```



## Acknowledgments
ICBM152_adult.WM.nii.gz: https://github.com/frankyeh/DSI-Studio-atlas/blob/main/ICBM152_adult/ICBM152_adult.WM.nii.gz