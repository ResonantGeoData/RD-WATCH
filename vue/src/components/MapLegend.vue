<script setup lang="ts">

import { annotationLegend } from '../mapstyle/annotationStyles';
import { state } from '../store';
</script>

<template>
  <v-row v-if="state.mapLegend">
    <v-card>
      <v-card-title>Legend</v-card-title>
      <v-card-text>
        <v-card>
          <v-row dense>
            <v-card style="height:150px">
              <v-card-title>
                Site Evaluations
              </v-card-title>
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
                    <span class="pl-1">
                      :{{ item.name }}
                    </span>
                  </v-row>
                </v-col>
              </v-row>
            </v-card>
            <v-card>
              <v-card-title>
                Scoring
              </v-card-title>
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
                    <span class="pl-1">
                      :{{ item.name }}
                    </span>
                  </v-row>
                </v-col>
              </v-row>
            </v-card>
          </v-row>
        </v-card>
      </v-card-text>
    </v-card>
  </v-row>
</template>

<style>

.color-icon {
  min-width: 15px;
  max-width: 15px;
  min-height: 15px;
  max-height: 15px;;
}
</style>
