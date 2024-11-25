<script setup lang="ts">
import { FitBoundsEvent } from '../../actions/map';
import { Site, useIQR } from '../../use/useIQR';
import { state } from "../../store";
import IqrCandidate from './IqrCandidate.vue';

const props = defineProps<{
  site: Site;
}>();

const iqr = useIQR();

const { queryResults } = iqr;

function updateCandidateStatus(uuid: string, status: 'positive' | 'neutral' | 'negative') {
  iqr.adjudicate([{ uuid, status }]);
}

function refine() {
  iqr.refine();
}

function focusCandidate(candidate: (typeof iqr.queryResults)['value'][number]) {
  // open the image browser
  state.selectedImageSite = {
    siteId: candidate.siteUid,
    siteName: candidate.siteId,
  };

  FitBoundsEvent.trigger({
    xmin: candidate.geomExtent[0],
    ymin: candidate.geomExtent[1],
    xmax: candidate.geomExtent[2],
    ymax: candidate.geomExtent[3],
  });
}
</script>

<template>
  <div class="pa-1 d-flex flex-column overflow-hidden h-100">
    <div class="overflow-auto flex-grow-1">
      <div class="text-h6 d-flex flex-row justify-space-between align-center pb-2 pl-2">
        <span>Similar Sites</span>
        <v-btn
          icon="mdi-close"
          variant="flat"
          size="small"
          @click="iqr.setPrimarySite(null)"
        />
      </div>
      <v-card
        variant="flat"
        color="light-blue-lighten-4"
      >
        <v-card-title class="text-subtitle-2">
          Query: {{ props.site.name }}
        </v-card-title>
        <v-card-text>
          <v-img :src="iqr.state.siteImageUrl" />
        </v-card-text>
      </v-card>
      <v-progress-linear
        :style="{
          visibility: iqr.state.refreshing ? 'visible' : 'hidden',
        }"
        class="my-2"
        indeterminate
      />
      <div class="mt-3">
        <iqr-candidate
          v-for="result, idx in queryResults"
          :key="result.smqtkUuid"
          class="iqr-candidate"
          :pk="result.pk"
          :index="idx + 1"
          :site-id="result.siteId"
          :image-url="result.imageUrl"
          :smqtk-uuid="result.smqtkUuid"
          :status="result.status"
          :confidence="result.confidence"
          @status-changed="updateCandidateStatus(result.smqtkUuid, $event)"
          @image-click="focusCandidate(result)"
        />
      </div>
    </div>
    <div
      class="flex-grow-0"
      style="border-top: 2px solid grey"
    >
      <v-btn
        color="secondary"
        class="w-100 my-2"
        @click="refine"
      >
        Refine Query
      </v-btn>
    </div>
  </div>
</template>
