import { ScoringResults } from "../client/services/ApiService";

export interface PopUpData {
    siteId: string;
    siteColor: string;
    score: number;
    groundTruth: boolean;
    scoreColor: string;
    area: string;
    annotatedStatus?: ScoringResults['statusAnnotated'];
    unionArea?: ScoringResults['unionArea'];
    temporalIOU?: ScoringResults['temporalIOU'];  
  }  