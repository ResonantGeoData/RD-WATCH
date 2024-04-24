<script setup lang="ts">
import {
  Ref,
  computed,
  onUnmounted,
  ref,
  watch,
  withDefaults,
} from "vue";
import { ApiService } from "../../client";
import { EvaluationImage, EvaluationImageResults } from "../../types";
import {
  ObsDetails,
  SiteObservationImage,
  loadAndToggleSatelliteImages,
  state,
} from "../../store";
import type { PixelPoly } from "./imageUtils";
import { drawData, processImagePoly } from "./imageUtils";
import maplibregl from "maplibre-gl";
import ImageGifCreation from "./ImageGifCreation.vue";
import ImageFilter from "./ImageFilter.vue";
import ImageEditorDetails from "./ImageEditorDetails.vue";
import ImageSliderDetails from "./ImageSliderDetails.vue";
import ImageSAM from "./ImageSAM.vue";
interface Props {
  siteEvalId: string;
  dialog?: boolean;
  editable?: boolean;
  siteEvaluationName?: string | null;
  dateRange?: number[] | null;
  obsDetails?: ObsDetails;
  fullscreen?: boolean;
}

type EditModes =
  | "SiteEvaluationLabel"
  | "StartDate"
  | "EndDate"
  | "SiteObservationLabel"
  | "SiteEvaluationNotes"
  | "SiteObservationNotes";

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
  (
    e: "eval-save",
    {
      label,
      startDate,
      endDate,
      notes,
    }: {
      label: string;
      startDate: string | null;
      endDate: string | null;
      notes: string;
    }
  ): void;
}>();

const loading = ref(false);
const currentImage = ref(0);
const editMode = ref(props.editable);

const editDialog = ref(false);
const currentEditMode: Ref<null | EditModes> = ref(null);
const siteEvaluationLabel = ref("unknown");
const startDate: Ref<string | null> = ref(
  props.dateRange && props.dateRange[0]
    ? new Date(props.dateRange[0] * 1000).toISOString().split("T")[0]
    : null
);
const endDate: Ref<string | null> = ref(
  props.dateRange && props.dateRange[1]
    ? new Date(props.dateRange[1] * 1000).toISOString().split("T")[0]
    : null
);
const siteEvaluationNotes = ref("");
const siteStatus: Ref<string | null> = ref(null);
const imageRef: Ref<HTMLImageElement | null> = ref(null);
const canvasRef: Ref<HTMLCanvasElement | null> = ref(null);
const combinedImages: Ref<
  { image: EvaluationImage; poly: PixelPoly; groundTruthPoly?: PixelPoly }[]
> = ref([]);
const filteredImages: Ref<
  { image: EvaluationImage; poly: PixelPoly; groundTruthPoly?: PixelPoly }[]
> = ref([]);
// Ease of display refs
const currentLabel = ref("unknown");
const currentDate = ref("");
// Ground Truth Values
const hasGroundTruth = ref(false);
const groundTruth: Ref<EvaluationImageResults["groundTruth"] | null> =
  ref(null);
const drawGroundTruth = ref(false);
const rescaleImage = ref(false);
const rescalingBBox = ref(1);
const editingPolygon = ref(false);
const SAMViewer: Ref<number | null> = ref(null);


const evaluationGeoJSON: Ref<GeoJSON.Polygon | null> = ref(null); // holds the site geoJSON so it can be edited

const showSitePoly = ref(props.editable); // Swap between showing the site polygon and the site observation polygon

const currentTimestamp = computed(() => {
  if (filteredImages.value[currentImage.value]) {
    const time = filteredImages.value[currentImage.value].image.timestamp;
    return new Date(time * 1000).toISOString().split("T")[0];
  }
  return new Date().toISOString().split("T")[0];
});

watch(currentTimestamp, () => {
  currentDate.value = currentTimestamp.value;
});

