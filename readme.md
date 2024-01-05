<a name="readme-top"></a>
<!-- [![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![LinkedIn][linkedin-shield]][linkedin-url] -->

<br />
<div align="center">
  <a href="images/Logo.svg">
    <img src="images/Logo.svg" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">DiVE</h3>

  <p align="center">
    Diffusion Visualization and Explorer
    <br />
    <a href="https://github.com/USC-LoBeS/DiVE/e"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/github_username/repo_name">View Demo</a>
    ·
    <a href="https://github.com/USC-LoBeS/DiVE/issues">Report Bug</a>
    ·
    <a href="https://github.com/USC-LoBeS/DiVE/issues">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#ui-interaction">UI Interaction</a></li>
    <li><a href="#usage-cli">Usage CLI</a></li>
    <li><a href="#usage">Usage GUI</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

 Diffusion Visualization and Explorer (DiVE) is a tool designed for visualizing medical imaging data. It allows users to visualize tractography in various formats (TRK, TCK, VTK), binary masks in NIfTI format, and meshes in VTK format. Users also have the flexibility to load multiple Regions of Interest (ROIs) in different combinations, whether they are exclusively of one type (mesh, mask, or tract) or a combination of types. Additionally, users can toggle between 3D visualization and saving the output by specifying a designated path.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

[![Fury][Fury.]][Fury-url]
[![OpenGL][OpenGL.]][OpenGL-url]
[![distinctipy][dist.]][dist-url]
<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

This is an example of how you may give instructions on setting up your project locally.
To get a local copy up and running follow these simple example steps.

### Prerequisites

Linux and Windows are supported, but we recommend Linux for performance and compatibility reasons.
1–8 GPUs with at least 12 GB of memory.
64-bit Python 3.8.

### Installation

1. Get a free Python 3.8 [https://www.python.org/downloads/release/python-3810/](https://www.python.org/downloads/release/python-3810/) and latest version of pip.
2. Clone the repo and go to the folder
   ```sh
   git clone https://github.com/github_username/repo_name.git
   ```
3. Install the required packages using requrements.txt
   ```sh
   pip install -r requirements.txt
   ```
<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- UI Interaction -->

## UI Interaction
1. <strong>Choose Type:</strong> Use the type of ROI type (Mask/Mesh/Tract/Brain) to open the drop down having the names of all the files of that type, to select that required ROI.
2. <strong>Change View:</strong> Click on the buttons to change the view to Sagittal/Coronal/Axial view.
3. <strong>Choose Slice:</strong> Change the brain slice value based on the selected view (a brain_2d file is required to use this)
4. <strong>Change Opacity (Streamlines, Mask, Mesh, Slice):</strong> 
Use the sliders to change the opacity of the file for a selected file.
5. <strong> Add Button: </strong> To add more items, click the add button and choose the type of file you want to add.
6. <strong> Remove Button: </strong> To remove a specific file, select it using the Choose type and then click this button.
   
![Image][ui-image]

<!-- USAGE -->
## USAGE CLI

Here are few example of how to use the code for specific features.

- [1] <strong>Rendering Tract/Mask/Mesh with a single color :</strong> ```
python main.py --mask mask1.nii.gz mask2.nii.gz  --tract tract1.trk tract2.trk --mesh mesh1.vtk mesh2.vtk --brain_2d brain.nii.gz --colors_mask red,#FF0000 --colors_mesh green,#96be25 --colors_tract blue,#2596be```
![Image][fig1-image]

  <strong> Note: For multiple files in Mask/Mesh/Tract use "SPACE" to separate For colors you can be provide either name or the hex , If colors_tract is not provided then uses direction of tracts to color it. If colors_mask/colors_mesh is not provided then uses a random color</strong>

- [2] <strong>Rendering Tract/Mask/Mesh with a multi labeled mask :</strong> ```
python main.py --mask mask1.nii.gz mask2.nii.gz  --tract tract1.trk tract2.trk --mesh mesh1.vtk mesh2.vtk --glass_brain brain_wm.nii.gz --width_tract 4 --background 1 ```
![Image][fig2-image]

  <strong> Note: Provide a mask that has multiple labels, it is automatically detected and colored using disctinctipy library. These colors are used to color the tract and mesh as well. Keep the order of files of same ROI constant e.g. if CST_L is < mask1.nii.gz > in mask then it should be the 1st in Mesh and Tract < tract1.trk> Use Glass Brain for a 3D white matter brain, background 0/1 (black/white) and width_tract to specify the width of all the tracts </strong>

- [3] <strong>Rendering Tract/Mask/Mesh with a multi labeled mask using a stas file (csv) :</strong> ```
python main.py --mask mask1.nii.gz mask2.nii.gz --tract tract1.trk tract2.trk --stats_mask_csv_value stats_file1.csv,stats_file2.csv --range_t_value -14 14 --threshold_mask 5 --map Spectral_r```
![Image][fig3-image]
  <strong> Note: Provide a mask that has multiple labels, it is automatically detected and colored using the stats file (It should have few values like labels,p_value and t_value). Labels column is used to map colors to the same label number present in the mask. P_value is used as the thresholding factor to make a label significant or not (color it grey). T_value is normalized and used to choose a color from color_map (Matplotlib color_map). These colors are used to color the tract and mesh as well.  </strong>

See the [open issues](https://github.com/github_username/repo_name/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Lobes - 

Project Link: [https://github.com/USC-LoBeS/DiVE/](https://github.com/USC-LoBeS/DiVE/)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* I. B. Gari et al., "Along-Tract Parameterization of White Matter Microstructure using Medial Tractography Analysis (MeTA)," 2023 19th International Symposium on Medical Information Processing and Analysis (SIPAIM), Mexico City, Mexico, 2023, pp. 1-5, doi: 10.1109/SIPAIM56729.2023.10373540.
* OHBM abstract

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
[contributors-shield]: https://img.shields.io/github/contributors/github_username/repo_name.svg?style=for-the-badge
[contributors-url]: https://github.com/github_username/repo_name/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/github_username/repo_name.svg?style=for-the-badge
[forks-url]: https://github.com/github_username/repo_name/network/members
[stars-shield]: https://img.shields.io/github/stars/github_username/repo_name.svg?style=for-the-badge
[stars-url]: https://github.com/github_username/repo_name/stargazers
[issues-shield]: https://img.shields.io/github/issues/github_username/repo_name.svg?style=for-the-badge
[issues-url]: https://github.com/USC-LoBeS/DiVE/issues
[license-shield]: https://img.shields.io/github/license/github_username/repo_name.svg?style=for-the-badge
<!-- [license-url]: https://github.com/github_username/repo_name/blob/master/LICENSE.txt -->
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/linkedin_username
[product-screenshot]: images/OHBM_Images_Brain3d.jpg
[ui-image]: images/UI.png
[fig1-image]: images/Figure1.png
[fig2-image]: images/Figure2.png
[fig3-image]: images/Figure3.png
[Fury.]: https://img.shields.io/badge/Fury-red?logo=https%3A%2F%2Ffury.gl%2Flatest%2F_static%2Fimages%2Flogo.svg
[Fury-url]: https://fury.gl/latest/index.html

[OpenGL.]: https://img.shields.io/badge/OpenGL-%235586A4?logo=https%3A%2F%2Ffury.gl%2Flatest%2F_static%2Fimages%2Flogo.svg
[OpenGL-url]:https://www.opengl.org/

[dist.]:https://img.shields.io/badge/distinctipy-blue?logo=https%3A%2F%2Ffury.gl%2Flatest%2F_static%2Fimages%2Flogo.svg
[dist-url]: https://doi.org/10.5281/zenodo.3985191

