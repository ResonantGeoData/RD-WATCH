<script setup lang="ts">
import { FitBoundsEvent } from '../../actions/map';
import { Site, useIQR } from '../../use/useIQR';
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

function focusCandidate(geomExtent: number[]) {
  FitBoundsEvent.trigger({
    xmin: geomExtent[0],
    ymin: geomExtent[1],
    xmax: geomExtent[2],
    ymax: geomExtent[3],
  });
}
</script>

<template>
  <div class="pa-1">
    <div class="text-h6">
      Similar Sites
    </div>
    <v-card
      variant="flat"
      color="light-blue-lighten-4"
    >
      <v-card-title class="text-subtitle-2">
        Query: {{ props.site.name }}
      </v-card-title>
    </v-card>
    <v-btn
      color="secondary"
      class="w-100 my-2"
      @click="refine"
    >
      Refine
    </v-btn>
    <div class="mt-3">
      <iqr-candidate
        v-for="result in queryResults"
        :key="result.smqtkUuid"
        class="iqr-candidate"
        :pk="result.pk"
        :site-id="result.siteId"
        :image-url="result.imageUrl"
        :smqtk-uuid="result.smqtkUuid"
        :status="result.status"
        :confidence="result.confidence"
        @status-changed="updateCandidateStatus(result.smqtkUuid, $event)"
        @image-click="focusCandidate(result.geomExtent)"
      />
    </div>
  </div>
</template>
