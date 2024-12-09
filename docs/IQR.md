# Iterative Query Refinement

## Getting Started Locally

### Initial IQR Data

To avoid generating the IQR mappings from scratch, you should have a `iqr-data.tar.gz` file with the following contents:

```
models/
    faiss_index_params.json
    faiss_index
sites/
    *.geojson
workdir/
    data.memorySet.pickle
    descriptor_set.pickle
    idx2uid.mem_kvstore.pickle
    uid2idx.mem_kvstore.pickle
```

Extract `iqr-data.tar.gz` to a suitable location. We will refer to it as `/path/to/iqr-data` from here on out.

### Docker Compose Volumes

Edit the `iqr_rest` service in `docker-compose.override.yaml`. Specifically, the volumes must be updated with the following mounts. These are commented accordingly in the `docker-compose.override.yaml` file.

**IMPORTANT**: Replace the `/path/to/iqr-data` path prefix with the correct path.

- `/path/to/iqr-data/workdir:/iqr/workdir`
- `/path/to/iqr-data/models:/iqr/models`

### Ingesting The Sites

First, start the docker services and perform the requisite migrations and setup.

```bash
docker compose up -d
docker compose run --rm django poetry run django-admin migrate
docker compose run --rm django poetry run django-admin createsuperuser
docker compose run --rm django poetry run django-admin loaddata lookups
```

Now, we can ingest the sites provided in the IQR data archive. The following snippet assumes a bash shell currently located in the RD-WATCH repo root.

**IMPORTANT**: Replace the `/path/to/iqr-data` path prefix with the correct path.

```bash
for region in "KR_R001" "KR_R002" "CH_R001" "NZ_R001"
do
  python ./scripts/loadModelRun.py "$region" "/path/to/iqr-data/sites/${region}_*.geojson" --title "$region" --performer_shortcode TE
done
```

### Loading The WorldView Images

To ensure that the IQR query results have an associated image, open the RD-WATCH interface in the browser and download the "WV" satellite chips for every model run. This may take a long time!

## Running IQR through RD-WATCH

1. Navigate to <http://localhost:8080/#/iqr> to enable IQR.
1. Select a model run, and then select a site. If the site has IQR enabled, then there will be an IQR button (as shown below). Clicking this button will initiate an IQR query on that site, and a right sidebar will show up with the results.

    <img width="32" height="32" src="images/iqr-button.png">

1. IQR refinement occurs in two steps:
   1. Update positive, neutral, and negative results in the IQR result listing.
   1. Run "Refine Query" to generate a new list of IQR results.
