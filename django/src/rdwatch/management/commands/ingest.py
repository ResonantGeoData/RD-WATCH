import json
import re
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import iso3166

from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand

from rdwatch.models import (
    HyperParameters,
    Region,
    SiteEvaluation,
    SiteObservation,
    lookups,
)


@lru_cache
def get_constellation(slug: str) -> lookups.Constellation:
    return lookups.Constellation.objects.get(slug=slug)


@lru_cache
def get_commonband(slug: str) -> lookups.CommonBand | None:
    if slug == "salient":
        return None
    return lookups.CommonBand.objects.get(slug=slug)


@lru_cache
def get_performer(slug: str) -> lookups.Performer:
    return lookups.Performer.objects.get(slug=slug)


@lru_cache
def get_regionclassification(slug: str) -> lookups.RegionClassification:
    return lookups.RegionClassification.objects.get(slug=slug)


@lru_cache
def get_label(slug: str) -> lookups.ObservationLabel:
    return lookups.ObservationLabel.objects.get(slug=slug)


@dataclass(frozen=True)
class CropParse:
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    timestamp: datetime
    constellation: lookups.Constellation
    spectrum: lookups.CommonBand | None

    @property
    def bbox(self):
        return (self.xmin, self.ymin, self.xmax, self.ymax)


def get_cropparse(crop_string: str) -> CropParse:
    pattern = re.compile(
        r"""
            ^crop_
            (?P<timestamp>\d+T\d+Z)_
            (?P<ymin_dir>[NS])(?P<ymin>\d+\.\d+)
            (?P<xmin_dir>[EW])(?P<xmin>\d+\.\d+)_
            (?P<ymax_dir>[NS])(?P<ymax>\d+\.\d+)
            (?P<xmax_dir>[EW])(?P<xmax>\d+\.\d+)_
            (?P<constellation>(?:L8) | (?:S2))_0_
            (?P<spectrum>\w+)
            \.tif$
        """,
        re.X,
    )
    match = pattern.match(crop_string)
    if not match:
        raise ValueError("Invalid crop string")

    def _latlong(direction: str, latlong_str: str) -> float:
        latlong = float(latlong_str)
        if direction in ("W", "S"):
            latlong *= -1
        return latlong

    return CropParse(
        xmin=_latlong(match["xmin_dir"], match["xmin"]),
        ymin=_latlong(match["ymin_dir"], match["ymin"]),
        xmax=_latlong(match["xmax_dir"], match["xmax"]),
        ymax=_latlong(match["ymax_dir"], match["ymax"]),
        timestamp=datetime.strptime(
            match["timestamp"][:-1] + "+0000",
            "%Y%m%dT%H%M%S%z",
        ),
        constellation=get_constellation(match["constellation"]),
        spectrum=get_commonband(match["spectrum"]),
    )


@dataclass(frozen=True)
class KWCOCOParse:
    code: str
    timestamp: datetime
    threshold: float | None


def get_kwcocoparse(kwcoco_file: Path, process: str) -> KWCOCOParse:
    code = kwcoco_file.parent.name.split("_")[-1]

    kwcoco = json.loads(kwcoco_file.read_text())
    kwcoco_info: list = kwcoco["info"]
    proc = next(
        filter(
            lambda t: t["properties"]["name"] == process,
            kwcoco_info,
        )
    )

    raw_timestr = proc["properties"]["timestamp"]
    fixed_timestr = raw_timestr[:-1] + raw_timestr[-1].zfill(2) + "00"
    timestamp = datetime.strptime(
        fixed_timestr,
        "%Y-%m-%dT%H%M%S%z",
    )

    match proc:
        case {"properties": {"args": {"track_kwargs": track_kwargs_str}}}:
            track_kwargs = json.loads(track_kwargs_str)
            threshold = track_kwargs["thresh"]
        case _:
            threshold = None

    return KWCOCOParse(
        code=code,
        timestamp=timestamp,
        threshold=threshold,
    )


