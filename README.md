## **BBox Tool for Change Visualisation**

This tool allows the user to visually assess surface changes within raster data,
by selecting a bounding box on an initial reference image and applying the same
spatial crop across multiple years of satellite or other raster data.

---

# Features

- Load multiple raster images from a folder by year name
- Interactive bounding box selection using the first image, with the option to manually set bounding box coordinates instead
- Automatic clipping and visualisation of change through time
- Normalised reflectance display with percentile-based stretch
- Adjustable lower and upper percentile values to highlight specific spectral ranges
- Option to apply the same stretch across all images for consistent visual comparison with enhanced surface features
- Returned bounding box coordinates, based on what you've drawn, both in the raster's CRS and lat/long coordinates
- Optional colourbar on all plots with customisable label (default: "Normalised reflectance")
- The example data in this repo is Landsat 8 panchromatic band imagery that displays an area of Austfonna (Svalbard)

---

# Usage notes

The tool expects the data to be organised as: 


```python 
<base_path>/
│
├── 2014/
│   └── 2014.tif
├── 2016/
│   └── 2016.tif
├── 2019/
│   └── 2019.tif
```

If your data covers a timescale shorter or longer than years (i.e. days, weeks or decades), consider saving it in another similar format. For example, if your data is daily, try:

```python
<base_path>/
│
├── 01012014/
│   └── 01012014.tif
├── 02012014/
│   └── 02012014.tif
├── 03012014/
│   └── 03012014.tif
```

Each folder must be named the same as the image. This is to make the tool agnostic and convenient! So, make sur each folder containing the data has a TIFF file with the same name as the folder. 

## Usage guide

# 1. To use it in Python (Or use it in Jupyter Labs), import the viewer class: 

```python 
from bbox_tool.viewer import BBoxViewer
```
# 2. Set the path to your data folder:
 
```python
base_path = r"<PATH_TO_YOUR_DATA_FOLDER>"
```

# 3. Specify the years you'd like to incorporate into your workflow's run of the script:

```python 
years = [2014, 2016, 2019]
```

# 4. Create the viewer object:

```python
viewer = BBoxViewer(base_path, years)
```

# 5. Load the first year's raster data to standardise the CRS:

```python
viewer.load_data()
```

# 6. If you already have a set of bounding box coordinates, manually input them this way:

```python
viewer.bbox_coords(lon_min=1, lon_max=2, lat_min=3, max_lat=4)
```

# 7. If you want to specify a new bounding box interactively, use:

```python
viewer.select_bbox()
```

# 8. Iterate the application of your bounding box to all years in your dataset stepwise:

```python
clipped, extents = viewer.apply_bbox_to_all()
```

# Visualise a single image with display options set by numpy and matplotlib as an example plot:

```python
viewer.normalised_viewer(
    image=clipped["year"], 
    title="2016 Surge Velocity",
    lower_percentile=2,
    upper_percentile=98,
    cmap="gray"
)
```

# 10. Visualise all years stacked with optional custom titles and a shared colourbar:

```python
titles_dict = {
    "2014": "A) 2014: Before",
    "2016": "B) 2016: During",
    "2019": "C) 2019: After"
}


viewer.set_colourbar(on=True, label="Normalised Band 8 Surface Reflectance")  # optional to the user
```

# 11. Then plot:

```python 
pythonviewer.plot_results(
    titles=titles_dict,
    lower_percentile=2,
    upper_percentile=98,
    cmap="gray"
)
```

# The stacked figure is then automatically saved to:

```python
<base_path>/deposit/stacked_rasters.png unless save=False
```
