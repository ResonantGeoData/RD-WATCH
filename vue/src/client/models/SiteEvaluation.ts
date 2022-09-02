/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

export type SiteEvaluation = {
  id: number;
  performer: {
    team_name: string;
    short_code: string;
  };
  configuration: any;
  site: string;
  timestamp: string;
  score: number;
  readonly bbox?: Array<number>;
};
