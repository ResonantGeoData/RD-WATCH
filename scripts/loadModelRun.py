from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from glob import glob
from multiprocessing import Pool

import requests

# TODO: Parameterize
rgd_endpoint = 'http://localhost:8000'


def main():
    parser = argparse.ArgumentParser(description='Upload sites to RGD')

    parser.add_argument('region_id', type=str, help='Region ID')
    parser.add_argument(
        'site_models_glob', type=str, help='Glob string for sites to upload'
    )
    parser.add_argument(
        '--rgd-auth-cookie',
        required=False,
        type=str,
        help='RGD Authentication cookie, e.g.: token=<LONG BASE64 STRING>',
    )
    parser.add_argument(
        '--title',
        default='Ground Truth',
        type=str,
        help='Title of the model run ' '(default: "Ground Truth")',
    )
    parser.add_argument(
        '--performer_shortcode',
        type=str,
        default='TE',
        help='Performer shortcode (default: "TE")',
    )
    parser.add_argument(
        '--proposal',
        default=False,
        action=argparse.BooleanOptionalAction,
        help='Marks all siteModels as proposals',
    )
    parser.add_argument('--eval_num', default=None, type=int, help='Evaluation Number')
    parser.add_argument(
        '--eval_run_num', default=None, type=int, help='Evaluation  Run Number'
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
    upload_to_rgd(**vars(parser.parse_args()))


def upload_to_rgd(
    region_id: str,
    site_models_glob: str,
    rgd_auth_cookie: str,
    parallelism: int,
    title='Ground Truth',
    performer_shortcode='TE',
    proposal: str | None = None,
    eval_num: int | None = None,
    eval_run_num: int | None = None,
    expiration_time: int | None = None,
):
    # Check that our run doesn't already exist
    model_run_results_url = f'{rgd_endpoint}/api/model-runs/'
    cookies = None
    if rgd_auth_cookie:
        cookies = {'token': rgd_auth_cookie}
    model_runs_result = requests.get(
        model_run_results_url,
        params={'limit': '0'},
        headers={'Content-Type': 'application/json'},
        cookies=cookies,
    )

    existing_model_run = None
    for model_run in model_runs_result.json().get('items', ()):
        if (
            model_run['title'] == title
            and model_run['performer']['short_code'] == performer_shortcode
            and 'region' in model_run
            and model_run['region'] == region_id
        ):  # noqa
            existing_model_run = model_run
            break

    if existing_model_run is not None:
        model_run_id = model_run['id']
    else:
        post_model_url = f'{rgd_endpoint}/api/model-runs/'

        post_model_data = {
            'performer': performer_shortcode,
            'title': title,
            'region': {'name': region_id},
            'parameters': {},
        }
        if expiration_time is not None:
            post_model_data['expiration_time'] = expiration_time
        if eval_num is not None:
            post_model_data['evaluation'] = eval_num
        if eval_run_num is not None:
            post_model_data['evaluation_run'] = eval_run_num
        if proposal is True:
            post_model_data['proposal'] = True
        if title == 'Ground Truth':
            post_model_data['parameters'] = {'ground_truth': True}

        post_model_result = requests.post(
            post_model_url,
            json=post_model_data,
            headers={'Content-Type': 'application/json'},
            cookies=cookies,
        )
        model_run_id = post_model_result.json()['id']

    post_site_url = f'{rgd_endpoint}/api/model-runs/{model_run_id}/site-model/'
    print(site_models_glob)
    site_files = glob(site_models_glob)
    with Pool(processes=parallelism) as pool:
        pool.starmap(
            post_site,
            zip(
                [post_site_url] * len(site_files),
                site_files,
                [rgd_auth_cookie] * len(site_files),
                strict=True,
            ),
        )


def post_site(post_site_url, site_filepath, rgd_auth_cookie):
    print(f"Uploading '{site_filepath}' ..")
    with open(site_filepath) as f:
        cookie = None
        if rgd_auth_cookie:
            cookie = {'token': rgd_auth_cookie}
        try:
            response = requests.post(
                post_site_url,
                json=json.load(f),
                headers={'Content-Type': 'application/json'},
                cookies=cookie,
            )
        except Exception:
            print('Exception occurred (printed below)')
            traceback.print_exception(*sys.exc_info())

    print(response)
    if response.status_code != 201:
        print(f'Error uploading site, status ' f'code: [{response.status_code}]')

    return response


if __name__ == '__main__':
    sys.exit(main())
