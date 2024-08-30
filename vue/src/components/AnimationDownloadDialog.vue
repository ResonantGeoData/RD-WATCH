<script setup lang="ts">
import { Ref, computed, defineProps, ref, withDefaults } from "vue";
import { debounce } from 'lodash';
import { Constellation, DownloadAnimationSettings } from "../client/services/ApiService";
import { useDate } from "vuetify/lib/framework.mjs";

const props = defineProps<{
  type: 'site' | 'modelRun';
  id: string;
}>();


const emit = defineEmits<{
    (e: "download", data: DownloadAnimationSettings): void;
    (e: "cancel"): void;
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

const download = debounce(
  () => {
    emit('download', {
      output_format: outputFormat.value,
      fps: fps.value,
      point_radius: pointRadius.value,
      sources: selectedSources.value,
      labels: labels.value,
      cloudCover: cloudCover.value,
      noData: noData.value,
      include: include.value,
      rescale: rescale.value,
      rescale_border: rescaleBorder.value

    });
  },
  5000,
  { leading: true },
);

const cancel = debounce(() => emit('cancel'), 5000, { leading: true });


const display = ref(true);

</script>

<template>
  <v-dialog
    v-model="display"
    width="400"
  >
    <v-card>
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
            <v-text-field
              v-model.number="fps"
              type="number"
              label="FPS"
              :rules="[v => v >= 0 || 'Must be >= 0']"
              class="mx-2"
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
              :label="`Cloud Cover < (${cloudCover.toFixed(2)})%`"
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
              :label="`NODATA < (${noData.toFixed(2)})%`"
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
              :label="`Rescale Border ${rescaleBorder.toFixed(2)})%`"
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
  </v-dialog>
</template>

<style scoped>
</style>
