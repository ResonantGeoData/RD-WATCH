<script setup lang="ts">
import { Ref, computed, onMounted, onUnmounted, ref, watch, withDefaults } from "vue";
import { ApiService, SiteEvaluationList } from "../../client";
import { EvaluationImage, EvaluationImageResults } from "../../types";
import { getColorFromLabel, styles } from '../../mapstyle/annotationStyles';
import { ObsDetails, SiteObservationImage, loadAndToggleSatelliteImages, state } from '../../store'
import { SiteModelStatus } from "../../client/services/ApiService";
import { CanvasCapture } from 'canvas-capture';
import type { PixelPoly } from './imageUtils';
import { createCanvas, drawData, processImagePoly } from './imageUtils';
import maplibregl from 'maplibre-gl';
interface Props {
  siteEvalId: string;
  dialog?: boolean;
  editable?: boolean;
  siteEvaluationName?: string | null;
  dateRange?: number[] | null
  obsDetails?: ObsDetails;
  fullscreen?: boolean;
}


type EditModes = 'SiteEvaluationLabel' | 'StartDate' | 'EndDate' | 'SiteObservationLabel' | 'SiteEvaluationNotes' | 'SiteObservationNotes'

const props = withDefaults(defineProps<Props>(), {
  dialog: false,
  editable: false,
  siteEvaluationName: null,
  dateRange: null,
  obsDetails: undefined,
});

const emit = defineEmits<{
  (e: "close"): void;
  (e: "update-list"): void;
  (e: "eval-save", {label, startDate, endDate, notes} :{
    label: string;
    startDate: string | null
    endDate: string | null;
    notes: string;
  }): void;
}>();

const loading = ref(false);
const currentImage = ref(0);
const editMode = ref(props.editable);

const editDialog = ref(false);
const currentEditMode: Ref<null | EditModes> = ref(null);
const notes = ref('');
const siteEvaluationLabel = ref('unknown');
const startDate: Ref<string|null> = ref(props.dateRange && props.dateRange[0] ? new Date(props.dateRange[0] * 1000).toISOString().split('T')[0] : null);
const endDate: Ref<string|null> = ref(props.dateRange && props.dateRange[1] ? new Date(props.dateRange[1] * 1000).toISOString().split('T')[0] : null);
const siteEvaluationNotes = ref('');
const siteEvaluationUpdated = ref(false)
const siteStatus: Ref<string | null> = ref(null);
const imageRef: Ref<HTMLImageElement | null> = ref(null);
const canvasRef: Ref<HTMLCanvasElement | null> = ref(null);
const baseImageSources = ref(['S2', 'WV', 'L8'])
const baseObs = ref(['observations', 'non-observations'])
const filterSettings = ref(false);
const combinedImages: Ref<{image: EvaluationImage; poly: PixelPoly, groundTruthPoly?: PixelPoly}[]> = ref([]);
const imageSourcesFilter: Ref<EvaluationImage['source'][]> = ref(['S2', 'WV', 'L8']);
const percentBlackFilter: Ref<number> = ref(100);
const cloudFilter: Ref<number> = ref(100);
const siteObsFilter: Ref<('observations' | 'non-observations')[]> = ref(['observations', 'non-observations'])
// Ease of display refs
const currentLabel = ref('unknown')
const currentDate = ref('');
// Ground Truth Values
const hasGroundTruth = ref(false);
const groundTruth: Ref<EvaluationImageResults['groundTruth'] | null > = ref(null);
const drawGroundTruth = ref(false);
const siteEvaluationList = computed(() => Object.entries(styles).filter(([, { type }]) => type === 'sites').map(([label]) => label));
const rescaleImage = ref(false);
const rescalingBBox = ref(1);
const editingPolygon = ref(false);

const playbackEnabled = ref(false); // Auto playback of images

const evaluationGeoJSON: Ref<GeoJSON.Polygon | null> = ref(null); // holds the site geoJSON so it can be edited

const showSitePoly = ref(props.editable); // Swap between showing the site polygon and the site observation polygon

const filteredImages = computed(() => {
  return combinedImages.value.filter((item) => {
    let add = true;
    if (!imageSourcesFilter.value.includes(item.image.source)) {
      add = false;
    }
    if (siteObsFilter.value.includes('observations') && siteObsFilter.value.length ===1 && item.image.observation_id === null) {
      add = false;
    }
    if (siteObsFilter.value.includes('non-observations') && siteObsFilter.value.length ===1 && item.image.observation_id !== null) {
      add = false;
    }
    if (item.image.percent_black > percentBlackFilter.value) {
      add = false;
    }
    if (item.image.cloudcover > cloudFilter.value) {
      add = false;
    }
    return add;
  })

})




