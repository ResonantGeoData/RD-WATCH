/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

export type SiteObservationList = {
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
  results: Array<{
    id: number;
    label: string;
    score: number;
    constellation: string;
    spectrum: string;
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
    images?: {image: string, timestamp: number, source: 'S2' |'WV'|'L8'}[],
  }>;
};
