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
    loopingInterval = setInterval(updateDownloading, 1000);
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
  loopingInterval = setInterval(updateDownloading, 1000);
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
    <v-card-actions
      v-if="modelRun.mode"
      class="pa-2"
      style="position: absolute; top: 0; right: 0;"
    >
      <v-chip
        label
        size="x-small"
      >
        <span class="text-caption mx-2">{{ modelRun.mode?.toUpperCase() }}</span>
        <v-icon>
          {{ getModeIcon(modelRun.mode) }}
        </v-icon>
      </v-chip>
    </v-card-actions>
    <v-card-text
      @click.prevent="handleClick(modelRun)"
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
          {{ modelRun.region || "(none)" }}
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
              : new Date(modelRun.timestamp * 1000).toISOString().substring(0, 10)
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
        v-if="modelRun.proposal && modelRun.adjudicated"
        dense
      >
        <div v-if="modelRun.adjudicated.proposed !== 0">
          <v-chip
            size="small"
            color="warning"
          >
            {{ modelRun.adjudicated.other }} / {{ modelRun.adjudicated.other + modelRun.adjudicated.proposed }} Adjudicated
          </v-chip>
        </div>
        <div v-else>
          <v-chip
            size="small"
            color="success"
          >
            All Proposals Adjudicated
          </v-chip>
        </div>
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
        <v-tooltip v-if="!scoringApp">
          <template #activator="{ props }">
            <v-btn
              size="x-small"
              v-bind="props"
              :disabled="downloadingModelRun"
              class="mx-1"
              @click.stop="determineDownload()"
            >
              <v-icon
                v-if="!downloadingModelRun"
                size="small"
              >
                mdi-export
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
          <span>Download JSON</span>
        </v-tooltip>
        <v-tooltip>
          <template #activator="{ props }">
            <v-btn
              :disabled="downloading > 0"
              size="x-small"
              v-bind="props"
              class="mx-1"
              @click.stop="downloadImages = true"
            >
              Get <v-icon>mdi-image</v-icon>
            </v-btn>
          </template>
          <span> Download Satellite Images</span>
        </v-tooltip>
      </v-row>
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

.fading {
  animation: fadeIcon 2s linear infinite;
  overflow:hidden;
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
