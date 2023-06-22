<script setup lang="ts">
import { Ref, ref, } from "vue";
import { ApiService } from "../../client";
import { annotationLegend } from "../../mapstyle/annotationStyles";
import { SiteObservation } from "../../store";

const props = defineProps<{
  siteObservation: SiteObservation;
}>();


const unionArea: Ref<null | number> = ref(null);
const temporalIOU: Ref<null | {site_preparation: string; active_construction: string; post_construction: string}> = ref(null);
const statusAnnotated: Ref<null | string> = ref(null);
const color: Ref<null | string> = ref(null);
const retrieveScoring = async () => {
    const scoreData = props.siteObservation.scoringBase;
    const scoringRequest = await ApiService.getScoringDetails(scoreData.configurationId, scoreData.regionId, scoreData.siteNumber, scoreData.version);
    unionArea.value = scoringRequest.unionArea;
    temporalIOU.value = scoringRequest.temporalIOU;
    statusAnnotated.value = scoringRequest.statusAnnotated;
    color.value = scoringRequest.color || null;
}
const getScoringLabel = (sampleColor: string) => {
  const index = annotationLegend.scoringLegend.findIndex((item) => item.color === sampleColor);
  if (index !== -1) {
    return annotationLegend.scoringLegend[index].name;
  }
  return '';
}
function standardize_color(str: string){
  const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d');
    let result = ''
    if (ctx){
    ctx.fillStyle = str;
    result = ctx.fillStyle;
    }
    canvas.remove();
    return result;
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
        <b> Union Area:</b>
        <span> {{ unionArea?.toFixed(6) }}</span>
      </v-col>
      <v-col v-if="statusAnnotated">
        <b> Status:</b>
        <span> {{ statusAnnotated }}</span>
      </v-col>      
    </v-row>
    <v-row
      v-if="color"
      dense
      justify="center"
      align="center"
    >
      <v-col v-if="unionArea">
        <b> Scoring Status:</b>
        <v-chip
          :color="standardize_color(color)"
          class="mx-2"
        > {{ getScoringLabel(color) }}</v-chip>
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