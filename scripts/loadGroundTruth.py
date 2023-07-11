import json
import argparse
import sys
from pathlib import Path

import requests

rgd_endpoint = "http://localhost:8000"

existing_model_runs = {}


def main():
    parser = argparse.ArgumentParser(description="Upload ground truth to server")
    parser.add_argument(
        "baseDir",
        type=str,
        help="Base Annotation Directory with subdirectories of site_models\
          || site-model || region_models || region-model",
    )
    parser.add_argument(
        "--skip_regions", action="store_true", help="expiration time in hours"
    )
    parser.add_argument(
        "--rgd-auth-cookie",
        required=False,
        type=str,
        help="RGD Authentication cookie, e.g.: "
        "AWSELBAuthSessionCookie-0=<LONG BASE64 STRING>",
    )
    parser.add_argument(
        "--expiration_time", default=None, type=int, help="expiration time in hours"
    )

    upload_to_rgd(**vars(parser.parse_args()))


def upload_to_rgd(baseDir, skip_regions, rgd_auth_cookie, expiration_time):
    check_vals = [("site_models", "site-model")]
    cookies = None
    if not skip_regions:
        check_vals.append(("region_models", "region-model"))
    if rgd_auth_cookie:
        cookies = {"AWSELBAuthSessionCookie-0": rgd_auth_cookie}
    for dir, endpoint in check_vals:
        geojson_dir_path = Path(baseDir) / dir
        for file in sorted(list(geojson_dir_path.iterdir())):
            if file.is_dir() or not file.suffix == ".geojson":
                print(f"Skipping {file}")
                continue

            model_run_name = "_".join(file.name.split("_")[:2])
            if model_run_name not in existing_model_runs:
                # Create model run if it doesn't exist
                print(f"Creating model run {model_run_name}")
                post_model_data = {
                    "performer": "TE",
                    "title": "Ground Truth",
                    "parameters": {},
                }
                if expiration_time is not None:
                    post_model_data["expiration_time"] = expiration_time

                res = requests.post(
                    f"{rgd_endpoint}/api/model-runs/",
                    json=post_model_data,
                    headers={"Content-Type": "application/json"},
                    cookies=cookies,
                )
                res.raise_for_status()
                existing_model_runs[model_run_name] = res.json()["id"]

            model_run_id = existing_model_runs[model_run_name]

            print(f"  Posting {file}...")
            res = requests.post(
                f"{rgd_endpoint}/api/model-runs/{model_run_id}/{endpoint}",
                data=file.read_text(),
                headers={"Content-Type": "application/json"},
                cookies=cookies,
            )
            if res.status_code >= 400:
                print(res.status_code, res.text)
                continue


if __name__ == "__main__":
    sys.exit(main())