const currentTimestamp = computed(() => {
    if (filteredImages.value[currentImage.value]) {
    const time = filteredImages.value[currentImage.value].image.timestamp;
    return new Date(time * 1000).toISOString().split('T')[0]
    }
    return new Date().toISOString().split('T')[0]
})

watch(currentTimestamp, () => {
  currentDate.value = currentTimestamp.value;
});


const getImageData = async () => {
    combinedImages.value = [];
    currentImage.value = 0;
    const data =  await ApiService.getEvaluationImages(props.siteEvalId);
    const images = data.images.results.sort((a, b) => a.timestamp - b.timestamp);
    const polygons = data.geoJSON;
    evaluationGeoJSON.value = data.evaluationGeoJSON;
    polygons.sort((a,b) => a.timestamp - b.timestamp);
    siteEvaluationNotes.value = data.notes || '';
    siteEvaluationLabel.value = data.label;
    siteStatus.value = data.status;
    if (data.groundTruth) {
      hasGroundTruth.value = true;
      groundTruth.value = data.groundTruth;
    } else {
      hasGroundTruth.value = false;
      groundTruth.value = null;
    }
    if (imageRef.value !== null) {
        imageRef.value.src = images[currentImage.value].image;
    }
    // Lets process the polygons to get them in pixel space.
    // For each polygon we need to convert it to the proper image sizing result.
    images.forEach((image) => {
        const result = processImagePoly(image, polygons, data.evaluationGeoJSON, data.evaluationBBox, data.label, hasGroundTruth.value, groundTruth.value, showSitePoly.value);
        combinedImages.value.push(result);
    })
}
let background: HTMLCanvasElement & { ctx?: CanvasRenderingContext2D | null };

watch(showSitePoly, () => {
  getImageData();
})

// GIF Settings and Variables


const downloadingGifFPS = computed({
  get() {
    return state.gifSettings.fps;
  },
  set(val: number) {
    state.gifSettings = { ...state.gifSettings, fps: val };
  },
});
const downloadingGifQuality = computed({
  get() {
    return state.gifSettings.quality || 0.01;
  },
  set(val: number) {
    state.gifSettings = { ...state.gifSettings, quality: val };
  },
});


const downloadingGif = ref(false);
const downloadingGifState: Ref<null | 'drawing' | 'generating'> = ref(null);
const downloadingGifProgress = ref(0);
const GifSettingsDialog = ref(false);
const exportProgress = (progress: number) => {
  downloadingGifProgress.value = progress * 100;
  if (progress === 1) {
    downloadingGif.value = false;
    downloadingGifState.value = null;
    downloadingGifProgress.value = 0;
  }
}

function drawForDownload() {
  downloadingGif.value = true;
  let width = -Infinity;
  let height = -Infinity;
  for (let i = 0; i< filteredImages.value.length; i += 1) {
    const [imgWidth, imgHeight ] =filteredImages.value[i].image.image_dimensions;
    width = Math.max(width, imgWidth);
    height = Math.max(height, imgHeight);
  }
  if (width < 500 || height < 500) {
    const ratio = width / height;
    if (width < 500) {
      width = 500;
      height = ratio / 500;
    }
    if (height < 500) {
      height = 500;
      width = ratio * 500;
    }
  }
  const offScreenCanvas = createCanvas(width * rescalingBBox.value, height * rescalingBBox.value);
  downloadingGifState.value = 'drawing';
  CanvasCapture.init(offScreenCanvas, { verbose: false});
  CanvasCapture.beginGIFRecord({
    name: props.siteEvaluationName || 'download',
    fps: downloadingGifFPS.value,
    quality: downloadingGifQuality.value,
    onExportProgress: exportProgress,
  });
  let index = 0;
  function drawImageForRecord(){
    requestAnimationFrame(drawImageForRecord);
    if (index < filteredImages.value.length ) {
      drawData(
        offScreenCanvas,
        filteredImages.value[index].image,
        filteredImages.value[index].poly,
        filteredImages.value[index].groundTruthPoly,
        width,
        height,
        background,
        drawGroundTruth.value,
        rescaleImage.value,
        props.fullscreen,
        rescalingBBox.value,
      );
      CanvasCapture.recordFrame();
      index += 1
      downloadingGifProgress.value = (index / filteredImages.value.length) * 100;
    } else {
      CanvasCapture.stopRecord();
      downloadingGifState.value = 'generating';
      downloadingGifProgress.value = 0;
    }
  }
  drawImageForRecord();
}
const load = async (newValue?: string, oldValue?: string) => {
  const index = state.enabledSiteObservations.findIndex((item) => item.id === oldValue);

  startDate.value = (props.dateRange && props.dateRange[0] ? new Date(props.dateRange[0] * 1000).toISOString().split('T')[0] : null);
  endDate.value= (props.dateRange && props.dateRange[1] ? new Date(props.dateRange[1] * 1000).toISOString().split('T')[0] : null);

  if (index !== -1) {
    const tempArr = [...state.enabledSiteObservations];
    tempArr.splice(index, 1);
    state.enabledSiteObservations = tempArr;
  }
  loading.value = true;
  await getImageData();
  if (props.editable) {
    loadAndToggleSatelliteImages(props.siteEvalId);
  }
  if (currentImage.value < filteredImages.value.length && canvasRef.value !== null) {
      drawData(
        canvasRef.value,
        filteredImages.value[currentImage.value].image,
        filteredImages.value[currentImage.value].poly,
        filteredImages.value[currentImage.value].groundTruthPoly,
        -1,
        -1,
        background,
        drawGroundTruth.value,
        rescaleImage.value,
        props.fullscreen,
        rescalingBBox.value,
        )
  }
  loading.value = false;
}

