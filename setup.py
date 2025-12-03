from setuptools import setup, find_packages

setup(
    name="bbox_tool",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "matplotlib",
        "rioxarray",
        "rasterio",
        "pyproj",
        "ipywidgets"
    ],
    python_requires='>=3.10',
    include_package_data=True,
    description="Interactive bounding box tool for visualising raster changes across years",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Your Name",
    url="https://github.com/yourusername/bbox_tool",  # replace with your repo
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
