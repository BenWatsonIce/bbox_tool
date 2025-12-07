import os
import numpy as np
import matplotlib
matplotlib.use("Qt5Agg") 
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
        self.colourbar_on = True
        self.colourbar_label = "Normalised reflectance"

    def bbox_coords(self, lon_min, lon_max, lat_min, lat_max):
        """
        Manually set the bounding box in lat/lon.
        If set, select_bbox() will skip the interactive window.
        """
        self.bbox_latlon = (lon_min, lon_max, lat_min, lat_max)
        if self.from_latlon is None:
            raise RuntimeError("Load data first with load_data() to set CRS.")
        x1c, y1c = self.from_latlon.transform(lon_min, lat_min)
        x2c, y2c = self.from_latlon.transform(lon_max, lat_max)
        self.bbox_crs = (min(x1c, x2c), max(x1c, x2c),
                        min(y1c, y2c), max(y1c, y2c))
        print("Manual LAT/LON bounding box set:", self.bbox_latlon)
        print("Manual raster CRS bounding box set:", self.bbox_crs)


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
        if self.bbox_latlon is not None:
            print("Bounding box already set manually, skipping interactive selection.")
            return
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

    def apply_bbox_to_all(self):
        """
        Clip all rasters using the selected bounding box
        and return dict of clipped arrays and spatial extents.
        """
        if self.bbox_crs is None:
            raise ValueError("Bounding box not set. Run select_bbox() first.")

        clipped = {}
        extents = {}

        for yr in self.years:
            fp = os.path.join(self.base_path, yr, f"{yr}.tif")
            ds = rxr.open_rasterio(fp).squeeze()

            ds = ds.rio.clip_box(
                minx=self.bbox_crs[0], maxx=self.bbox_crs[1],
                miny=self.bbox_crs[2], maxy=self.bbox_crs[3]
            )

            arr = np.nan_to_num(ds.values, nan=0)
            clipped[yr] = arr

            extents[yr] = [
                ds.x.min().item(),
                ds.x.max().item(),
                ds.y.min().item(),
                ds.y.max().item()
            ]

        return clipped, extents

    @staticmethod
    def preprocess(img):
        """Normalise image using 2–98 percentile stretch"""
        p2, p98 = np.percentile(img, (2, 98))
        stretched = np.clip((img - p2) / (p98 - p2), 0, 1)
        stretched = np.power(stretched, 0.8)
        return stretched

    def set_colourbar(self, on=True, label="Normalised reflectance"):
        """
        Configure colourbar display for subsequent plots.

        Parameters
        ----------
        on : bool
            If True, colourbar will be shown. If False, it will be hidden.
        label : str
            Label to display alongside the colourbar.
        """
        self.colourbar_on = on
        self.colourbar_label = label

    def normalised_viewer(self, image, title="Normalised View", lower_percentile=2, upper_percentile=98, cmap="gray"):
        p_low, p_high = np.percentile(image, [lower_percentile, upper_percentile])
        stretched = np.clip((image - p_low) / (p_high - p_low), 0, 1)

        plt.figure(figsize=(6, 6))
        im_plot = plt.imshow(stretched, cmap=cmap)
        plt.title(title)

        if self.colourbar_on:
            cbar = plt.colorbar(im_plot)
            cbar.set_label(self.colourbar_label, rotation=90)
            cbar.set_ticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])

        plt.axis("off")
        plt.show()

    def plot_results(self, titles=None, save=True, save_path=None, lower_percentile=2, upper_percentile=98, cmap="gray"):
        """
        Plot clipped rasters stacked vertically with optional custom titles,
        normalisation, and a single shared colourbar.

        Parameters
        ----------
        titles : dict or list
            Custom titles per year.
        save : bool
            Whether to save the figure.
        save_path : str
            Path to save the figure.
        lower_percentile : float
            Lower percentile for normalisation.
        upper_percentile : float
            Upper percentile for normalisation.
        cmap : str
            Matplotlib colormap.
        """
        if self.bbox_crs is None:
            raise ValueError("Bounding box not set. Run select_bbox() first.")

        self.datasets = []
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

        fig, axes = plt.subplots(
            nrows=len(self.datasets), ncols=1,
            figsize=(10, 5*len(self.datasets)), dpi=300
        )

        if len(self.datasets) == 1:
            axes = [axes]

        im_list = []

        for ax, ds, yr in zip(axes, self.datasets, self.years):
            # Normalisation
            p_low, p_high = np.percentile(ds.values, [lower_percentile, upper_percentile])
            arr = np.clip((ds.values - p_low) / (p_high - p_low), 0, 1)
            im = ax.imshow(arr, cmap=cmap,
                        extent=[ds.x.min(), ds.x.max(), ds.y.min(), ds.y.max()],
                        origin="upper", aspect="equal")
            im_list.append(im)

            # Tick conversion to lat/lon
            xlim, ylim = ax.get_xlim(), ax.get_ylim()
            xticks = np.linspace(xlim[0], xlim[1], 5)
            yticks = np.linspace(ylim[0], ylim[1], 5)
            lons, lats = transformer.transform(xticks, yticks)

            ax.set_xticks(xticks)
            ax.set_yticks(yticks)
            ax.set_xticklabels([f"{lon:.2f}°E" for lon in lons], fontsize=8)
            ax.set_yticklabels([f"{lat:.2f}°N" for lat in lats], fontsize=8)

            # Apply user titles
            if titles:
                if isinstance(titles, dict):
                    ax.set_title(titles.get(str(yr), str(yr)), fontsize=12)
                elif isinstance(titles, list) and len(titles) == len(self.years):
                    idx = self.years.index(yr)
                    ax.set_title(titles[idx], fontsize=12)
            else:
                ax.set_title(str(yr), fontsize=12)

            ax.set_xlabel("Longitude (°E)", fontsize=9)
            ax.set_ylabel("Latitude (°N)", fontsize=9)

        fig.tight_layout()

        # Single shared colourbar
        if self.colourbar_on and im_list:
            from matplotlib.cm import ScalarMappable
            sm = ScalarMappable(cmap=cmap, norm=im_list[0].norm)
            sm.set_array([])
            cbar = fig.colorbar(sm, ax=axes, fraction=0.046, pad=0.04)
            cbar.set_label(self.colourbar_label, rotation=90, fontsize=10)
            cbar.set_ticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])

        if save:
            save_path = save_path or os.path.join(self.base_path, "deposit", "stacked_rasters.png")
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            fig.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"Saved: {save_path}")

        plt.show()