watch(() => props.siteEvalId , () => {
  state.enabledSiteObservations = []; // toggle off all other satellite images
  cancelEditingPolygon();
  load();

});
load();

watch([percentBlackFilter, cloudFilter, siteObsFilter, imageSourcesFilter], () => {
  if (currentImage.value > filteredImages.value.length) {
    currentImage.value = 0;
  }
});

const copyURL = async (mytext: string) => {
    try {
      await navigator.clipboard.writeText(mytext);
    } catch($e) {
      alert('Cannot copy');
    }
  }


watch([currentImage, imageRef, filteredImages, drawGroundTruth, rescaleImage, rescalingBBox], () => {
    if (currentImage.value < filteredImages.value.length && imageRef.value !== null) {
        imageRef.value.src = filteredImages.value[currentImage.value].image.image;
    }
    currentLabel.value = filteredImages.value[currentImage.value].poly.label;
    if (currentImage.value < filteredImages.value.length && canvasRef.value !== null) {
        drawData(
          canvasRef.value,
          filteredImages.value[currentImage.value].image,
          filteredImages.value[currentImage.value].poly,
          filteredImages.value[currentImage.value].groundTruthPoly,
          -1,
          -1,
          background,
          drawGroundTruth.value,
          rescaleImage.value,
          props.fullscreen,
          rescalingBBox.value,
        )
    }
    if (props.dialog === false && !props.fullscreen && filteredImages.value[currentImage.value]) {
      state.timestamp = filteredImages.value[currentImage.value].image.timestamp;
    }

});

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const updateTime = (time: any, date: 'StartDate' | 'EndDate'| 'StartDateTemp' | 'EndDateTemp') => {
  if (time === null) {
    if (date === 'StartDate') {
      startDate.value = null;
    } else if (date === 'EndDate') {
      endDate.value = null
    } else if (date === 'StartDateTemp') {
      startDateTemp.value = null;
    }  else if (date === 'EndDateTemp') {
      endDateTemp.value = null;
    }
    editDialog.value = false;
  } else {
    if (date === 'StartDate') {
      startDate.value = new Date(time as string).toISOString().split('T')[0];
    } else if (date === 'EndDate') {
      endDate.value = new Date(time as string).toISOString().split('T')[0];
    } else if (date === 'StartDateTemp') {
      startDateTemp.value = new Date(time as string).toISOString().split('T')[0];
    } else if (date === 'EndDateTemp') {
      endDateTemp.value = new Date(time as string).toISOString().split('T')[0];
    }
  }
  siteEvaluationUpdated.value = true;
}

const mapImagesOn = computed(() => (state.enabledSiteObservations.findIndex((item) => item.id === props.siteEvalId) !== -1));
const startDateTemp: Ref<string | null> = ref(null);
const endDateTemp: Ref<string | null> = ref(null);
const setEditingMode = (mode: EditModes) => {
  if (['StartDate', 'EndDate'].includes(mode)){
    if (startDate.value === null) {
      startDateTemp.value = currentDate.value;
    } else {
      startDateTemp.value = startDate.value;
    }
    if (endDate.value === null) {
      endDateTemp.value = currentDate.value;
    } else {
      endDateTemp.value = endDate.value;
    }
  }
  editDialog.value = true;
  currentEditMode.value = mode;
}


const saveSiteEvaluationChanges = async () => {
 await  ApiService.patchSiteEvaluation(props.siteEvalId, {
    label: siteEvaluationLabel.value,
    start_date: startDate.value,
    end_date: endDate.value,
    notes: siteEvaluationNotes.value ? siteEvaluationNotes.value : undefined,
  });
  siteEvaluationUpdated.value = false;
  emit('update-list');
  // reset cache after changing siteEvals for vector tiles
  await getImageData();
  maplibregl.clearStorage();
  // We need to update the source to get information
  // This reloads the source vector-tile to color it properly after data has been changed.
  state.filters.randomKey = `?randomKey=randomKey_${Math.random()*1000}`;
}

