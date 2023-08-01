<script setup lang="ts">
import TimeSlider from "./TimeSlider.vue";
import { ApiService, ModelRun } from "../client";
import { state } from "../store";
import { Ref, onBeforeMount, onBeforeUnmount, ref, withDefaults } from "vue";
import { timeRangeFormat } from "../utils";
import ImagesDownloadDialog from "./ImagesDownloadDialog.vue";
import { DownloadSettings } from "../client/services/ApiService";

interface Props {
  modelRun: ModelRun;
  open?: boolean;
  compact?: boolean
}
const props = withDefaults(defineProps<Props>(), {
  compact: false,
});

const emit = defineEmits<{
  (e: "toggle"): void;
}>();

async function handleClick() {
  emit("toggle");
}

const useScoring = ref(false);
const downloadImages = ref(false);

let loopingInterval: NodeJS.Timeout | null = null;

async function getScoringColoring() {
  if (!useScoring.value) { // inverted value because of the delay
    const results = await ApiService.getScoreColoring(props.modelRun.id, props.modelRun.region?.id || 0)
    let tempResults = state.filters.scoringColoring;
    if (!tempResults) {
      tempResults = {};
    }
    if (tempResults !== undefined && tempResults !== null)  {
      tempResults[`${props.modelRun.id}_${props.modelRun.region?.id || 0}`] = results;
    }
    state.filters = { ...state.filters, scoringColoring: tempResults };
  } else {
    let tempResults = state.filters.scoringColoring;
    if (tempResults) {
      if (Object.keys(tempResults).includes(`${props.modelRun.id}_${props.modelRun.region?.id || 0}`)) {
        delete tempResults[`${props.modelRun.id}_${props.modelRun.region?.id || 0}`];
      }
      if (Object.values(tempResults).length === 0) {
        tempResults = null;
      }
    }
    state.filters = { ...state.filters, scoringColoring: tempResults };
  }
}
const downloading = ref(props.modelRun.downloading);

const updateDownloading = async () => {
  const data = await ApiService.getModelRun(props.modelRun.id);
  downloading.value = data.downloading;
  if (loopingInterval !== null && downloading.value == 0) {
    clearInterval(loopingInterval);
    loopingInterval = null;
  }

}
const startDownload = (data: DownloadSettings) => {
  ApiService.getModelRunImages(props.modelRun.id.toString(), data )
  downloadImages.value = false;
  downloading.value = props.modelRun.numsites;
  setTimeout(() => {
  updateDownloading();
  loopingInterval = setInterval(updateDownloading, 1000);
  }, 2000)
}

const cancelDownload = () => { 
  ApiService.cancelModelRunsImageTask(props.modelRun.id);
}

onBeforeMount(() => {
  if (loopingInterval !== null) {
    clearInterval(loopingInterval);
    loopingInterval = null;
  }
  if (props.modelRun.downloading > 0 && loopingInterval === null)
  loopingInterval = setInterval(updateDownloading, 1000);
})

onBeforeUnmount(() => {
  if (loopingInterval !== null) {
    clearInterval(loopingInterval);
    loopingInterval = null;
  }
})
</script>

<template>
  <v-card
    outlined
    class="my-3 modelRunCard"
    :class="{selectedCard: props.open}"
  >
    <v-card-text
      @click.prevent="handleClick"
    >
      <v-row dense>
        <div class="model-title">
          {{ modelRun.title }}
        </div>
      </v-row>
      <v-row dense>
        <div>
          region:
        </div>
        <div>
          {{ modelRun.region?.name || "(none)" }}
        </div>
      </v-row>
      <v-row dense>
        <div>
          last updated:
        </div>
        <div>
          {{
            modelRun.timestamp === null
              ? "--"
              : new Date(modelRun.timestamp * 1000).toLocaleString()
          }}
        </div>
      </v-row>
      <v-row dense>
        <div>
          number of sites:
        </div>
        <div>
          {{ modelRun.numsites }}
        </div>
      </v-row>
      <v-row
        v-if="!compact"
        dense
      >
        <div>
          average score:
        </div>
        <div>
          {{ modelRun.score === null ? "--" : modelRun.score.toFixed(2) }}
        </div>
      </v-row>
      <v-row dense>
        <div>
          date coverage:
        </div>
        <div>
          {{
            timeRangeFormat(modelRun.timerange)
          }}
        </div>
      </v-row>
      <v-row
        v-if="!compact && modelRun.hasScores && props.open"
        dense
      >
        <input
          v-model="useScoring"
          type="checkbox"
          @click.stop="getScoringColoring()"
        >
        <span class="ml-2"> Scoring Coloring</span>
      </v-row>
      <v-row dense>
        <v-icon
          v-if="modelRun.performer.short_code === 'TE' && modelRun.score == 1"
          color="rgb(37, 99, 235)"
        >
          mdi-check-decagram
        </v-icon>
        <div
          class="float-right "
        >
          {{ modelRun.performer.short_code }}
        </div>
        <v-spacer />
        <v-btn
          :disabled="downloading > 0"
          size="x-small"
          @click.stop="downloadImages = true"
        >
          Get <v-icon>mdi-image</v-icon>
        </v-btn>
      </v-row>
      <v-row v-if="downloading > 0">
        <b class="small">Downloading {{ downloading }} site(s) Images</b>
        <v-progress-linear indeterminate />
      </v-row>
      <v-row v-if="downloading > 0">
        <v-btn
          size="x-small"
          color="error"
          class="mt-2"
          @click="cancelDownload()"
        >
          Cancel
        </v-btn>
      </v-row>
    </v-card-text>
    <v-card-actions v-if="open && !compact">
      <TimeSlider
        :min="modelRun.timerange?.min || 0"
        :max="modelRun.timerange?.max || 0"
      />
    </v-card-actions>
    <images-download-dialog
      v-if="downloadImages"
      @download="startDownload($event)"
      @cancel="downloadImages = false"
    />
  </v-card>
</template>

<style scoped>
.modelRunCard{
  border: 3px solid transparent;
}
.modelRunCard:hover {
  cursor: pointer;
  border: 3px solid blue;
}
.selectedCard{
  background-color: lightblue;
}
.model-title {
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
