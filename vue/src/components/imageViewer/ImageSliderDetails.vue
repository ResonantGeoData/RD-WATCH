<script setup lang="ts">
import { Ref, onMounted, onUnmounted, ref, watch, withDefaults } from "vue";
import { EvaluationImage } from "../../types";
import { state } from "../../store";
import { PixelPoly } from "./imageUtils";
import { getColorFromLabel } from "../../mapstyle/annotationStyles";

type EditModes =
  | "SiteEvaluationLabel"
  | "StartDate"
  | "EndDate"
  | "SiteObservationLabel"
  | "SiteEvaluationNotes"
  | "SiteObservationNotes";

interface Props {
    filteredImages: {image: EvaluationImage; poly: PixelPoly, groundTruthPoly?: PixelPoly}[];
    startDate: string | null;
    endDate: string | null;
    currentDate: string;
    currentLabel: string;
    editMode: boolean;
    imageIndex: number;
}
const props = withDefaults(defineProps<Props>(), {
});

const emit = defineEmits<{
    (e: "currentImage", num:number): void;
    (e: "editDialog", mode: EditModes | null): void;
}>();

const currentImage = ref(props.imageIndex);
const startDateTemp: Ref<string | null> = ref(null);
const endDateTemp: Ref<string | null> = ref(null);
const playbackEnabled = ref(false); // Auto playback of images

watch(() => props.imageIndex, () => {
  currentImage.value = props.imageIndex;
})

const setEditingMode = (mode: EditModes) => {
  if (["StartDate", "EndDate"].includes(mode)) {
    if (props.startDate === null) {
      startDateTemp.value = props.currentDate;
    } else {
      startDateTemp.value = props.startDate;
    }
    if (props.endDate === null) {
      endDateTemp.value = props.currentDate;
    } else {
      endDateTemp.value = props.endDate;
    }
  }
  emit('editDialog', mode);
};

const copyURL = async (mytext: string) => {
  try {
    await navigator.clipboard.writeText(mytext);
  } catch ($e) {
    alert("Cannot copy");
  }
};


const adjustImage = (direction: number) => {
  if (currentImage.value + direction < 0) {
    currentImage.value = props.filteredImages.length - 1;
  } else if (currentImage.value + direction >= props.filteredImages.length) {
    currentImage.value = 0;
  } else {
    currentImage.value = currentImage.value + direction;
  }
};

let loopingInterval: NodeJS.Timeout | null = null;

const togglePlayback = () => {
  if (loopingInterval && playbackEnabled.value) {
    clearInterval(loopingInterval);
    playbackEnabled.value = false;
    return;
  }
  loopingInterval = setInterval(() => {
    adjustImage(1);
  }, (1.0 / state.gifSettings.fps) * 1000);
  playbackEnabled.value = true;
};

const keyboardEventListener = (e: KeyboardEvent) => {
  if (e.key === "ArrowLeft") {
    if (e.ctrlKey) {
      currentImage.value = 0;
    } else {
      adjustImage(-1);
    }
  }
  if (e.key === "ArrowRight") {
    if (e.ctrlKey) {
      currentImage.value = props.filteredImages.length - 1;
    } else {
      adjustImage(1);
    }
  }
  if (e.key === " ") {
    togglePlayback();
  }
};

watch(currentImage, () =>{
  emit('currentImage', currentImage.value);
})

onMounted(() => {
  window.addEventListener("keydown", keyboardEventListener);
});

onUnmounted(() => {
  if (loopingInterval) {
    clearInterval(loopingInterval);
  }
  window.removeEventListener("keydown", keyboardEventListener);
});
</script>

<template>
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
        <template #activator="{ props: subProps }">
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
            v-if="
              editMode &&
                filteredImages[currentImage].image.observation_id !== null
            "
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
        <div>
          NODATA:
          {{ filteredImages[currentImage].image.percent_black.toFixed(0) }}%
        </div>
        <div>
          Cloud:
          {{ filteredImages[currentImage].image.cloudcover.toFixed(0) }}%
        </div>
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
      {{ playbackEnabled ? "mdi-pause" : "mdi-play" }}
    </v-icon>
    <v-icon
      class="mx-2 hover"
      @click="adjustImage(1)"
    >
      mdi-skip-next
    </v-icon>
    <v-icon
      class="mx-2 hover"
      @click="currentImage = filteredImages.length - 1"
    >
      mdi-skip-forward
    </v-icon>
    <v-spacer />
  </v-row>
</template>
