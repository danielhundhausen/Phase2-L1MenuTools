class RatePlotConfig:
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
    def bin_width(self):
        return self._cfg["binning"]["step"]

    @property
    def xmin(self):
        return self._cfg["binning"]["min"]

    @property
    def xmax(self):
        return self._cfg["binning"]["max"]

    @property
    def compare_versions(self):
        return len(self.versions) == 2

    @property
    def versions(self):
        try:
            versions = self._cfg["versions"]
        except KeyError:
            raise ValueError(
                "`versions` must be specified as either a single"
                "version (e.g. `V30`) or a list of exactly two versions"
                "(e.g. [`V29`, `V30`])."
            )
        if isinstance(versions, str):
            return [versions]
        if isinstance(versions, list):
            assert (
                len(versions) == 2
            ), "To compare versions, exactly two must be specified."
            return versions

    @property
    def version(self):
        version = self._cfg["versions"]
        assert isinstance(version, str)
        return version

    @property
    def objects(self):
        return self._cfg["objects"]