import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import djclick as click  # type: ignore
import orjson

from django.contrib.gis.gdal import GDALRaster
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from rdwatch.models import (
    PredictionConfiguration,
    Saliency,
    SaliencyTile,
    SatelliteImage,
    Site,
    SiteObservation,
    TrackingConfiguration,
)

label_mapping = {
    "Active Construction": SiteObservation.ACTIVE_CONSTRUCTION,
    "Post Construction": SiteObservation.POST_CONSTRUCTION,
    "Site Preparation": SiteObservation.SITE_PREPARATION,
}


@dataclass
class CropParse:
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    timestamp: datetime
    sensor: str
    band: str

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

    @classmethod
    def from_string(cls, crop_string: str) -> "CropParse":
        pattern = re.compile(
            r"""
                ^crop_
                (?P<timestamp>\d+T\d+Z)_
                (?P<ymin_dir>[NS])(?P<ymin>\d+\.\d+)
                (?P<xmin_dir>[EW])(?P<xmin>\d+\.\d+)_
                (?P<ymax_dir>[NS])(?P<ymax>\d+\.\d+)
                (?P<xmax_dir>[EW])(?P<xmax>\d+\.\d+)_
                (?P<sensor>(?:L8) | (?:S2))_0_
                (?P<band>\w+)
                \.tif$
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
            band=match["band"],
        )


def _latlong_str_to_float(direction: str, latlong_str: str) -> float:
    latlong = float(latlong_str)
    if direction in ("W", "S"):
        latlong *= -1
    return latlong


def open_raster(fn: str) -> GDALRaster:
    path = Path(fn)

    with open(path, "rb") as f:
        rst = GDALRaster(f.read())

    if not len(rst.bands) == 1:
        raise ValueError("Expected single-band raster")

    bnd = rst.bands[0]
    info = CropParse.from_string(path.name)

    return GDALRaster(
        {
            "width": bnd.width,
            "height": bnd.height,
            "scale": [
                (info.xmax - info.xmin) / bnd.width,
                (info.ymax - info.ymin) / bnd.height,
            ],
            "origin": [info.xmin, info.ymin],
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


def tile_raster(rst: GDALRaster) -> Iterable[GDALRaster]:
    if not len(rst.bands) == 1:
        raise ValueError("Expected single-band raster")
    if not rst.srid == 3857:
        raise ValueError("Expected raster projected to SRID 3857")

    bnd = rst.bands[0]
    tilesize = 64

    for xoffset in range(0, bnd.width, tilesize):
        for yoffset in range(0, bnd.height, tilesize):
            size = (
                tilesize if xoffset + tilesize <= rst.width else rst.width - xoffset,
                tilesize if yoffset + tilesize <= rst.height else rst.height - yoffset,
            )
            data = bnd.data(
                offset=(xoffset, yoffset),
                size=size,
            )
            yield GDALRaster(
                {
                    "width": tilesize,
                    "height": tilesize,
                    "scale": rst.scale,
                    "origin": [
                        rst.origin.x + xoffset * rst.scale.x,
                        rst.origin.y + yoffset * rst.scale.y,
                    ],
                    "skew": rst.skew,
                    "srid": rst.srid,
                    "nr_of_bands": 1,
                    "datatype": bnd.datatype(),
                    "bands": [
                        {
                            "data": data,
                            "size": size,
                            "nodata_value": bnd.nodata_value,
                        }
                    ],
                }
            )


def _ingest_geojson(
    site_geojson_file: Path,
    prediction_configuration: PredictionConfiguration,
    tracking_configuration: TrackingConfiguration,
) -> Iterable[SiteObservation]:
    """
    Ingest the geojson file at the given path into the Site model,
    creating all SiteObservation instances.
    """
    site_observation_geojson = orjson.loads(site_geojson_file.read_bytes())
    site_json = site_observation_geojson["features"][0]
    site_geometry = GEOSGeometry(orjson.dumps(site_json["geometry"]))
    site, _ = Site.objects.get_or_create(
        geometry=site_geometry,
        score=site_json["properties"]["score"],
    )

    # Ingest each site observation in the geojson
    for site_observation_json in site_observation_geojson["features"][1:]:
        properties: dict = site_observation_json["properties"]
        label = label_mapping[properties["current_phase"]]
        score = properties["score"]
        geometry = GEOSGeometry(orjson.dumps(site_observation_json["geometry"]))
        crop_path = Path(properties["source"])
        crop_string = crop_path.name
        crop_parse = CropParse.from_string(crop_string)
        sensor_name = crop_parse.sensor
        satellite_timestamp = crop_parse.timestamp
        tif_filepath = (
            site_geojson_file.parents[3]
            / "_assets"
            / "pred_saliency"
            / f"{crop_path.parent.name}_salient.tif"
        )
        satellite_image, satellite_image_created = SatelliteImage.objects.get_or_create(
            sensor=sensor_name,
            timestamp=satellite_timestamp,
        )
        saliency, saliency_created = Saliency.objects.get_or_create(
            configuration=prediction_configuration,
            source=satellite_image,
        )
        # TODO: not sure why some crop strings don't have
        # a corresponding saliency TIF; there's quite a few in
        # the sample data that don't. If one is encountered,
        # just skip it and move on to the next raster.
        if saliency_created:
            if not tif_filepath.exists():
                relative_filepath = str(
                    tif_filepath.relative_to(site_geojson_file.parents[4])
                )
                click.echo(message=f"WARNING: {relative_filepath} doesn't exist.")
                Saliency.objects.filter(pk=saliency.pk).delete()
                if satellite_image_created:
                    SatelliteImage.objects.filter(pk=satellite_image.pk).delete()
                continue
            raster = crop_parse.open_raster(tif_filepath)
            saliency_tiles: Iterable[SaliencyTile] = (
                SaliencyTile(raster=tile, saliency=saliency)
                for tile in tile_raster(raster)
            )
            SaliencyTile.objects.bulk_create(
                saliency_tiles,
                ignore_conflicts=True,
            )
        yield SiteObservation(
            site=site,
            configuration=tracking_configuration,
            label=label,
            score=score,
            geometry=geometry,
            saliency=saliency,
            band=crop_parse.band,
        )


@click.command()
@click.argument(
    "directory", required=True, type=click.Path(exists=True, path_type=Path)
)
def ingest(directory: Path):
    """
    Ingests the WATCH format files located in the given directory.

    NOTE: DIRECTORY must be a valid file path to a kwcoco directory.
    """

    for pred in directory.iterdir():
        if not pred.is_dir():
            continue

        prediction_json_file = pred / "pred.kwcoco.json"

        if not prediction_json_file.exists():
            click.echo(message=f"WARNING: {prediction_json_file} doesn't exist.")
            continue

        prediction_json = orjson.loads(
            (pred / "pred.kwcoco.json")
            .read_bytes()
            .replace("NaN".encode("utf-8"), "null".encode("utf-8"))
        )
        prediction_process_info = prediction_json["info"][1]

        assert (
            prediction_process_info["properties"]["name"]
            == "watch.tasks.fusion.predict"
        )

        timestamp_str = prediction_process_info["properties"]["timestamp"]
        prediction_timestamp_str = (
            timestamp_str[:-1] + timestamp_str[-1].zfill(2) + "00"
        )

        prediction_timestamp = datetime.strptime(
            prediction_timestamp_str,
            "%Y-%m-%dT%H%M%S%z",
        )
        prediction_slug = pred.stem.split("_")[-1]
        prediction_configuration, _ = PredictionConfiguration.objects.get_or_create(
            slug=prediction_slug,
            timestamp=prediction_timestamp,
        )

        for trackcfg in (pred / "tracking").iterdir():
            if not trackcfg.is_dir():
                continue

            tracks_json = orjson.loads((trackcfg / "tracks.json").read_bytes())
            tracks_process_info = list(
                filter(lambda t: t["type"] == "process", tracks_json["info"])
            )[0]

            tracking_threshold = orjson.loads(
                tracks_process_info["properties"]["args"]["track_kwargs"]
            )["thresh"]
            timestamp_str = tracks_process_info["properties"]["timestamp"]
            tracking_timestamp_str = (
                timestamp_str[:-1] + timestamp_str[-1].zfill(2) + "00"
            )

            tracking_timestamp = datetime.strptime(
                tracking_timestamp_str,
                "%Y-%m-%dT%H%M%S%z",
            )
            tracking_timestamp.utcoffset
            tracking_slug = trackcfg.name.split("_")[-1]
            tracking_configuration, _ = TrackingConfiguration.objects.get_or_create(
                slug=tracking_slug,
                timestamp=tracking_timestamp,
                threshold=tracking_threshold,
            )

            for site_geojson_file in (trackcfg / "tracked_sites").iterdir():
                assert site_geojson_file.suffix == ".geojson"
                SiteObservation.objects.bulk_create(
                    _ingest_geojson(
                        site_geojson_file,
                        prediction_configuration,
                        tracking_configuration,
                    ),
                    ignore_conflicts=True,
                )
