<script setup lang="ts">
import { Ref, computed, ref, watch, } from "vue";
import { ApiService } from "../../client";
import {EvaluationGeoJSON, EvaluationImage } from "../../types";
import { getColorFromLabel } from '../../mapstyle/annotationStyles';
const props = defineProps<{
  siteEvalId: number;
}>();

interface PixelPoly {
    coords: {x:number; y:number}[];
    label: string;
}


const currentImage = ref(0);
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
const displayImage = ref(false);
const getClosestPoly = (timestamp: number, polys: EvaluationGeoJSON[]) => {
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
    const time = combinedImages.value[currentImage.value].image.timestamp;
    return new Date(time * 1000).toLocaleDateString()
})

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
    const polygons = data.geoJSON.results;
    if (imageRef.value !== null) {
        imageRef.value.src = images[currentImage.value].image;
    }
    // Lets process the polygons to get them in pixel space.
    // For each polygon we need to convert it to the proper image sizing result.
    images.forEach((image) => {
        const closestPoly = getClosestPoly(image.timestamp, polygons);
        // Now we convert the coordinates to 
        const bboxWidth = image.bbox.xmax - image.bbox.xmin;
        const bboxHeight = image.bbox.ymax - image.bbox.ymin;
        const imageWidth = image.image_dimensions[0];
        const imageHeight = image.image_dimensions[1];
        const imageNormalizePoly: {x: number, y: number}[] = []
        closestPoly.geoJSON.coordinates[0].forEach((coord) => {
            const normalize_x = (coord[0] - image.bbox.xmin) / bboxWidth;
            const normalize_y = (coord[1] - image.bbox.ymin) / bboxHeight;
            const image_x = normalize_x * imageWidth;
            const image_y = normalize_y * imageHeight;
            imageNormalizePoly.push({x: image_x, y: image_y});
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
        context.beginPath();
        context.moveTo(coords[0].x, image.image_dimensions[1] - coords[0].y);
        coords.forEach(({x, y}) => {
            if (context){
                context.lineTo(x, image.image_dimensions[1] - y);
            }
        });
        context.lineWidth = 1;
        context.strokeStyle = getColorFromLabel(poly.label);
        context.stroke();
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

watch(displayImage, async () => {
    if (displayImage.value) {
        await getImageData();
        if (currentImage.value < filteredImages.value.length && canvasRef.value !== null) {
            drawData(canvasRef.value, filteredImages.value[currentImage.value].image, filteredImages.value[currentImage.value].poly)
        }
    }
});

watch([percentBlackFilter, cloudFilter, siteObsFilter, imageSourcesFilter], () => {
  if (currentImage.value > filteredImages.value.length) {
    currentImage.value = 0;
  }
});

watch([currentImage, imageRef, filteredImages], () => {
    if (currentImage.value < filteredImages.value.length && imageRef.value !== null) {
        imageRef.value.src = filteredImages.value[currentImage.value].image.image;
    }
    if (currentImage.value < filteredImages.value.length && canvasRef.value !== null) {
        drawData(canvasRef.value, filteredImages.value[currentImage.value].image, filteredImages.value[currentImage.value].poly)
    }

});


</script>

<template>
  <div>
    <v-btn @click="displayImage = true">
      Show Image Viewer
    </v-btn>
    <v-dialog
      v-model="displayImage"
      width="800"
    >
      <v-card
        class="pa-4"
      >
        <v-row dense>
          <v-spacer />
          <v-icon @click="displayImage = false">
            mdi-close
          </v-icon>
        </v-row>
        <v-card-title> Site Image Display</v-card-title>
        <v-row
          dense
          class="my-1"
        >
          <v-icon @click="filterSettings = !filterSettings">
            mdi-filter
          </v-icon>
          <div>
            Displaying {{ filteredImages.length }} of {{ combinedImages.length }} images
          </div>
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
        <canvas
          v-if="filteredImages.length"
          ref="canvasRef"
        />
        <v-row
          v-if="filteredImages.length && filteredImages[currentImage]"
          dense
          class="mt-2"
        >
          <v-col cols="3">
            <div v-if="filteredImages[currentImage].image.siteobs_id !== null">
              Site Observation
            </div>
            <div v-else>
              Non Site Observation
            </div>
            <v-tooltip
              open-delay="50"
              bottom
            >
              <template #activator="{ props }">
                <v-icon v-bind="props">
                  mdi-information
                </v-icon>
              </template>
              <span>
                {{ filteredImages[currentImage].image.aws_location }}
              </span>
            </v-tooltip>
          </v-col>
          <v-spacer />
          <v-col class="text-center">
            <div>
              <div>{{ filteredImages[currentImage].image.source }}</div>
              <div>{{ currentTimestamp }}</div>
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
          v-model="currentImage"
          min="0"
          :max="filteredImages.length - 1"
          step="1"
        />
      </v-card>
    </v-dialog>
  </div>
</template>
