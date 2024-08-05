import json
import os

import click
from shapely.geometry import mapping, shape


@click.command()
@click.argument(
    'input_folder', type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
def convert_folder_to_centroids(input_folder):
    """Convert polygons in all GeoJSON files in a
    folder to theircentroid points and save to a
    new folder."""
    output_folder = f"{input_folder.replace('/', '')}_points"
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if filename.endswith('.geojson'):
            input_file_path = os.path.join(input_folder, filename)
            output_file_path = os.path.join(output_folder, filename)

            with open(input_file_path) as input_file:
                geojson_data = json.load(input_file)

                if 'features' not in geojson_data:
                    click.echo(
                        f"Skipping {filename}: \
                            Invalid GeoJSON file (no 'features' key)."
                    )
                    continue

                new_features = []
                for feature in geojson_data['features']:
                    geom = shape(feature['geometry'])
                    centroid = geom.centroid
                    new_feature = {
                        'type': 'Feature',
                        'geometry': mapping(centroid),
                        'properties': feature['properties'],
                    }
                    new_features.append(new_feature)

                new_geojson_data = {
                    'type': 'FeatureCollection',
                    'features': new_features,
                }

                with open(output_file_path, 'w') as output_file:
                    json.dump(new_geojson_data, output_file, indent=2)

            click.echo(
                f'Converted centroids for {filename} saved to {output_file_path}'
            )


if __name__ == '__main__':
    convert_folder_to_centroids()
