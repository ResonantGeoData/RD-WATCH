# Getting data in

There is currently append-only support for ingesting data into the system.

You can `POST` a [Site Model Specification](https://smartgitlab.com/TE/standards/-/wikis/Site-Model-Specification) JSON to the endpoint `/api/site-model`.

Example `curl` command posting a [Site Model Specification](https://smartgitlab.com/TE/standards/-/wikis/Site-Model-Specification) JSON file in the current working directory named "site.json":
```bash
$ curl \
    -H "Content-Type: application/json" \
    -X POST \
    -d @site.json \
    https://resonantgeodata.dev/api/site-model
```

Ensure the JSON correctly validates against the [Site Model Specification](https://smartgitlab.com/TE/standards/-/wikis/Site-Model-Specification). While many validation errors are reported, a malformed JSON will not report helpful errors. For example, the specification mandates each 'Observation' feature must include a `current_phase` string, but some data in the wild is not compliant with this and instead includes `"current_phase": null`. This is a malformed JSON and will not able to be parsed.
