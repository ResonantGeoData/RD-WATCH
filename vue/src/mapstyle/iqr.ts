import { LayerSpecification, SourceSpecification } from "maplibre-gl";
import { IQROrderedResultItem } from "../client/services/ApiService";
import { ImageBBox, siteOverviewSatSettings } from "../store";

function unflattenXYXYBounds(arrBounds: [number, number, number, number]) {
  const [xmin, ymin, xmax, ymax] = arrBounds;
  return [
    [xmin, ymax],
    [xmax, ymax],
    [xmax, ymin],
    [xmin, ymin],
  ];
}

export function buildIQRImageSources(results: IQROrderedResultItem[]): Record<string, SourceSpecification> {
  return results
    .filter((item): item is IQROrderedResultItem & { image_url: string } => !!item.image_url)
    .reduce((sources, item) => {
      const sourceId = `iqrSiteImageSource_${item.site_id}`;
      return {
        ...sources,
        [sourceId]: {
          type: 'image',
          url: item.image_url,
          coordinates: (item.image_bbox ? unflattenXYXYBounds(item.image_bbox) : [[0,0], [0,0], [0,0], [0,0]]) as ImageBBox,
        },
      };
  }, {});
}

export function buildIQRImageLayers(results: IQROrderedResultItem[], settings: siteOverviewSatSettings): LayerSpecification[] {
  return results
    .filter((item): item is IQROrderedResultItem & { image_url: string } => !!item.image_url)
    .map((item) => {
      const layerId = `iqrSiteImageLayer_${item.site_id}`;
      const sourceId = `iqrSiteImageSource_${item.site_id}`;
      return {
        id: layerId,
        type: 'raster',
        source: sourceId,
        paint: {
          'raster-fade-duration': 0,
          'raster-opacity': settings.imageOpacity / 100,
        },
      };
    });
}
