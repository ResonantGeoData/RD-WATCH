<script setup lang="ts">
import { Ref, onMounted, ref, watch } from "vue";
import { ApiService, ScoringResults } from "../client/services/ApiService";
import { union } from "lodash";

interface PopUpData {
  siteId: string;
  siteColor: string;
  score: number;
  groundTruth: boolean;
  scoreColor: string;
  area: string;
  annotatedStatus?: ScoringResults['statusAnnotated'];
  unionArea?: ScoringResults['unionArea'];
  temporalIOU?: ScoringResults['temporalIOU'];
}

const data: PopUpData[] = [];



</script>

<template>
  <v-card dense>
    <v-row
      v-for="item in data"
      :key="item.siteId"
      dense
      align="center"
      justify="center"
      class="ma-5"
    >
      <v-chip
        label
        :color="item.siteColor"
        class="mx-2"
      >
        <v-icon
          v-if="item.groundTruth"
          size="small"
          :color="item.siteColor"
        >
          mdi-check-decagram
        </v-icon>
        SiteId: {{ item.siteId }}
      </v-chip>
      <v-chip
        label
        :color="item.scoreColor"
        class="mx-2"
      >
        Score: {{ item.score.toFixed(2) }}
      </v-chip>
      <v-chip
        label
        color="black"
        variant="elevated"
        class="mx-2"
      >
        Area: {{ item.area }}m²
      </v-chip>
      <v-row
        v-if="item.unionArea && item.temporalIOU"
        class="pa-5"
        align="center"
        justify="center"
      >
        <h6>Scoring:</h6>
        <v-chip
          label
          color="black"
          variant="elevated"
          size="small"
          class="mx-2"
        >
          Union Area: {{ item.unionArea.toFixed(6) }}
        </v-chip>
        <v-chip
          label
          color="black"
          variant="elevated"
          size="small"
          class="mx-2"
        >
          Status: {{ item.annotatedStatus }}
        </v-chip>
      </v-row>
      <v-row
        v-if="item.temporalIOU
          && (
            item.temporalIOU.active_construction !== null ||
            item.temporalIOU.post_construction !== null ||
            item.temporalIOU.site_preparation !== null
          )"
        align="center"
        justify="center"
      >
        <h6> Temporal IOU:</h6>
        <v-chip
          v-if="item.temporalIOU && item.temporalIOU.site_preparation !== null"
          label
          color="black"
          variant="elevated"
          size="small"
          class="mx-2"
        >
          Prep: {{ parseFloat(item.temporalIOU.site_preparation).toFixed(6) }}
        </v-chip>

        <v-chip
          v-if="item.temporalIOU && item.temporalIOU.active_construction !== null"
          label
          color="black"
          variant="elevated"
          size="small"
          class="mx-2"
        >
          Active: {{ parseFloat(item.temporalIOU.active_construction).toFixed(6) }}
        </v-chip>
        <v-chip
          v-if="item.temporalIOU && item.temporalIOU.post_construction !== null"
          label
          color="black"
          variant="elevated"
          size="small"
          class="mx-2"
        >
          Post: {{ parseFloat(item.temporalIOU.post_construction).toFixed(6) }}
        </v-chip>
      </v-row>
    </v-row>
  </v-card>
</template>