const getImageData = async () => {
  combinedImages.value = [];
  currentImage.value = 0;
  const data = await ApiService.getEvaluationImages(props.siteEvalId);
  const images = data.images.results.sort((a, b) => a.timestamp - b.timestamp);
  const polygons = data.geoJSON;
  evaluationGeoJSON.value = data.evaluationGeoJSON;
  polygons.sort((a, b) => a.timestamp - b.timestamp);
  siteEvaluationNotes.value = data.notes || "";
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
    const result = processImagePoly(
      image,
      polygons,
      data.evaluationGeoJSON,
      data.evaluationBBox,
      data.label,
      hasGroundTruth.value,
      groundTruth.value,
      showSitePoly.value
    );
    combinedImages.value.push(result);
  });
};
const background: Ref<
  (HTMLCanvasElement & { ctx?: CanvasRenderingContext2D | null }) | undefined
> = ref();

watch(showSitePoly, () => {
  getImageData();
});

const load = async (newValue?: string, oldValue?: string) => {
  currentImage.value = 0;
  const index = state.enabledSiteObservations.findIndex(
    (item) => item.id === oldValue
  );

  startDate.value =
    props.dateRange && props.dateRange[0]
      ? new Date(props.dateRange[0] * 1000).toISOString().split("T")[0]
      : null;
  endDate.value =
    props.dateRange && props.dateRange[1]
      ? new Date(props.dateRange[1] * 1000).toISOString().split("T")[0]
      : null;

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
  if (
    currentImage.value < filteredImages.value.length &&
    canvasRef.value !== null
  ) {
    drawData(
      canvasRef.value,
      filteredImages.value[currentImage.value].image,
      filteredImages.value[currentImage.value].poly,
      filteredImages.value[currentImage.value].groundTruthPoly,
      -1,
      -1,
      background.value,
      drawGroundTruth.value,
      rescaleImage.value,
      props.fullscreen,
      rescalingBBox.value
    );
  }
  loading.value = false;
};

watch(
  () => props.siteEvalId,
  () => {
    state.enabledSiteObservations = []; // toggle off all other satellite images
    load();
  }
);
load();

watch(filteredImages, () => {
  if (currentImage.value > filteredImages.value.length) {
    currentImage.value = 0;
  }
});


watch(
  [
    currentImage,
    imageRef,
    filteredImages,
    drawGroundTruth,
    rescaleImage,
    rescalingBBox,
  ],
  () => {
    if (
      currentImage.value < filteredImages.value.length &&
      imageRef.value !== null
    ) {
      imageRef.value.src = filteredImages.value[currentImage.value].image.image;
    }
    if (filteredImages.value.length) {
      currentLabel.value = filteredImages.value[currentImage.value].poly.label;
      if (
        currentImage.value < filteredImages.value.length &&
        canvasRef.value !== null
      ) {
        drawData(
          canvasRef.value,
          filteredImages.value[currentImage.value].image,
          filteredImages.value[currentImage.value].poly,
          filteredImages.value[currentImage.value].groundTruthPoly,
          -1,
          -1,
          background.value,
          drawGroundTruth.value,
          rescaleImage.value,
          props.fullscreen,
          rescalingBBox.value
        );
      }
      if (
        props.dialog === false &&
        !props.fullscreen &&
        filteredImages.value[currentImage.value]
      ) {
        state.timestamp =
          filteredImages.value[currentImage.value].image.timestamp;
      }
    }
  }
);

const mapImagesOn = computed(
  () =>
    state.enabledSiteObservations.findIndex(
      (item) => item.id === props.siteEvalId
    ) !== -1
);


onUnmounted(() => {
  if (
    props.editable &&
    state.enabledSiteObservations.find((item) => item.id === props.siteEvalId)
  ) {
    loadAndToggleSatelliteImages(props.siteEvalId);
  }
  if (editingPolygon.value) {
    state.filters.editingPolygonSiteId = null;
    editingPolygon.value = false;
  }
  Object.keys(embeddingCheckInterval).forEach((key) => {
    clearInterval(embeddingCheckInterval.value[key]);
  });
});

//SAM Integration
const embeddingCheckInterval: Ref<Record<string, NodeJS.Timeout>> = ref({});

