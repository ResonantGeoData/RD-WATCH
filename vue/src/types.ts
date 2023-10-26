import { SiteModelStatus } from "./client/services/ApiService";
import { SiteObservationImage } from "./store";


export interface BaseBBox {
    xmin: number,
    ymin: number,
    xmax: number,
    ymax: number,
  }
export interface EvaluationImage {
    timestamp: number;
    source: SiteObservationImage['source'];
    cloudcover: number;
    image: string;
    observation_id: string | null;
    percent_black: number;
    bbox: BaseBBox;
    image_dimensions: [number, number];
    aws_location: string;
}

export interface EvaluationGeoJSON {
    timestamp: number;
    label: string;
    geoJSON: GeoJSON.Polygon;
    bbox: BaseBBox;
}

export interface EvaluationImageResults {
    images: {
        count: number;
        results: EvaluationImage[];
    }
    label: string;
    status: SiteModelStatus
    evaluationGeoJSON: EvaluationGeoJSON['geoJSON']
    evaluationBBox: BaseBBox;
    geoJSON: EvaluationGeoJSON[];
    notes: null | string;
    groundTruth?: {
        timerange: {
            min: number,
            max: number,
        },
        geoJSON: GeoJSON.Polygon,
        label: string
    } | null;
}
