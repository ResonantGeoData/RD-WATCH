import { EnabledSiteObservations, ImageBBox, SiteObservationImage, siteObsSatSettings } from '../store';
import type { LayerSpecification, SourceSpecification } from "maplibre-gl";
import { ImageSource, Map } from "maplibre-gl";



const getClosestTimestamp = (id: string, timestamp: number, enabledSiteObservations: EnabledSiteObservations[], settings: siteObsSatSettings) => {
    if (enabledSiteObservations.length > 0) {
        const observation = enabledSiteObservations.find((item) => item.id === id);
        const images = observation?.images.filter((item) => imageFilter(item, settings));
        if (observation && images?.length) {
            const closest = images.map((item) => item.timestamp).reduce((prev, curr) => {
                return Math.abs(curr - timestamp) < Math.abs(prev - timestamp) ? curr : prev
            });
            const index = observation.images.findIndex((item) => item.timestamp === closest);
            if (index !== -1) {
                const bbox = observation.images[index].bbox
                const coordinates = [[bbox.xmin, bbox.ymax], [bbox.xmax, bbox.ymax], [bbox.xmax, bbox.ymin], [bbox.xmin, bbox.ymin]] as ImageBBox;
                return {url: observation.images[index].image, coordinates };
            }
        }
    }
    return {url: '', coordinates: [[0,0], [0,0], [0,0], [0,0]] as ImageBBox};
}

export const updateImageMapSources =  (
    timestamp: number,
    enabledSiteObservations: EnabledSiteObservations[],
    settings: siteObsSatSettings,
    map?: Map | null,
) => {
    enabledSiteObservations.forEach((item) => {
        const source  = `siteImageSource_${item.id}`;
        if (map ) {
            const mapSource = map.getSource(source) as ImageSource;
            if (mapSource) {
                const { url, coordinates} = getClosestTimestamp(item.id, timestamp, enabledSiteObservations, settings);
                mapSource.updateImage({
                    url,
                    coordinates,
                });
            }
        }
    });
}
export const buildImageSourceFilter = (
    timestamp: number,
    enabledSiteObservations: EnabledSiteObservations[],
    settings: siteObsSatSettings,
    map?: Map | null,
) => {
    const results: Record<string, SourceSpecification> = {};
    enabledSiteObservations.forEach((item) => {
        const source  = `siteImageSource_${item.id}`;
        let update = false;
        if (map) {
            const mapSource = map.getSource(source) as ImageSource;
            if (mapSource) {
                results[source] =
                {
                    type: 'image',
                    url: mapSource.url,
                    coordinates: mapSource.coordinates,
                }
                update = true;
            }
        }
        if (!update) {
            const { url, coordinates} = getClosestTimestamp(item.id, timestamp, enabledSiteObservations, settings);
            console.log(url);
            console.log(coordinates);
            results[source] =
            {
                type: 'image',
                url,
                coordinates,
            }
        }
    });
    return results;
}

export const buildImageLayerFilter = (
    timestamp: number,
    enabledSiteObservations: EnabledSiteObservations[],
    settings: siteObsSatSettings,
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
                'raster-fade-duration': 0,
                "raster-opacity": settings.imageOpacity/100,

            }
        });
    });
    return results;

}


export const imageFilter = (item:SiteObservationImage, settings: siteObsSatSettings) =>  {
    if (!item.disabled) {
      if (item.cloudcover !== undefined && item.cloudcover > settings.cloudCoverFilter) {
        return false;
      }
      if (item.percent_black !== undefined && item.percent_black > settings.percentBlackFilter ) {
        return false;
      }
      return true;
    }
    return false;
};
