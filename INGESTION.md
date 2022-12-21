# Getting data in

There is currently append-only support for ingesting data into the system.

## Create a `model-run`

A `model-run` is a grouping of site evaluations. This grouping can contain outputs of a machine learning model, ground truth outputs, etc. In order to ingest data, it must be associated with a `model-run`.

You can view and create `model-runs` on the `/api/model-runs` endpoint.

- GET `/api/model-runs`: list all
- GET `/api/model-runs/{id}`: retrieve a single instance
- POST `/api/model-runs`: create an instance

The following JSON is an example of data to be used to create a `model-run`:

```jsonc
//model-run.json
{
  // must be a valid performer short-code
  "performer": "KIT",
  // a human-readable title
  "title": "Ingestion 3.2",
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
    -X POST \
    -d @model-run.json \
    https://some.rgd.host/api/model-runs
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
  "bbox": null
}
```

## Add data to a `model-run`

You can `POST` a [Site Model Specification](https://smartgitlab.com/TE/standards/-/wikis/Site-Model-Specification) JSON to the endpoint `/api/model-runs/{id}/site-model`.

Following the above example, lets POST a [Site Model Specification](https://smartgitlab.com/TE/standards/-/wikis/Site-Model-Specification) JSON file in the current working directory named "site.json" to the newly created `model-run`:

```bash
$ curl \
    -H "Content-Type: application/json" \
    -X POST \
    -d @site.json \
    https://some.rgd.host/api/model-runs/12/site-model
```

Ensure the JSON correctly validates against the [Site Model Specification](https://smartgitlab.com/TE/standards/-/wikis/Site-Model-Specification). While many validation errors are reported, a malformed JSON will not report helpful errors. For example, the specification mandates each 'Observation' feature must include a `current_phase` string, but some data in the wild is not compliant with this and instead includes `"current_phase": null`. This is a malformed JSON and will not able to be parsed.
