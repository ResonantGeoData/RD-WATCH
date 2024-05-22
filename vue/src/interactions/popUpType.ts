
export interface PopUpData {
    siteId: string;
    obsColor?: string;
    siteColor: string;
    score?: number;
    groundTruth: boolean;
    scoreColor?: string;
    area?: string;
    timestamp?: string;
    version: string,
    configName: string,
    performerName: string,
    siteLabel: string,
  }  

export interface PopUpSiteData {
  siteId: string,
  groundTruth: boolean,
  performerName: string,
  timeRange?: string;
  version: string,
  configName: string;
  siteLabel: string;
  siteColor: string;
  scoreLabel?: string;
  scoreColor?:string;
}