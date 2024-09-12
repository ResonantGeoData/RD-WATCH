<script setup lang="ts">
import { Ref, defineProps, onMounted, ref } from "vue";
import { debounce } from "lodash";
import {
  ApiService,
  Constellation,
  DownloadAnimationSettings,
} from "../../client/services/ApiService";
import AnimationDownloaded from "./AnimationDownloaded.vue";

const props = defineProps<{
  type: "site" | "modelRun";
  id: string;
}>();

const emit = defineEmits<{
  (e: "download", data: DownloadAnimationSettings): void;
  (e: "close"): void;
}>();

const validForm = ref(true);
const outputFormat: Ref<DownloadAnimationSettings["output_format"]> =
  ref("mp4");
const formatChoices = ref(["mp4", "gif"]);
const fps = ref(1);
const pointRadius = ref(5);
const constellationChoices = ref(["S2", "WV", "L8", "PL"]);
const selectedSources: Ref<Constellation[]> = ref(["WV", "S2", "WV", "PL"]);
const labelChoices = ref(["geom", "date", "source", "obs", "obs_label"]);
const labels: Ref<DownloadAnimationSettings["labels"]> = ref([
  "geom",
  "date",
  "source",
  "obs",
  "obs_label",
]);
const cloudCover = ref(95);
const noData = ref(100);
const include: Ref<DownloadAnimationSettings["include"]> = ref([
  "obs",
  "nonobs",
]);
const includeChoices = ref([
  { value: "obs", name: "Include Observation Images" },
  { value: "nonobs", name: "Include Non-Observation Images" },
]);
const rescale = ref(false);
const rescaleBorder = ref(1);

const currentTab: Ref<"download" | "downloaded"> = ref("download");
const noImages = ref(true);
const loading = ref(false);
onMounted(async () => {
  if (props.type === 'modelRun') { // Check for any available images
    loading.value = true;
    const data = await ApiService.getSitesList(props.id);
    // Determine if we have any images
    const { sites } = data;

    for (let i = 0; i< sites.length; i += 1) {
      if (sites[i].WV > 0 || sites[i].S2 > 0 || sites[i].L8 > 0  || sites[i].PL > 0 ) {
        noImages.value = false;
        break;
      }
    }
    loading.value = false;
  } else {
    noImages.value = false;
  }
})
const download = debounce(
  async () => {
    const downloadSettings: DownloadAnimationSettings = {
      output_format: outputFormat.value,
      fps: fps.value,
      point_radius: pointRadius.value,
      sources: selectedSources.value,
      labels: labels.value,
      cloudCover: cloudCover.value,
      noData: noData.value,
      include: include.value,
      rescale: rescale.value,
      rescale_border: rescaleBorder.value,
    };
    
    const response = props.type === 'site' ?
    await ApiService.generateSiteAnimation(props.id,downloadSettings) :
     await ApiService.generateModelRunAnimation(props.id, downloadSettings);
    if (response) {
      currentTab.value = 'downloaded';
    }
  },
  5000,
  { leading: true }
);

const cancel = debounce(() => emit("close"), 5000, { leading: true });
</script>

<template>
  <v-card
    v-if="!noImages && !loading"
  >
    <v-card-title>
      <v-tabs
        v-model="currentTab"
        density="compact"
        color="primary"
      >
        <v-tab
          value="download"
          size="small"
          variant="tonal"
        >
          Create Animation
        </v-tab>
        <v-tab
          value="downloaded"
          size="small"
          variant="tonal"
        >
          Animation Status
        </v-tab>
      </v-tabs>
    </v-card-title>
    <v-card-text    
      style="max-height:70vh; overflow-y:auto"
    >
      <div v-if="currentTab === 'download'">
        <v-form v-model="validForm">
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
              label="Include Observations"
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
        </v-form>
      </div>
      <div v-else-if="currentTab === 'downloaded'">
        <animation-downloaded
          :id="id"
          :type="type"
        />
      </div>
    </v-card-text>
    <v-card-actions>
      <v-row>
        <v-spacer />
        <v-btn
          color="error"
          class="mx-3"
          @click="cancel()"
        >
          {{ currentTab === 'download' ? 'Cancel' : 'Close' }}
        </v-btn>
        <v-btn
          v-if="currentTab === 'download'"
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
  <v-card v-else-if="noImages && !loading">
    <v-card-title>No Image</v-card-title>
    <v-card-text>
      <p>
        There are no images downloaded for this {{ type }}.  Please download images before exporting animations.
      </p>
    </v-card-text>
  </v-card>
  <v-card v-else-if="loading">
    <v-card-title>Loading</v-card-title>
    <v-card-text>
      <v-row dense>
        <v-progress-linear indeterminate />
      </v-row>
      <v-row dense>
        <v-spacer />
        <h3>Loading Images Information</h3>
        <v-spacer />
      </v-row>
    </v-card-text>
  </v-card>
</template>

