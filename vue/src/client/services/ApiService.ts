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
import type { RegionDetailList, RegionList } from "../models/RegionList";
import type { Region } from "../models/Region";
import type { EvalList } from "../models/EvalList";
import type { Eval } from "../models/Eval";

import type { CancelablePromise } from "../core/CancelablePromise";
import { OpenAPI } from "../core/OpenAPI";
import { request as __request } from "../core/request";
import { SatelliteTimeStamp, SiteObservationImage } from "../../store";
import { EvaluationImage, EvaluationImageResults } from "../../types";

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

export interface SiteInfo {
    images: number,
    S2: number,
    WV: number,
    L8: number,
    PL: number,
    number: number,
    start_date: number;
    end_date: number;
    id: string
    bbox: { xmin: number; ymin: number; xmax: number; ymax: number }
    status: SiteModelStatus
    timestamp: number;
    color_code?: number;
    filename?: string | null;
    downloading: boolean;
    groundtruth?: boolean;
    originator?: string;
}
export interface SiteList {
  region: Region;
  modelRunDetails: {
    region: string;
    version: string;
    title: string;
    proposal: boolean | null;
    performer: {
      id: number;
      team_name: string;
      short_code: string;
    }
  }
  sites: SiteInfo[];
}
export interface SiteEvaluationUpdateQuery {
  label?: string;
  geom?: GeoJSON.Polygon | GeoJSON.Point;
  score?: number,
  start_date?: string | null;
  end_date?: string | null;
  notes?: string;
  status?: SiteModelStatus
}

export interface SiteObservationUpdateQuery {
  label?: string;
  geom?: GeoJSON.Polygon | GeoJSON.Point;
  score?: number,
  timestamp: string;
  constellation: string;
  spectrum?: string;
  notes?: string;

}

export type Constellation  = 'S2' | 'WV' | 'L8' | 'PL';
export interface DownloadSettings {
  constellation: Constellation[];
  worldviewSource?: 'cog' | 'nitf',
  dayRange?: number;
  noData?: number;
  overrideDates?: [string, string];
  force?: boolean;
  scale?: 'default' | 'bits' | 'custom';
  scaleNum?: number[];
  bboxScale?: number;
  pointArea?: number;
}

export interface DownloadAnimationSettings {
  output_format: 'mp4' | 'gif';
  fps: number;
  point_radius: number;
  sources: Constellation[];
  labels: ('geom' | 'date' | 'source' | 'obs' | 'obs_label')[];
  cloudCover: number;
  noData: number;
  include: ('obs'|'nonobs')[];
  rescale: boolean;
  rescale_border: number;
}

export interface DownloadAnimationState {
  state: string;
  status: string;
  error?: string;
  info: {
    current?: number;
    total?: number;
    mode?: string;
    siteEvalId?: string;
    modelRunId?: string;

  }
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

export interface SMARTSiteFeatureCache {
  originator_file?: string;
  timestamp?: string;
  commit_hash?: string;
}
export interface SMARTSiteFeature {
  type: 'Feature';
  properties: {
  type: 'site';
  region_id: string;
  site_id: string;
  version: string;
  mgrs: string;
  status: string;
  start_date: string | null;
  end_date: string | null;
  model_content: 'annotation' | 'proposed' | 'update';
  originator: string;
  comments: string;
  // Optional fields
  score?: number;
  validated?: boolean;
  cache?: SMARTSiteFeatureCache;
  predicted_phase_transition?: 'Active Construction' | 'Post Construction';
  predicted_phase_transition_date?: string;
  misc_info?: Record<string, any>;
  performer_cache?: Record<string, any>;
  }
  geometry: GeoJSON.Geometry;
}

export interface SMARTRegionFeature {
  type: 'Feature';
  properties: {
  type: 'region';
  region_id: string;
  start_date: null;
  end_date: null;
  mgrs: string;
  originator: string;
  }
  geometry: GeoJSON.Geometry;
}
export interface SiteModelUpload {
  type: 'FeatureCollection',
  features: SMARTSiteFeature[];
}

export interface RegionUpload {
    type: 'FeatureCollection',
  features: SMARTRegionFeature[];

}

export interface DownloadedAnimation {
  created: string;
  completed: boolean;
  arguments: DownloadAnimationSettings;
  taskId: string;
  state?: DownloadAnimationState;
}

export interface ModelRunUpload {
  title: string;
  region: string | null | undefined;
  performer: string | null | undefined;
  zipfileKey: string;
  private: boolean;
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
      url: "/api/status/",
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
      url: `${this.getApiPrefix()}/observations/{id}/`,
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
    public static getSite(
      id: string
    ): CancelablePromise<SiteInfo> {
      return __request(OpenAPI, {
        method: "GET",
        url: `${this.getApiPrefix()}/sites/{id}/`,
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
        url: `${this.getApiPrefix()}/sites/{id}/details/`,
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
      url: `${this.getApiPrefix()}/model-runs/`,
      query: Object.fromEntries(
        Object.entries(query).filter(([key, value]) => value !== undefined)
      ),
    });
  }

