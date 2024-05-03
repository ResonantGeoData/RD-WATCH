/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import { SiteObservationImage, SiteDownloadJob } from "../../store";

export type SiteObservationList = {
  count: number;
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
  results: Array<{
    id: string;
    label: string;
    score: number;
    constellation: string;
    spectrum: string;
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
  job?: SiteDownloadJob
  images: {
    count: number;
    results: SiteObservationImage[],
  },
};
