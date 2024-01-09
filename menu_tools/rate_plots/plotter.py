#!/afs/cern.ch/user/d/dhundhau/public/miniconda3/envs/py310/bin/python
import argparse
import os
import warnings

import awkward as ak
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
from progress.bar import IncrementalBar
import yaml
import json

from menu_tools.utils import scalings
from menu_tools.rate_plots.config import RatePlotConfig

plt.style.use(hep.style.CMS)


class RatePlotter:
    # Common plot properties
    _figsize = (10, 10)
    _llabel = "Phase-2 Simulation"
    _com = 14

    def __init__(self, cfg, data, offline_pt: bool):
        self.cfg = cfg
        self.data = data
        self.offline_pt = offline_pt

    @property
    def _online_offline(self):
        if self.offline_pt:
            return "Offline"
        return "Online"

    def _style_plot(self, fig, ax0, ax1=None, legend_loc="upper right"):
        ax0.legend(loc=legend_loc, frameon=False)
        ax0.set_ylabel("Rate [kHz]")
        ax0.set_yscale("log")
        ax0.grid()
        ax0.tick_params(direction="in")
        if ax1:
            ax1.set_xlabel(rf"{self._online_offline} $p_T$ [GeV]")
            ax1.grid()
        else:
            ax0.set_xlabel(rf"{self._online_offline} $p_T$ [GeV]")
        fig.tight_layout()

    def _plot_single_version_rate_curves(self):
        """
        TODO: Write description!
        """
        version = self.cfg.version
        fig, ax = plt.subplots(figsize=self._figsize)
        hep.cms.label(ax=ax, llabel=self._llabel, com=self._com)

        for obj_key, rate_values in self.data.items():
            rate_values = rate_values[
                version
            ]  # TODO: This is not ideal. Think of a more elegant way to pass the data.
            ax.plot(
                list(rate_values.keys()),
                list(rate_values.values()),
                marker="o",
                label=f"{obj_key} @ {version}",
            )

        self._style_plot(fig, ax)
        for ext in [".png", ".pdf"]:
            plt.savefig(
                f"outputs/rate_plots/{version}_{self._online_offline}_{self.cfg.plot_name}{ext}"
            )

        # TODO: Add styling
        plt.close()

    def _plot_version_comparsion_rate_curves(self):
        """
        TODO: Write description!
        """
        v1, v2 = self.cfg.versions
        fig, axs = plt.subplots(
            2,
            1,
            figsize=self._figsize,
            sharex=True,
            gridspec_kw={"height_ratios": [3, 1]},
        )
        hep.cms.label(ax=axs[0], llabel=self._llabel, com=self._com)

        for obj_key, rate_values in self.data.items():
            xvalues = np.fromiter(rate_values[v1].keys(), dtype=float)
            v1_values = np.fromiter(rate_values[v1].values(), dtype=float)
            v2_values = np.fromiter(rate_values[v2].values(), dtype=float)
            p = axs[0].plot(
                xvalues,
                v1_values,
                marker="o",
                linestyle="solid",
                label=f"{obj_key} @ {v1}",
            )
            axs[0].plot(
                xvalues,
                v2_values,
                marker="o",
                linestyle="dashed",
                label=f"{obj_key} @ {v2}",
                color=p[0].get_color(),
            )
            axs[1].plot(
                xvalues,
                v1_values / v2_values,
                marker="o",
                linestyle="dotted",
                label=f"({obj_key} @ {v1}) / ({obj_key} @ {v2})",
            )
            axs[1].axhline(1, alpha=0.6, color="black")

        self._style_plot(fig, axs[0], axs[1])
        for ext in [".png", ".pdf"]:
            plt.savefig(
                f"outputs/rate_plots/{v1}-vs-{v2}_{self._online_offline}_{self.cfg.plot_name}{ext}"
            )

        plt.close()

    def plot(self):
        os.makedirs(f"outputs/rate_plots", exist_ok=True)
        if self.cfg.compare_versions:
            self._plot_version_comparsion_rate_curves()
        else:
            self._plot_single_version_rate_curves()


