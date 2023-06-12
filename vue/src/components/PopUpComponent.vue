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
      >
      <h6>Scoring:</h6>
        <v-chip
          label
          color="black"
          variant="elevated"
          class="mx-2"
        >
          Union Area: {{ item.unionArea }}
        </v-chip>
        <v-chip
          label
          color="black"
          variant="elevated"
          class="mx-2"
        >
          Status: {{ item.annotatedStatus }}
        </v-chip>
        <v-chip
          v-if="item.temporalIOU"
          label
          color="black"
          variant="elevated"
          class="mx-2"
        >
          Active: {{ item.temporalIOU.active_construction }}
        </v-chip>
        <v-chip
          label
          color="black"
          variant="elevated"
          class="mx-2"
        >
          Post: {{ item.temporalIOU?.post_construction }}
        </v-chip>
        <v-chip
          label
          color="black"
          variant="elevated"
          class="mx-2"
        >
          Prep: {{ item.temporalIOU?.site_preparation }}
        </v-chip>

      </v-row>
    </v-row>
  </v-card>
</template>