const checkSAMStatus = async (id: number, uuid: string) => {
  const result = await ApiService.getSiteImageEmbeddingStatus(id, uuid);
  if (result.state === "SUCCESS" || result.status === "SUCCESS") {
    // We update the button status to open in a new tab instead
    const index = combinedImages.value.findIndex(
      (item) => item.image.id === id
    );
    if (index !== -1) {
      const base = combinedImages.value[index];
      // Get the image Embedding so we can replace it in the list
      const newData = await ApiService.getSiteImage(id);
      base.image.image_embedding = newData.image_embedding;
      combinedImages.value.splice(index, 1, base);
      if (embeddingCheckInterval.value[id]) {
        clearInterval(embeddingCheckInterval.value[id]);
        delete embeddingCheckInterval.value[id];
      }
    }
  }
};

const generateImageEmbedding = async (
  image: SiteObservationImage | EvaluationImage
) => {
  const result = await ApiService.postSiteImageEmbedding(image.id);
  embeddingCheckInterval.value[image.id] = setInterval(
    () => checkSAMStatus(image.id, result),
    1000
  );
};

const openSAMView = (id: number) => {
  SAMViewer.value = id;
  // const name = `#${ApiService.getApiPrefix()
  //   .replace("api/", "")
  //   .replace("/api", "")}/SAM/${id}`;
  // window.open(name, "_blank");
};

const processImageEmbeddingButton = (
  image: SiteObservationImage | EvaluationImage
) => {
  if (image && !image.image_embedding) {
    generateImageEmbedding(image);
  } else {
    openSAMView(image.id);
  }
};

// Clearing Storage
const clearStorage = async () => {
  maplibregl.clearStorage();
  // We need to update the source to get information
  // This reloads the source vector-tile to color it properly after data has been changed.
  state.filters.randomKey = `randomKey=randomKey_${Math.random() * 1000}`;
  await getImageData();
};
</script>

