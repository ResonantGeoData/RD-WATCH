import { SiteObservationImage } from "./store";

export interface EvaluationImage {
    timestamp: number;
    source: SiteObservationImage['source'];
    cloudcover: number;
    image: string;
    site_obsid: number
    percent_black: number;
    bbox: { xmin: number; ymin: number; xmax: number; ymax: number };
    image_dimensions: [number, number];
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
    geoJSON: {
        results: EvaluationGeoJSON[];
    }
}