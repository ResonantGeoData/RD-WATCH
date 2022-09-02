/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ServerStatus } from "../models/ServerStatus";
import type { SiteEvaluation } from "../models/SiteEvaluation";
import type { SiteObservation } from "../models/SiteObservation";

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
      url: "/api/status/",
    });
  }

  /**
   * @returns SiteEvaluation
   * @throws ApiError
   */
  public static getSiteEvaluations(): CancelablePromise<Array<SiteEvaluation>> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/site/",
    });
  }

  /**
   * @param id
   * @returns SiteObservation
   * @throws ApiError
   */
  public static getSiteObservations(
    id: string
  ): CancelablePromise<SiteObservation> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/site/{id}/",
      path: {
        id: id,
      },
    });
  }
}
