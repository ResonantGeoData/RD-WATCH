<script setup lang="ts">
import { computed, onBeforeMount, onBeforeUnmount } from "vue";
import { ApiService } from "../../client";
import { getSiteObservationDetails, state } from "../../store";
import { SiteObservation } from "../../store";
import { imageFilter } from "../../mapstyle/images";

const props = defineProps<{
  siteObservation: SiteObservation;
  imagesActive: boolean;
}>();

const emit = defineEmits<{
  (e: "change-timestamp", {dir, loop}: {dir: number; loop: boolean }): void;
}>();

let loopingInterval: NodeJS.Timeout | null = null;

const checkSiteObs = async () => {
  await getSiteObservationDetails(props.siteObservation.id.toString(), props.siteObservation.scoringBase);
  if (loopingInterval !== null && props.siteObservation.job && props.siteObservation.job.status !== 'Running') {
    clearInterval(loopingInterval);
    loopingInterval = null;
  }
}

onBeforeMount(() => {
  if (props.siteObservation.job && props.siteObservation.job.status === 'Running') {
    if (loopingInterval !== null) {
      clearInterval(loopingInterval);
      loopingInterval = null;
    }
    loopingInterval = setInterval(checkSiteObs, 1000);
  }
})

onBeforeUnmount(() => {
  if (loopingInterval !== null) {
    clearInterval(loopingInterval);
    loopingInterval = null;
  }
})

const getImages = async (id:number, constellation: 'WV' | 'S2' | 'L8' = 'WV')  => {
    await ApiService.getObservationImages(id.toString(), constellation);
    // Now we get the results to see if the service is running
    await getSiteObservationDetails(props.siteObservation.id.toString());
    // The props should be updated now we start an interval to update until we exist, deselect or other
    if (loopingInterval !== null) {
      clearInterval(loopingInterval);
      loopingInterval = null;
    }
    loopingInterval = setInterval(checkSiteObs, 1000);
}
const canGetImages = computed(() => ({
  WV: props.siteObservation.imageCounts.WV.total,
  S2: props.siteObservation.imageCounts.S2.total,
  L8: props.siteObservation.imageCounts.L8.total,
}));

const startLooping = () => {
  if (state.loopingInterval !== null) {
    clearInterval(state.loopingInterval);
  }
  state.loopingInterval = setInterval(() => {
    emit('change-timestamp', {dir: 1, loop:true})
  }, 1000);
  state.loopingId = props.siteObservation.id;
}
const stopLooping = () => {
  if (state.loopingInterval !== null) {
    clearInterval(state.loopingInterval);
    state.loopingId = null;
  }
}
const isRunning = computed(() => {
  return !!(props.siteObservation.job && props.siteObservation.job.status === 'Running');
});

const cancelTask = async (siteId: number) => {
  await ApiService.cancelSiteObservationImageTask(siteId);
  if (state.loopingInterval !== null) {
    clearInterval(state.loopingInterval);
  }
}
const progressInfo = computed(() => {
  if (isRunning.value) {
    if (props.siteObservation.job?.celery?.info) {
      const state = {
        title: props.siteObservation.job.celery.info.mode,
        current:props.siteObservation.job.celery.info.current,
        total: props.siteObservation.job.celery.info.total,
      }
      return state;
    }
  }
  return null
})
</script>

