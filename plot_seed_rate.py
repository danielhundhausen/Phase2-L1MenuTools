import os

import matplotlib.pyplot as plt
import mplhep as hep
import pandas as pd


plt.style.use(hep.style.CMS)


# Parameters
xvals = [0, 30, 60, 90, 120, 150]
plot_name = "tau_seed_rate_plot_test"
csv_path = "outputs/V29/rate_tables/rates_tau_plot.csv"
csv_path = "outputs/V29/rate_tables/rates_full_Final_V29.csv"
xlabel = rf"$p_T$ [GeV]"
_figsize = (10, 10)
_llabel = "Phase-2 Simulation"
_com = 14
_outdir = "outputs/rate_plots/"
_version = "V29"


# Load rates from csv
rate_table = pd.read_csv(csv_path)
print(rate_table)


def _style_plot(fig, ax0, ax1=None, legend_loc="upper right"):
    ax0.legend(loc=legend_loc, frameon=False)
    ax0.set_ylabel("Rate [kHz]")
    ax0.set_yscale("log")
    ax0.grid()
    ax0.tick_params(direction="in")
    if ax1:
        ax1.set_xlabel(xlabel)
        ax1.grid()
    else:
        ax0.set_xlabel(xlabel)
    fig.tight_layout()


def plot(yvals):
    fig, ax = plt.subplots(figsize=_figsize)
    hep.cms.label(ax=ax, llabel=_llabel, com=_com)

    label = "foo"

    plot_dict = {
        "x_values": xvals,
        "y_values": yvals,
        "object": None,  # TODO
        "label": label,
        "version": _version,
    }

    ax.plot(
        xvals,
        yvals,
        marker="o",
        label=label,
    )

    _style_plot(fig, ax)

    # Save plot
    fname = os.path.join(_outdir, f"{_version}_seedRate_{plot_name}")
    plt.savefig(fname + ".png")
    plt.savefig(fname + ".pdf")
    print("Saved to ", fname)
    plt.close()


if __name__ == "__main__":
    yvals = rate_table["rate"][:len(xvals)]
    plot(yvals)
