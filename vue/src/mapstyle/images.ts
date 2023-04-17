import { EnabledSiteObservations } from '../store';
import type { LayerSpecification, SourceSpecification } from "maplibre-gl";



const getClosestTimestamp = (id: number, timestamp: number, enabledSiteObservations: EnabledSiteObservations[]) => {
    if (enabledSiteObservations.length > 0) {
        const observation = enabledSiteObservations.find((item) => item.id === id);
        if (observation) {
            const closest = observation.images.map((item) => item.timestamp).reduce((prev, curr) => {
                return Math.abs(curr - timestamp) < Math.abs(prev - timestamp) ? curr : prev
            });
            const index = observation.images.findIndex((item) => item.timestamp === closest);
            if (index !== -1) {
                return observation.images[index].url 
            }
        }
    }
    return '';
}




export const buildImageSourceFilter = (
    timestamp: number,
    enabledSiteObservations: EnabledSiteObservations[],
) => {
    const results: Record<string, SourceSpecification> = {};
    enabledSiteObservations.forEach((item) => {
        const source  = `siteImageSource_${item.id}`;
        results[source] = 
        {
            type: 'image',
            url: getClosestTimestamp(item.id, timestamp, enabledSiteObservations),
            coordinates: item.bbox,
        }
    });
    return results;
}

export const buildImageLayerFilter = (
    timestamp: number,
    enabledSiteObservations: EnabledSiteObservations[],
): LayerSpecification[] => {
    const results: LayerSpecification[] = [];
    enabledSiteObservations.forEach((item) => {
        const layer = `siteImageLayer_${item.id}`;
        const source  = `siteImageSource_${item.id}`;
        results.push({
            id: layer,
            'type': 'raster',
            'source': source,
            'paint': {
                'raster-fade-duration': 0
            }
        });
    });
    return results;

}