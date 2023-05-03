/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ServerStatus } from "../models/ServerStatus";
import type { SiteEvaluationList } from "../models/SiteEvaluationList";
import type { SiteObservationList } from "../models/SiteObservationList";
import type { ModelRunList } from "../models/ModelRunList";
import type { ModelRun } from "../models/ModelRun";
import type { PerformerList } from "../models/PerformerList";
import type { Performer } from "../models/Performer";
import type { RegionList } from "../models/RegionList";
import type { Region } from "../models/Region";

import type { CancelablePromise } from "../core/CancelablePromise";
import { OpenAPI } from "../core/OpenAPI";
import { request as __request } from "../core/request";
import { SatelliteTimeStamp } from "../../store";

export interface QueryArguments {
  performer?: string;
  groundtruth?: boolean;
  region?: string;
  page?: number;
  limit?: number;
}

export class ApiService {
  /**
   * @returns ServerStatus
   * @throws ApiError
   */
  public static getStatus(): CancelablePromise<ServerStatus> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/status",
    });
  }

  /**
   * @returns SiteEvaluationList
   * @throws ApiError
   */
  public static getSiteEvaluations(
    query: QueryArguments = {}
  ): CancelablePromise<SiteEvaluationList> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/evaluations",
      query,
    });
  }

  /**
   * @param id
   * @returns SiteObservationList
   * @throws ApiError
   */
  public static getSiteObservations(
    id: string
  ): CancelablePromise<SiteObservationList> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/evaluations/{id}",
      path: {
        id: id,
      },
    });
  }

      /**
   * @param id
   * @returns boolean
   * @throws ApiError
   */
      public static getObservationImages(
        id: string,
        constellation: 'WV' | 'S2' | 'L8' = 'WV'
      ): CancelablePromise<boolean> {
        return __request(OpenAPI, {
          method: "POST",
          url: "/api/observations/{id}/get-images",
          path: {
            id: id,
          },
          query: {
            constellation,
          }
        });
      }
  
  /**
   * @returns ModelRunList
   * @throws ApiError
   */
  public static getModelRuns(
    query: QueryArguments = {}
  ): CancelablePromise<ModelRunList> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/model-runs",
      query: Object.fromEntries(
        Object.entries(query).filter(([key, value]) => value !== undefined)
      ),
    });
  }

  /**
   * @param id
   * @returns ModelRun
   * @throws ApiError
   */
  public static getModelRun(id: number): CancelablePromise<ModelRun> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/model-runs/{id}",
      path: {
        id: id,
      },
    });
  }

  /**
   * @returns PerformerList
   * @throws ApiError
   */
  public static getPerformers(): CancelablePromise<PerformerList> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/performers",
    });
  }

  /**
   * @param id
   * @returns Performer
   * @throws ApiError
   */
  public static getPerformer(id: number): CancelablePromise<Performer> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/performers/{id}",
      path: {
        id: id,
      },
    });
  }

  /**
   * @returns PerformerList
   * @throws ApiError
   */
  public static getRegions(): CancelablePromise<RegionList> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/regions",
    });
  }

  /**
   * @param id
   * @returns Performer
   * @throws ApiError
   */
  public static getRegion(id: number): CancelablePromise<Region> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/regions/{id}",
      path: {
        id: id,
      },
    });
  }

  public static getSatelliteTimestamps(
    constellation="S2",
    spectrum="visual",
    level="2A",
    startTimestamp=0,
    endTimestamp=0,
    bbox: [number, number][]=[],
  ): CancelablePromise<string[]>
  {
    const startTime = new Date(startTimestamp * 1000).toISOString().substring(0, 10);
    const endTime = new Date(endTimestamp * 1000).toISOString().substring(0, 10);
    // Convert bbox into array of numbers, min/max
    let minX = Infinity;
    let maxX = -Infinity;
    let minY = Infinity;
    let maxY = -Infinity;
    bbox.forEach((item: [number, number]) => {
      minX = Math.min(minX, item[1]);
      minY = Math.min(minY, item[0]);
      maxX = Math.max(maxX, item[1]);
      maxY = Math.max(maxY, item[0]);
    })
    const bboxstr = `${minY},${minX},${maxY},${maxX}`;;
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/satellite-image/timestamps",
      query: { constellation, level, spectrum, start_timestamp: startTime, end_timestamp: endTime, bbox: bboxstr,
      }
    });
  }

  public static getSatelliteVisualTimestamps(
    constellation="S2",
    spectrum="visual",
    level="2A",
    startTimestamp=0,
    endTimestamp=0,
    bbox: [number, number][] =[],
    cloudcover = 100
  ): CancelablePromise<string[]>
  {
    const startTime = new Date(startTimestamp * 1000).toISOString().substring(0, 10);
    const endTime = new Date(endTimestamp * 1000).toISOString().substring(0, 10);
    // Convert bbox into array of numbers, min/max
    let minX = Infinity;
    let maxX = -Infinity;
    let minY = Infinity;
    let maxY = -Infinity;
    bbox.forEach((item: [number, number]) => {
      minX = Math.min(minX, item[1]);
      minY = Math.min(minY, item[0]);
      maxX = Math.max(maxX, item[1]);
      maxY = Math.max(maxY, item[0]);
    })
    const bboxstr = `${minY},${minX},${maxY},${maxX}`;
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/satellite-image/visual-timestamps",
      query: { constellation, level, spectrum, start_timestamp: startTime, end_timestamp: endTime, bbox: bboxstr,
      }
    });
  }
  public static getAllSatelliteTimestamps(
    constellation="S2",
    spectrum="visual",
    level="2A",
    startTimestamp=0,
    endTimestamp=0,
    bbox=[],
  ): CancelablePromise<SatelliteTimeStamp[]>
  {
    const startTime = new Date(startTimestamp * 1000).toISOString().substring(0, 10);
    const endTime = new Date(endTimestamp * 1000).toISOString().substring(0, 10);
    // Convert bbox into array of numbers, min/max
    let minX = Infinity;
    let maxX = -Infinity;
    let minY = Infinity;
    let maxY = -Infinity;
    bbox.forEach((item: [number, number]) => {
      minX = Math.min(minX, item[1]);
      minY = Math.min(minY, item[0]);
      maxX = Math.max(maxX, item[1]);
      maxY = Math.max(maxY, item[0]);
    })
    const bboxstr = `${minY},${minX},${maxY},${maxX}`;
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/satellite-image/all-timestamps",
      query: { constellation, level, spectrum, start_timestamp: startTime, end_timestamp: endTime, bbox: bboxstr,
      }
    });
  }
}
