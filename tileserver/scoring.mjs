import postgres from 'postgres'
import { commandOptions, createClient } from 'redis';

const sql = postgres(process.env.RDWATCH_POSTGRESQL_SCORING_URI);

const redisClient = createClient({
  url: process.env.RDWATCH_REDIS_URI,
});

const logging = process.env.RDWATCH_VECTOR_TILE_LOGGING || false;

await redisClient.connect();

function query(z, x, y, modelRunId, year) {
  return sql`
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
        "site"."site_id" AS "uuid",
        ST_AsMVTGeom(
          ST_Transform(
            ST_GeomFromText("site"."union_geometry", 4326),
            3857
          ),
          ST_TileEnvelope(${z}, ${x}, ${y})
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
            "site"."originator" = 'te'
            OR "site"."originator" = 'iMERIT'
          ) THEN (
            SELECT
              U0."color_code"
            FROM
              "evaluation_broad_area_search_detection" U0
            WHERE
              (
                U0."activity_type" = 'overall'
                AND U0."evaluation_run_uuid" = ${modelRunId}
                AND U0."rho" = 0.5
                AND U0."site_truth" = ("site"."site_id")
                AND U0."tau" = 0.2
                AND U0."min_confidence_score" = 0.0
                AND (U0."min_spatial_distance_threshold" IS NULL OR U0."min_spatial_distance_threshold" = 100.0)
                AND (U0."central_spatial_distance_threshold" IS NULL OR U0."central_spatial_distance_threshold" = 500.0)
                AND U0."max_spatial_distance_threshold" IS NULL
                AND (U0."min_temporal_distance_threshold" IS NULL OR U0."min_temporal_distance_threshold" = 730.0)
                AND U0."central_temporal_distance_threshold" IS NULL
                AND U0."max_temporal_distance_threshold" IS NULL
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
                AND U0."evaluation_run_uuid" = ${modelRunId}
                AND U0."rho" = 0.5
                AND U0."site_proposal" = ("site"."site_id")
                AND U0."tau" = 0.2
                AND U0."min_confidence_score" = 0.0
                AND (U0."min_spatial_distance_threshold" IS NULL OR U0."min_spatial_distance_threshold" = 100.0)
                AND (U0."central_spatial_distance_threshold" IS NULL OR U0."central_spatial_distance_threshold" = 500.0)
                AND U0."max_spatial_distance_threshold" IS NULL
                AND (U0."min_temporal_distance_threshold" IS NULL OR U0."min_temporal_distance_threshold" = 730.0)
                AND U0."central_temporal_distance_threshold" IS NULL
                AND U0."max_temporal_distance_threshold" IS NULL
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
          "site"."evaluation_run_uuid" = ${modelRunId}
          AND ST_Intersects(
            ST_Transform(
              ST_GeomFromText("site"."union_geometry", 4326),
              3857
            ),
            ST_TileEnvelope(${z}, ${x}, ${y})
          )
        )
    ),
    sites_points AS (
      SELECT
        "site"."uuid" AS "id",
        ST_AsMVTGeom(
          ST_Transform(
            ST_GeomFromText("site"."point_geometry", 4326),
            3857
          ),
          ST_TileEnvelope(${z}, ${x}, ${y})
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
          WHEN "site"."point_status" IS NOT NULL THEN LOWER(REPLACE("site"."point_status", ' ', '_'))
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
            "site"."originator" = 'te'
            OR "site"."originator" = 'iMERIT'
          ) THEN (
            SELECT
              U0."color_code"
            FROM
              "evaluation_broad_area_search_detection" U0
            WHERE
              (
                U0."activity_type" = 'overall'
                AND U0."evaluation_run_uuid" = ${modelRunId}
                AND U0."rho" = 0.5
                AND U0."site_truth" = ("site"."site_id")
                AND U0."tau" = 0.2
                AND U0."min_confidence_score" = 0.0
                AND (U0."min_spatial_distance_threshold" IS NULL OR U0."min_spatial_distance_threshold" = 100.0)
                AND (U0."central_spatial_distance_threshold" IS NULL OR U0."central_spatial_distance_threshold" = 500.0)
                AND U0."max_spatial_distance_threshold" IS NULL
                AND (U0."min_temporal_distance_threshold" IS NULL OR U0."min_temporal_distance_threshold" = 730.0)
                AND U0."central_temporal_distance_threshold" IS NULL
                AND U0."max_temporal_distance_threshold" IS NULL
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
                AND U0."evaluation_run_uuid" = ${modelRunId}
                AND U0."rho" = 0.5
                AND U0."site_proposal" = ("site"."site_id")
                AND U0."tau" = 0.2
                AND U0."min_confidence_score" = 0.0
                AND (U0."min_spatial_distance_threshold" IS NULL OR U0."min_spatial_distance_threshold" = 100.0)
                AND (U0."central_spatial_distance_threshold" IS NULL OR U0."central_spatial_distance_threshold" = 500.0)
                AND U0."max_spatial_distance_threshold" IS NULL
                AND (U0."min_temporal_distance_threshold" IS NULL OR U0."min_temporal_distance_threshold" = 730.0)
                AND U0."central_temporal_distance_threshold" IS NULL
                AND U0."max_temporal_distance_threshold" IS NULL
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
          "site"."evaluation_run_uuid" = ${modelRunId}
          AND ST_Intersects(
            ST_Transform(
              ST_GeomFromText("site"."point_geometry", 4326),
              3857
            ),
            ST_TileEnvelope(${z}, ${x}, ${y})
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
        CASE
          WHEN EXTRACT(YEAR FROM "observation"."date") < ${year} THEN ST_AsMVTGeom(ST_Transform(ST_GeomFromText("prev_obs"."prev_observation_geom", 4326), 3857), ST_TileEnvelope(${z}, ${x}, ${y}))
          ELSE ST_AsMVTGeom(ST_Transform(ST_GeomFromText("observation"."geometry", 4326), 3857), ST_TileEnvelope(${z}, ${x}, ${y}))
        END AS mvtgeom,
        "site"."evaluation_run_uuid" AS "configuration_id",
        CONCAT(
          'Eval ',
          "evaluation_run"."evaluation_number",
          ' ',
          "evaluation_run"."evaluation_run_number",
          ' ',
          "evaluation_run"."performer"
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
        LEFT JOIN LATERAL (
          SELECT
            "uuid" AS "prev_observation_uuid",
            "geometry" AS "prev_observation_geom"
          FROM
            "observation" AS "prev_observation"
          WHERE
            "prev_observation"."site_uuid" = "observation"."site_uuid"
            AND EXTRACT(YEAR FROM "prev_observation"."date") < ${year}
          ORDER BY
            "prev_observation"."date" DESC
          LIMIT 1
        ) AS "prev_obs" ON TRUE

      WHERE
        (
          "site"."evaluation_run_uuid" = ${modelRunId}
          AND ST_Intersects(
            ST_Transform(
              ST_GeomFromText(
                CASE WHEN EXTRACT(YEAR FROM "observation"."date") < ${year}
                  THEN "prev_obs"."prev_observation_geom"
                  ELSE "observation"."geometry"
                END,
                4326
              ),
              3857
            ),
            ST_TileEnvelope(${z}, ${x}, ${y})
          )
          AND (
            EXTRACT(YEAR FROM "observation"."date") = ${year}
            OR prev_obs."prev_observation_uuid" IS NOT NULL
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
          ST_TileEnvelope(${z}, ${x}, ${y})
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
                V0."evaluation_run_uuid" = ${modelRunId}
                AND ST_Intersects(
                  ST_Transform(ST_GeomFromText(V0."union_geometry", 4326), 3857),
                  ST_TileEnvelope(${z}, ${x}, ${y})
                )
              )
            LIMIT
              1
          )
          AND ST_Intersects(
            ST_Transform(ST_GeomFromText("region"."geometry", 4326), 3857),
            ST_TileEnvelope(${z}, ${x}, ${y})
          )
        )
    )
    SELECT
    (
        (
          SELECT
            ST_AsMVT(sites.*, ${'sites-' + modelRunId}, 4096, 'mvtgeom')
          FROM
            sites
        ) || (
          SELECT
            ST_AsMVT(sites_points.*, ${'sites_points-' + modelRunId}, 4096, 'mvtgeom')
          FROM
            sites_points
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
async function getCacheKey(modelRunId, z, x, y, year) {
  // TODO: is this cache key sufficiently unique?
  const result = await sql`
    SELECT
      start_datetime
    FROM
      evaluation_run
    WHERE
    evaluation_run.uuid = ${modelRunId}
  `;

  const { start_datetime } = result[0];

  return `scoring-vector-tile-${modelRunId}-${z}-${x}-${y}-${start_datetime}-${year}`;
}

export async function getVectorTiles(modelRunId, z, x, y, year) {
  const cacheKey = await getCacheKey(modelRunId, z, x, y, year);

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
    redisClient.set(cacheKey, vectorTileData, 'EX', 60 * 60 * 24 * 7);
  }

  return vectorTileData;
}