def iterkwcoco(
    root: Path,
    kwcoco_file_name: str,
    kwcoco_process_name: str,
) -> Iterable[tuple[KWCOCOParse, Path]]:
    for kwcoco_dir in root.iterdir():
        kwcoco_file = kwcoco_dir / kwcoco_file_name
        if not kwcoco_file.exists():
            continue
        kwcoco = get_kwcocoparse(
            kwcoco_file,
            kwcoco_process_name,
        )
        yield kwcoco, kwcoco_dir


class Command(BaseCommand):
    help = "Ingest KWCOCO directory"

    def add_arguments(self, parser):
        parser.add_argument(
            "directory",
            type=Path,
            help="A KWCOCO direcotry",
        )

    def handle(self, *args, **options):
        directory: Path = options["directory"]

        siteevals: list[SiteEvaluation] = []
        regions: dict[str, Region] = {}
        hyperparams: dict[tuple[str, str, float], HyperParameters] = {}
        siteobservations: list[SiteObservation] = []

        for predcfg_kwcoco, predcfg_dir in iterkwcoco(
            root=directory,
            kwcoco_file_name="pred.kwcoco.json",
            kwcoco_process_name="watch.tasks.fusion.predict",
        ):
            for trackcfg_kwcoco, trackcfg_dir in iterkwcoco(
                root=(predcfg_dir / "tracking"),
                kwcoco_file_name="tracks.json",
                kwcoco_process_name="watch.cli.kwcoco_to_geojson",
            ):
                cfg_key = (
                    predcfg_kwcoco.code,
                    trackcfg_kwcoco.code,
                    trackcfg_kwcoco.threshold,
                )
                if cfg_key not in hyperparams:
                    cfg = HyperParameters(
                        performer=get_performer("KIT"),
                        parameters={
                            "predcfg": predcfg_kwcoco.code,
                            "trackcfg": trackcfg_kwcoco.code,
                            "thresh": trackcfg_kwcoco.threshold,
                        },
                    )
                    hyperparams[cfg_key] = cfg  # type: ignore
                else:
                    cfg = hyperparams[cfg_key]

                for geojson_file in (trackcfg_dir / "tracked_sites").iterdir():
                    geojson = json.loads(geojson_file.read_text())
                    site_json = geojson["features"][0]
                    region_str = site_json["properties"]["region_id"]

                    if region_str not in regions:
                        countrystr, numstr = region_str.split("_")
                        contrynum = iso3166.countries_by_alpha2[countrystr].numeric
                        region = Region(
                            country=int(contrynum),
                            classification=get_regionclassification(numstr[0]),
                            number=int(numstr[1:]),
                        )
                        regions[region_str] = region
                    else:
                        region = regions[region_str]

                    siteeval = SiteEvaluation(
                        configuration=cfg,
                        region=region,
                        number=int(site_json["properties"]["site_id"][8:]),
                        timestamp=max(
                            predcfg_kwcoco.timestamp,
                            trackcfg_kwcoco.timestamp,
                        ),
                        geom=GEOSGeometry(json.dumps(site_json["geometry"])),
                        score=site_json["properties"]["score"],
                    )
                    siteevals.append(siteeval)

                    for feature in geojson["features"][1:]:
                        properties = feature["properties"]
                        crop_path = Path(properties["source"])
                        crop_parse = get_cropparse(crop_path.name)
                        geom = GEOSGeometry(json.dumps(feature["geometry"]))
                        geom.srid = 4326
                        geom.transform(3857)

                        siteobservations.append(
                            SiteObservation(
                                siteeval=siteeval,
                                label=get_label(
                                    ("_")
                                    .join(properties["current_phase"].split(" "))
                                    .lower()
                                ),
                                score=properties["score"],
                                geom=geom,
                                constellation=crop_parse.constellation,
                                spectrum=crop_parse.spectrum,
                                timestamp=crop_parse.timestamp,
                            )
                        )

        Region.objects.bulk_create(regions.values())
        HyperParameters.objects.bulk_create(hyperparams.values())
        SiteEvaluation.objects.bulk_create(siteevals)
        SiteObservation.objects.bulk_create(siteobservations)