    /**
   * @returns EvaluationsList
   * @throws ApiError
   */
    public static getProposals(id: string): CancelablePromise<SiteList> {
      return __request(OpenAPI, {
        method: "GET",
        url: `${this.getApiPrefix()}/model-runs/{id}/proposals/`,
        path: {
          id: id,
        },
      });
    }

    /**
    * @returns EvaluationsList
    * @throws ApiError
    */
     public static getSitesList(id: string): CancelablePromise<SiteList> {
       return __request(OpenAPI, {
         method: "GET",
         url: `${this.getApiPrefix()}/model-runs/{id}/sites/`,
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
      url: `${this.getApiPrefix()}/performers/`,
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
   * @returns RegionList
   * @throws ApiError
   */
  public static getRegions(): CancelablePromise<RegionList> {
    return __request(OpenAPI, {
      method: "GET",
      url: `${this.getApiPrefix()}/regions/`,
    });
  }


  /**
   * @returns RegionList
   * @throws ApiError
   */
  public static getRegionDetails(): CancelablePromise<RegionDetailList> {
    return __request(OpenAPI, {
      method: "GET",
      url: `${this.getApiPrefix()}/regions/details/`,
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
      url: "/api/satellite-image/timestamps/",
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
      url: "/api/satellite-image/visual-timestamps/",
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
    const startTime = startTimestamp ? new Date(startTimestamp * 1000).toISOString().substring(0, 10) : '2013-01-01';
    const endTime = endTimestamp ? new Date(endTimestamp * 1000).toISOString().substring(0, 10): new Date().toISOString().substring(0, 10);
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
      url: "/api/scores/details/",
      query: { configurationId, region, siteNumber, version },
    });
  }

  public static getEvaluationImages(id: string): CancelablePromise<EvaluationImageResults> {
    return __request(OpenAPI, {
      method: "GET",
      url: `${this.getApiPrefix()}/evaluations/images/{id}/`,
      path: {
        id: id,
      },
    });

  }




  public static postSiteImageEmbedding(id: number): CancelablePromise<string> {
    return __request(OpenAPI, {
      method: "POST",
      url: `${this.getApiPrefix()}/evaluations/images/{id}/image_embedding/`,
      path: {
        id: id,
      },
    });

  }

  public static postModelRunUpload(data: ModelRunUpload): CancelablePromise<string> {
    return __request(OpenAPI, {
      method: "POST",
      url: `${this.getApiPrefix()}/model-runs/start_upload_processing`,
      body: { ...data },
    });
  }

  public static getModelRunUploadTaskStatus(taskId: string): CancelablePromise<{ status: string, traceback: string | null }> {
    return __request(OpenAPI, {
      method: "GET",
      url: `${this.getApiPrefix()}/model-runs/upload_status/${taskId}`,
    });
  }

  public static getSiteImageEmbeddingStatus(id: number, uuid: string): CancelablePromise<{state: string, status: string}> {
    return __request(OpenAPI, {
      method: "GET",
      url: `${this.getApiPrefix()}/evaluations/images/{id}/image_embedding_status/{uuid}/`,
      path: {
        id: id,
        uuid: uuid,
      },
    });

  }

  public static getSiteImage(id: number): CancelablePromise<SiteObservationImage> {
    return __request(OpenAPI, {
      method: "GET",
      url: `${this.getApiPrefix()}/evaluations/images/{id}/image/`,
      path: {
        id: id,
      },
    });

  }

  public static patchSiteEvaluation(id: string, data: SiteEvaluationUpdateQuery): CancelablePromise<boolean> {
    return __request(OpenAPI, {
      method: 'PATCH',
      url: `${this.getApiPrefix()}/evaluations/{id}/`,
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
      url: `${this.getApiPrefix()}/model-runs/download_status/${task_id}`,
    })
  }

  public static getSatelliteFetchingRunning(modelRunIds?: string[], limit=2000, offset=0): CancelablePromise<{items: string[], count: number}> {
    return __request(OpenAPI, {
      method: 'GET',
      url: `${this.getApiPrefix()}/satellite-fetching/running/`,
      query: { model_runs: modelRunIds, limit, offset },
    })
  }

  public static addSiteModel(
    modelRunId: string,
    siteModel: SiteModelUpload
  ): CancelablePromise<boolean> {
    return __request(OpenAPI, {
      method: "POST",
      url: `${this.getApiPrefix()}/model-runs/{id}/editor/site-model/`,
      path: {
        id: modelRunId,
      },
      body: {
        ...siteModel
      }
    });
  }

  public static addRegionModel(
    regionModel: RegionUpload
  ): CancelablePromise<boolean> {
    return __request(OpenAPI, {
      method: "POST",
      url: `${this.getApiPrefix()}/regions/`,
      body: {
        ...regionModel
      }
    });
  }

  public static deleteRegionModel(
    regionId: number
  ): CancelablePromise<{error?: string, success?: string}> {
    return __request(OpenAPI, {
      method: "DELETE",
      url: `${this.getApiPrefix()}/regions/${regionId}/`,
    });
  }

  public static generateSiteAnimation(
    siteEvaluationid: string,
    data: DownloadAnimationSettings
  ): CancelablePromise<string> {
    return __request(OpenAPI, {
      method: "POST",
      url: `${this.getApiPrefix()}/animation/site/{id}/`,
      path: {
        id: siteEvaluationid,
      },
      body: {
        ...data
      }
    });
  }

  public static generateModelRunAnimation(
    modelRunId: string,
    data: DownloadAnimationSettings
  ): CancelablePromise<string> {
    return __request(OpenAPI, {
      method: "POST",
      url: `${this.getApiPrefix()}/animation/modelrun/{id}/`,
      path: {
        id: modelRunId,
      },
      body: {
        ...data
      }
    });
  }

  public static getSiteAnimationDownloadStatus(task_id: string): CancelablePromise<DownloadAnimationState> {
    return __request(OpenAPI, {
      method: 'GET',
      url: `${this.getApiPrefix()}/animation/${task_id}/status/`,
    })
  }
  public static getAnimationDownloadString(task_id: string, type: 'site' | 'modelRun'): CancelablePromise<{url: string, filename: string}> {
    return __request(OpenAPI, {
      method: 'GET',
      url: `${this.getApiPrefix()}/animation/download/${type.toLowerCase()}/${task_id}/`,
    })
  }


  public static getAnimationSiteDownloaded(siteId: string): CancelablePromise<DownloadedAnimation[]> {
    return __request(OpenAPI, {
      method: 'GET',
      url: `${this.getApiPrefix()}/animation/site/${siteId}/downloads/`,
    })
  }
  public static getAnimationModelRunDownloaded(modelRun: string): CancelablePromise<DownloadedAnimation[]> {
    return __request(OpenAPI, {
      method: 'GET',
      url: `${this.getApiPrefix()}/animation/modelrun/${modelRun}/downloads/`,
    })
  }

  public static cancelAnimationDownload(taskId: string): CancelablePromise<{error?: string, success?: string}> {
    return __request(OpenAPI, {
      method: 'POST',
      url: `${this.getApiPrefix()}/animation/${taskId}/cancel/`,
    })
  }

  public static deleteAnimationSiteDownload(taskId: string): CancelablePromise<{error?: string, success?: string}> {
    return __request(OpenAPI, {
      method: 'DELETE',
      url: `${this.getApiPrefix()}/animation/site/${taskId}/`,
    })
  }

  public static deleteAnimationModelRunDownload(taskId: string): CancelablePromise<{error?: string, success?: string}> {
    return __request(OpenAPI, {
      method: 'DELETE',
      url: `${this.getApiPrefix()}/animation/modelrun/${taskId}/`,
    })
  }

}
