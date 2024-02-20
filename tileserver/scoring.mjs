import pg from 'pg';
import { commandOptions, createClient } from 'redis';

const dbPool = new pg.Pool({
  connectionString: process.env.RDWATCH_POSTGRESQL_SCORING_URI,
});

const redisClient = createClient({
  url: process.env.RDWATCH_REDIS_URI,
});

await redisClient.connect();

const QUERY = `
  WITH sites AS (
    SELECT
      "site"."uuid",
      "site"."site_id",
      "site"."region_id",
      "site"."evaluation_run_uuid",
      "site"."originator",
      "site"."version",
      "site"."crs",
      "site"."mgrs",
      "site"."status_annotated",
      "site"."predicted_phase",
      "site"."predicted_date",
      "site"."score",
      "site"."union_geometry",
      "site"."union_area",
      "site"."sites",
      "site"."start_date",
      "site"."end_date",
      "site"."start_activity",
      "site"."end_activity",
      "site"."len_activity",
      "site"."end_observed_activity",
      "site"."len_observed_activity",
      "site"."max_area",
      "site"."first_obs_date",
      "site"."last_obs_date",
      "site"."confidence_score",
      "site"."site_id" AS "id",
      ST_AsMVTGeom(
        ST_Transform(
          ST_GeomFromText("site"."union_geometry", 4326),
          3857
        ),
        ST_TileEnvelope($1, $2, $3)
      ) AS "mvtgeom",
      "site"."evaluation_run_uuid" AS "configuration_id",
      CONCAT(
        'Eval ',
        CONCAT(
          "evaluation_run"."evaluation_number",
          CONCAT(
            ' ',
            CONCAT(
              "evaluation_run"."evaluation_run_number",
              CONCAT(' ', "evaluation_run"."performer")
            )
          )
        )
      ) AS "configuration_name",
      CASE
        WHEN "site"."status_annotated" IS NOT NULL THEN LOWER(REPLACE("site"."status_annotated", ' ', '_'))
        ELSE 'unknown'
      END AS "label",
      EXTRACT(
        epoch
        FROM
          "site"."start_date"
      ) :: bigint AS "timestamp",
      EXTRACT(
        epoch
        FROM
          "site"."start_date"
      ) :: bigint AS "timemin",
      EXTRACT(
        epoch
        FROM
          "site"."end_date"
      ) :: bigint AS "timemax",
      "site"."originator" AS "performer_id",
      "site"."originator" AS "performer_name",
      "site"."region_id" AS "region",
      CASE
        WHEN (
          "site"."originator" = 'te'
          OR "site"."originator" = 'iMERIT'
        ) THEN TRUE
        ELSE FALSE
      END AS "groundtruth",
      FALSE AS "site_polygon",
      SUBSTRING("site"."site_id", 9) AS "site_number",
      CASE
        WHEN (
          "site"."originator" = 'TE'
          OR "site"."originator" = 'iMERIT'
        ) THEN (
          SELECT
            U0."color_code"
          FROM
            "evaluation_broad_area_search_detection" U0
          WHERE
            (
              U0."activity_type" = 'overall'
              AND U0."evaluation_run_uuid" = $4
              AND U0."rho" = 0.5
              AND U0."site_truth" = ("site"."site_id")
              AND U0."tau" = 0.2
            )
        )
        WHEN (
          NOT ("site"."originator" = 'te')
          AND NOT ("site"."originator" = 'iMERIT')
        ) THEN (
          SELECT
            U0."color_code"
          FROM
            "evaluation_broad_area_search_proposal" U0
          WHERE
            (
              U0."activity_type" = 'overall'
              AND U0."evaluation_run_uuid" = $4
              AND U0."rho" = 0.5
              AND U0."site_proposal" = ("site"."site_id")
              AND U0."tau" = 0.2
            )
        )
        ELSE NULL
      END AS "color_code"
    FROM
      "site"
      INNER JOIN "evaluation_run" ON (
        "site"."evaluation_run_uuid" = "evaluation_run"."uuid"
      )
    WHERE
      (
        "site"."evaluation_run_uuid" = $4
        AND ST_Intersects(
          ST_Transform(
            ST_GeomFromText("site"."union_geometry", 4326),
            3857
          ),
          ST_TileEnvelope($1, $2, $3)
        )
      )
  ),
  observations AS (
    SELECT
      "observation"."uuid",
      "observation"."site_uuid",
      "observation"."date",
      "observation"."source",
      "observation"."sensor",
      "observation"."phase",
      "observation"."score",
      "observation"."crs",
      "observation"."geometry",
      "observation"."is_site_boundary",
      "observation"."area",
      "observation"."confidence_score",
      "observation"."uuid" AS "id",
      "observation"."date" AS "timestamp",
      ST_AsMVTGeom(
        ST_Transform(
          ST_GeomFromText("observation"."geometry", 4326),
          3857
        ),
        ST_TileEnvelope($1, $2, $3)
      ) AS "mvtgeom",
      "site"."evaluation_run_uuid" AS "configuration_id",
      CONCAT(
        'Eval ',
        CONCAT(
          "evaluation_run"."evaluation_number",
          CONCAT(
            ' ',
            CONCAT(
              "evaluation_run"."evaluation_run_number",
              CONCAT(' ', "evaluation_run"."performer")
            )
          )
        )
      ) AS "configuration_name",
      "site"."status_annotated" AS "site_label",
      SUBSTRING("site"."site_id", 9) AS "site_number",
      CASE
        WHEN "observation"."phase" IS NOT NULL THEN LOWER(REPLACE("observation"."phase", ' ', '_'))
        ELSE 'unknown'
      END AS "label",
      ST_Area(
        ST_Transform(
          ST_Transform(
            ST_GeomFromText("observation"."geometry", 4326),
            3857
          ),
          6933
        )
      ) AS "area",
      "observation"."site_uuid" AS "siteeval_id",
      EXTRACT(
        epoch
        FROM
          "observation"."date"
      ) :: bigint AS "timemin",
      EXTRACT(
        epoch
        FROM
          MIN("observation"."date") OVER (
            PARTITION BY "observation"."site_uuid"
            ORDER BY
              "observation"."date" ROWS BETWEEN CURRENT ROW
              AND UNBOUNDED FOLLOWING EXCLUDE GROUP
          )
      ) :: bigint AS "timemax",
      "site"."originator" AS "performer_id",
      "site"."originator" AS "performer_name",
      "site"."region_id" AS "region",
      "site"."version" AS "version",
      "observation"."confidence_score" AS "score",
      CASE
        WHEN (
          "site"."originator" = 'te'
          OR "site"."originator" = 'iMERIT'
        ) THEN TRUE
        ELSE FALSE
      END AS "groundtruth"
    FROM
      "observation"
      INNER JOIN "site" ON ("observation"."site_uuid" = "site"."uuid")
      INNER JOIN "evaluation_run" ON (
        "site"."evaluation_run_uuid" = "evaluation_run"."uuid"
      )
    WHERE
      (
        "site"."evaluation_run_uuid" = $4
        AND ST_Intersects(
          ST_Transform(
            ST_GeomFromText("observation"."geometry", 4326),
            3857
          ),
          ST_TileEnvelope($1, $2, $3)
        )
      )
  ),
  regions AS (
    SELECT
      "region"."id",
      "region"."start_date",
      "region"."end_date",
      "region"."crs",
      "region"."mgrs",
      "region"."geometry",
      "region"."area",
      "region"."id" AS "name",
      ST_AsMVTGeom(
        ST_Transform(ST_GeomFromText("region"."geometry", 4326), 3857),
        ST_TileEnvelope($1, $2, $3)
      ) AS "mvtgeom"
    FROM
      "region"
    WHERE
      (
        "region"."id" = (
          SELECT
            V0."region_id"
          FROM
            "site" V0
            INNER JOIN "evaluation_run" V1 ON (V0."evaluation_run_uuid" = V1."uuid")
          WHERE
            (
              V0."evaluation_run_uuid" = $4
              AND ST_Intersects(
                ST_Transform(ST_GeomFromText(V0."union_geometry", 4326), 3857),
                ST_TileEnvelope($1, $2, $3)
              )
            )
          LIMIT
            1
        )
        AND ST_Intersects(
          ST_Transform(ST_GeomFromText("region"."geometry", 4326), 3857),
          ST_TileEnvelope($1, $2, $3)
        )
      )
  )
  SELECT
  (
      (
        SELECT
          ST_AsMVT(sites.*, $5, 4096, 'mvtgeom')
        FROM
          sites
      ) || (
        SELECT
          ST_AsMVT(observations.*, $6, 4096, 'mvtgeom')
        FROM
          observations
      ) || (
        SELECT
          ST_AsMVT(regions.*, $7, 4096, 'mvtgeom')
        FROM
          regions
      )
    )
`;

async function getCacheKey(modelRunId, z, x, y) {
  // TODO: is this cache key sufficiently unique?
  const result = await dbPool.query(`
    SELECT
      start_datetime
    FROM
      evaluation_run
    WHERE
    evaluation_run.uuid = $1
  `, [modelRunId]);

  const { start_datetime } = result.rows[0];

  return `scoring-vector-tile-${modelRunId}-${z}-${x}-${y}-${start_datetime}`;
}

export async function getVectorTiles(modelRunId, z, x, y) {
  const cacheKey = await getCacheKey(modelRunId, z, x, y);

  let vectorTileData = await redisClient.get(commandOptions({ returnBuffers: true }), cacheKey);
  // TODO: re-enable caching
  vectorTileData = null;
  if (!vectorTileData) {
    const params = [z, x, y, modelRunId, `sites-${modelRunId}`, `observations-${modelRunId}`, `regions-${modelRunId}`];
    const result = await dbPool.query(QUERY, params);
    vectorTileData = result.rows[0]['?column?'];

    // Cache for 7 days. Don't bother awaiting, as we can do this in the background after this function returns.
    redisClient.set(cacheKey, vectorTileData, 'EX', 60 * 60 * 24 * 7);
  }

  return vectorTileData;
}
