/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

export type SiteEvaluationList = {
  count: number;
  timerange: {
    min: number;
    max: number;
  };
  bbox: {
    xmin: number;
    xmax: number;
    ymin: number;
    ymax: number;
  };
  performers: Array<any>;
  results: Array<{
    id: string;
    site: string;
    configuration: any;
    performer: {
      team_name: string;
      short_code: string;
    };
    score: number;
    timestamp: number;
    timerange: {
      min: number;
      max: number;
    };
    bbox: {
      xmin: number;
      xmax: number;
      ymin: number;
      ymax: number;
    };
  }>;
  next: string;
  previous: string;
};
