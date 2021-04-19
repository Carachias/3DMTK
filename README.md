# 3D Model Toolkit <br>
<br>
Application (with GUI) to inspect various 3D Model fileformats and convert them to ML-ready Pointclouds <br>
<br>
![UI Image:](images/3dmtkui.png?raw=true "UI")
<br>
<br>
<br>
Features: <br>

* Inspect all kinds of 3D Meshes <br>
* Display Vertices of a Mesh <br>
* Sample a random Subset of Vertices with adjustable Samplesize <br>
* Sample roughly uniformly distributed Points from the Surface of the Mesh <br>
* Preprocess whole Folders of 3D Models to be usable in Machine Learning, by: <br>
	* uniformly Sampling Points from the Surface of each Object <br>
	* Scaling each Pointcloud to fit in a Unit-Sphere <br>
	* Translating each Pointcloud to have Coordinates (0, 0, 0) as Center <br>
	* Randomly rotating each Pointcloud along its Z-axis (1 degree Stepsize) <br>
	* Creating as many rotations/ perspectives per Object as the User desires <br>

<br>
Supported input Fileformats: <br>

* .obj <br>
* .stl <br>
* .off <br>
* .ply <br>
...and many more <br>

<br>
Output Fileformat: <br>

* .pt <br>

<br>
Used Librarys: <br>

* PyQT5 <br>
* Trimesh <br>
* PyVista <br>
* PyVistaQt <br>
* Pytorch <br>
