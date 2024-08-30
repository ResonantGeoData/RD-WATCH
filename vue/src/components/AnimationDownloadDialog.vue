<script setup lang="ts">
import { Ref, computed, defineProps, ref, withDefaults } from "vue";
import { debounce } from 'lodash';
import { ApiService, Constellation, DownloadAnimationSettings } from "../client/services/ApiService";
import { useDate } from "vuetify/lib/framework.mjs";

const props = defineProps<{
  type: 'site' | 'modelRun';
  id: string;
}>();


const emit = defineEmits<{
    (e: "download", data: DownloadAnimationSettings): void;
    (e: "close"): void;
}>();

const validForm = ref(true);
const outputFormat: Ref<DownloadAnimationSettings['output_format']> = ref('mp4');
const formatChoices = ref(['mp4', 'gif']);
const fps = ref(1);
const pointRadius = ref(5);
const constellationChoices = ref(['S2', 'WV', 'L8', 'PL'])
const selectedSources: Ref<Constellation[]> = ref(['WV', 'S2', 'WV', 'PL']);
const labelChoices = ref(['geom', 'date', 'source', 'obs', 'obs_label']);
const labels: Ref<DownloadAnimationSettings['labels']> = ref(['geom', 'date', 'source', 'obs', 'obs_label']);
const cloudCover = ref(100);
const noData = ref(100);
const include: Ref<DownloadAnimationSettings['include']> = ref(['obs', 'nonobs']);
const includeChoices = ref([{value: 'obs', name: 'Include Observation Images'},{ value: 'nonobs', name: 'Include Non-Observation Images' }])
const rescale = ref(false);
const rescaleBorder = ref(1);
const taskId = ref('');
const downloading = ref(false);
const downloadError = ref(false);
const currentMode = ref('');
const currentCount = ref(0);
const total = ref(0);


const download = debounce(
  async () => {
    const downloadSettings: DownloadAnimationSettings = {
      output_format: outputFormat.value,
      fps: fps.value,
      sources: selectedSources.value,
      labels: labels.value,
      cloudCover: cloudCover.value,
      noData: noData.value,
      rescale: rescale.value,
      rescale_border: rescaleBorder.value,
    }
    const response = await ApiService.generateSiteAnimation(props.id, downloadSettings);
    if (response) {
      taskId.value = response;
      downloading.value = true;
      checkDownloadStatus();
    }
  },
  5000,
  { leading: true },
);

const cancel = debounce(() => emit('close'), 5000, { leading: true });


const checkDownloadStatus = async () => {
  if (taskId.value) {
    const info = await ApiService.getSiteAnimationDownloadStatus(taskId.value);
    const status = info.status;
    if (info.info) {
      if (info.info.mode) {
        currentMode.value = info.info.mode;
      }
      if (info.info.current !== undefined && info.info.total !== undefined) {
        currentCount.value = info.info.current;
        total.value = info.info.total;
      }
    }
    if (status === 'SUCCESS') {
      const url = `${ApiService.getApiPrefix()}/evaluations/animation/${taskId.value}/`
      window.location.assign(url);
      downloading.value = false;
      emit('close');
    } else if (['REVOKED', 'FAILURE'].includes(status)) {
      downloadError.value = true;
      downloading.value = false;
      emit('close');
    } else {
      setTimeout(checkDownloadStatus, 1000)
    }
  }
}
</script>

<template>
  <v-card v-if="downloading">
    <v-card-title>
      Downloading Animated Images
    </v-card-title>
    <v-card-text>
      <v-row dense>
        <v-progress-linear
          :model-value="currentCount"
          :max="total"
          height="25"
        />
      </v-row>
      <v-row dense>
        <v-spacer />
        <div>{{ currentMode }}</div>
        <v-spacer />
      </v-row>
    </v-card-text>
  </v-card>
  <v-card v-if="!downloading">
    <v-card-title>Download Animated Images</v-card-title>
    <v-form v-model="validForm">
      <v-card-text>
        <v-row
          dense
          align="center"
        >
          <v-select
            v-model="outputFormat"
            :items="formatChoices"
            label="Output Format"
            class="mr-2"
          />
        </v-row>
        <v-row
          dense
          align="center"
        >
          <v-select
            v-model="selectedSources"
            multiple
            :items="constellationChoices"
            label="Source"
            class="mr-2"
          />
        </v-row>
        <v-row
          dense
          align="center"
          class="pb-5"
        >
          <v-slider
            v-model="fps"
            min="1"
            max="60"
            step="1"
            thumb-label="always"
            label="FPS"
            class="pt-2"
          />
        </v-row>
        <v-row
          dense
          align="center"
        >
          <v-select
            v-model="labels"
            multiple
            :items="labelChoices"
            label="Display Labels"
            class="mr-2"
          />
        </v-row>

        <v-row
          dense
          align="center"
          class="pb-5"
        >
          <v-slider
            v-model="cloudCover"
            min="0"
            max="100"
            step="1"
            thumb-label="always"
            label="Cloud Cover<"
            class="pt-2"
          />
        </v-row>
        <v-row
          dense
          align="center"
          class="pb-5"
        >
          <v-slider
            v-model="noData"
            min="0"
            max="100"
            step="1"
            thumb-label="always"
            label="NODATA<"
            class="pt-2"
          />
        </v-row>
        <v-row
          dense
          align="center"
        >
          <v-select
            v-model="include"
            multiple
            :items="includeChoices"
            item-value="value"
            item-title="name"
            label="Display Labels"
            class="mr-2"
          />
        </v-row>
        <v-row dense>
          <v-checkbox
            v-model="rescale"
            label="Rescale"
          />
        </v-row>
        <v-row
          dense
          align="center"
          class="pb-5"
        >
          <v-slider
            v-model="rescaleBorder"
            min="0"
            max="5"
            step="0.1"
            :label="`Rescale Border ${rescaleBorder.toFixed(2)}X`"
          />
        </v-row>
      </v-card-text>
    </v-form>
    <v-card-actions>
      <v-row>
        <v-spacer />
        <v-btn
          color="error"
          class="mx-3"
          @click="cancel()"
        >
          Cancel
        </v-btn>
        <v-btn
          color="success"
          class="mx-3"
          :disabled="!validForm"
          @click="download()"
        >
          Download
        </v-btn>
      </v-row>
    </v-card-actions>
  </v-card>
</template>

<style scoped>
</style>
