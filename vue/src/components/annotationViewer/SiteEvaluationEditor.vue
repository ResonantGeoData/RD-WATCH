<script setup lang="ts">
import { Ref, computed, ref, watch } from "vue";
import { ApiService } from "../../client";
import { styles } from "../../mapstyle/annotationStyles";
import { state } from "../../store";

const props = defineProps<{
  siteEval: number;
}>();
const regionList = ref(Object.values(state.regionMap));
const selectedRegion = ref(null);
const labelList = computed(() => styles.filter((item) => item.labelType === 'observation').map((item) => item.label));
const selectedLabel = ref(null);
const notes = ref('');
</script>

<template>
  <v-card>
    <v-card-title> Site Evaluation Editor</v-card-title>
    <v-card-text>
      <v-row dense>
        <v-select
          v-model="selectedRegion"
          :items="regionList"
          label="Region"
          class="mx-2"
        />
        <v-select
          v-model="selectedLabel"
          :items="labelList"
          label="Label"
          class="mx-2"
        />
      </v-row>
      <v-row dense>
        <v-col>
          <h6>Start Date:</h6>
          <v-date-picker />
        </v-col>
        <v-col>
          <h6>End Date:</h6>
          <v-date-picker />
        </v-col>
      </v-row>
      <v-row dense>
        <v-textarea
          v-model="notes"
          label="Notes"
        />
      </v-row>
    </v-card-text>
  </v-card>
</template>