<template>
  <v-card
    class="pa-4"
    :class="{ review: !dialog && !fullscreen, fullscreen: fullscreen }"
  >
    <v-row
      v-if="dialog || fullscreen"
      dense
      class="top-bar"
    >
      <v-col v-if="obsDetails">
        <span>{{ obsDetails.performer }} {{ obsDetails.title }} : V{{
          obsDetails.version
        }}</span>
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
          <span>
            {{
              new Date(groundTruth.timerange.min * 1000)
                .toISOString()
                .split("T")[0]
            }}
          </span>
          <span> to </span>
          <span>
            {{
              new Date(groundTruth.timerange.max * 1000)
                .toISOString()
                .split("T")[0]
            }}</span>
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
          style="max-width: 20px"
        >
          <v-tooltip
            open-delay="50"
            bottom
          >
            <template #activator="{ props }">
              <v-icon
                v-bind="props"
                :color="mapImagesOn ? 'rgb(37, 99, 235)' : ''"
                @click="loadAndToggleSatelliteImages(siteEvalId)"
              >
                mdi-image
              </v-icon>
            </template>
            <span> Toggle Map Images </span>
          </v-tooltip>
          <br>
          <v-tooltip
            v-if="hasGroundTruth"
            open-delay="50"
            bottom
          >
            <template #activator="{ props }">
              <v-icon
                v-bind="props"
                :color="drawGroundTruth ? 'rgb(37, 99, 235)' : ''"
                @click="drawGroundTruth = !drawGroundTruth"
              >
                {{
                  drawGroundTruth
                    ? "mdi-checkbox-marked"
                    : "mdi-checkbox-blank-outline"
                }}
              </v-icon>
            </template>
            <span> Toggle Map Images </span>
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
        <image-editor-details
          v-if="combinedImages.length"
          :site-eval-id="siteEvalId"
          :editable="editable"
          :date-range="dateRange"
          :ground-truth="groundTruth"
          :has-ground-truth="hasGroundTruth"
          :evaluation-label="siteEvaluationLabel"
          :evaluation-notes="siteEvaluationNotes"
          :eval-current-date="currentDate"
          :status="siteStatus"
          :sam-viewer="SAMViewer"
          :eval-geo-j-s-o-n="evaluationGeoJSON"
          :current-timestamp="currentTimestamp"
          @clear-storage="clearStorage()"
          @update-list="$emit('update-list')"
        />
      </v-row>
    </v-card-title>
    <v-row
      v-if="SAMViewer === null"
      dense
      class="my-1"
    >
      <image-filter
        :combined-images="combinedImages"
        @image-filter="filteredImages = $event"
      />
      <v-tooltip
        open-delay="50"
        bottom
      >
        <template #activator="{ props }">
          <v-icon
            v-bind="props"
            :color="showSitePoly ? 'blue' : ''"
            class="mx-2"
            @click="showSitePoly = !showSitePoly"
          >
            mdi-vector-polygon
          </v-icon>
        </template>
        <span> Toggle between Site Polygon and Observation Polygon </span>
      </v-tooltip>
      <v-tooltip
        v-if="
          !loading && !ApiService.getApiPrefix().includes('scoring') && filteredImages.length &&
            filteredImages[currentImage] &&
            filteredImages[currentImage].image &&
            filteredImages[currentImage].image.source === 'WV'
        "
        open-delay="50"
        bottom
      >
        <template #activator="{ props }">
          <v-icon
            v-if="
              filteredImages[currentImage] && filteredImages[currentImage].image && !embeddingCheckInterval[filteredImages[currentImage].image.id]
            "
            v-bind="props"
            :color="
              filteredImages[currentImage].image.image_embedding ? 'blue' : ''
            "
            :disabled="filteredImages[currentImage].image.image_embedding"
            class="mx-2"
            @click="
              processImageEmbeddingButton(filteredImages[currentImage].image)
            "
          >
            {{
              filteredImages[currentImage].image.image_embedding
                ? "mdi-image-plus-outline"
                : "mdi-image-refresh-outline"
            }}
          </v-icon>
          <v-icon
            v-else
            v-bind="props"
            class="mx-2"
          >
            mdi-spin mdi-sync
          </v-icon>
        </template>
        <span> Has or Generate Image embedding </span>
      </v-tooltip>
      <v-spacer />
      <v-tooltip
        open-delay="50"
        bottom
      >
        <template #activator="{ props }">
          <v-icon
            v-bind="props"
            :color="rescaleImage ? 'blue' : ''"
            @click="rescaleImage = !rescaleImage"
          >
            mdi-resize
          </v-icon>
        </template>
        <span> Rescale Images </span>
      </v-tooltip>
      <image-gif-creation
        v-if="SAMViewer === null"
        :background="background"
        :filtered-images="filteredImages"
        :fullscreen="fullscreen"
        :rescale-image="rescaleImage"
        :site-evaluation-name="siteEvaluationName"
        :rescaling-b-box="rescalingBBox"
        :draw-ground-truth="drawGroundTruth"
        @rescale-b-box="rescalingBBox = $event"
      />
    </v-row>
    <v-row v-show="SAMViewer === null">
      <v-spacer />
      <canvas ref="canvasRef" />
      <v-spacer />
    </v-row>
    <v-row v-if="SAMViewer !== null">
      <ImageSAM
        :id="SAMViewer.toString()"
        :site-eval-id="siteEvalId"
        :image="filteredImages[currentImage].image"
        @cancel="SAMViewer = null"
      />
    </v-row>
    <image-slider-details
      v-if="SAMViewer === null"
      :filtered-images="filteredImages"
      :current-date="currentDate"
      :current-label="currentLabel"
      :edit-mode="editMode"
      :start-date="startDate"
      :end-date="endDate"
      :image-index="currentImage"
      @current-image="currentImage = $event"
      @edit-dialog="editDialog = true; currentEditMode = $event"
    />
    <v-progress-linear
      v-if="loading"
      indeterminate
      color="primary"
      height="15"
      class="mt-4"
    />
  </v-card>
</template>

<style scoped>
.hover:hover {
  cursor: pointer;
  color: blue;
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
  font-size: 12px;
  font-weight: bold;
}
</style>
