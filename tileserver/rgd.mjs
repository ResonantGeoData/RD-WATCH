import pg from 'pg';
import { commandOptions, createClient } from 'redis';

const dbPool = new pg.Pool({
  connectionString: process.env.RDWATCH_POSTGRESQL_URI,
});

const redisClient = createClient({
  url: process.env.RDWATCH_REDIS_URI,
});

const logging = process.env.RDWATCH_VECTOR_TILE_LOGGING || false;

await redisClient.connect();

const QUERY = `
  WITH evaluations AS (
    SELECT
      "rdwatch_siteevaluation"."id",
      "rdwatch_siteevaluation"."timestamp",
      "rdwatch_siteevaluation"."configuration_id",
      "rdwatch_siteevaluation"."region_id",
      "rdwatch_siteevaluation"."number",
      "rdwatch_siteevaluation"."start_date",
      "rdwatch_siteevaluation"."end_date",
      "rdwatch_siteevaluation"."geom" :: bytea,
      "rdwatch_siteevaluation"."label_id",
      "rdwatch_siteevaluation"."score",
      "rdwatch_siteevaluation"."version",
      "rdwatch_siteevaluation"."notes",
      "rdwatch_siteevaluation"."validated",
      "rdwatch_siteevaluation"."status",
      "rdwatch_siteevaluation"."cache_originator_file",
      "rdwatch_siteevaluation"."cache_timestamp",
      "rdwatch_siteevaluation"."cache_commit_hash",
      "rdwatch_siteevaluation"."id" AS "id",
      "rdwatch_siteevaluation"."id" AS "uuid",
      ST_AsMVTGeom(
        "rdwatch_siteevaluation"."geom",
        ST_TileEnvelope($1, $2, $3)
      ) AS "mvtgeom",
      "rdwatch_siteevaluation"."configuration_id" AS "configuration_id",
      "rdwatch_modelrun"."title" AS "configuration_name",
      "rdwatch_observationlabel"."slug" AS "label",
      EXTRACT(
        epoch
        FROM
          "rdwatch_siteevaluation"."timestamp"
      ) :: bigint AS "timestamp",
      EXTRACT(
        epoch
        FROM
          "rdwatch_siteevaluation"."start_date"
      ) :: bigint AS "timemin",
      EXTRACT(
        epoch
        FROM
          "rdwatch_siteevaluation"."end_date"
      ) :: bigint AS "timemax",
      "rdwatch_modelrun"."performer_id" AS "performer_id",
      "rdwatch_performer"."slug" AS "performer_name",
      "rdwatch_region"."name" AS "region",
      CASE
        WHEN (
          "rdwatch_performer"."slug" = 'TE'
          AND "rdwatch_siteevaluation"."score" = 1.0
        ) THEN TRUE
        ELSE FALSE
      END AS "groundtruth",
      "rdwatch_siteevaluation"."number" AS "site_number",
      CASE
        WHEN COUNT("rdwatch_siteobservation"."id") = 0 THEN TRUE
        ELSE FALSE
      END AS "site_polygon"
    FROM
      "rdwatch_siteevaluation"
      INNER JOIN "rdwatch_modelrun" ON (
        "rdwatch_siteevaluation"."configuration_id" = "rdwatch_modelrun"."id"
      )
      INNER JOIN "rdwatch_region" ON (
        "rdwatch_siteevaluation"."region_id" = "rdwatch_region"."id"
      )
      INNER JOIN "rdwatch_observationlabel" ON (
        "rdwatch_siteevaluation"."label_id" = "rdwatch_observationlabel"."id"
      )
      LEFT OUTER JOIN "rdwatch_siteobservation" ON (
        "rdwatch_siteevaluation"."id" = "rdwatch_siteobservation"."siteeval_id"
      )
      INNER JOIN "rdwatch_performer" ON (
        "rdwatch_modelrun"."performer_id" = "rdwatch_performer"."id"
      )
    WHERE
      (
        "rdwatch_siteevaluation"."configuration_id" = $4
        AND ST_Intersects(
          "rdwatch_siteevaluation"."geom",
          ST_TileEnvelope($1, $2, $3)
        )
      )
    GROUP BY
      "rdwatch_siteevaluation"."id",
      ST_AsMVTGeom(
        "rdwatch_siteevaluation"."geom",
        ST_TileEnvelope($1, $2, $3)
      ),
      "rdwatch_modelrun"."title",
      "rdwatch_observationlabel"."slug",
      EXTRACT(
        epoch
        FROM
          "rdwatch_siteevaluation"."timestamp"
      ) :: bigint,
      EXTRACT(
        epoch
        FROM
          "rdwatch_siteevaluation"."start_date"
      ) :: bigint,
      EXTRACT(
        epoch
        FROM
          "rdwatch_siteevaluation"."end_date"
      ) :: bigint,
      "rdwatch_modelrun"."performer_id",
      "rdwatch_performer"."slug",
      "rdwatch_region"."name",
      CASE
        WHEN (
          "rdwatch_performer"."slug" = 'TE'
          AND "rdwatch_siteevaluation"."score" = 1.0
        ) THEN TRUE
        ELSE FALSE
      END
  ),
  observations AS (
    SELECT
      "rdwatch_siteobservation"."id",
      "rdwatch_siteobservation"."siteeval_id",
      "rdwatch_siteobservation"."label_id",
      "rdwatch_siteobservation"."score",
      "rdwatch_siteobservation"."geom" :: bytea,
      "rdwatch_siteobservation"."constellation_id",
      "rdwatch_siteobservation"."spectrum_id",
      "rdwatch_siteobservation"."timestamp",
      "rdwatch_siteobservation"."notes",
      "rdwatch_siteobservation"."id" AS "id",
      ST_AsMVTGeom(
        "rdwatch_siteobservation"."geom",
        ST_TileEnvelope($1, $2, $3)
      ) AS "mvtgeom",
      "rdwatch_siteevaluation"."configuration_id" AS "configuration_id",
      "rdwatch_modelrun"."title" AS "configuration_name",
      T7."slug" AS "site_label",
      "rdwatch_siteevaluation"."number" AS "site_number",
      "rdwatch_observationlabel"."slug" AS "label",
      ST_Area(
        ST_Transform("rdwatch_siteobservation"."geom", 6933)
      ) AS "area",
      EXTRACT(
        epoch
        FROM
          "rdwatch_siteobservation"."timestamp"
      ) :: bigint AS "timemin",
      EXTRACT(
        epoch
        FROM
          MIN("rdwatch_siteobservation"."timestamp") OVER (
            PARTITION BY "rdwatch_siteobservation"."siteeval_id"
            ORDER BY
              "rdwatch_siteobservation"."timestamp" ROWS BETWEEN CURRENT ROW
              AND UNBOUNDED FOLLOWING EXCLUDE GROUP
          )
      ) :: bigint AS "timemax",
      "rdwatch_modelrun"."performer_id" AS "performer_id",
      "rdwatch_performer"."slug" AS "performer_name",
      "rdwatch_region"."name" AS "region",
      "rdwatch_siteevaluation"."version" AS "version",
      CASE
        WHEN (
          "rdwatch_performer"."slug" = 'TE'
          AND "rdwatch_siteevaluation"."score" = 1.0
        ) THEN TRUE
        ELSE FALSE
      END AS "groundtruth"
    FROM
      "rdwatch_siteobservation"
      INNER JOIN "rdwatch_siteevaluation" ON (
        "rdwatch_siteobservation"."siteeval_id" = "rdwatch_siteevaluation"."id"
      )
      INNER JOIN "rdwatch_modelrun" ON (
        "rdwatch_siteevaluation"."configuration_id" = "rdwatch_modelrun"."id"
      )
      INNER JOIN "rdwatch_observationlabel" ON (
        "rdwatch_siteobservation"."label_id" = "rdwatch_observationlabel"."id"
      )
      INNER JOIN "rdwatch_observationlabel" T7 ON ("rdwatch_siteevaluation"."label_id" = T7."id")
      INNER JOIN "rdwatch_performer" ON (
        "rdwatch_modelrun"."performer_id" = "rdwatch_performer"."id"
      )
      INNER JOIN "rdwatch_region" ON (
        "rdwatch_siteevaluation"."region_id" = "rdwatch_region"."id"
      )
    WHERE
      (
        "rdwatch_siteevaluation"."configuration_id" = $4
        AND ST_Intersects(
          "rdwatch_siteobservation"."geom",
          ST_TileEnvelope($1, $2, $3)
        )
        AND EXTRACT(YEAR FROM "rdwatch_siteobservation"."timestamp") = $5
      )
  ),
  regions AS (
    SELECT
      "rdwatch_region"."id",
      "rdwatch_region"."name",
      "rdwatch_region"."geom" :: bytea,
      "rdwatch_region"."name" AS "name",
      ST_AsMVTGeom(
        "rdwatch_region"."geom",
        ST_TileEnvelope($1, $2, $3)
      ) AS "mvtgeom"
    FROM
      "rdwatch_region"
      INNER JOIN "rdwatch_siteevaluation" ON (
        "rdwatch_region"."id" = "rdwatch_siteevaluation"."region_id"
      )
    WHERE
      (
        "rdwatch_siteevaluation"."configuration_id" = $4
        AND ST_Intersects(
          "rdwatch_region"."geom",
          ST_TileEnvelope($1, $2, $3)
        )
      )
  )
  SELECT
    (
      (
        SELECT
          ST_AsMVT(evaluations.*, $6, 4096, 'mvtgeom')
        FROM
          evaluations
      ) || (
        SELECT
          ST_AsMVT(observations.*, $7, 4096, 'mvtgeom')
        FROM
          observations
      ) || (
        SELECT
          ST_AsMVT(regions.*, $8, 4096, 'mvtgeom')
        FROM
          regions
      )
    )
`;

