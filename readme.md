<a name="readme-top"></a>
<!-- [![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![LinkedIn][linkedin-shield]][linkedin-url] -->

<br />
<div align="center">
  <a href="https://raw.githubusercontent.com/USC-LoBeS/dive/main/images/Logo.svg">
    <img src="https://raw.githubusercontent.com/USC-LoBeS/dive/main/images/Logo.svg" alt="Logo" width="80" height="80">
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
  <li><a href="#built-with">Built With</a></li>
    <li>
      <a href="#about-the-project">About The Project</a>
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
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

### Built With

[![Fury][Fury.]][Fury-url]
[![OpenGL][OpenGL.]][OpenGL-url]
[![distinctipy][dist.]][dist-url]
[![pypi][pypi.]][pypi-url]
<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ABOUT THE PROJECT -->
## About The Project

 Diffusion Visualization and Explorer (DiVE) is a tool designed for visualizing medical imaging data. It allows users to visualize tractography in various formats (TRK, TCK, VTK), binary masks in NIfTI format, and meshes in VTK format. Users also have the flexibility to load multiple Regions of Interest (ROIs) in different combinations, whether they are exclusively of one type (mesh, mask, or tract) or a combination of types. Additionally, users can toggle between 3D visualization and saving the output by specifying a designated path.

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

   ```sh
   pip install dive-mri
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

<strong>Rendering Tract/Mask/Mesh :</strong> 
![Image][fig1-image]
```
The user can give a 3D region of interest label image in NIFTI format and the tool will render it as a set of 3D contours (Figure A). Tract rendering can be conducted across all common formats (trk, tck, trx, vtk), with user defined coloring options, as well as available defaults (Figure B). Each fiber tract is displayed as tubes with a user-defined width. The tool applies either the color specified by the user or a random color for single labeled masks and chooses a set of distinct colors for multi-labeled masks using “distinctipy” or uses the colormap specified by the user (Figure C). DiVE also allows for the overlay of NIFTI masks and surface meshes on the fiber tracts, which can map scalar values to color or opacity, providing insights into tissue microstructure. The tool supports backgrounds using either a 3D glass brain or 2D slices. Visualization can be done in any stereotaxic space.
```
  <strong> Note: Specific Use cases can be found in [open Examples](https://github.com/USC-LoBeS/DiVE/example/Readme.md) </strong>


See the [open issues](https://github.com/USC-LoBeS/DiVE/issues) for a full list of proposed features (and known issues).

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

Lobes - njahansh@usc.edu, narulas@usc.edu, bagari@usc.edu

Project Link: [https://github.com/USC-LoBeS/DiVE/](https://github.com/USC-LoBeS/DiVE/)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* Narula Siddharth, Iyad Ba Gari, Shruti P. Gadewar, Sunanda Somu, Neda Jahanshad, "Diffusion Visualization Explorer (DiVE)"

* Gari, Iyad Ba, Shayan Javid, Alyssa H. Zhu, Shruti P. Gadewar, Siddharth Narula, Abhinaav Ramesh, Sophia I. Thomopoulos et al. "Along-Tract Parameterization of White Matter Microstructure using Medial Tractography Analysis (MeTA)." In 2023 19th International Symposium on Medical Information Processing and Analysis (SIPAIM), pp. 1-5. IEEE, 2023. doi: 10.1109/SIPAIM56729.2023.10373540.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- [contributors-shield]: https://img.shields.io/github/contributors/github_username/repo_name.svg?style=for-the-badge
[contributors-url]: https://github.com/USC-LoBeS/DiVE/graphs/contributors
[forks-shield]: https://github.com/USC-LoBeS/DiVE/repo_name.svg?style=for-the-badge
[forks-url]: https://github.com/github_username/repo_name/network/members
[stars-shield]: https://img.shields.io/github/stars/github_username/repo_name.svg?style=for-the-badge
[stars-url]: https://github.com/github_username/repo_name/stargazers
[issues-shield]: https://img.shields.io/github/issues/github_username/repo_name.svg?style=for-the-badge
[issues-url]: https://github.com/USC-LoBeS/DiVE/issues
[license-shield]: https://img.shields.io/github/license/github_username/repo_name.svg?style=for-the-badge -->
<!-- [license-url]: https://github.com/github_username/repo_name/blob/master/LICENSE.txt -->
<!-- [linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/linkedin_username -->
[ui-image]: https://raw.githubusercontent.com/USC-LoBeS/dive/main/images/UI.png
[fig1-image]: https://raw.githubusercontent.com/USC-LoBeS/dive/main/images/Figure_1.png

[Fury.]: https://img.shields.io/badge/Fury-red?logo=https%3A%2F%2Ffury.gl%2Flatest%2F_static%2Fimages%2Flogo.svg
[Fury-url]: https://fury.gl/latest/index.html

[OpenGL.]: https://img.shields.io/badge/OpenGL-%235586A4?logo=https%3A%2F%2Ffury.gl%2Flatest%2F_static%2Fimages%2Flogo.svg
[OpenGL-url]:https://www.opengl.org/

[dist.]:https://img.shields.io/badge/distinctipy-blue?logo=https%3A%2F%2Ffury.gl%2Flatest%2F_static%2Fimages%2Flogo.svg
[dist-url]: https://doi.org/10.5281/zenodo.3985191

[pypi.]:https://img.shields.io/badge/pypi-v1.0-blue
[pypi-url]: https://pypi.org/project/dive-mri/