const setSiteModelStatus = async (status: SiteModelStatus) => {
  if (status) {
    await ApiService.patchSiteEvaluation(props.siteEvalId, {
      status
    });
    siteStatus.value = status;
    emit('update-list');
    load();
  }
}

const adjustImage = (direction: number) => {
  if (currentImage.value + direction < 0) {
    currentImage.value = filteredImages.value.length - 1;
  } else if (currentImage.value + direction >= filteredImages.value.length) {
    currentImage.value = 0;
  } else {
    currentImage.value = currentImage.value + direction
  }
}

let loopingInterval: NodeJS.Timeout | null = null;


const togglePlayback = () => {

  if (loopingInterval && playbackEnabled.value) {
    clearInterval(loopingInterval);
    playbackEnabled.value = false;
    return;
  }
  loopingInterval =
  setInterval(() => {
    adjustImage(1)
  }, (1.0 / downloadingGifFPS.value) * 1000);
  playbackEnabled.value = true;
};

const keyboardEventListener = (e: KeyboardEvent) => {
  if (e.key === 'ArrowLeft') {
    if (e.ctrlKey) {
      currentImage.value = 0;
    } else {
      adjustImage(-1);
    }
  }
  if (e.key === 'ArrowRight') {
    if (e.ctrlKey) {
      currentImage.value = filteredImages.value.length - 1;
    } else {
      adjustImage(1);
    }
  }
  if (e.key === ' ') {
    togglePlayback();
  }
}

onMounted(() => {
  window.addEventListener('keydown', keyboardEventListener);
})

onUnmounted(() => {
  if (loopingInterval) {
    clearInterval(loopingInterval);
  }
  window.removeEventListener('keydown', keyboardEventListener);
  if (props.editable && state.enabledSiteObservations.find((item) => item.id === props.siteEvalId)) {
    loadAndToggleSatelliteImages(props.siteEvalId);
  }
  if (editingPolygon.value) {
    state.filters.editingPolygonSiteId = null;
    editingPolygon.value = false;
  }
});


const startEditingPolygon = () => {
  state.filters.editingPolygonSiteId = props.siteEvalId;
  if (state.editPolygon && evaluationGeoJSON.value) {
    state.editPolygon.setPolygonEdit(evaluationGeoJSON.value);
    editingPolygon.value = true;
  }
}

const cancelEditingPolygon = () => {
  state.filters.editingPolygonSiteId = null;
  if (state.editPolygon && evaluationGeoJSON.value) {
    state.editPolygon.cancelPolygonEdit();
    editingPolygon.value = false;
  }
}

const saveEditingPolygon = async () => {
  if (state.editPolygon) {
    const polyGeoJSON = state.editPolygon.getEditingPolygon();
    if (polyGeoJSON) {
      evaluationGeoJSON.value = polyGeoJSON;
      await ApiService.patchSiteEvaluation(props.siteEvalId, { geom: polyGeoJSON });
      cancelEditingPolygon();
      maplibregl.clearStorage();
      // We need to update the source to get information
      // This reloads the source vector-tile to color it properly after data has been changed.
      state.filters.randomKey = `?randomKey=randomKey_${Math.random()*1000}`;
      await getImageData();
    }
  }
}
const selectedPoints = computed(() => state.editPolygon && (state.editPolygon.selectedPoints).length);

const deleteSelectedPoints = () => {
  if (state.editPolygon && selectedPoints.value) {
    state.editPolygon.deleteSelectedPoints();
  }
}


const generateImageEmbedding = (image: SiteObservationImage | EvaluationImage) => {
  ApiService.postSiteImageEmbedding(image.id);
}
const openSAMView = (id: number) => {
  const name = `#${ApiService.getApiPrefix().replace('api/','').replace('/api','')}/SAM/${id}`
  window.open(name, '_blank');
};

const processImageEmbeddingButton = (image: SiteObservationImage | EvaluationImage) => {
  if (image && !image.image_embedding) {
    generateImageEmbedding(image);
  } else {
    openSAMView(image.id);
  }
}

// Set Keyboard Shortcuts


</script>