async function getCacheKey(modelRunId, z, x, y, year, randomKey) {
  const result = await dbPool.query(`
    SELECT
      MAX(rdwatch_siteevaluation.timestamp) AS latestEvaluationTimestamp,
      MAX(rdwatch_modelrun.created) AS modelRunTimestamp
    FROM
      rdwatch_modelrun
    LEFT JOIN
      rdwatch_siteevaluation ON rdwatch_modelrun.id = rdwatch_siteevaluation.configuration_id
    WHERE
      rdwatch_modelrun.id = $1
  `, [modelRunId]);

  const { latestEvaluationTimestamp, modelRunTimestamp } = result.rows[0];

  if (logging) {
  console.log(result.rows[0]);
  }

  const latestTimestamp = latestEvaluationTimestamp || modelRunTimestamp;

  return `rgd-vector-tile-${modelRunId}-${z}-${x}-${y}-${latestTimestamp}-${year}${randomKey ? "-"+randomKey : ''}`;
}

export async function getVectorTiles(modelRunId, z, x, y, year, randomKey) {
  const cacheKey = await getCacheKey(modelRunId, z, x, y, year, randomKey);
  if (logging) {
    console.log(`cacheKey: ${cacheKey}`);
  }

  let vectorTileData = await redisClient.get(commandOptions({ returnBuffers: true }), cacheKey);
  vectorTileData = null;

  if (logging) {
    if (vectorTileData) {
      console.log('cache hit!');
    } else {
      console.log('cache miss!')
    }
  }

  if (!vectorTileData) {
    const params = [z, x, y, modelRunId, year, `sites-${modelRunId}`, `observations-${modelRunId}`, `regions-${modelRunId}`];
    if (logging) {
      console.log(params)
    }
    const result = await dbPool.query(QUERY, params);
    if (logging) {
    console.log(result)
    }
    vectorTileData = result.rows[0]['?column?'];

    // Cache for 7 days. Don't bother awaiting, as we can do this in the background after this function returns.
    // We want to remove the randomKey if it exists so it caches the edited data
    cacheKey.replace(`-${randomKey}`, '');
    redisClient.set(cacheKey, vectorTileData, 'EX', 60 * 60 * 24 * 7);
  }
  return vectorTileData;
}
