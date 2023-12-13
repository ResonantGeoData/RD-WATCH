/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import { ref } from 'vue';

import type { ServerStatus } from "../models/ServerStatus";
import type { SiteEvaluationList } from "../models/SiteEvaluationList";
import type { SiteObservationList } from "../models/SiteObservationList";
import type { ModelRunList } from "../models/ModelRunList";
import type { ModelRun } from "../models/ModelRun";
import type { PerformerList } from "../models/PerformerList";
import type { Performer } from "../models/Performer";
import type { RegionList } from "../models/RegionList";
import type { Region } from "../models/Region";
import type { EvalList } from "../models/EvalList";
import type { Eval } from "../models/Eval";

import type { CancelablePromise } from "../core/CancelablePromise";
import { OpenAPI } from "../core/OpenAPI";
import { request as __request } from "../core/request";
import { SatelliteTimeStamp } from "../../store";
import { EvaluationImageResults } from "../../types";

export interface QueryArguments {
  performer?: string[];
  region?: string;
  mode?: string[];
  eval?: string[];
  page?: number;
  limit?: number;
  proposal?: 'PROPOSAL' | 'APPROVED';
  groundtruth?: boolean;
}

export interface ScoringResults {
  region_name: string;
  evaluationId?: string;
  evaluation_run?: number;
  performer: string;
  evaluation_uuid: string;
  unionArea: number;
  statusAnnotated: string;
  temporalIOU: {
    site_preparation: string;
    active_construction: string;
    post_construction: string;

  }
  color?: string;
}

export type SiteModelStatus = 'PROPOSAL' | 'APPROVED' | 'REJECTED'

export interface ModelRunEvaluations {
  region: Region;

  evaluations: {
    images: number,
    S2: number,
    WV: number,
    L8: number,
    number: number,
    start_date: number;
    end_date: number;
    id: string
    bbox: { xmin: number; ymin: number; xmax: number; ymax: number }
    status: SiteModelStatus
    timestamp: number;
    filename?: string | null;
  }[];
}
export interface SiteEvaluationUpdateQuery {
  label?: string;
  geom?: GeoJSON.Polygon;
  score?: number,
  start_date?: string | null;
  end_date?: string | null;
  notes?: string;
  status?: SiteModelStatus
}

export interface SiteObservationUpdateQuery {
  label?: string;
  geom?: GeoJSON.Polygon;
  score?: number,
  timestamp: string;
  constellation: string;
  spectrum?: string;
  notes?: string;

}

export type Constellation  = 'S2' | 'WV' | 'L8';
export interface DownloadSettings {
  constellation: Constellation[];
  dayRange?: number;
  noData?: number;
  overrideDates?: [string, string];
  force?: boolean;
  scale?: 'default' | 'bits' | 'custom';
  scaleNum?: number[];
  bboxScale?: number;
}

export type CeleryStates = 'FAILURE' | 'PENDING' | 'SUCCESS' | 'RETRY' | 'REVOKED' | 'STARTED';

export interface SiteDetails {
  regionName: string;
  configurationId: number;
  siteNumber: string;
  version: string;
  performer: string;
  title: string;
  timemin: number;
  timemax: number;
}

type ApiPrefix = '/api' | '/api/scoring';

export class ApiService {
  private static apiPrefix = ref<ApiPrefix>("/api");

  public static getApiPrefix(): ApiPrefix {
    return ApiService.apiPrefix.value;
  }

  public static setApiPrefix(prefix: ApiPrefix) {
    ApiService.apiPrefix.value = prefix;
  }

