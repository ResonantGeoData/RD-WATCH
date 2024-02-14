import { computed, reactive } from "vue";

import { ApiService, ModelRun, Performer, Region } from "./client";
import { EditPolygonType } from "./interactions/editPolygon";
export interface MapFilters {
  configuration_id?: string[];
  performer_ids?: number[];
  regions?: Region[];
  mode?: string[];
  drawSiteOutline?: string[]; //looking for either 'model' | 'groundtruth'
  drawObservations?: string[]; //looking for either 'model' | 'groundtruth'
  scoringColoring?: 'simple' | 'detailed';
  groundTruthPattern?: boolean;
  drawRegionPoly?: boolean;
  otherPattern?: boolean;
  hoverSiteId?: string;
  showText?: boolean;
  siteTimeLimits?: boolean;
  drawMap?: boolean;
  proposals?: {
    accepted?: string[],
    rejected?: string[],
  }
  randomKey?: string;
  editingPolygonSiteId?: string | null; //currently editing a polygon
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
  observation_id: string | null;
  disabled?: boolean;
  bbox: { xmin: number; ymin: number; xmax: number; ymax: number };
  id: number;
  image_embedding? : string;
}

export interface ObsDetails {
  region: string;
  configurationId: number;
  siteNumber: number;
  version: string;
  performer: string;
  title: string;
}

export interface EnabledSiteObservations {
  id: string;
  images: SiteObservationImage[];
  bbox: ImageBBox;
  timestamp: number;
}

export interface SiteObservationJob {
  status: 'Running' | 'Complete' | 'Error';
  error?: string;
  timestamp: number;
  celery?: {
    info?:  {
      current: number
      total: number;
      mode: 'Image Captures' | 'Searching All Images' | 'Site Observations' | 'No Captures'
    }
  }
}

export interface SiteObservation {
  id: string;
  obsDetails?: ObsDetails;
  timerange: {
    min: number;
    max: number;
  } | null,
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
  job?: SiteObservationJob;
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

export interface KeyedModelRun extends ModelRun {
  key: string;
}

export const state = reactive<{
  errorText: string;
  timestamp: number;
  timeMin: number;
  settings: {
    autoZoom: boolean;
  };
  bbox: { xmin: number; ymin: number; xmax: number; ymax: number };
  filters: MapFilters;
  mapLegend: boolean;
  satellite: SatelliteData;
  patterns: {
    patternThickness: number;
    patternOpacity: number;
  };
  selectedObservations: SiteObservation[];
  enabledSiteObservations: EnabledSiteObservations[],
  siteObsSatSettings: siteObsSatSettings,
  loopingInterval: NodeJS.Timeout | null,
  loopingId: string | null,
  modelRuns: KeyedModelRun[],
  openedModelRuns: Set<KeyedModelRun["key"]>
  gifSettings: { fps: number, quality: number},
  performerMapping: Record<number, Performer>,
  proposals: {
    ground_truths?: string | null,
  }
  editPolygon: EditPolygonType | null,

}>({
  errorText: '',
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
    drawObservations: ['model'],
    drawSiteOutline: undefined,
    groundTruthPattern: false,
    otherPattern: false,
    showText: false,
    drawMap: true,
  },
  mapLegend: true,
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
  selectedObservations: [],
  enabledSiteObservations: [],
  siteObsSatSettings: {
    observationSources: ['S2', 'WV', 'L8'],
    cloudCoverFilter: 70,
    percentBlackFilter: 70,
    imageOpacity: 100.0,
  },
  loopingInterval: null,
  loopingId: null,
  modelRuns: [],
  openedModelRuns: new Set<KeyedModelRun["key"]>(),
  gifSettings: { fps: 1, quality: 1},
  performerMapping: {},
  proposals: {},
  editPolygon: null,
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



export const getSiteObservationDetails = async (siteId: string, obsDetails?: ObsDetails, select=true) => {
  const data = await ApiService.getSiteObservations(siteId);
  const { results } = data;
  const { images } = data;
  const worldViewList = images.results.filter((item) => item.source === 'WV' && item.image !== null)
    .sort((a, b) => (a.timestamp - b.timestamp));
  const S2List = images.results.filter((item) => item.source === 'S2' && item.image !== null).sort((a, b) => (a.timestamp - b.timestamp));
  const L8List = images.results.filter((item) => item.source === 'L8' && item.image !== null).sort((a, b) => (a.timestamp - b.timestamp));

  const L8 = {
    total: results.filter((item) => item.constellation === 'L8').length,
    loaded:L8List.length,
    images: L8List,
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
  const numId = siteId
  const foundIndex = state.selectedObservations.findIndex((item) => item.id === numId);
  const obsData =  {
    id: numId,
    obsDetails,
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
  if (foundIndex === -1 && select) {
    state.selectedObservations.push(obsData)
  } else {
    state.selectedObservations.splice(foundIndex, 1, obsData)
  }
  return obsData;
}

export const toggleSatelliteImages = (siteObs: SiteObservation, off= false) => {
  const found = state.enabledSiteObservations.find((item) => item.id === siteObs.id);
  if (found === undefined && !off) {
      const baseBBox = siteObs.bbox;
      const bbox = [
          [baseBBox.xmin, baseBBox.ymax],
          [baseBBox.xmax, baseBBox.ymax],
          [baseBBox.xmax, baseBBox.ymin],
          [baseBBox.xmin, baseBBox.ymin],
      ] as ImageBBox;
      if (siteObs.imageCounts.WV.images || siteObs.imageCounts.S2.images) {
          const tempArr = [...state.enabledSiteObservations];
          let imageList: SiteObservationImage[] = [];
          if (siteObs.imageCounts.WV.images && state.siteObsSatSettings.observationSources.includes('WV')) {
            imageList = [...siteObs.imageCounts.WV.images]
          }
          if (siteObs.imageCounts.S2.images && state.siteObsSatSettings.observationSources.includes('S2')) {
            imageList = [...imageList, ...siteObs.imageCounts.S2.images]
          }
          if (siteObs.imageCounts.L8.images && state.siteObsSatSettings.observationSources.includes('L8')) {
            imageList = [...imageList, ...siteObs.imageCounts.L8.images]
          }
          tempArr.push({
              id: siteObs.id,
              timestamp: siteObs.timerange ? siteObs.timerange.min : 0,
              images: imageList,
              bbox,
          });
          state.enabledSiteObservations = tempArr;
      }
  } else {
      const tempArr = [...state.enabledSiteObservations];
      const index = tempArr.findIndex((item) => item.id === siteObs.id);
      if (index !== -1) {
          tempArr.splice(index, 1);
          state.enabledSiteObservations = tempArr;
      }
  }
}

const loadAndToggleSatelliteImages = async (siteId: string) => {
  const index = state.enabledSiteObservations.findIndex((item) => item.id === siteId);
  if (index !== -1) {
    const tempArr = [...state.enabledSiteObservations];
    tempArr.splice(index, 1);
    state.enabledSiteObservations = tempArr;
  } else {
  const data = await getSiteObservationDetails(siteId, undefined, false);
  toggleSatelliteImages(data);
  }
}

export {
  loadAndToggleSatelliteImages,
}