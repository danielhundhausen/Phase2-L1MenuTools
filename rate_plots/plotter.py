#!/afs/cern.ch/user/d/dhundhau/public/miniconda3/envs/py310/bin/python
import argparse
import os

import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
from progress.bar import IncrementalBar
import yaml
import json

from plot_config import PlotConfig

plt.style.use(hep.style.CMS)


class Plotter():

    def _create_new_plot(self):
        fig, ax = plt.subplots(figsize=(10, 10))
        hep.cms.label(ax=ax, llabel="Phase-2 Simulation", com=14)
        return fig, ax


class RatePlotter(Plotter):

    def __init__(self, cfg, data):
        self.cfg = cfg
        self.data = data

    def _style_plot(self, fig, ax, legend_loc="upper right"):
        ax.legend(loc=legend_loc, frameon=False)
        ax.set_xlabel(rf"{self.cfg.xlabel}")
        ax.set_ylabel(rf"{self.cfg.ylabel}")
        ax.tick_params(direction="in")
        fig.tight_layout()

    def _plot_single_version_rate_curves(self):
        """
        TODO: Write description!
        """
        version = self.cfg.versions[0]
        fig, ax = self._create_new_plot()

        for obj_key, rate_values in self.data.items():
            rate_values = rate_values[version]  # TODO: This is not ideal. Think of a more elegant way to pass the data.
            ax.plot(
               list(rate_values.keys()),
               list(rate_values.values()),
               marker='o',
               label=f"{obj_key} @ {version}"
            )
                    
        self._style_plot(fig, ax)
        for ext in [".png",".pdf"]:
            plt.savefig(f"outputs/{version}_{self.cfg.plot_name}{ext}")

        # TODO: Add styling
        plt.close()

    def _plot_version_comparsion_rate_curves(self):
        """
        TODO: Write description!
        """
        v1, v2 = self.cfg.versions
        fig, ax = self._create_new_plot()

        # TODO: Add the actual rate curves

        self._style_plot(fig, ax)
        for ext in [".png",".pdf"]:
            plt.savefig(f"outputs/rate_plots/{v1}-vs-{v2}_{self.cfg.plot_name}{ext}")

        # TODO: Add ratio plot
        # TODO: Add grouped styling (same color, dashed vs. non-dashed)
        plt.close()

    def plot(self):
        os.makedirs(f"outputs/rate_plots", exist_ok=True)
        if self.cfg.compare_versions:
            self._plot_version_comparsion_rate_curves()
        else:
            self._plot_single_version_rate_curves()


class RatePlotCentral:
    """
    Class that orchestrates the plotting of the rate plots
    (pt thresholds vs. rate).
    """

    def __init__(self, cfg_plots_path):
        with open(cfg_plots_path, 'r') as f:
            self.cfg_plots = yaml.safe_load(f)

    def compute_rates(self, plot_config, obj_properties) -> dict:
        rate_data = {}
        # Iterate over version(s)
        for v in plot_config.versions:
            rate_data[v] = {}
            # Iterate over thresholds
            for thr in np.logspace(plot_config.x_min, plot_config.x_max, plot_config.n_bins):
                if v == "V30":  # TODO: Compute actual value
                    rate_data[v][thr] = 1
                else:
                    rate_data[v][thr] = 2
        return rate_data

    def run(self):
        """
        This function iterates over all plots defined
        in the configuration file, computes the rates
        at the configured thresholds and passes it to
        the RatePlotter for plotting.
        """
        # Iterate over plots
        for plot_name, cfg_plot in self.cfg_plots.items():
            plot_config = PlotConfig(plot_name, cfg_plot)
            rate_plot_data = {}

            # Iterate over objects in plot
            for obj_name, obj_properties in plot_config.objects.items():
                print(obj_name)
                rate_plot_data[obj_name] = self.compute_rates(plot_config, obj_properties)

            # Plot Rate vs. Threshold after all data has been aggregated
            plotter = RatePlotter(plot_config, rate_plot_data)
            plotter.plot()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "cfg_plots",
        help="Path of YAML file specifying the desired plots."
    )
    args = parser.parse_args()

    plotter = RatePlotCentral(args.cfg_plots)
    plotter.run()

