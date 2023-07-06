<script setup lang="ts">
import { Ref, computed, onBeforeMount, onBeforeUnmount, onMounted, ref, render, watch, } from "vue";
import { ApiService } from "../../client";
import { ImageBBox, SiteObservationImage, getSiteObservationDetails, state } from "../../store";
import {EvaluationGeoJSON, EvaluationImage } from "../../types";
import { getColorFromLabel } from '../../mapstyle/annotationStyles';
const props = defineProps<{
  siteEvalId: number;
}>();

interface PixelPoly {
    coords: {x:number; y:number}[];
    label: string;
}


const images: Ref<EvaluationImage[]> = ref([]);
const polygons: Ref<EvaluationGeoJSON[]> = ref([]);
const currentImage = ref(0);
const imageRef: Ref<HTMLImageElement | null> = ref(null);
const canvasRef: Ref<HTMLCanvasElement | null> = ref(null);
const pixelPolys: Ref<PixelPoly[]> = ref([]);
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

const currentTimestamp = computed(() => {
    const time = images.value[currentImage.value].timestamp;
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
    const data =  await ApiService.getEvaluationImages(props.siteEvalId);
    images.value = data.images.results.sort((a, b) => a.timestamp - b.timestamp);
    polygons.value = data.geoJSON.results;
    if (imageRef.value !== null) {
        imageRef.value.src = images.value[currentImage.value].image;
    }
    // Lets process the polygons to get them in pixel space.
    // For each polygon we need to convert it to the proper image sizing result.
    images.value.forEach((image) => {
        const closestPoly = getClosestPoly(image.timestamp, polygons.value);
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
        pixelPolys.value.push({coords: imageNormalizePoly, label: closestPoly.label});

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
        if (currentImage.value < images.value.length && canvasRef.value !== null) {
            drawData(canvasRef.value, images.value[currentImage.value], pixelPolys.value[currentImage.value])
        }
    }
})

watch([currentImage, imageRef], () => {
    if (currentImage.value < images.value.length && imageRef.value !== null) {
        imageRef.value.src = images.value[currentImage.value].image;
    }
    if (currentImage.value < images.value.length && canvasRef.value !== null) {
        drawData(canvasRef.value, images.value[currentImage.value], pixelPolys.value[currentImage.value])
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
      <v-card v-if="images.length" class="pa-4">
        <v-row dense>
          <v-spacer />
          <v-icon @click="displayImage = false">
            mdi-close
          </v-icon>
        </v-row>
        <v-card-title> Site Image Display</v-card-title>
        <canvas ref="canvasRef" />
        <v-row dense>
          <v-spacer />
          <div>
            {{ currentTimestamp }}
          </div>
          <v-spacer />
        </v-row>
        <v-slider
          v-model="currentImage"
          min="0"
          :max="images.length"
          step="1"
        />
      </v-card>
    </v-dialog>
  </div>
</template>
