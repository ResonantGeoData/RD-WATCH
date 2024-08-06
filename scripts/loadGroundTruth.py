#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

import requests


def main():
    parser = argparse.ArgumentParser(description='Upload ground truth to server')
    parser.add_argument(
        'base_dir',
        type=str,
        help='Base Annotation Directory with subdirectories of site_models\
          || site-model || region_models || region-model',
    )
    parser.add_argument(
        '--skip_regions', action='store_true', help='expiration time in hours'
    )
    parser.add_argument(
        '--rgd-api-key',
        type=str,
        help='RGD API key',
        default='secretkey',
    )
    parser.add_argument(
        '--expiration_time', default=None, type=int, help='expiration time in hours'
    )
    parser.add_argument(
        '--parallelism',
        default=os.cpu_count(),
        type=int,
        help='max number of uploads to perform at once',
    )
    parser.add_argument(
        '--rgd-endpoint',
        default='http://localhost:8000',
        type=str,
        help='RGD server base URL',
    )

    upload_to_rgd(**vars(parser.parse_args()))


def _upload_model_run(
    region: str,
    endpoint: str,
    model_runs: dict[str, list[Path]],
    rgd_api_key: str,
    expiration_time: int | None,
    rgd_endpoint: str,
) -> None:
    # Create model run
    print(f'Creating model run for {region}')
    post_model_data = {
        'performer': 'TE',
        'region': region,
        'title': 'Ground Truth',
        'parameters': {},
    }
    if expiration_time is not None:
        post_model_data['expiration_time'] = str(expiration_time)

    res = requests.post(
        f'{rgd_endpoint}/api/model-runs/',
        json=post_model_data,
        headers={'Content-Type': 'application/json', 'X-RDWATCH-API-KEY': rgd_api_key},
    )
    res.raise_for_status()

    model_run_id = res.json()['id']

    for file in model_runs[region]:
        print(f'Uploading {file}')
        res = requests.post(
            f'{rgd_endpoint}/api/model-runs/{model_run_id}/{endpoint}/',
            data=file.read_text(),
            headers={
                'Content-Type': 'application/json',
                'X-RDWATCH-API-KEY': rgd_api_key,
            },
        )
        if res.status_code >= 400:
            print(res.status_code, res.text)
            continue


def upload_to_rgd(
    base_dir: Path,
    skip_regions: bool,
    rgd_api_key: str | None,
    expiration_time: str,
    parallelism: int,
    rgd_endpoint: str,
):
    check_vals = [('site_models', 'site-model')]
    if not skip_regions:
        check_vals.append(('region_models', 'region-model'))

    for dir, endpoint in check_vals:
        model_runs: defaultdict[str, list[Path]] = defaultdict(list)

        geojson_dir_path = Path(base_dir) / dir
        geojson_files = sorted(geojson_dir_path.iterdir())

        for file in geojson_files:
            if file.is_dir() or not file.suffix == '.geojson':
                print(f'Skipping {file}')
                continue

            region = '_'.join(file.name.split('_')[:2])
            model_runs[region].append(file)

        with Pool(processes=parallelism) as pool:
            pool.starmap(
                _upload_model_run,
                zip(
                    model_runs.keys(),
                    [endpoint] * len(model_runs),
                    [model_runs] * len(model_runs),
                    [rgd_api_key] * len(model_runs),
                    [expiration_time] * len(model_runs),
                    [rgd_endpoint] * len(model_runs),
                    strict=True,
                ),
            )


if __name__ == '__main__':
    sys.exit(main())
