<script setup lang="ts">
import TimeSlider from "./TimeSlider.vue";
import { ApiService, ModelRun } from "../client";
import { Ref, computed, onBeforeMount, onBeforeUnmount, ref, withDefaults } from "vue";
import { timeRangeFormat } from "../utils";
import ImagesDownloadDialog from "./ImagesDownloadDialog.vue";
import { DownloadSettings } from "../client/services/ApiService";
import { useRoute } from "vue-router";
import { debounce } from 'lodash';
import { state } from "../store";

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

async function handleClick(modelRun: ModelRun) {
  if (modelRun.adjudicated?.ground_truths) {
    state.proposals.ground_truths = modelRun.adjudicated?.ground_truths
  } else {
    state.proposals.ground_truths = undefined;
  }
  emit("toggle");
}

const route = useRoute();
const scoringApp = computed(() => route.path.includes('scoring'));
const downloadImages = ref(false);

let loopingInterval: NodeJS.Timeout | null = null;


const downloading = ref(props.modelRun.downloading);

const updateDownloading = async () => {
  const data = await ApiService.getModelRun(props.modelRun.id);
  downloading.value = data.downloading;
  if (loopingInterval !== null && downloading.value == 0) {
    clearInterval(loopingInterval);
    loopingInterval = null;
  }

}

const startDownload = debounce((data: DownloadSettings) => {
  downloadImages.value = false;
  ApiService.getModelRunImages(props.modelRun.id.toString(), data)
  downloading.value = props.modelRun.numsites;
  setTimeout(() => {
    updateDownloading();
    loopingInterval = setInterval(updateDownloading, 10000);
  }, 2000);
}, 5000, { leading: true });

const cancelDownload = debounce(() => {
  ApiService.cancelModelRunsImageTask(props.modelRun.id);
}, 5000, { leading: true });

onBeforeMount(() => {
  if (loopingInterval !== null) {
    clearInterval(loopingInterval);
    loopingInterval = null;
  }
  if (props.modelRun.downloading > 0 && loopingInterval === null)
  loopingInterval = setInterval(updateDownloading, 10000);
})

onBeforeUnmount(() => {
  if (loopingInterval !== null) {
    clearInterval(loopingInterval);
    loopingInterval = null;
  }
})
const taskId = ref('');
const downloadError = ref(false);
const downloadingModelRun = ref(false);

const checkDownloadStatus = async () => {
  if (taskId.value) {
    const status = await ApiService.getModelRunDownloadStatus(taskId.value);
    if (status === 'SUCCESS') {
      const url = `${ApiService.getApiPrefix()}/model-runs/${props.modelRun.id}/download/${taskId.value}/`
      window.location.assign(url);
      downloadingModelRun.value = false;
    } else if (['REVOKED', 'FAILURE'].includes(status)) {
      downloadError.value = true;
      downloadingModelRun.value = false;
    } else {
      setTimeout(checkDownloadStatus, 1000)
    }
  }
}
const downloadDialog = ref(false);
const downloadMode: Ref<'all' | 'rejected' | 'approved'> = ref('all');


const downloadModelRun = async() => {
  downloadError.value = false;
  downloadingModelRun.value = true;
  taskId.value = await ApiService.startModelRunDownload(props.modelRun.id, downloadMode.value);
  // Now we poll to see when the download is finished
  checkDownloadStatus();
}

const determineDownload = () => {
  if (props.modelRun.proposal) {
    downloadDialog.value = true;
  } else {

    downloadModelRun();
  }
}

const getModeIcon = (mode: ModelRun['mode']) => (mode ? {
  batch: 'mdi-checkbox-multiple-blank',
  incremental: 'mdi-trending-up',
}[mode] : null);

</script>

