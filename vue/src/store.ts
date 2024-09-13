import { computed, reactive } from "vue";

import { ApiService, CancelError, CancelablePromise, ModelRun, ModelRunList, Performer, QueryArguments, Region } from "./client";
import { EditGeoJSONType } from "./interactions/editGeoJSON";
import { BaseBBox, EvaluationImage } from "./types";
import { LngLatBounds } from "maplibre-gl";
import { RegionDetail } from "./client/models/Region";
import { emptyModelRunList } from "./client/models/ModelRunList";

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
  editingGeoJSONSiteId?: string | null; //currently editing a polygon
  addingSitePolygon?: boolean;
  addingRegionPolygon?: boolean;
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

export type RegionMapType = Record<string, {id: number, deleteBlock?: string, hasGeom?: boolean }>;
export interface SiteObservationImage {
  image: string; // URL string toImage
  timestamp: number;
  source: 'S2' | 'WV' | 'L8' | 'PL';
  cloudcover?: number;
  percent_black?: number;
  observation_id: string | null;
  disabled?: boolean;
  bbox: BaseBBox;
  id: number;
  image_embedding? : string;
  image_dimensions?: [number, number];
}

export interface SelectedImageSite {
    siteId: string,
    siteName: string,
    dateRange?: number[] | null
    siteDetails?: SiteDetails;
}

export interface SiteDetails {
  region: string;
  configurationId: number;
  siteNumber: number;
  version: string;
  performer: string;
  title: string;
}

export interface EnabledSiteOverviews {
  id: string;
  images: SiteObservationImage[];
  bbox: ImageBBox;
  timestamp: number;
}

