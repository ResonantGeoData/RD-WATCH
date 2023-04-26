/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import { SiteObservationImage } from "../../store";

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
  }>;
  images: {
    count: number;
    results: SiteObservationImage[],
  },
};
