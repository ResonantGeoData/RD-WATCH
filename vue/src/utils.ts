import { SiteOverview } from "./store"

const timeRangeFormat = (range: SiteOverview['timerange']) => {
    if (range === null || (range.max === null && range.min === null)) {
      return '--'
    } else {
      const first = range.min ? `${new Date(range.min * 1000).toISOString().substring(0, 10)}` : 'None'
      const second = range.max ? `${new Date(range.max * 1000).toISOString().substring(0, 10)}` : 'None'
      return `${first} - ${second}`
    }
    return '--'
  }

  async function downloadPresignedFile(url: string, filename: string) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('Response error');
        }
        const blob = await response.blob();
        const a = document.createElement('a');
        a.href = window.URL.createObjectURL(blob);
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(a.href);
    } catch (error) {
        console.error('Error downloading file:', error);
    }
}

export type EventCallback<T> = (e: T) => void;

const createEventHook = <T = unknown>() => {
  const cbs = new Set<EventCallback<T>>();

  const off = (fn: EventCallback<T>) => {
    cbs.delete(fn);
  };

  const on = (fn: EventCallback<T>) => {
    cbs.add(fn);
    return { off: () => off(fn) };
  };

  const trigger = (e: T) => {
    Array.from(cbs).forEach((fn) => fn(e));
  };

  return { on, off, trigger };
}

export type BoundingBox = { xmin: number; ymin: number; xmax: number; ymax: number };

const unionBoundingBox = (b1: BoundingBox, b2: BoundingBox): BoundingBox => {
  return {
    xmin: Math.min(b1.xmin, b2.xmin),
    xmax: Math.max(b1.xmax, b2.xmax),
    ymin: Math.min(b1.ymin, b2.ymin),
    ymax: Math.max(b1.ymax, b2.ymax),
  }
}

/**
 * Gets the bounding box for a geojson.
 *
 * Assumes WGS84 coordinates.
 */
const getGeoJSONBounds = (geojson: GeoJSON.GeoJSON): BoundingBox => {
  let bounds: BoundingBox = {
    xmin: 180,
    xmax: -180,
    ymin: 90,
    ymax: -90,
  };

  if (geojson.type === 'FeatureCollection') {
    geojson.features.forEach((feature) => {
      bounds = unionBoundingBox(bounds, getGeoJSONBounds(feature.geometry));
    })
  } else if (geojson.type === 'Feature') {
    bounds = unionBoundingBox(bounds, getGeoJSONBounds(geojson.geometry));
  } else if (geojson.type === 'GeometryCollection') {
    geojson.geometries.forEach((geom) => {
      bounds = unionBoundingBox(bounds, getGeoJSONBounds(geom));
    })
  } else {
    geojson.coordinates.flat(Infinity).forEach((val, idx) => {
      if (idx % 2 == 0) {
        // longitude
        bounds.xmin = Math.min(bounds.xmin, val as number);
        bounds.xmax = Math.max(bounds.xmax, val as number);
      } else {
        // latitude
        bounds.ymin = Math.min(bounds.ymin, val as number);
        bounds.ymax = Math.max(bounds.ymax, val as number);
      }
    });
  }
  return bounds;
}

function timeoutBatch(cb: () => void, timeout: number) {
  let t: number | null = null;
  return function() {
    if (t != null) return;
    t = setTimeout(() => {
      cb();
      t = null;
    }, timeout);
  };
}

export {
    timeRangeFormat,
    downloadPresignedFile,
    createEventHook,
    getGeoJSONBounds,
    timeoutBatch,
}
