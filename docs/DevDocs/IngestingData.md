### Ingesting Data

## RDWATCH_MODEL_RUN_API_KEY
Check the `./dev/.env.docker-compose` environment file or the `.env` file in the root of the repository for the presence of the `RDWATCH_MODEL_RUN_API_KEY` variable.
This is a special key used for services outside of the standard Django login to be able to push data into the system.
The key will be used in the scripts and in the headers for pushing data into the system. Copy the value from that file when running the below script against a local instance. When running against a production deployment, you'll need to acquire an API key for that instance and use that instead.


## Loading Ground Truth Data
Within the `scripts` directory is a python script named `loadGroundTruth.py`.  This file can be used in conjunction with the ground truth annotations located in the annotation Repo:
[Annotation Repo](https://smartgitlab.com/TE/annotations)
Running a command like:

```bash
python loadGroundTruth.py ~/AnnotationRepoLocation --rgd-api-key {RDWATCH_MODEL_RUN_API_KEY}
```

will load all of the annotations for the ground truth while skipping the regions.


## Loading Single Model Runs
Within the `scripts` directory is a python script named `loadModelRuns.py`. This can be used to load a folder filled with geojson data into the system by using a command like:

```bash
python loadModelRuns.py 'KR_0001' "./site_models/KR_R001_*.geojson" --title Test_Eval_12 --performer_shortcode 'KIT' --eval_num 12 --eval_run_num 0 --rgd-api-key {RDWATCH_MODEL_RUN_API_KEY}
```

By default, this command uploads to the RGD server hosted at `http://localhost:8000`, but that can be changed by passing an optional `--rgd-endpoint` argument to the command.
Be sure that the system is up and running before running the commands.
The above command will load the data that match the provided glob exprssion and give it the title 'Test_Eval_12'. The `eval_num` and `eval_run_num` aren't required unless the scoring database is going to be connected to the system.

## Scoring

The [Metrics and Test Framework](https://smartgitlab.com/TE/metrics-and-test-framework#creating-a-metrics-database) can be used in addition with RGD to display scores from results.
In development mode a scoring Database is automatically initialized at URI: `postgresql+psycopg2://scoring:secretkey@localhost:5433/scoring`

To score data:
- Clone the [Metrics and Test Framework](https://smartgitlab.com/TE/metrics-and-test-framework) repo.
- In the Metrics and Test Framework repo:
  - Copy the `alembic_example.ini` to `alembic.ini` and set the `sqlalchemy.url = postgresql+psycopg2://scoring:secretkey@localhost:5433/scoring`
  - Run `pip install -e .` to install the metrics-and-test-framework package
  - Run `alembic upgrade head` to initialize the scoring database schema
  - Execute the scoring code from inside the metrics and test framework:
```
  python -m iarpa_smart_metrics.run_evaluation \
               --roi KR_R001 \
               --gt_dir ../annotations/site_models/ \
               --rm_dir ../KR_R001/region_models/ \
               --sm_dir ../KR_R001/site_models/ \
               --output_dir ../KR_R001/output \
               --eval_num 12 \
               --eval_run_num 0 \
               --performer kit \
               --no-viz \
               --no-viz-detection-table \
               --no-viz-comparison-table \
               --no-viz-associate-metrics \
               --no-viz-activity-metrics \
               --sequestered_id KR_R001 \
               --db_conn_str postgresql+psycopg2://scoring:secretkey@localhost:5433/scoring
```
- the `rm_dir` and `sm_dir` shgould be your test annotaitons.
- ground truth annotations can be retrieved from the [Annotation Repo](https://smartgitlab.com/TE/annotations)
- be sure to set the `val_num` and `eval_run_num` and remember them when ingesting data into RGD. The `region`, `eval_num`, `eval_run_num` and `performer` are used to connect data loaded in RGD to the scoring data.

## Manually Loading

### Create a `model-run`

A `model-run` is a grouping of site evaluations. This grouping can contain outputs of a machine learning model, ground truth outputs, etc. In order to ingest data, it must be associated with a `model-run`.

You can view and create `model-runs` on the `/api/model-runs` endpoint.

- GET `/api/model-runs`: list all
- GET `/api/model-runs/{id}`: retrieve a single instance
- POST `/api/model-runs`: create an instance

Prior to creating a model run, you may have to create a performer to associate it with. RD-WATCH comes pre-configured with some performers by default; you can send a request to the `/api/performers/` endpoint to check the available performers:

```bash
$ curl https://some.rgd.host/api/performers/
```

To create a new performer, you can make a separate POST request to the API.
The following JSON is an example of data to be used to create a `performer`:

```jsonc
// performer.json
{
  "team_name": "Kitware",
  "short_code": "KIT"
}
```

To create this performer:

```bash
$ curl \
    -H "Content-Type: application/json" \
    -H "X-RDWATCH-API-KEY: {RDWATCH_MODEL_RUN_API_KEY}" \
    -X POST \
    -d @performer.json \
    https://some.rgd.host/api/performers/
```

Once you've ensured the desired performer exists, you can create a model run.
The following JSON is an example of data to be used to create a `model-run`:

```jsonc
//model-run.json
{
  // must be a valid performer short-code
  "performer": "KIT",
  // must be a valid region string
  "region": "KW_R001",
  // a human-readable title
  "title": "Ingestion 3.2",
  // number of hours after upload when this model run should be automatically deleted.
  // exclude this field if you want the model run to remain in the database permanently.
  "expiration_time": 2,
  // can be any JSON that helps keep track of what this model-run is
  "parameters": {
    "any": "data"
  }
}
```

To create this `model-run`:

```bash
$ curl \
    -H "Content-Type: application/json" \
    -H "X-RDWATCH-API-KEY: {RDWATCH_MODEL_RUN_API_KEY}" \
    -X POST \
    -d @model-run.json \
    https://some.rgd.host/api/model-runs/
```

You'll get the newly created `model-run` as a response:

```json
{
  "id": 12,
  "title": "Ingestion 3.2",
  "region": null,
  "performer": {
    "id": 7,
    "team_name": "Kitware",
    "short_code": "KIT"
  },
  "parameters": {
    "any": "data"
  },
  "numsites": 0,
  "score": null,
  "timestamp": null,
  "timerange": null,
  "bbox": null,
  "created": "<creation_datetime>",
  "expiration_time": "01:00:00"
}
```

## Add data to a `model-run`

You can `POST` a [Site Model Specification](https://smartgitlab.com/TE/standards/-/wikis/Site-Model-Specification) JSON to the endpoint `/api/model-runs/{id}/site-model/` or a [Region Model Specification](https://smartgitlab.com/TE/standards/-/wikis/Region-Model-Specification) JSON to the endpoint `/api/model-runs/{id}/region-model/`.

Following the above example, lets POST a [Site Model Specification](https://smartgitlab.com/TE/standards/-/wikis/Site-Model-Specification) JSON file in the current working directory named "site.json" to the newly created `model-run`:

```bash
$ curl \
    -H "Content-Type: application/json" \
    -H "X-RDWATCH-API-KEY: {RDWATCH_MODEL_RUN_API_KEY}" \
    -X POST \
    -d @site.json \
    https://some.rgd.host/api/model-runs/12/site-model/
```

Ensure the JSON correctly validates against the [Site Model Specification](https://smartgitlab.com/TE/standards/-/wikis/Site-Model-Specification). While many validation errors are reported, a malformed JSON will not report helpful errors. For example, the specification mandates each 'Observation' feature must include a `current_phase` string, but some data in the wild is not compliant with this and instead includes `"current_phase": null`. This is a malformed JSON and will not able to be parsed.
