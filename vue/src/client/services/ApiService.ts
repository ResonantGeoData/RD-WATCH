/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ServerStatus } from "../models/ServerStatus";
import type { SiteEvaluationList } from "../models/SiteEvaluationList";
import type { SiteObservationList } from "../models/SiteObservationList";

import type { CancelablePromise } from "../core/CancelablePromise";
import { OpenAPI } from "../core/OpenAPI";
import { request as __request } from "../core/request";

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
    query?: Record<string, string>
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
}