  public static isScoring(): boolean {
    return ApiService.apiPrefix.value === '/api/scoring';
  }

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
      url: `${this.getApiPrefix()}/evaluations`,
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
      url: `${this.getApiPrefix()}/observations/{id}`,
      path: {
        id: id,
      },
    });
  }

    /**
   * @param id
   * @returns SiteObservationList
   * @throws ApiError
   */
    public static getSiteDetails(
      id: string
    ): CancelablePromise<SiteDetails> {
      return __request(OpenAPI, {
        method: "GET",
        url: `${this.getApiPrefix()}/sites/{id}/details`,
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
        data: DownloadSettings
      ): CancelablePromise<boolean> {
        return __request(OpenAPI, {
          method: "POST",
          url: `${this.getApiPrefix()}/observations/{id}/generate-images/`,
          path: {
            id: id,
          },
          query: {
            ...data,
          }
        });
      }


      /**
   * @param id
   * @returns boolean
   * @throws ApiError
   */
      public static getModelRunImages(
        id: string,
        data: DownloadSettings
      ): CancelablePromise<boolean> {
        return __request(OpenAPI, {
          method: "POST",
          url: `${this.getApiPrefix()}/model-runs/{id}/generate-images/`,
          path: {
            id: id,
          },
          query: {
            ...data,
          }
        });
      }

      /**
   * @param id
   * @returns boolean
   * @throws ApiError
   */
      public static cancelSiteObservationImageTask(
        id: string,
      ): CancelablePromise<boolean> {
        return __request(OpenAPI, {
          method: "PUT",
          url: `${this.getApiPrefix()}/observations/{id}/cancel-generate-images/`,
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
      public static cancelModelRunsImageTask(
        id: string,
      ): CancelablePromise<boolean> {
        return __request(OpenAPI, {
          method: "PUT",
          url: `${this.getApiPrefix()}/model-runs/{id}/cancel-generate-images/`,
          path: {
            id: id,
          },
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
      url: `${this.getApiPrefix()}/model-runs`,
      query: Object.fromEntries(
        Object.entries(query).filter(([key, value]) => value !== undefined)
      ),
    });
  }

    /**
   * @returns EvaluationsList
   * @throws ApiError
   */
    public static getModelRunEvaluations(id: string): CancelablePromise<ModelRunEvaluations> {
      return __request(OpenAPI, {
        method: "GET",
        url: `${this.getApiPrefix()}/model-runs/{id}/evaluations`,
        path: {
          id: id,
        },
      });
    }



  /**
   * @param id
   * @returns ModelRun
   * @throws ApiError
   */
  public static getModelRun(id: string): CancelablePromise<ModelRun> {
    return __request(OpenAPI, {
      method: "GET",
      url: `${this.getApiPrefix()}/model-runs/{id}`,
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
      url: `${this.getApiPrefix()}/performers`,
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
      url: `${this.getApiPrefix()}/performers/{id}`,
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
      url: `${this.getApiPrefix()}/regions`,
    });
  }

  /**
   * @returns EvalList
   * @throws ApiError
   */
  public static getEvals(): CancelablePromise<EvalList> {
    return __request(OpenAPI, {
      method: "GET",
      url: `${this.getApiPrefix()}/eval-numbers/`,
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

  public static getScoringDetails(
    configurationId: number,
    region: string,
    siteNumber: number,
    version: string
  ): CancelablePromise<ScoringResults>
  {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/scores/details",
      query: { configurationId, region, siteNumber, version },
    });
  }

  public static hasScores(
    configurationId: number,
    region: string,
  ): CancelablePromise<boolean>
  {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/scores/has-scores",
      query: { configurationId, region },
    });
  }

  public static getEvaluationImages(id: string): CancelablePromise<EvaluationImageResults> {
    return __request(OpenAPI, {
      method: "GET",
      url: `${this.getApiPrefix()}/evaluations/images/{id}`,
      path: {
        id: id,
      },
    });

  }

  public static patchSiteEvaluation(id: string, data: SiteEvaluationUpdateQuery): CancelablePromise<boolean> {
    return __request(OpenAPI, {
      method: 'PATCH',
      url: "/api/evaluations/{id}/",
      path: {
        id: id,
      },
      body: {...data}
    })
  }

  public static patchSiteObservation(id: string, data: SiteObservationUpdateQuery): CancelablePromise<boolean> {
    return __request(OpenAPI, {
      method: 'PATCH',
      url: `${this.getApiPrefix()}/observations/{id}/`,
      path: {
        id: id,
      },
      body: {...data}
    })
  }

  public static addSiteObservation(id: string, data: SiteObservationUpdateQuery): CancelablePromise<boolean> {
    return __request(OpenAPI, {
      method: 'PUT',
      url: "/api/observations/{id}/",
      path: {
        id: id,
      },
      query: {...data}
    })
  }

  public static startModelRunDownload(id: string, mode: 'all' | 'approved' | 'rejected'='all'): CancelablePromise<string> {
    return __request(OpenAPI, {
      method: 'POST',
      url: `${this.getApiPrefix()}/model-runs/{id}/download/`,
      path: {
        id: id,
      },
      query: {mode},
    })
  }

  public static getModelRunDownloadStatus(task_id: string): CancelablePromise<CeleryStates> {
    return __request(OpenAPI, {
      method: 'GET',
      url: `${this.getApiPrefix()}/model-runs/download_status`,
      query: {task_id},
    })
  }


}
