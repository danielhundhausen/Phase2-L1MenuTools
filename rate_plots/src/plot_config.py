class PlotConfig:

    def __init__(self, name, cfg: dict):
        self._name = name
        self._cfg = cfg

    @property
    def plot_name(self):
        return self._name

    @property
    def sample(self):
        return self._cfg["sample"]

    @property
    def n_bins(self):
        return self._cfg["binning"]["num"]

    @property
    def x_min(self):
        return self._cfg["binning"]["start"]

    @property
    def x_max(self):
        return self._cfg["binning"]["stop"]

    @property
    def xlabel(self):
        return self._cfg["xlabel"]

    @property
    def ylabel(self):
        return self._cfg["ylabel"]

    @property
    def compare_versions(self):
        if len(self.versions) == 1:
            return False
        if len(self.versions) == 2:
            return True
        if len(self.versions) > 2:
            raise ValueError("Only a single or the comparison between two version is supported.")

    @property
    def versions(self):
        return list(self._cfg["objects"].keys())

    @property
    def objects(self):
        return self._cfg["objects"][self.versions[0]].keys()