<template>
  <span class="pb-5">
    <v-row
      dense
      justify="center"
      align="center"
    >
      <v-col cols="3">
        Source
      </v-col>
      <v-col cols="3">
        Cached
      </v-col>
      <v-col cols="3">
        Obs
      </v-col>
      <v-col cols="3">
        Non-Obs
      </v-col>
    </v-row>
    <v-row
      dense
      justify="center"
      align="center"
    >
      <v-col cols="3">
        <b>L8</b>
      </v-col>
      <v-col cols="3">
        <b>{{ siteObservation.imageCounts.L8.loaded }}</b>
      </v-col>
      <v-col cols="3">
        <b>{{ siteObservation.imageCounts.L8.total }}</b>
      </v-col>
      <v-col cols="3">
        <b>{{ siteObservation.imageCounts.L8.loaded !== 0 ?Math.max(siteObservation.imageCounts.L8.loaded - siteObservation.imageCounts.L8.total, 0) : '-' }}</b>
      </v-col>
    </v-row>
    <v-row
      dense
      justify="center"
      align="center"
    >
      <v-col cols="3">
        <b>S2</b>
      </v-col>
      <v-col cols="3">
        <b>{{ siteObservation.imageCounts.S2.loaded }}</b>
      </v-col>
      <v-col cols="3">
        <b>{{ siteObservation.imageCounts.S2.total }}</b>
      </v-col>
      <v-col cols="3">
        <b>{{ siteObservation.imageCounts.S2.loaded !== 0 ?Math.max(siteObservation.imageCounts.S2.loaded - siteObservation.imageCounts.S2.total, 0) : '-' }}</b>
      </v-col>
    </v-row>
    <v-row
      dense
      justify="center"
      align="center"
    >
      <v-col cols="3">
        <b>WV</b>
      </v-col>
      <v-col cols="3">
        <b>{{ siteObservation.imageCounts.WV.loaded }}</b>
      </v-col>
      <v-col cols="3">
        <b>{{ siteObservation.imageCounts.WV.total }}</b>
      </v-col>
      <v-col cols="3">
        <b>{{ siteObservation.imageCounts.WV.loaded !== 0 ?Math.max(siteObservation.imageCounts.WV.loaded - siteObservation.imageCounts.WV.total, 0) : '-' }}</b>
      </v-col>
    </v-row>
    <v-row
      v-if="isRunning"
      dense
      justify="center"
      align="center"
      class="my-4"
    >
      <div
        v-if="isRunning && progressInfo"
        class="px-2 text-sm col-span-4"
        style="width: 100%"
      >
        <b>Downloading Images
          <span
            v-if="progressInfo !== null"
            style="font-size: 0.75em"
          >  ({{ progressInfo.title }})</span>
        </b>
        <div v-if="progressInfo !== null && progressInfo.total !== 0">
          {{ progressInfo.current }} of {{ progressInfo.total }}
        </div>
        <v-progress-linear
          v-if="progressInfo !== null && progressInfo.current === 0 && progressInfo.total === 0"
          color="primary"
          height="8"
          indeterminate
        />
        <v-progress-linear
          v-else-if="progressInfo !== null"
          color="primary"
          height="8"
          :model-value="(progressInfo.total / progressInfo.current) * 100.0 "
          indeterminate
        />

        <v-btn
          size="small"
          color="error"
          @click="cancelTask(siteObservation.id)"
        >
          Cancel
        </v-btn>
      </div>
    </v-row>
    <v-row
      dense
      justify="center"
      align="center"
    >
      <v-btn
        size="x-small"
        color="secondary"
        :disabled="canGetImages.WV === 0 || isRunning"
        class="mx-1"
        @click="getImages(siteObservation.id, 'WV')"
      >
        Get WV
      </v-btn>
      <v-btn
        size="x-small"
        color="secondary"
        :disabled="canGetImages.S2 === 0 || isRunning"
        class="mx-1"
        @click="getImages(siteObservation.id, 'S2')"
      >
        Get S2
      </v-btn>
      <v-btn
        v-if="false"
        size="x-small"
        color="secondary"
        :disabled="canGetImages.L8 === 0 || isRunning"
        class="mx-1"
        @click="getImages(siteObservation.id, 'L8')"
      >
        Get L8
      </v-btn>

      <span v-if="imagesActive">
        <v-btn
          v-if="state.loopingId !== siteObservation.id"
          size="x-small"
          color="primary"
          class="mx-1"
          @click="startLooping"
        >Play</v-btn>
        <v-btn
          v-if="state.loopingId === siteObservation.id"
          size="x-small"
          color="primary"
          class="mx-1"
          @click="stopLooping"
        >Stop</v-btn>
      </span>
      <v-spacer />
    </v-row>
  </span>
</template>

<style scoped>

</style>
