<script setup lang="ts">

import { annotationLegend } from '../mapstyle/annotationStyles';
import { state } from '../store';
</script>

<template>
  <div
    v-if="state.mapLegend"
    class="legend"
  >
    <v-card density="compact">
      <v-card-title
        :class="{'legend-title-single': !state.filters.scoringColoring, 'legend-title': state.filters.scoringColoring}"
      >
        Legend
      </v-card-title>
      <v-card-text>
        <v-row dense>
          <v-card density="compact">
            <v-card-title
              class="legend-title"
              :class="{'legend-title-single': !state.filters.scoringColoring}"
            >
              Site Evaluations
            </v-card-title>
            <v-card-text>
              <v-row dense>
                <v-col>
                  <v-row
                    v-for="item in annotationLegend.observationLegend"
                    :key="item.name"
                    align="center"
                    class="px-5"
                  >
                    <span
                      :style="`background-color: ${item.color}`"
                      class="color-icon pr-1"
                    />
                    <span
                      class="pl-1 legend-label"
                      :class="{'legend-label-single': !state.filters.scoringColoring}"
                    >
                      :{{ item.name }}
                    </span>
                  </v-row>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
          <v-card
            v-if="state.filters.scoringColoring"
            density="compact"
          >
            <v-card-title class="legend-title">
              Scoring
            </v-card-title>
            <v-card-text>
              <v-row dense>
                <v-col>
                  <v-row
                    v-for="item in annotationLegend.scoringLegend"
                    :key="item.name"
                    align="center"
                    class="px-5"
                  >
                    <span
                      :style="`background-color: ${item.color}`"
                      class="color-icon pr-1"
                    />
                    <span class="pl-1 legend-label">
                      :{{ item.name }}
                    </span>
                  </v-row>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-row>
      </v-card-text>
    </v-card>
  </div>
</template>

<style>
.legend {
  max-width: 400px;
}
.legend-title {
  font-size:0.75em !important;
}
.legend-label {
  font-size: 0.75em;
}
.legend-title-single {
  font-size:1em !important;
}
.legend-label-single {
  font-size: 1em;
}
.color-icon {
  min-width: 15px;
  max-width: 15px;
  min-height: 15px;
  max-height: 15px;;
}
</style>
