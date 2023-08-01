<script setup lang="ts">
import { Ref, computed, ref, watch, withDefaults } from "vue";
import { ApiService } from "../../client";
import {EvaluationGeoJSON, EvaluationImage } from "../../types";
import { getColorFromLabel, styles } from '../../mapstyle/annotationStyles';
import { state } from '../../store'
import { VDatePicker } from 'vuetify/labs/VDatePicker'

interface Props {
  siteEvalId: number;
  dialog?: boolean;
  editable?: boolean;
  siteEvaluationName?: string | null;
  dateRange?: number[] | null
}

type EditModes = 'SiteEvaluationLabel' | 'StartDate' | 'EndDate' | 'SiteObservationLabel' | 'SiteEvaluationNotes' | 'SiteObservationNotes'

const props = withDefaults(defineProps<Props>(), {
  dialog: false,
  editable: false,
  siteEvaluationName: null,
  dateRange: null,
});

interface PixelPoly {
    coords: {x:number; y:number}[][];
    label: string;
}

const emit = defineEmits<{
  (e: "close"): void;
}>();

const loading = ref(false);
const currentImage = ref(0);
const editMode = ref(props.editable);

const editDialog = ref(false);
const currentEditMode: Ref<null | EditModes> = ref(null);
const notes = ref('');
const siteEvaluationLabel = ref('');
const startDate: Ref<string|null> = ref(props.dateRange && props.dateRange[0] ? new Date(props.dateRange[0] * 1000).toISOString().split('T')[0] : null);
const endDate: Ref<string|null> = ref(props.dateRange && props.dateRange[1] ? new Date(props.dateRange[1] * 1000).toISOString().split('T')[0] : null);
const siteEvaluationNotes = ref('');
const siteEvaluationUpdated = ref(false)
const imageRef: Ref<HTMLImageElement | null> = ref(null);
const canvasRef: Ref<HTMLCanvasElement | null> = ref(null);
const baseImageSources = ref(['S2', 'WV'])
const baseObs = ref(['observations', 'non-observations'])
const filterSettings = ref(false);
const combinedImages: Ref<{image: EvaluationImage; poly: PixelPoly}[]> = ref([]);
const imageSourcesFilter: Ref<EvaluationImage['source'][]> = ref(['S2', 'WV', 'L8']);
const percentBlackFilter: Ref<number> = ref(100);
const cloudFilter: Ref<number> = ref(100);
const siteObsFilter: Ref<('observations' | 'non-observations')[]> = ref(['observations', 'non-observations'])
const currentLabel = ref('')
const currentDate = ref('');
const labelList = computed(() => styles.filter((item) => item.labelType === 'observation').map((item) => item.label));
const siteEvaluationList = computed(() => styles.filter((item) => item.labelType === 'sites').map((item) => item.label));
const getClosestPoly = (timestamp: number, polys: EvaluationGeoJSON[], evaluationPoly: EvaluationGeoJSON['geoJSON'], siteEvalLabel: string) => {
  if (polys.length === 0) {
    return {geoJSON: evaluationPoly, label:siteEvalLabel};
  }
    let found = polys[0];
    for (let i = 0; i < polys.length; i += 1) {
        if (timestamp > polys[i].timestamp) {
            if (i > 0) {
                found = polys[i -1]
            }
        }
    }
    return found;
}

