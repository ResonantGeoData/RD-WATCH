import { ModelRunEvaluations } from "./client/services/ApiService";
import { SiteObservationImage } from "./store";

export interface EvaluationImage {
    timestamp: number;
    source: SiteObservationImage['source'];
    cloudcover: number;
    image: string;
    siteobs_id: number | null;
    percent_black: number;
    bbox: { xmin: number; ymin: number; xmax: number; ymax: number };
    image_dimensions: [number, number];
    aws_location: string;
}

export interface EvaluationGeoJSON {
    timestamp: number;
    label: string;
    geoJSON: GeoJSON.Polygon;
}

export interface EvaluationImageResults {
    images: {
        count: number;
        results: EvaluationImage[];
    }
    label: string;
    status: ModelRunEvaluations['evaluations'][0]['status']
    evaluationGeoJSON: EvaluationGeoJSON['geoJSON']
    geoJSON: EvaluationGeoJSON[];
    notes: null | string;
}