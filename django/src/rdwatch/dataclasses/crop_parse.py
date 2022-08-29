from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from django.contrib.gis.gdal import GDALRaster


@dataclass
class CropParse:
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    timestamp: datetime
    sensor: str

    def open_raster(self, filepath: str | Path) -> GDALRaster:
        """
        Open the raster at the given file path using the metadata from this CropParse
        and return it as a GDALRaster.
        """
        if isinstance(filepath, str):
            filepath = Path(filepath)

        with open(filepath, "rb") as f:
            rst = GDALRaster(f.read())

        if not len(rst.bands) == 1:
            raise ValueError("Expected single-band raster")

        bnd = rst.bands[0]

        return GDALRaster(
            {
                "width": bnd.width,
                "height": bnd.height,
                "scale": [
                    (self.xmax - self.xmin) / bnd.width,
                    (self.ymax - self.ymin) / bnd.height,
                ],
                "origin": [self.xmin, self.ymin],
                "skew": [0, 0],
                "srid": 4326,
                "datatype": bnd.datatype(),
                "bands": [
                    {
                        "data": bnd.data(),
                        "nodata_value": bnd.nodata_value,
                    }
                ],
            }
        ).transform(3857)

    # TODO: use PEP-673's typing.Self for return type annotation
    # once mypy supports it https://github.com/python/mypy/issues/11871
    @classmethod
    def from_string(cls, crop_string: str) -> CropParse:
        pattern = re.compile(
            r"""
                ^crop_
                (?P<timestamp>\d+T\d+Z)_
                (?P<ymin_dir>[NS])(?P<ymin>\d+\.\d+)
                (?P<xmin_dir>[EW])(?P<xmin>\d+\.\d+)_
                (?P<ymax_dir>[NS])(?P<ymax>\d+\.\d+)
                (?P<xmax_dir>[EW])(?P<xmax>\d+\.\d+)_
                (?P<sensor>(?:L8) | (?:S2))_
                \d$
            """,
            re.X,
        )

        match = pattern.match(crop_string)
        if not match:
            raise TypeError("Invalid crop string")

        return cls(
            xmin=_latlong_str_to_float(match["xmin_dir"], match["xmin"]),
            ymin=_latlong_str_to_float(match["ymin_dir"], match["ymin"]),
            xmax=_latlong_str_to_float(match["xmax_dir"], match["xmax"]),
            ymax=_latlong_str_to_float(match["ymax_dir"], match["ymax"]),
            timestamp=datetime.strptime(match["timestamp"], "%Y%m%dT%H%M%SZ"),
            sensor=match["sensor"],
        )


def _latlong_str_to_float(direction: str, latlong_str: str) -> float:
    latlong = float(latlong_str)
    if direction in ("W", "S"):
        latlong *= -1
    return latlong