export interface SiteDownloadJob {
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

export interface SiteOverview {
  id: string;
  siteDetails?: SiteDetails;
  timerange: {
    min: number;
    max: number;
  } | null,
  imagesLoaded: boolean;
  imageCounts: {
    L8: {total:number, unmatched:number | null, loaded: number, images?: SiteObservationImage[]};
    S2: {total:number, unmatched:number | null, loaded: number, images?: SiteObservationImage[]};
    PL: {total:number, unmatched:number | null, loaded: number, images?: SiteObservationImage[]};
    WV: {total:number, unmatched:number | null, loaded: number, images?: SiteObservationImage[]};
  }
  score: {
    min: number,
    max: number,
    average: number,
  }
  imagesActive: boolean;
  job?: SiteDownloadJob;
  bbox: { xmin: number; ymin: number; xmax: number; ymax: number };
}


export interface SatelliteData {
  satelliteImagesOn: boolean;
  imageOpacity: number;
  satelliteTimeList: SatelliteTimeStamp[];
  satelliteTimeSource: 'S2' | 'WorldView' | 'Planet'
  satelliteTimeStamp: string | null,
  satelliteBounds:[number,number][];
  loadingSatelliteImages: boolean;
  cloudCover: number;
  satelliteSources: ('S2' |'WorldView' | 'Planet')[];
}

export interface siteOverviewSatSettings {
  observationSources: ('S2' | 'WV' | 'L8' | 'PL')[];
  percentBlackFilter: number;
  cloudCoverFilter: number;
  imageOpacity: number;
}

export interface KeyedModelRun extends ModelRun {
  key: string;
}

export const state = reactive<{
  appVersion: string;
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
  selectedSites: SiteOverview[];
  enabledSiteImages: EnabledSiteOverviews[],
  siteOverviewSatSettings: siteOverviewSatSettings,
  loopingInterval: NodeJS.Timeout | null,
  loopingId: string | null,
  modelRuns: KeyedModelRun[],
  totalNumModelRuns: number;
  openedModelRuns: Set<KeyedModelRun["key"]>;
  gifSettings: { fps: number, quality: number, pointSize: number},
  performerMapping: Record<number, Performer>,
  proposals: {
    ground_truths?: string | null,
  }
  editGeoJSON: EditGeoJSONType | null,
  // Filters between the detail image viewer panel
  imageFilter: {
    sources: EvaluationImage['source'][];
    cloudCover: number;
    noData: number;
    obsFilter: ('observations' | 'non-observations')[];
  },
  // used to open the detail image viewer panel
  selectedImageSite?: SelectedImageSite | null;
  // Tooltip Display
  toolTipDisplay: Record<string, boolean>;
  toolTipMenuOpen: boolean;
  // GroundTruthLinks - regular model runs list of ground truths that can be opened
  // KeyValue store of the sourceModelRun UID and the groundTruth UID
  groundTruthLinks: Record<string, string>,
  // Region map is used to index names and owners with ids
  regionMap: RegionMapType;
  regionList: RegionDetail[];
  // Query states - stores states for network queries
  queryStates: {
    loadModelRuns: {
      request: CancelablePromise<ModelRunList> | undefined;
      inflightQueries: number;
      nextPage: number;
      activeFilters: QueryArguments;
    };
  };
}>({
  appVersion: '',
  errorText: '',
  timestamp: Math.floor(Date.now() / 1000),
  timeMin: Math.floor(new Date(0).valueOf() / 1000),
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
    drawObservations: undefined,
    drawSiteOutline: ['model'],
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
  selectedSites: [],
  enabledSiteImages: [],
  siteOverviewSatSettings: {
    observationSources: ['S2', 'WV', 'L8', 'PL'],
    cloudCoverFilter: 70,
    percentBlackFilter: 70,
    imageOpacity: 100.0,
  },
  loopingInterval: null,
  loopingId: null,
  modelRuns: [],
  totalNumModelRuns: 0,
  openedModelRuns: new Set<KeyedModelRun["key"]>(),
  gifSettings: { fps: 1, quality: 1, pointSize: 1},
  performerMapping: {},
  proposals: {},
  editGeoJSON: null,
  imageFilter: {
    sources: ['WV', 'S2', 'L8', 'PL'],
    cloudCover: 95,
    noData: 100,
    obsFilter: ['observations', 'non-observations']
  },
  toolTipDisplay: {
    Type: true,
    SiteId: true,
    Performer: true,
    ModelRun: false,
    Status: true,
    Time: true,
    Score: false,
    Area: false,
    ObsLabel:false,
  },
  toolTipMenuOpen: false,
  groundTruthLinks: {},
  regionMap: {},
  regionList: [],
  queryStates: {
    loadModelRuns: {
      inflightQueries: 0,
      request: undefined,
      nextPage: 1,
      activeFilters: {},
    },
  },
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
  const selected = state.selectedSites;
  return selected.map((item) => item.id);
})



export const getSiteObservationDetails = async (siteId: string, siteDetails?: SiteDetails, select=true) => {
  const data = await ApiService.getSiteObservations(siteId);
  const { results } = data;
  const { images } = data;
  const worldViewList = images.results.filter((item) => item.source === 'WV' && item.image !== null)
    .sort((a, b) => (a.timestamp - b.timestamp));
  const S2List = images.results.filter((item) => item.source === 'S2' && item.image !== null).sort((a, b) => (a.timestamp - b.timestamp));
  const L8List = images.results.filter((item) => item.source === 'L8' && item.image !== null).sort((a, b) => (a.timestamp - b.timestamp));
  const PLList = images.results.filter((item) => item.source === 'PL' && item.image !== null).sort((a, b) => (a.timestamp - b.timestamp));

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
  const PL = {
    total: results.filter((item) => item.constellation === 'PL').length,
    loaded:PLList.length,
    images: PLList,
    unmatched: null,
  }
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
  const foundIndex = state.selectedSites.findIndex((item) => item.id === numId);
  const obsData =  {
    id: numId,
    siteDetails,
    timerange: data.timerange,
    imagesLoaded: false,
    imagesActive: false,
    imageCounts: {
      L8,
      S2,
      WV,
      PL,
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
    state.selectedSites.push(obsData)
  } else {
    state.selectedSites.splice(foundIndex, 1, obsData)
  }
  return obsData;
}

export const toggleSatelliteImages = (siteOverview: SiteOverview, off= false) => {
  const found = state.enabledSiteImages.find((item) => item.id === siteOverview.id);
  if (found === undefined && !off) {
      const baseBBox = siteOverview.bbox;
      const bbox = [
          [baseBBox.xmin, baseBBox.ymax],
          [baseBBox.xmax, baseBBox.ymax],
          [baseBBox.xmax, baseBBox.ymin],
          [baseBBox.xmin, baseBBox.ymin],
      ] as ImageBBox;
      if (siteOverview.imageCounts.WV.images || siteOverview.imageCounts.S2.images) {
          const tempArr = [...state.enabledSiteImages];
          let imageList: SiteObservationImage[] = [];
          if (siteOverview.imageCounts.WV.images && state.siteOverviewSatSettings.observationSources.includes('WV')) {
            imageList = [...siteOverview.imageCounts.WV.images]
          }
          if (siteOverview.imageCounts.S2.images && state.siteOverviewSatSettings.observationSources.includes('S2')) {
            imageList = [...imageList, ...siteOverview.imageCounts.S2.images]
          }
          if (siteOverview.imageCounts.L8.images && state.siteOverviewSatSettings.observationSources.includes('L8')) {
            imageList = [...imageList, ...siteOverview.imageCounts.L8.images]
          }
          if (siteOverview.imageCounts.PL.images && state.siteOverviewSatSettings.observationSources.includes('PL')) {
            imageList = [...imageList, ...siteOverview.imageCounts.PL.images]
          }
          tempArr.push({
              id: siteOverview.id,
              timestamp: siteOverview.timerange ? siteOverview.timerange.min : 0,
              images: imageList,
              bbox,
          });
          state.enabledSiteImages = tempArr;
      }
  } else {
      const tempArr = [...state.enabledSiteImages];
      const index = tempArr.findIndex((item) => item.id === siteOverview.id);
      if (index !== -1) {
          tempArr.splice(index, 1);
          state.enabledSiteImages = tempArr;
      }
  }
}

const loadAndToggleSatelliteImages = async (siteId: string) => {
  const index = state.enabledSiteImages.findIndex((item) => item.id === siteId);
  if (index !== -1) {
    const tempArr = [...state.enabledSiteImages];
    tempArr.splice(index, 1);
    state.enabledSiteImages = tempArr;
  } else {
  const data = await getSiteObservationDetails(siteId, undefined, false);
  toggleSatelliteImages(data);
  }
}



/**
 * Set the camera bounds/viewport based on the currently selected model run(s).
 */
function updateCameraBoundsBasedOnModelRunList(filtered = true, force = false) {
  const bounds = new LngLatBounds();
  let list = state.modelRuns;
  if (filtered) {
    list = state.modelRuns.filter((modelRun) =>
      state.openedModelRuns.has(modelRun.key)
    );
  }
  if (
    !force &&
    !state.settings.autoZoom &&
    state.filters.regions &&
    state.filters.regions?.length > 0
  ) {
    return;
  }
  list.forEach((modelRun) => {
    modelRun.bbox?.coordinates
      .flat()
      .forEach((c) => bounds.extend(c as [number, number]));
  });
  if (bounds.isEmpty()) {
    const bbox = {
      xmin: -180,
      ymin: -90,
      xmax: 180,
      ymax: 90,
    };
    state.bbox = bbox;
  } else {
    state.bbox = {
      xmin: bounds.getWest(),
      ymin: bounds.getSouth(),
      xmax: bounds.getEast(),
      ymax: bounds.getNorth(),
    };
  }
}


const updateRegionList = async () => {
  const regionList = await ApiService.getRegionDetails();
  const regionResults = regionList.items;

  const tempRegionMap: RegionMapType = {};
  regionResults.forEach((item) => tempRegionMap[item.value] = { id:item.id, deleteBlock: item.deleteBlock, hasGeom: item.hasGeom });
  state.regionMap = tempRegionMap;
  regionResults.sort((a, b) => {
    // First sort by whether the owner is not 'None'
    if (a.ownerUsername !== 'None' && b.ownerUsername === 'None') {
      return -1;
    }
    if (a.ownerUsername === 'None' && b.ownerUsername !== 'None') {
      return 1;
    }
    // If both have owners or both do not, sort by name
    return a.name.localeCompare(b.name);
  });
  state.regionList = regionResults;
}

const updateRegionMap = async () => {
  const regionList = await ApiService.getRegionDetails();
  const regionResults = regionList.items;
  const tempRegionMap: RegionMapType = {};
  regionResults.forEach((item) => tempRegionMap[item.value] = { id:item.id, deleteBlock: item.deleteBlock, hasGeom: item.hasGeom });
  state.regionMap = tempRegionMap;
}

/**
 * Loads a page of model runs.
 *
 * Next page information is only saved when the request completes.
 * Therefore, request nextPage while firstPage is inflight will cancel
 * the firstPage request.
 *
 * @param type "firstPage" or "nextPage"
 * @param filters query filters
 * @param compact
 * @returns
 */
async function queryModelRuns(type: 'firstPage' | 'nextPage', filters: QueryArguments, compact  = false): Promise<ModelRunList> {
  const queryState = state.queryStates.loadModelRuns;

  queryState.request?.cancel();
  queryState.request = undefined;

  if (type !== 'firstPage' && state.modelRuns.length === state.totalNumModelRuns) {
    return emptyModelRunList();
  }

  let page = 0;
  if (type === 'firstPage') {
    page = 1;
  } else if (type === 'nextPage') {
    page = queryState.nextPage;
  } else {
    throw new Error('Invalid call to loadModelRuns');
  }

  const { mode, performer } = filters; // unwrap performer and mode arrays
  queryState.activeFilters = {
    ...filters,
    mode,
    performer,
    proposal: compact ? 'PROPOSAL' : undefined, // if compact we are doing proposal adjudication
  };
  queryState.request = ApiService.getModelRuns({
    ...queryState.activeFilters,
    page,
  });
  try {
    queryState.inflightQueries++;
    const modelRunList = await queryState.request;
    queryState.request = undefined;
    state.totalNumModelRuns = modelRunList.count;
    queryState.nextPage = page + 1;

    // sort list to show ground truth near the top
    const modelRunResults = modelRunList.items;
    const keyedModelRunResults = modelRunResults.map((val) => {
      return {
        ...val,
        key: `${val.id}`,
      };
    });

    // If a bounding box was provided for this model run list, zoom the camera to it.
    if (modelRunList.bbox) {
      const bounds = new LngLatBounds();
      modelRunList.bbox.coordinates
        .flat()
        .forEach((c) => bounds.extend(c as [number, number]));
      const bbox = {
        xmin: bounds.getWest(),
        ymin: bounds.getSouth(),
        xmax: bounds.getEast(),
        ymax: bounds.getNorth(),
      };
      state.bbox = bbox;
    } else if (!state.filters.regions?.length) {
      const bbox = {
        xmin: -180,
        ymin: -90,
        xmax: 180,
        ymax: 90,
      };
      state.bbox = bbox;
    }

    // If we're on page 1, we *might* have switched to a different filter/grouping in the UI,
    // meaning we would need to clear out any existing results.
    // To account for this, just set the array to the results directly instead of concatenating.
    if (page === 1) {
      state.modelRuns = keyedModelRunResults;
    } else {
      state.modelRuns = state.modelRuns.concat(keyedModelRunResults);
    }

    if (modelRunList['timerange'] !== null) {
      state.timeMin = modelRunList['timerange'].min;
    }

    return modelRunList;
  } catch (e) {
    if (e instanceof CancelError) {
      console.log('Request has been cancelled');
    } else {
      throw e;
    }
  } finally {
    queryState.inflightQueries--;
  }

  return emptyModelRunList();
}

/**
 * Refreshes the downloading state for the queried model runs.
 *
 * This will paginate the model run listing endpoint until all loaded
 * pages are satisfied.
 *
 * - Only operates on the loaded pages at the time of invocation.
 * - If an existing request is inflight, this will chain onto the
 *   existing request (a CancelablePromise).
 * - If cancelled, the entire chain is cancelled.
 */
const refreshModelRunDownloadingStatuses = async () => {
  const queryState = state.queryStates.loadModelRuns;
  const loadedPages = queryState.nextPage - 1;
  const activeFilters = queryState.activeFilters;

  let existingRequest = queryState.request as CancelablePromise<void> | undefined;

  // chain cancelable requests
  for (let page = 0; page < loadedPages; page++) {
    const prevReq = existingRequest;
    existingRequest = new CancelablePromise(async (resolve, reject, onCancel) => {
      let apiCallRequest: CancelablePromise<ModelRunList> | undefined;

      onCancel(() => {
        prevReq?.cancel();
        apiCallRequest?.cancel();
      });

      try {
        await prevReq;

        apiCallRequest = ApiService.getModelRuns({
          ...activeFilters,
          page,
        });
        const modelRunList = await apiCallRequest;

        const modelRuns = modelRunList.items;
        // NOTE this is inefficient if modelRuns.length is large and/or
        // if the page size is large. Practically, this shouldn't be an issue.
        // A better solution here is to use a lookup table (id -> modelRun).
        for (let i = 0; i < state.modelRuns.length; i += 1) {
          const currentModelRun = state.modelRuns[i];
          const found = modelRuns.find((item) => item.id === currentModelRun.id);
          if (found) {
            if (found.downloading) {
              state.modelRuns[i].downloading = found.downloading;
            }
          }
        }
      } catch (err) {
        if (!(err instanceof CancelError)) reject(err);
      }

      resolve();
    });
  }
};

export {
  loadAndToggleSatelliteImages,
  updateCameraBoundsBasedOnModelRunList,
  updateRegionList,
  updateRegionMap,
  queryModelRuns,
  refreshModelRunDownloadingStatuses,
}

