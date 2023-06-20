<script setup lang="ts">
import { Ref, ref, } from "vue";
import { ApiService } from "../../client";
import { SiteObservation } from "../../store";

const props = defineProps<{
  siteObservation: SiteObservation;
}>();


const unionArea: Ref<null | number> = ref(null);
const temporalIOU: Ref<null | {site_preparation: string; active_construction: string; post_construction: string}> = ref(null);
const statusAnnotated: Ref<null | string> = ref(null);
const retrieveScoring = async () => {
    const scoreData = props.siteObservation.scoringBase;
    const scoringRequest = await ApiService.getScoring(scoreData.configurationId, scoreData.regionId, scoreData.siteNumber, scoreData.version);
    unionArea.value = scoringRequest.unionArea;
    temporalIOU.value = scoringRequest.temporalIOU;
    statusAnnotated.value = scoringRequest.statusAnnotated;
}
retrieveScoring();

</script>

<template>
  <span class="pb-5">
    <v-row
      dense
      justify="center"
      align="center"
    >
      <v-col v-if="unionArea">
        <span> Union Area:</span>
        <span> {{ unionArea?.toFixed(6) }}</span>
      </v-col>
      <v-col v-if="statusAnnotated">
        <span> Status:</span>
        <span> {{ statusAnnotated }}</span>
      </v-col>
      
    </v-row>
    <h3
      v-if="temporalIOU"
      class="mt-3"
    > Temporal IOU</h3>
    <v-container>
      <v-row
        v-if="temporalIOU"
        dense
        justify="center"
        align="center"
      >
        <v-col v-if="temporalIOU.site_preparation">
          <span> Site Prep: </span>
          <span> {{ parseFloat(temporalIOU.site_preparation).toFixed(6) }}</span>
        </v-col>      
      </v-row>
      <v-row
        v-if="temporalIOU"
        dense
        justify="center"
        align="center"
      >
        <v-col v-if="temporalIOU.active_construction">
          <span> Active: </span>
          <span> {{ parseFloat(temporalIOU.active_construction).toFixed(6) }}</span>
        </v-col>      
      </v-row>
      <v-row
        v-if="temporalIOU"
        dense
        justify="center"
        align="center"
      >
        <v-col v-if="temporalIOU.post_construction">
          <span> Post: </span>
          <span> {{ parseFloat(temporalIOU.post_construction).toFixed(6) }}</span>
        </v-col>      
      </v-row>
    </v-container>
    
  </span>
</template>