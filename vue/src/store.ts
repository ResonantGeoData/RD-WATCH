import { computed, reactive } from "vue";

import { ApiService, Region } from "./client";

export interface MapFilters {
  configuration_id?: number[];
  performer_id?: number[];
  region_id?: number[];
  showSiteOutline?: boolean;
  groundTruthPattern?: boolean;
  otherPattern?: boolean;
  showRegionPolygon?: boolean;
}

export interface SatelliteTimeStamp {
  timestamp: string;
  cloudcover: number;
  collection: string;
  source: 'S2' | 'WorldView'
}

export type ImageBBox = [
  [
    number,
    number
  ],
  [
    number,
    number
  ],
  [
    number,
    number
  ],
  [
    number,
    number
  ]
];

export interface SiteObservationImage {
  image: string; // URL string toImage
  timestamp: number;
  source: 'S2' | 'WV' | 'L8';
  cloudcover?: number;
  percent_black?: number;
  siteobs_id: number | null;
  disabled?: boolean;
}

export interface EnabledSiteObservations {
  id: number;
  images: SiteObservationImage[];
  bbox: ImageBBox;
  timestamp: number;
}

export interface SiteObservation {
  id: number;
  timerange: {
    min: number;
    max: number;
  },
  imagesLoaded: boolean;
  imageCounts: {
    L8: {total:number, unmatched:number | null, loaded: number, images?: SiteObservationImage[]};
    S2: {total:number, unmatched:number | null, loaded: number, images?: SiteObservationImage[]};
    WV: {total:number, unmatched:number | null, loaded: number, images?: SiteObservationImage[]};
  }
  score: {
    min: number,
    max: number,
    average: number,
  }
  imagesActive: boolean;
  job?: { status: 'Running' | 'Complete' | 'Error', error?: '', timestamp: number };
  bbox: { xmin: number; ymin: number; xmax: number; ymax: number };
}


export interface SatelliteData {
  satelliteImagesOn: boolean;
  imageOpacity: number;
  satelliteTimeList: SatelliteTimeStamp[];
  satelliteTimeSource: 'S2' | 'WorldView'
  satelliteTimeStamp: string | null,
  satelliteBounds:[number,number][];
  loadingSatelliteImages: boolean;
  cloudCover: number;
  satelliteSources: ('S2' |'WorldView')[];
}

export interface siteObsSatSettings {
  observationSources: ('S2' | 'WV' | 'L8')[];
  percentBlackFilter: number;
  cloudCoverFilter: number;
  imageOpacity: number;
}

export const state = reactive<{
  timestamp: number;
  timeMin: number;
  settings: {
    autoZoom: boolean;
  };
  bbox: { xmin: number; ymin: number; xmax: number; ymax: number };
  filters: MapFilters;
  satellite: SatelliteData;
  patterns: {
    patternThickness: number;
    patternOpacity: number;
  };
  regionMap: Record<Region["id"], Region["name"]>
  selectedObservations: SiteObservation[];
  enabledSiteObservations: EnabledSiteObservations[],
  siteObsSatSettings: siteObsSatSettings,
  loopingInterval: NodeJS.Timeout | null,
  loopingId: number | null,
}>({
  timestamp: Math.floor(Date.now() / 1000),
  timeMin: new Date(0).valueOf(),
  settings: {
    autoZoom: false,
  },
  bbox: {
    xmin: -180,
    ymin: -90,
    xmax: 180,
    ymax: 90,
  },
  filters: {
    groundTruthPattern: false,
    otherPattern: false,
  },
  satellite: {
    satelliteImagesOn: false,
    satelliteTimeList:[],
    satelliteTimeStamp: null,
    satelliteBounds: [],
    imageOpacity: 1.0,
    loadingSatelliteImages: false,
    satelliteTimeSource: 'S2',
    cloudCover: 100,
    satelliteSources: ['S2'],
  },
  patterns: {
    patternThickness: 8,
    patternOpacity: 255,
  },
  regionMap: {},
  selectedObservations: [],
  enabledSiteObservations: [],
  siteObsSatSettings: {
    observationSources: ['S2', 'WV'],
    cloudCoverFilter: 70,
    percentBlackFilter: 70,
    imageOpacity: 1.0,
  },
  loopingInterval: null,
  loopingId: null,
});

export const filteredSatelliteTimeList = computed(() => {
  let filtered = state.satellite.satelliteTimeList;
  if (state.satellite.cloudCover <  100 ) {
    filtered = filtered.filter((item) => item.cloudcover < state.satellite.cloudCover);
  }
  filtered = filtered.filter((item) => state.satellite.satelliteSources.includes(item.source))
  return filtered;
})

export const selectedObservationList = computed(() => {
  const selected = state.selectedObservations;
  return selected.map((item) => item.id);
})


export const getSiteObservationDetails = async (siteId: string) => {
  const data = await ApiService.getSiteObservations(siteId);
  const { results } = data;
  const { images } = data;
  const worldViewList = images.results.filter((item) => item.source === 'WV' && item.image !== null)
    .sort((a, b) => (a.timestamp - b.timestamp));
  const S2List = images.results.filter((item) => item.source === 'S2' && item.image !== null).sort((a, b) => (a.timestamp - b.timestamp));

  const L8 = { 
    total: results.filter((item) => item.constellation === 'L8').length,
    loaded:images.results.filter((item) => item.source === 'L8').length,
    unmatched: null,

  };
  const S2 = {
    total: results.filter((item) => item.constellation === 'S2').length,
    loaded:S2List.length,
    images: S2List,
    unmatched: null,
  };
  const WV = { 
    total: results.filter((item) => item.constellation === 'WV').length,
    loaded:worldViewList.length,
    images: worldViewList,
    unmatched: null,
  };
  let minScore = Infinity;
  let maxScore = -Infinity;
  let avgScore = 0;
  results.forEach((item) => {
    minScore = Math.min(minScore, item.score);
    maxScore = Math.max(maxScore, item.score);
    avgScore += item.score
  })
  avgScore = avgScore / results.length;
  const numId = parseInt(siteId, 10)
  const foundIndex = state.selectedObservations.findIndex((item) => item.id === numId);
  const obsData =  {
  id: numId,
  timerange: data.timerange,
  imagesLoaded: false,
  imagesActive: false,
  imageCounts: {
    L8,
    S2,
    WV,
  },
  score: {
    min: minScore,
    max: maxScore,
    average: avgScore,
  },
  job: data.job,
  bbox: data.bbox,
};
  if (foundIndex === -1) {
    state.selectedObservations.push(obsData)
  } else {
    state.selectedObservations.splice(foundIndex, 1, obsData)
  }
}