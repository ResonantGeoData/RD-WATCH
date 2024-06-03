/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RunDagRequestSchema } from '../models/RunDagRequestSchema';

import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';

export class SmartflowService {

    /**
     * List Dags
     * @returns any OK
     * @throws ApiError
     */
    public static rdwatchSmartflowViewsListDags(query: Record<string, any>): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/smartflow/dags/',
            query,
        });
    }

    /**
     * List Dag Runs
     * @param dagId
     * @returns any OK
     * @throws ApiError
     */
    public static rdwatchSmartflowViewsListDagRuns(
        dagId: string,
        query: Record<string, any> = {},
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/smartflow/dags/{dag_id}/dagRuns/',
            path: {
                'dag_id': dagId,
            },
            query,
        });
    }

    /**
     * Create Dag Run
     * @param dagId
     * @param requestBody
     * @returns any OK
     * @throws ApiError
     */
    public static rdwatchSmartflowViewsCreateDagRun(
        dagId: string,
        requestBody: RunDagRequestSchema,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/smartflow/dags/{dag_id}/dagRuns/',
            path: {
                'dag_id': dagId,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }

    /**
     * Get Dag Run
     * @param dagId
     * @param dagRunId
     * @returns any OK
     * @throws ApiError
     */
    public static rdwatchSmartflowViewsGetDagRun(
        dagId: string,
        dagRunId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/smartflow/dags/{dag_id}/dagRuns/{dag_run_id}/',
            path: {
                'dag_id': dagId,
                'dag_run_id': dagRunId,
            },
        });
    }

}
