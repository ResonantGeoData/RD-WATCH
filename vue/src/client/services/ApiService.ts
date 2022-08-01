/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ServerStatus } from "../models/ServerStatus";

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
}