<template>
  <v-card
    class="pa-4"
    :class="{review: !dialog && !fullscreen, 'fullscreen': fullscreen}"
  >
    <v-row
      v-if="dialog || fullscreen"
      dense
      class="top-bar"
    >
      <v-col v-if="obsDetails">
        <span>{{ obsDetails.performer }} {{ obsDetails.title }} : V{{ obsDetails.version }}</span>
        <div v-if="hasGroundTruth && editable">
          <v-checkbox
            v-model="drawGroundTruth"
            density="compact"
            label="Draw GT"
          />
        </div>
      </v-col>
      <v-col v-if="obsDetails">
        <span>{{ siteEvaluationName }}</span>
      </v-col>

      <v-col v-if="obsDetails">
        <b
          v-if="groundTruth && hasGroundTruth" 
          class="mr-1"
        >Model Date Range:</b>
        <span>{{ startDate }}</span> to <span> {{ endDate }}</span>
        <div v-if="groundTruth && hasGroundTruth">
          <b class="mr-1">GroundTruth Date Range:</b>
          <span> {{ new Date(groundTruth.timerange.min * 1000).toISOString().split('T')[0] }}
          </span>
          <span> to </span>
          <span> {{ new Date(groundTruth.timerange.max * 1000).toISOString().split('T')[0] }}</span>
        </div>
      </v-col>
      <v-spacer />
      <v-icon
        v-if="dialog"
        @click="emit('close')"
      >
        mdi-close
      </v-icon>
    </v-row>
    <v-card-title
      v-else
      class="edit-title"
    >
      <v-row dense>
        <v-col
          v-if="editable"
          style="max-width:20px"
        >
          <v-tooltip
            open-delay="50"
            bottom
          >
            <template #activator="{ props:subProps }">
              <v-icon
                v-bind="subProps"
                :color="mapImagesOn ? 'rgb(37, 99, 235)' : ''"
                @click="loadAndToggleSatelliteImages(siteEvalId)"
              >
                mdi-image
              </v-icon>
            </template>
            <span>
              Toggle Map Images
            </span>
          </v-tooltip>
          <br>
          <v-tooltip
            v-if="hasGroundTruth"
            open-delay="50"
            bottom
          >
            <template #activator="{ props:subProps }">
              <v-icon
                v-bind="subProps"
                :color="drawGroundTruth ? 'rgb(37, 99, 235)' : ''"
                @click="drawGroundTruth = !drawGroundTruth"
              >
                {{ drawGroundTruth ? 'mdi-checkbox-marked' : 'mdi-checkbox-blank-outline' }}
              </v-icon>
            </template>
            <span>
              Toggle Map Images
            </span>
          </v-tooltip>
        </v-col>
        <v-col>
          <h3 class="mr-3">
            {{ siteEvaluationName }}:
          </h3>
          <h3
            v-if="hasGroundTruth"
            class="mr-3"
          >
            Ground Truth
          </h3>
        </v-col>
        <v-col>
          <div>
            <b class="mr-1">Date Range:</b>
            <span> {{ startDate ? startDate : 'null' }}
              <v-icon
                v-if="editMode"
                class="ma-0"
                @click="setEditingMode('StartDate')"
              >
                mdi-pencil
              </v-icon>

            </span>
            <span class="mx-1"> to</span>
            <span> {{ endDate ? endDate : 'null' }}
              <v-icon
                v-if="editMode"
                class="ma-0"
                @click="setEditingMode('EndDate')"
              >
                mdi-pencil
              </v-icon>

            </span>
          </div>
          <div v-if="groundTruth && hasGroundTruth">
            <b class="mr-1">Date Range:</b>
            <span> {{ new Date(groundTruth.timerange.min * 1000).toISOString().split('T')[0] }}
              <v-icon
                class="ma-0"
                color="white"
              />
            </span>
            <span class="mx-1"> to</span>
            <span> {{ new Date(groundTruth.timerange.max * 1000).toISOString().split('T')[0] }}</span>
          </div>
        </v-col>
        <v-col>
          <div class="ml-5">
            <b>Label:</b>
            <v-chip
              size="small"
              :color="getColorFromLabel(siteEvaluationLabel)"
              class="ml-2"
            >
              {{ siteEvaluationLabel }}
            </v-chip>
            <v-icon
              v-if="editMode"
              @click="setEditingMode('SiteEvaluationLabel')"
            >
              mdi-pencil
            </v-icon>
          </div>
          <div
            v-if="hasGroundTruth && groundTruth"
            class="ml-5"
          >
            <b>Label:</b>
            <v-chip
              size="small"
              :color="getColorFromLabel(groundTruth.label)"
              class="ml-2"
            >
              {{ groundTruth.label }}
            </v-chip>
          </div>
        </v-col>
        <v-col>
          <div class="notesPreview">
            <b>Notes:</b>
            <v-icon
              v-if="editMode"
              @click="setEditingMode('SiteEvaluationNotes')"
            >
              mdi-pencil
            </v-icon>
            <v-tooltip
              :text="siteEvaluationNotes"
              location="bottom center"
            >
              <template #activator="{ props:subProps }">
                <span v-bind="subProps"> {{ siteEvaluationNotes }}</span>
              </template>
            </v-tooltip>
          </div>
        </v-col>
        <v-spacer />
        <v-col v-if="!siteEvaluationUpdated">
          <v-btn
            v-if="!editingPolygon"
            size="small"
            :disabled="editingPolygon"
            @click="startEditingPolygon()"
          >
            Edit Polygon
          </v-btn>
          <span
            v-if="editingPolygon"
          >
            <h3 style="display:inline">Polygon:</h3>
            <v-btn
              v-if="selectedPoints"
              size="small"
              color="error"
              class="mx-2"
              @click="deleteSelectedPoints()"
            >
              <v-icon>mdi-delete</v-icon>
              points
            </v-btn>

            <v-btn
              size="small"
              color="error"
              class="mx-2"
              @click="cancelEditingPolygon()"
            >
              Cancel
            </v-btn>
            <v-btn
              size="small"
              color="success"
              class="mx-2"
              @click="saveEditingPolygon()"
            >
              Save
            </v-btn>
          </span>
        </v-col>
        <v-col v-if="!editingPolygon">
          <v-btn
            v-if="siteEvaluationUpdated"
            size="small"
            color="success"
            @click="saveSiteEvaluationChanges"
          >
            Save Changes
          </v-btn>
          <v-btn
            v-if="siteStatus !== 'APPROVED'"
            size="small"
            class="mx-1"
            color="success"
            @click="setSiteModelStatus('APPROVED')"
          >
            Approve
          </v-btn>
          <v-btn
            v-if="siteStatus === 'APPROVED'"
            size="small"
            class="mx-1"
            color="warning"
            @click="setSiteModelStatus('PROPOSAL')"
          >
            Un-Approve
          </v-btn>
          <v-btn
            v-if="siteStatus !== 'REJECTED'"
            size="small"
            class="mx-1"
            color="error"
            @click="setSiteModelStatus('REJECTED')"
          >
            Reject
          </v-btn>
          <v-btn
            v-if="siteStatus === 'REJECTED'"
            size="small"
            class="mx-1"
            color="warning"
            @click="setSiteModelStatus('PROPOSAL')"
          >
            Un-Reject
          </v-btn>
        </v-col>
      </v-row>
    </v-card-title>
    <v-row
      dense
      class="my-1"
    >
      <v-icon @click="filterSettings = !filterSettings">
        mdi-filter
      </v-icon>
      <div>
        {{ filteredImages.length }} of {{ combinedImages.length }} images
      </div>
      <v-tooltip
        open-delay="50"
        bottom
      >
        <template #activator="{ props:subProps }">
          <v-icon
            v-bind="subProps"
            :color="showSitePoly ? 'blue' : ''"
            class="mx-2"
            @click="showSitePoly = !showSitePoly"
          >
            mdi-vector-polygon
          </v-icon>
        </template>
        <span>
          Toggle between Site Polygon and Observation Polygon
        </span>
      </v-tooltip>
      <v-tooltip
      v-if="filteredImages.length && filteredImages[currentImage]"
        open-delay="50"
        bottom
      >
        <template #activator="{ props:subProps }">
          <v-icon
            v-bind="subProps"
            :color="filteredImages[currentImage].image.image_embedding ? 'blue' : ''"
            :disabled="filteredImages[currentImage].image.image_embedding"
            class="mx-2"
            @click="processImageEmbeddingButton(filteredImages[currentImage].image)"
          >
            {{filteredImages[currentImage].image.image_embedding ? 'mdi-image-plus-outline' : 'mdi-image-refresh-outline'}}
          </v-icon>
        </template>
        <span>
          Has or Generate Image embedding
        </span>
      </v-tooltip>
      <v-spacer />
      <v-tooltip
        open-delay="50"
        bottom
      >
        <template #activator="{ props:subProps }">
          <v-icon
            v-bind="subProps"
            :color="rescaleImage ? 'blue' : ''"
            @click="rescaleImage = !rescaleImage"
          >
            mdi-resize
          </v-icon>
        </template>
        <span>
          Rescale Images
        </span>
      </v-tooltip>
      <div v-if="downloadingGif">
        <span> {{ downloadingGifState === 'drawing' ? 'Drawing' : 'GIF Creation' }}</span>
        <v-progress-linear
          v-model="downloadingGifProgress"
          width="50"
        />
      </div>
      <v-tooltip
        open-delay="50"
        bottom
      >
        <template #activator="{ props:subProps }">
          <v-icon
            v-if="!downloadingGif"
            v-bind="subProps"
            @click="drawForDownload()"
          >
            mdi-download-box-outline
          </v-icon>
          <v-icon v-else>
            mdi-spin mdi-sync
          </v-icon>
          <v-icon @click="GifSettingsDialog = true">
            mdi-cog
          </v-icon>
        </template>
        <span>
          Download Images to GIF.
        </span>
      </v-tooltip>
    </v-row>
    <div v-if="filterSettings">
      <v-row dense>
        <v-select
          v-model="siteObsFilter"
          label="Site Observations"
          :items="baseObs"
          multiple
          closable-chips
          chips
          class="mx-2"
        />
        <v-select
          v-model="imageSourcesFilter"
          label="Sources"
          :items="baseImageSources"
          multiple
          closable-chips
          chips
          class="mx-2"
        />
      </v-row>
      <v-row
        dense
        justify="center"
        align="center"
      >
        <v-col cols="3">
          <span>Cloud Cover:</span>
        </v-col>
        <v-col cols="7">
          <v-slider
            v-model.number="cloudFilter"
            min="0"
            max="100"
            step="1"
            color="primary"
            density="compact"
            class="mt-5"
          />
        </v-col>
        <v-col>
          <span class="pl-2">
            {{ cloudFilter }}%
          </span>
        </v-col>
      </v-row>
      <v-row
        dense
        justify="center"
        align="center"
      >
        <v-col cols="3">
          <span>NoData:</span>
        </v-col>
        <v-col cols="7">
          <v-slider
            v-model.number="percentBlackFilter"
            min="0"
            max="100"
            step="1"
            color="primary"
            density="compact"
            class="mt-5"
          />
        </v-col>
        <v-col>
          <span class="pl-2">
            {{ percentBlackFilter }}%
          </span>
        </v-col>
      </v-row>
    </div>
    <v-row>
      <v-spacer />
      <canvas
        ref="canvasRef"
      />
      <v-spacer />
    </v-row>
    <v-row
      v-if="filteredImages.length && filteredImages[currentImage]"
      dense
      class="mt-2"
    >
      <v-col cols="3">
        <div v-if="filteredImages[currentImage].image.observation_id !== null">
          <div>Site Observation</div>
        </div>
        <div v-else>
          <div>Non Site Observation</div>
        </div>
        <v-tooltip
          open-delay="50"
          bottom
        >
          <template #activator="{ props:subProps }">
            <v-icon
              v-bind="subProps"
              @click="copyURL(filteredImages[currentImage].image.aws_location)"
            >
              mdi-information
            </v-icon>
          </template>
          <span>
            Click to Copy: {{ filteredImages[currentImage].image.aws_location }}
          </span>
        </v-tooltip>
      </v-col>
      <v-spacer />
      <v-col class="text-center">
        <div>
          <div>{{ filteredImages[currentImage].image.source }}</div>

          <div>
            {{ currentDate }}
          </div>
          <div>
            <v-chip
              size="small"
              :color="getColorFromLabel(currentLabel)"
            >
              {{ currentLabel }}
            </v-chip>
            <v-icon
              v-if="editMode && filteredImages[currentImage].image.observation_id !== null"
              size="small"
              @click="setEditingMode('SiteObservationLabel')"
            >
              mdi-pencil
            </v-icon>
          </div>
        </div>
      </v-col>
      <v-spacer />
      <v-col
        class="text-right"
        cols="3"
      >
        <div>
          <div>NODATA: {{ filteredImages[currentImage].image.percent_black.toFixed(0) }}%</div>
          <div>Cloud: {{ filteredImages[currentImage].image.cloudcover.toFixed(0) }}%</div>
        </div>
      </v-col>
    </v-row>
    <v-slider
      v-if="filteredImages.length && filteredImages[currentImage]"
      v-model="currentImage"
      min="0"
      :max="filteredImages.length - 1"
      step="1"
    />
    <v-row v-if="filteredImages.length">
      <v-spacer />
      <v-icon
        class="mx-2 hover"
        @click="currentImage = 0"
      >
        mdi-skip-backward
      </v-icon>
      <v-icon
        class="mx-2 hover"
        @click="adjustImage(-1)"
      >
        mdi-skip-previous
      </v-icon>
      <v-icon
        class="mx-2 hover"
        @click="togglePlayback()"
      >
        {{ playbackEnabled ? 'mdi-pause' : 'mdi-play' }}
      </v-icon>
      <v-icon
        class="mx-2 hover"
        @click="adjustImage(1)"
      >
        mdi-skip-next
      </v-icon>
      <v-icon
        class="mx-2 hover"
        @click="currentImage = filteredImages.length -1"
      >
        mdi-skip-forward
      </v-icon>
      <v-spacer />
    </v-row>
    <v-progress-linear
      v-if="loading"
      indeterminate
      color="primary"
      height="15"
      class="mt-4"
    />
    <div v-if="false">
      <v-icon
        v-if="editMode && filteredImages[currentImage] && filteredImages[currentImage].image.observation_id !== null"
        @click="setEditingMode('SiteObservationNotes')"
      >
        mdi-pencil
      </v-icon>Notes:
      <p>
        {{ notes }}
      </p>
    </div>
    <v-dialog
      v-model="GifSettingsDialog"
      width="400"
    >
      <v-card>
        <v-card-title> GIF Downloading Settings</v-card-title>
        <v-card-text>
          <v-row dense>
            <v-text-field
              v-model.number="downloadingGifFPS"
              type="number"
              label="FPS"
              step="0.1"
              :rules="[v => v > 0 || 'Value must be greater than 0']"
            />
          </v-row>
          <v-row dense>
            <v-slider
              v-model="rescalingBBox"
              min="1"
              max="5"
              step="0.1"
              :label="`Zoom out (${rescalingBBox.toFixed(2)})X`"
            />
          </v-row>

          <v-row dense>
            <v-slider
              v-model="downloadingGifQuality"
              min="0"
              max="1"
              step="0.1"
              :label="`Quality (${downloadingGifQuality.toFixed(2)})`"
            />
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-row>
            <v-spacer />
            <v-btn
              color="success"
              @click="GifSettingsDialog = false"
            >
              OK
            </v-btn>
          </v-row>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <v-dialog
      v-model="editDialog"
      width="400"
    >
      <v-card v-if="currentEditMode === 'SiteEvaluationLabel'">
        <v-card-title>Edit Site Model Label</v-card-title>
        <v-card-text>
          <v-select
            v-model="siteEvaluationLabel"
            :items="siteEvaluationList"
            label="Label"
            class="mx-2"
          />
        </v-card-text>
        <v-card-actions>
          <v-row dense>
            <v-btn
              color="error"
              class="mx-3"
              @click="editDialog = false"
            >
              Cancel
            </v-btn>
            <v-btn
              color="success"
              class="mx-3"
              @click="editDialog = false; siteEvaluationUpdated = true"
            >
              Save
            </v-btn>
          </v-row>
        </v-card-actions>
      </v-card>
      <v-card v-if="currentEditMode === 'StartDate'">
        <v-card>
          <v-card-title>Observation Time</v-card-title>
          <v-card-text>
            <v-row
              dense
              justify="center"
            >
              <v-btn
                color="error"
                class="mb-2 mx-1"
                size="small"
                @click="updateTime(null, 'StartDate'); editDialog=false"
              >
                Set Time to Null
              </v-btn>
              <v-btn
                color="primary"
                class="mb-2 mx-1"
                size="small"
                @click="updateTime(currentDate, 'StartDate'); editDialog=false"
              >
                Current: {{ currentDate }}
              </v-btn>
            </v-row>
            <v-date-picker
              v-if="startDateTemp !== null"
              :model-value="[startDateTemp ? startDateTemp : currentTimestamp]"
              @update:model-value="updateTime($event, 'StartDate')"
              @click:cancel="editDialog = false"
              @click:save="editDialog = false"
            />
          </v-card-text>
        </v-card>
      </v-card>
      <v-card v-if="currentEditMode === 'EndDate'">
        <v-card>
          <v-card-title>Observation Time</v-card-title>
          <v-card-text>
            <v-row
              dense
              justify="center"
            >
              <v-btn
                color="error"
                class="mb-2 mx-1"
                size="small"
                @click="updateTime(null, 'EndDate'); editDialog=false"
              >
                Set Time to Null
              </v-btn>
              <v-btn
                color="primary"
                class="mb-2 mx-1"
                size="small"
                @click="updateTime(currentDate, 'EndDate'); editDialog=false"
              >
                Current: {{ currentDate }}
              </v-btn>
            </v-row>
            <v-date-picker
              v-if="endDateTemp !== null"
              :model-value="[endDateTemp ? endDateTemp : currentTimestamp]"
              @update:model-value="updateTime($event, 'EndDate')"
              @click:cancel="editDialog = false"
              @click:save="editDialog = false"
            />
          </v-card-text>
        </v-card>
      </v-card>
      <v-card v-if="currentEditMode === 'SiteEvaluationNotes'">
        <v-card-title>Edit Site Model Notes</v-card-title>
        <v-card-text>
          <v-textarea
            v-model="siteEvaluationNotes"
            label="Notes"
          />
        </v-card-text>
        <v-card-actions>
          <v-row dense>
            <v-spacer />
            <v-btn
              color="error"
              class="mx-3"
              @click="editDialog = false"
            >
              Cancel
            </v-btn>
            <v-btn
              color="success"
              class="mx-3"
              @click="editDialog = false; siteEvaluationUpdated = true"
            >
              Save
            </v-btn>
          </v-row>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<style scoped>
.hover:hover {
  cursor: pointer;
  color:blue
}

.review {
  min-height: 50vh;
  max-height: 60vh;
  overflow-y: auto;
}
.fullscreen {
  min-height: 100vh;
  max-height: 100vh;
  overflow-y: auto;
}

.edit-title {
  font-size: 0.75em;
}
.top-bar {
  font-size:12px;
  font-weight: bold;
}

.notesPreview {
  min-width: 150px;
  max-width: 150px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
