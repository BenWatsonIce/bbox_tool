# BBox Tool for Change Visualisation

This tool allows the user to visually assess surface changes within raster data,
by selecting a bounding box on an initial reference image and applying the same
spatial crop across multiple years of satellite or other raster data.

---

## Features

- Load multiple raster images from a folder by year name
- Interactive bounding box selection using the first image
- Automatic clipping and visualisation of change through time
- Normalised reflectance stretch for enhanced visual clarity (the percentile values in the stretch variable can be used to adjust this)
- Returned bounding box coordinates, based on what you've drawn
- The example data in this repo is Landsat 8 panchromatic band imagery that displays an area of Austfonna (Svalbard)

---

## Usage notes

The tool expects the data to be organised as: 

<base_path>/
│
├── 2014/
│   └── 2014.tif
├── 2015/
│   └── 2015.tif
├── 2025/
│   └── 2025.tif
...

Each folder must be named after the year of the image. This is to make the tool year agnostic and convenient! Each folder containing the data myst have a .tif file with the same name as the folder. 

To use it in Python (Or use it in Jupyter Labs): 

from bbox_tool.viewer import BBoxViewer

# Path to the folder containing year subfolders
base_path = r"<PATH_TO_YOUR_DATA_FOLDER>"

# Optionally, specify the years you want to process
years = [2014, 2025]

# Create the viewer object
viewer = BBoxViewer(base_path, years)

# Step 1: Load the first year's data
viewer.load_data()

# Step 2: Open interactive window to draw bounding box
viewer.select_bbox()

# Step 3: Plot all clipped datasets and save figure (optional)
viewer.plot_results()  # saves figure in <base_path>/deposit/stacked_rasters.png
