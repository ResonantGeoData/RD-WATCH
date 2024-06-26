import postgres from 'postgres'
import { commandOptions, createClient } from 'redis';

const sql = postgres(process.env.RDWATCH_POSTGRESQL_URI);

const redisClient = createClient({
  url: process.env.RDWATCH_REDIS_URI,
});

const logging = process.env.RDWATCH_VECTOR_TILE_LOGGING || false;

await redisClient.connect();

function query(z, x, y, modelRunId, year) {
  return sql`
    WITH evaluations AS (
      SELECT
        "rdwatch_siteevaluation"."id",
        "rdwatch_siteevaluation"."timestamp",
        "rdwatch_siteevaluation"."configuration_id",
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
          ST_TileEnvelope(${z}, ${x}, ${y})
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
        "rdwatch_performer"."short_code" AS "performer_name",
        "rdwatch_region"."name" AS "region",
        CASE
          WHEN (
            "rdwatch_performer"."short_code" = 'TE'
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
        INNER JOIN "rdwatch_observationlabel" ON (
          "rdwatch_siteevaluation"."label_id" = "rdwatch_observationlabel"."id"
        )
        LEFT OUTER JOIN "rdwatch_siteobservation" ON (
          "rdwatch_siteevaluation"."id" = "rdwatch_siteobservation"."siteeval_id"
        )
        INNER JOIN "rdwatch_performer" ON (
          "rdwatch_modelrun"."performer_id" = "rdwatch_performer"."id"
        )
        INNER JOIN "rdwatch_region" ON (
          "rdwatch_modelrun"."region_id" = "rdwatch_region"."id"
        )
      WHERE
        (
          "rdwatch_siteevaluation"."configuration_id" = ${modelRunId}
          AND ST_Intersects(
            "rdwatch_siteevaluation"."geom",
            ST_TileEnvelope(${z}, ${x}, ${y})
          )
        )
      GROUP BY
        "rdwatch_siteevaluation"."id",
        ST_AsMVTGeom(
          "rdwatch_siteevaluation"."geom",
          ST_TileEnvelope(${z}, ${x}, ${y})
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
        "rdwatch_performer"."short_code",
        "rdwatch_region"."name",
        CASE
          WHEN (
            "rdwatch_performer"."short_code" = 'TE'
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
        -- Use previous polygon if current observation is from a different year
        CASE
          WHEN EXTRACT(YEAR FROM "rdwatch_siteobservation"."timestamp") != ${year} THEN ST_AsMVTGeom("prev_obs"."prev_observation_geom", ST_TileEnvelope(${z}, ${x}, ${y}))
          ELSE ST_AsMVTGeom("rdwatch_siteobservation"."geom", ST_TileEnvelope(${z}, ${x}, ${y}))
        END AS "mvtgeom",
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
        "rdwatch_performer"."short_code" AS "performer_name",
        "rdwatch_region"."name" AS "region",
        "rdwatch_siteevaluation"."version" AS "version",
        CASE
          WHEN (
            "rdwatch_performer"."short_code" = 'TE'
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
          "rdwatch_modelrun"."region_id" = "rdwatch_region"."id"
        )
        -- Join in the previous observation for the same site if it exists
        LEFT JOIN LATERAL (
          SELECT
            "id" AS "prev_observation_id",
            "geom" AS "prev_observation_geom"
          FROM
            "rdwatch_siteobservation" AS "prev_observation"
          WHERE
            "prev_observation"."siteeval_id" = "rdwatch_siteevaluation"."id"
            AND EXTRACT(YEAR FROM "prev_observation"."timestamp") < ${year}
          ORDER BY
            "prev_observation"."timestamp" DESC
          LIMIT 1
        ) AS prev_obs ON TRUE
      WHERE
        (
          "rdwatch_siteevaluation"."configuration_id" = ${modelRunId}
          AND ST_Intersects(
            CASE WHEN EXTRACT(YEAR FROM "rdwatch_siteobservation"."timestamp") < ${year}
              THEN "prev_obs"."prev_observation_geom"
              ELSE "rdwatch_siteobservation"."geom"
            END,
            ST_TileEnvelope(${z}, ${x}, ${y})
          )
          AND (
            EXTRACT(YEAR FROM "rdwatch_siteobservation"."timestamp") = ${year}
            OR prev_obs."prev_observation_id" IS NOT NULL
          )
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
          ST_TileEnvelope(${z}, ${x}, ${y})
        ) AS "mvtgeom"
      FROM
        "rdwatch_region"
        INNER JOIN "rdwatch_modelrun" ON (
          "rdwatch_region"."id" = "rdwatch_modelrun"."region_id"
        )
      WHERE
        (
          "rdwatch_modelrun"."id" = ${modelRunId}
          AND ST_Intersects(
            "rdwatch_region"."geom",
            ST_TileEnvelope(${z}, ${x}, ${y})
          )
        )
    )
    SELECT
      (
        (
          SELECT
            ST_AsMVT(evaluations.*, ${'sites-' + modelRunId}, 4096, 'mvtgeom')
          FROM
            evaluations
        ) || (
          SELECT
            ST_AsMVT(observations.*, ${'observations-' + modelRunId}, 4096, 'mvtgeom')
          FROM
            observations
        ) || (
          SELECT
            ST_AsMVT(regions.*, ${'regions-' + modelRunId}, 4096, 'mvtgeom')
          FROM
            regions
        )
      )
  `
}

async function getCacheKey(modelRunId, z, x, y, year, randomKey) {
  const result = await sql`
    SELECT
      MAX(rdwatch_siteevaluation.timestamp) AS latestEvaluationTimestamp,
      MAX(rdwatch_modelrun.created) AS modelRunTimestamp
    FROM
      rdwatch_modelrun
    LEFT JOIN
      rdwatch_siteevaluation ON rdwatch_modelrun.id = rdwatch_siteevaluation.configuration_id
    WHERE
      rdwatch_modelrun.id = ${modelRunId}
  `;
  const { latestevaluationtimestamp, modelruntimestamp } = result[0];

  if (logging) {
    console.log(result[0]);
  }

  const latestTimestamp = latestevaluationtimestamp || modelruntimestamp;

  return `rgd-vector-tile-${modelRunId}-${z}-${x}-${y}-${latestTimestamp}-${year}${randomKey ? "-"+randomKey : ''}`;
}

export async function getVectorTiles(modelRunId, z, x, y, year, randomKey) {
  const cacheKey = await getCacheKey(modelRunId, z, x, y, year, randomKey);
  if (logging) {
    console.log(`cacheKey: ${cacheKey}`);
  }

  let vectorTileData = await redisClient.get(commandOptions({ returnBuffers: true }), cacheKey);

  if (logging) {
    if (vectorTileData) {
      console.log('cache hit!');
    } else {
      console.log('cache miss!')
    }
  }

  if (!vectorTileData) {
    const result = await query(z, x, y, modelRunId, year);

    vectorTileData = result[0]['?column?'];

    // Cache for 7 days. Don't bother awaiting, as we can do this in the background after this function returns.
    // We want to remove the randomKey if it exists so it caches the edited data
    cacheKey.replace(`-${randomKey}`, '');
    redisClient.set(cacheKey, vectorTileData, 'EX', 60 * 60 * 24 * 7);
  }
  return vectorTileData;
}
