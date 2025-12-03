import os
import numpy as np
import matplotlib
matplotlib.use("Qt5Agg")  # Interactive window
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector, Button
from pyproj import Transformer
import rioxarray as rxr

class BBoxViewer:
    def __init__(self, base_path, years=None):
        """
        base_path: folder containing year subfolders, each with 'year.tif'
        years: list of years to process; if None, automatically detected
        """
        self.base_path = base_path
        # Ensure years are strings for path operations
        self.years = [str(y) for y in (years or sorted([
            name for name in os.listdir(base_path)
            if os.path.isdir(os.path.join(base_path, name))
        ]))]
        self.datasets = []
        self.bbox_latlon = None
        self.bbox_crs = None
        self.transform = None
        self.crs = None
        self.to_latlon = None
        self.from_latlon = None
        self.image = None

    def load_data(self):
        """Load first year's raster to setup coordinate transforms"""
        first_year_path = os.path.join(self.base_path, self.years[0], f"{self.years[0]}.tif")
        ds = rxr.open_rasterio(first_year_path).squeeze()
        self.image = np.nan_to_num(ds.values, nan=0)
        self.transform = ds.rio.transform()
        self.crs = ds.rio.crs
        self.to_latlon = Transformer.from_crs(self.crs, "EPSG:4326", always_xy=True)
        self.from_latlon = Transformer.from_crs("EPSG:4326", self.crs, always_xy=True)

    def select_bbox(self):
        """Open interactive Qt window to select bounding box and confirm"""
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(self.image, cmap="gray", origin='upper')
        ax.set_title(f"Draw bounding box on {self.years[0]} image → click CONFIRM", fontsize=12)
        plt.axis("off")

        def update_bbox(eclick, erelease):
            x1p, y1p = int(eclick.xdata), int(eclick.ydata)
            x2p, y2p = int(erelease.xdata), int(erelease.ydata)
            xmin_p, xmax_p = sorted([x1p, x2p])
            ymin_p, ymax_p = sorted([y1p, y2p])

            def pix_to_map(px, py):
                X = self.transform[2] + px * self.transform[0]
                Y = self.transform[5] + py * self.transform[4]
                return X, Y

            x1m, y1m = pix_to_map(xmin_p, ymin_p)
            x2m, y2m = pix_to_map(xmax_p, ymax_p)

            lon1, lat1 = self.to_latlon.transform(x1m, y1m)
            lon2, lat2 = self.to_latlon.transform(x2m, y2m)
            self.bbox_latlon = (min(lon1, lon2), max(lon1, lon2),
                                min(lat1, lat2), max(lat1, lat2))

            x1c, y1c = self.from_latlon.transform(self.bbox_latlon[0], self.bbox_latlon[2])
            x2c, y2c = self.from_latlon.transform(self.bbox_latlon[1], self.bbox_latlon[3])
            self.bbox_crs = (min(x1c, x2c), max(x1c, x2c),
                             min(y1c, y2c), max(y1c, y2c))

        rect_selector = RectangleSelector(
            ax, update_bbox,
            interactive=True,
            drag_from_anywhere=True,
            minspanx=10,
            minspany=10,
            button=[1]
        )

        def confirm(event):
            plt.close()
            print("LAT/LON bounding box:", self.bbox_latlon)
            print("Raster CRS bounding box:", self.bbox_crs)

        button_ax = fig.add_axes([0.8, 0.02, 0.15, 0.05])
        button = Button(button_ax, "CONFIRM")
        button.on_clicked(confirm)

        plt.show()

    @staticmethod
    def preprocess(img):
        """Normalize image using 2–98 percentile stretch"""
        p2, p98 = np.percentile(img, (2, 98))
        stretched = np.clip((img - p2) / (p98 - p2), 0, 1)
        stretched = np.power(stretched, 0.8)
        return stretched

    def plot_results(self, save=True, save_path=None):
        """Clip all datasets and plot them stacked; optionally save figure"""
        # Load and clip datasets if not already loaded
        if not self.datasets:
            for yr in self.years:
                fp = os.path.join(self.base_path, yr, f"{yr}.tif")
                ds = rxr.open_rasterio(fp).squeeze()
                ds = ds.rio.clip_box(
                    minx=self.bbox_crs[0], maxx=self.bbox_crs[1],
                    miny=self.bbox_crs[2], maxy=self.bbox_crs[3]
                )
                self.datasets.append(ds)

        crs = self.datasets[0].rio.crs
        transformer = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)

        fig, axes = plt.subplots(nrows=len(self.datasets), ncols=1,
                                 figsize=(10, 5*len(self.datasets)), dpi=150)

        if len(self.datasets) == 1:
            axes = [axes]

        for ax, ds, yr in zip(axes, self.datasets, self.years):
            arr = self.preprocess(ds.values)
            ax.imshow(
                arr,
                cmap="gray",
                vmin=0, vmax=1,
                extent=[ds.x.min().item(), ds.x.max().item(), ds.y.min().item(), ds.y.max().item()],
                origin="upper",
                interpolation="none",
                aspect='equal'
            )

            # Add lat/lon ticks
            xlim, ylim = ax.get_xlim(), ax.get_ylim()
            x_ticks_m = np.linspace(xlim[0], xlim[1], 6)
            y_ticks_m = np.linspace(ylim[0], ylim[1], 6)
            lon_ticks, lat_ticks = transformer.transform(x_ticks_m, y_ticks_m)
            ax.set_xticks(x_ticks_m)
            ax.set_xticklabels([f"{lon:.2f}°E" for lon in lon_ticks], fontsize=8)
            ax.set_yticks(y_ticks_m)
            ax.set_yticklabels([f"{lat:.2f}°N" for lat in lat_ticks], fontsize=8)

            ax.set_title(f"{yr}", fontsize=12)
            ax.set_xlabel("Longitude (°E)")
            ax.set_ylabel("Latitude (°N)")

        fig.tight_layout()
        plt.show()

        if save:
            # Default save path in 'deposit' folder
            save_path = save_path or os.path.join(self.base_path, "deposit", "stacked_rasters.png")
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            fig.savefig(save_path, dpi=400, bbox_inches="tight", format="png")
            print(f"Saved figure to: {save_path}")