class RateComputer:
    def __init__(
        self,
        obj: str,
        obj_cuts: list,
        sample: str,
        version: str,
        apply_offline_conversion: bool,
    ):
        self.object = obj
        self.cuts = obj_cuts
        self.sample = sample
        self.version = version
        self.apply_offline_conversion = apply_offline_conversion
        self.arrays = self._load_cached_arrays()

    def _apply_scalings(self, arr: ak.Array) -> ak.Array:
        """
        Apply conversion from online pt to offline pt according to linear
        scaling function parametrized by the scalings computed by the
        objectPerformance code.
        If no file with scaling parameters is found, a warning is printed
        and the online pt is left unchanged.
        """
        try:
            scaling_params = scalings.load_scaling_params(self.object, self.version)
        except FileNotFoundError:
            warnings.warn(
                f"No file was found at `outputs/scalings/{self.version}/{self.object}.yaml`! Setting offline pt = online pt",
                UserWarning,
            )
        return scalings.compute_offline_pt(arr, scaling_params, "pt")

    def _load_cached_arrays(self):
        """
        Loads array for specified object/version combination
        from the cached parquet file.
        """
        fpath = f"cache/{self.version}/{self.version}_{self.sample}_{self.object}.parquet"  # TODO: unify place of cache folder across submodules
        arr = ak.from_parquet(fpath)

        # Remove object name prefix from array fields
        arr = ak.zip(
            {var.replace(self.object, "").lower(): arr[var] for var in arr.fields}
        )

        # Apply scalings if so configured
        if self.apply_offline_conversion:
            arr["pt"] = self._apply_scalings(arr)

        return arr

    def compute_rate(self, thr: float) -> float:
        """
        Computes rate at `thr` after application of all cuts specified in the
        object definition.
        """
        mask = self.arrays.pt > 0
        # TODO: Create Object object from utils and iterate over cuts from
        # there. Load object definitons as a function of version.
        for cut in self.cuts:
            mask = mask & eval(cut.replace("{", "self.arrays.").replace("}", ""))
        mask = mask & (self.arrays.pt >= thr)
        return ak.sum(ak.any(mask, axis=1)) / len(self.arrays)


class RatePlotCentral:
    """
    Class that orchestrates the creation of the rate plots
    (pt thresholds vs. rate).
    """

    def __init__(self, cfg_plots_path: str):
        with open(cfg_plots_path, "r") as f:
            self.cfg_plots = yaml.safe_load(f)

    def get_bins(self, plot_config: RatePlotConfig) -> np.ndarray:
        """
        Set bins according to configuration.
        """
        bin_width = plot_config.bin_width
        xmax = plot_config.xmax + 1e-5
        xmin = plot_config.xmin
        return np.arange(xmin, xmax, bin_width)

    def _compute_rates(
        self,
        plot_config: RatePlotConfig,
        obj_name: str,
        obj_properties: dict,
        apply_offline_conversion: bool,
    ) -> dict:
        """
        This function orchestrates the computations of
        the rates at the different thresholds that are
        to be plotted. Instances of RateComputer are created
        and called for this purpose.
        """
        rate_data: dict[str, dict] = {}

        # Iterate over version(s)
        for version in plot_config.versions:
            rate_data[version] = {}
            rate_computer = RateComputer(
                obj_name,
                obj_properties["cuts"],
                plot_config.sample,
                version,
                apply_offline_conversion,
            )

            # Iterate over thresholds
            for thr in self.get_bins(plot_config):
                rate_data[version][thr] = rate_computer.compute_rate(thr)

        return rate_data

    def run(self, apply_offline_conversion: bool = False):
        """
        This function iterates over all plots defined
        in the configuration file, computes the rates
        at the configured thresholds and passes it to
        the RatePlotter for plotting.
        """
        # Iterate over plots
        for plot_name, cfg_plot in self.cfg_plots.items():
            print("Plotting ", plot_name)
            plot_config = RatePlotConfig(plot_name, cfg_plot)
            rate_plot_data = {}

            # Iterate over objects in plot
            for obj_name, obj_properties in plot_config.objects.items():
                # TODO: Only iterate over object names and load object
                # properties from somewhere else, ideally a central place.
                rate_plot_data[obj_name] = self._compute_rates(
                    plot_config, obj_name, obj_properties, apply_offline_conversion
                )

            # Plot Rate vs. Threshold after all data has been aggregated
            plotter = RatePlotter(plot_config, rate_plot_data, apply_offline_conversion)
            plotter.plot()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "cfg_plots", help="Path of YAML file specifying the desired plots."
    )
    args = parser.parse_args()

    plotter = RatePlotCentral(args.cfg_plots)
    plotter.run()
    plotter.run(apply_offline_conversion=True)