<template>
  <v-card
    outlined
    class="my-3 modelRunCard"
    :class="{selectedCard: props.open}"
  >
    <v-card-text>
      <v-row
        dense
        align="center"
      >
        <div class="model-title">
          {{ modelRun.title }}
        </div>
        <v-spacer />
        <v-col cols="1">
          <v-checkbox 
            v-if="!props.modelRun.proposal"
            :model-value="props.open"
            density="compact"
            color="#29B6F6"
            hide-details
            @update:model-value="handleClick(modelRun)"
          />
          <v-radio 
            v-else-if="props.modelRun.proposal"
            :model-value="props.open"
            density="compact"
            color="#29B6F6"
            hide-details
            @click="handleClick(modelRun)"
          />
        </v-col>
      </v-row>
      <v-row dense>
        <div class="label-text">
          Region:
        </div>
        <div class="value-text">
          {{ modelRun.region || "(none)" }}
        </div>
      </v-row>
      <v-row dense>
        <div class="label-text">
          Date Coverage:
        </div>
        <div class="value-text">
          {{
            timeRangeFormat(modelRun.timerange)
          }}
        </div>
      </v-row>
      <v-row dense>
        <div class="label-text">
          Last Updated:
        </div>
        <div class="value-text">
          {{
            modelRun.timestamp === null
              ? "--"
              : new Date(modelRun.timestamp * 1000).toISOString().substring(0, 10)
          }}
        </div>
      </v-row>
      <v-row dense>
        <v-tooltip>
          <template #activator="{ props }">
            <v-icon
              v-if="modelRun.performer.short_code === 'TE' && modelRun.score == 1"
              v-bind="props"
              color="primary"
            >
              mdi-check-decagram
            </v-icon>
          </template>
          <span>Ground Truth</span>
        </v-tooltip>
        <div
          class="performer"
        >
          {{ modelRun.performer.short_code }}
        </div>
      </v-row>
      <v-row
        dense
        align="center"
      >
        <v-tooltip>
          <template #activator="{ props }">
            <v-icon
              v-bind="props"
              color="#BDBDBD"
              size="x-large"
              style="left:-5px"
            >
              mdi-map-marker-outline
            </v-icon>
          </template>
          <span>Site Count</span>
        </v-tooltip>
        <div class="site-count">
          {{ modelRun.numsites }}
        </div>
        <v-tooltip v-if="!modelRun.proposal">
          <template #activator="{ props }">
            <v-icon
              v-bind="props"
              color="#BDBDBD"
              size="x-large"
            >
              mdi-license
            </v-icon>
          </template>
          <span>Average Score</span>
        </v-tooltip>
        <div
          v-if="!modelRun.proposal"
          class="site-score"
        >
          {{ modelRun.score === null ? "--" : modelRun.score.toFixed(2) }}
        </div>
        <v-tooltip
          v-if="modelRun.mode"
        >
          <template #activator="{ props }">
            <v-icon
              v-bind="props"
              color="#BDBDBD"
              size="x-large"
              class="pl-2"
            >
              {{ getModeIcon(modelRun.mode) }}
            </v-icon>
          </template>
          <span>Mode: <b style="text-transform: uppercase">{{ modelRun.mode }}</b></span>
        </v-tooltip>
        <v-tooltip
          v-if="modelRun.proposal && modelRun.adjudicated"
        >
          <template #activator="{ props }">
            <div v-if="modelRun.adjudicated.proposed !== 0">
              <v-chip
                v-bind="props"
                size="small"
                variant="elevated"
                class="ml-2"
                :color="modelRun.adjudicated.other === 0 ? 'error' : modelRun.adjudicated.proposed === 0 ? 'success' : 'warning'"
              >
                <b>{{ modelRun.adjudicated.other }} / {{ modelRun.adjudicated.other + modelRun.adjudicated.proposed }}</b>
              </v-chip>
            </div>
          </template>
          <span><b>Number of Sites Adjudicated</b></span>
        </v-tooltip>

        <v-spacer />
        <v-tooltip v-if="!scoringApp">
          <template #activator="{ props }">
            <v-spacer />
            <v-btn
              v-bind="props"
              variant="tonal"
              density="compact"
              class="pa-0 ma-1 modelrun-icon"
              :disabled="downloadingModelRun"
              :color="downloadError ? 'error' : 'primary'"
              @click.stop="determineDownload()"
            >
              <v-icon
                v-if="!downloadingModelRun"
              >
                mdi-download-box-outline
              </v-icon>
              <v-icon
                v-else-if="downloadError"
                size="small"
                color="error"
              >
                mdi-alert
              </v-icon>

              <v-icon
                v-else-if="downloadingModelRun"
                size="small"
              >
                mdi-spin mdi-sync
              </v-icon>
            </v-btn>
          </template>
          <div>
            <span v-if="!downloadingModelRun">Download JSON</span>
            <span v-else-if="downloadError">Downloading Error</span>
            <span v-else-if="downloadingModelRun">Downloading Model Run</span>
          </div>
        </v-tooltip>
        <v-tooltip>
          <template #activator="{ props }">
            <v-btn
              v-bind="props"
              variant="tonal"
              density="compact"
              class="pa-0 ma-1 modelrun-icon"
              :disabled="downloading > 0"
              color="primary"
              @click.stop="downloadImages = true"
            >
              <v-icon
                v-if="!downloadingModelRun"
              >
                mdi-image
              </v-icon>
            </v-btn>
          </template>
          <span> Download Satellite Images</span>
        </v-tooltip>
      </v-row>
      <v-row dense />
      <v-row v-if="downloading > 0">
        <b class="small">Downloading {{ downloading }} site(s) Images <v-icon class="fading">mdi-download</v-icon></b>
        <v-progress-linear :model-value="((modelRun.numsites - downloading)/modelRun.numsites)*100" />
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
        compact
      />
    </v-card-actions>
    <images-download-dialog
      v-if="downloadImages"
      :date-range="modelRun.timerange"
      @download="startDownload($event)"
      @cancel="downloadImages = false"
    />
    <v-dialog
      v-model="downloadDialog"
      width="400"
    >
      <v-card>
        <v-card-title>Download Annotations</v-card-title>
        <v-card-text>
          <v-select
            v-model="downloadMode"
            :items="['all', 'approved', 'rejected']"
            label="Label"
            class="mx-2"
          />
        </v-card-text>
        <v-card-actions>
          <v-row dense>
            <v-spacer />
            <v-btn
              color="error"
              class="mx-3"
              @click="downloadDialog = false"
            >
              Cancel
            </v-btn>
            <v-btn
              color="success"
              class="mx-3"
              @click="downloadDialog =false; downloadModelRun()"
            >
              Download
            </v-btn>
          </v-row>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<style scoped>
.modelRunCard{
  border: 3px solid transparent;
  background-color: white;
}
.modelRunCard:hover {
  border: 3px solid blue;
}
.baseCard {
  background-color: #166DB7;
}
.selectedCard{
  background-color: #e8f1f8;
}
.model-title {
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: bolder;
}

.fading {
  animation: fadeIcon 2s linear infinite;
  overflow:hidden;
}

.label-text {
  color: gray
}

.value-text {
  color: black;
  font-weight: bolder;
  margin-left: 5px;
}

.performer {
  text-transform: uppercase;
  font-weight: bold;
}
.site-count {
  margin-left: -5px;
  font-weight: bolder;
}
.site-score {
  margin-left: 0px;
  font-weight: bolder;
}

.modelrun-icon {
  min-width: 40px;
  min-height: 40px;;
}


@keyframes fadeIcon {
  0% {
    opacity: 0;
  }
  50% {
    opacity: 1;

  }
  100% {
    opacity: 0;
  }
}
</style>
