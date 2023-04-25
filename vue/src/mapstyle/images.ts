import { EnabledSiteObservations, ImageBBox } from '../store';
import type { LayerSpecification, SourceSpecification } from "maplibre-gl";



const getClosestTimestamp = (id: number, timestamp: number, enabledSiteObservations: EnabledSiteObservations[]) => {
    if (enabledSiteObservations.length > 0) {
        const observation = enabledSiteObservations.find((item) => item.id === id);
        const images = observation?.images.filter((item) => !item.disabled);
        if (observation && images?.length) {
            const closest = images.map((item) => item.timestamp).reduce((prev, curr) => {
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


function scaleBoundingBox(bbox: ImageBBox, scale: number) {
    // Get the width and height of the bounding box
    const width = bbox[2][0] - bbox[0][0];
    const height = bbox[2][1] - bbox[0][1];

    // Calculate the new width and height based on the scaling factor
    const newWidth = width * scale;
    const newHeight = height * scale;

    // Calculate the new coordinates of the bounding box
    const newX1 = bbox[0][0] - ((newWidth - width) / 2);
    const newY1 = bbox[0][1] - ((newHeight - height) / 2);
    const newX2 = bbox[2][0] + ((newWidth - width) / 2);
    const newY2 = bbox[2][1] + ((newHeight - height) / 2);

    // Return the new bounding box
    return [[newX1, newY1], [newX2, newY1], [newX2, newY2],  [newX1, newY2]] as ImageBBox;
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
            coordinates: scaleBoundingBox(item.bbox, 1.2),
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