const filteredImages = computed(() => {
  return combinedImages.value.filter((item) => {
    let add = true;
    if (!imageSourcesFilter.value.includes(item.image.source)) {
      add = false;
    }
    if (siteObsFilter.value.includes('observations') && siteObsFilter.value.length ===1 && item.image.siteobs_id === null) {
      add = false;      
    }
    if (siteObsFilter.value.includes('non-observations') && siteObsFilter.value.length ===1 && item.image.siteobs_id !== null) {
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
    if (combinedImages.value[currentImage.value]) {
    const time = combinedImages.value[currentImage.value].image.timestamp;
    return new Date(time * 1000).toISOString().split('T')[0]
    }
    return new Date().toISOString().split('T')[0]
})

watch(currentTimestamp, () => {
  currentDate.value = currentTimestamp.value;
});

function createCanvas(width: number, height: number){
    const myOffScreenCanvas: HTMLCanvasElement & { ctx?: CanvasRenderingContext2D | null } = document.createElement("canvas");
    myOffScreenCanvas.width = width;
    myOffScreenCanvas.height = height;
    // attach the context to the canvas for easy access and to reduce complexity.
    myOffScreenCanvas.ctx = myOffScreenCanvas.getContext("2d"); 
    return myOffScreenCanvas;
 }


const getImageData = async () => {
    combinedImages.value = [];
    currentImage.value = 0;
    const data =  await ApiService.getEvaluationImages(props.siteEvalId);
    const images = data.images.results.sort((a, b) => a.timestamp - b.timestamp);
    const polygons = data.geoJSON;
    siteEvaluationNotes.value = data.notes || '';
    siteEvaluationLabel.value = data.label;
    if (imageRef.value !== null) {
        imageRef.value.src = images[currentImage.value].image;
    }
    // Lets process the polygons to get them in pixel space.
    // For each polygon we need to convert it to the proper image sizing result.
    images.forEach((image) => {
        const closestPoly = getClosestPoly(image.timestamp, polygons, data.evaluationGeoJSON, data.label);
        // Now we convert the coordinates to 
        const bboxWidth = image.bbox.xmax - image.bbox.xmin;
        const bboxHeight = image.bbox.ymax - image.bbox.ymin;
        const imageWidth = image.image_dimensions[0];
        const imageHeight = image.image_dimensions[1];
        const imageNormalizePoly: {x: number, y: number}[][] = []
        closestPoly.geoJSON.coordinates.forEach((ring) => {
          imageNormalizePoly.push([]);
            ring.forEach((coord) => {
                const normalize_x = (coord[0] - image.bbox.xmin) / bboxWidth;
            const normalize_y = (coord[1] - image.bbox.ymin) / bboxHeight;
            const image_x = normalize_x * imageWidth;
            const image_y = normalize_y * imageHeight;
            imageNormalizePoly[imageNormalizePoly.length -1].push({x: image_x, y: image_y});

            })
        })
        combinedImages.value.push({ image: image, poly: {coords: imageNormalizePoly, label: closestPoly.label} });
    })
}
let background: HTMLCanvasElement & { ctx?: CanvasRenderingContext2D | null };
const drawData = (canvas: HTMLCanvasElement, image: EvaluationImage, poly:PixelPoly) => {
    const context = canvas.getContext('2d');
    const imageObj = new Image();
    imageObj.src = image.image;
    if (!background) {
        background = createCanvas(image.image_dimensions[0], image.image_dimensions[1]);
    }
    background.width = image.image_dimensions[0];
    background.height = image.image_dimensions[1];
    const { coords } = poly;
    const renderFunction = () => {
        if (context) {
        canvas.width = image.image_dimensions[0];
        canvas.height = image.image_dimensions[1];
        // draw the offscreen canvas
        context.drawImage(background, 0, 0);
        coords.forEach((ring) => {
          context.moveTo(ring[0].x, image.image_dimensions[1] - ring[0].y);
          ring.forEach(({x, y}) => {
            if (context){
                context.lineTo(x, image.image_dimensions[1] - y);
            }
          });
          context.lineWidth = 1;
          context.strokeStyle = getColorFromLabel(poly.label);
          currentLabel.value = siteEvaluationLabel.value == poly.label ? '' : poly.label;
          context.stroke();
        });
        // Now scale the canvas to the proper size
        const ratio = image.image_dimensions[1] / image.image_dimensions[0];
        const maxHeight = document.documentElement.clientHeight * 0.30;
        const maxWidth = document.documentElement.clientWidth - 550;
        let width = maxWidth
        let height = width * ratio;
        if (height > maxHeight) {
          height = maxHeight;
          width = height / ratio;
        }
        context.canvas.style.width = `${width}px`
        context.canvas.style.height = `${height}px`;
        }
    }

    imageObj.onload = () => {
        if (background.ctx) {
            background.width = image.image_dimensions[0];
            background.height = image.image_dimensions[1];
            background.ctx.drawImage(imageObj, 0, 0, image.image_dimensions[0], image.image_dimensions[1]);
            renderFunction();
        }
    }
    };

const load = async () => {
  loading.value = true;
  await getImageData();
  if (currentImage.value < filteredImages.value.length && canvasRef.value !== null) {
      drawData(canvasRef.value, filteredImages.value[currentImage.value].image, filteredImages.value[currentImage.value].poly)
  }
  loading.value = false;
}

watch(() => props.siteEvalId , load);
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


watch([currentImage, imageRef, filteredImages], () => {
    if (currentImage.value < filteredImages.value.length && imageRef.value !== null) {
        imageRef.value.src = filteredImages.value[currentImage.value].image.image;
    }
    if (currentImage.value < filteredImages.value.length && canvasRef.value !== null) {
        drawData(canvasRef.value, filteredImages.value[currentImage.value].image, filteredImages.value[currentImage.value].poly)
    }
    if (props.dialog === false && filteredImages.value[currentImage.value]) {
      state.timestamp = filteredImages.value[currentImage.value].image.timestamp;
    }

});

const updateTime = (time: any, date: 'StartDate' | 'EndDate') => {
  if (time === null) {
    if (date === 'StartDate') {
      startDate.value = null;
    } else if (date === 'EndDate') {
      endDate.value = null
    }
    editDialog.value = false;
  } else {
    if (date === 'StartDate') {
      startDate.value = new Date(time as string).toISOString().split('T')[0];
    } else if (date === 'EndDate') {
      endDate.value = new Date(time as string).toISOString().split('T')[0];
    }
  }
  siteEvaluationUpdated.value = true;
}

const setEditingMode = (mode: EditModes) => {
  if (['StartDate', 'EndDate'].includes(mode)){
    if (startDate.value === null) {
      startDate.value = new Date().toISOString().split('T')[0];
    }
    if (endDate.value === null) {
      endDate.value = new Date().toISOString().split('T')[0];
    }
  }
  editDialog.value = true;
  currentEditMode.value = mode;
}


const saveSiteEvaluationChanges = () => {
  ApiService.patchSiteEvaluation(props.siteEvalId, {
    label: siteEvaluationLabel.value,
    start_date: startDate.value,
    end_date: endDate.value,
    notes: siteEvaluationNotes.value ? siteEvaluationNotes.value : undefined,
  });
  siteEvaluationUpdated.value = false;
}

</script>

<template>
  <v-card
    class="pa-4"
    :class="{review: !dialog}"
  >
    <v-row
      v-if="dialog"
      dense
    >
      <v-spacer />
      <v-icon @click="emit('close')">
        mdi-close
      </v-icon>
    </v-row>
    <v-card-title v-if="!editable">
      Site Image Display
    </v-card-title>
    <v-card-title
      v-else
      class="edit-title"
    >
      <v-row dense>
        <h3 class="mr-3">
          {{ siteEvaluationName }}
        </h3>
        <div>
          <b class="mr-2">Date Range:</b>
          <span> {{ startDate ? startDate : 'null' }}
            <v-icon
              v-if="editMode"
              class="ml-2"
              @click="setEditingMode('StartDate')"
            >
              mdi-pencil
            </v-icon>

          </span>
          <span class="mx-2"> to</span>
          <span> {{ endDate ? endDate : 'null' }}
            <v-icon
              v-if="editMode"
              class="ml-2"
              @click="setEditingMode('EndDate')"
            >
              mdi-pencil
            </v-icon>

          </span>
        </div>
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
        <div class="ml-3">
          <b>Notes:</b>
          <span> {{ siteEvaluationNotes }}</span>
          <v-icon
            v-if="editMode"
            @click="setEditingMode('SiteEvaluationNotes')"
          >
            mdi-pencil
          </v-icon>
        </div>
        <v-spacer />
        <v-btn
          v-if="siteEvaluationUpdated"
          size="small"
          color="success"
          @click="saveSiteEvaluationChanges"
        >
          Save Changes
        </v-btn>
      </v-row>
    </v-card-title>
    <v-row
      dense
      class="my-1"
    >
      <v-btn
        v-if="editable && false"
        :color="editMode ? 'success' : ''"
        class="mx-3"
        size="x-small"
        @click="editMode = !editMode"
      >
        Edit Mode
        <v-icon
          class="mx-3"
          @click="editMode = !editMode"
        >
          mdi-pencil
        </v-icon>
      </v-btn>
      <v-icon @click="filterSettings = !filterSettings">
        mdi-filter
      </v-icon>
      <div>
        Displaying {{ filteredImages.length }} of {{ combinedImages.length }} images
      </div>
      <v-spacer />
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
        <div v-if="filteredImages[currentImage].image.siteobs_id !== null">
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
              v-if="editMode && filteredImages[currentImage].image.siteobs_id !== null"
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
    <v-progress-linear
      v-if="loading"
      indeterminate
      color="primary"
      height="15"
      class="mt-4"
    />
    <div>
      <v-icon
        v-if="false && editMode && filteredImages[currentImage] && filteredImages[currentImage].image.siteobs_id !== null"
        @click="setEditingMode('SiteObservationNotes')"
      >
        mdi-pencil
      </v-icon>Notes:
      <p>
        {{ notes }}
      </p>
    </div>
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
              v-if="startDate !== null"
              :model-value="[startDate ? startDate : new Date()]"
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
              v-if="endDate !== null"
              :model-value="[endDate ? endDate : new Date()]"
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
          <v-text-field
            v-model="siteEvaluationNotes"
            label="Notes"
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
    </v-dialog>
  </v-card>
</template>

<style scoped>
.review {
  min-height: 50vh;
  max-height: 60vh;
  overflow-y: auto;
}

.edit-title {
  font-size: 0.75em;
}
</style>
