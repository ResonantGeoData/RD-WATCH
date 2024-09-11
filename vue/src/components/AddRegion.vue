<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { state, updateRegionList, updateRegionMap } from "../store";
import { ApiService, RegionUpload } from "../client/services/ApiService";
import maplibregl from "maplibre-gl";


onMounted(() => {
  if (state.editGeoJSON) {
    state.editGeoJSON.setGeoJSONNew('Polygon');
  }
  publicRegionId.value = true;
  regionId.value = 'Custom RegionId'
});


const regionId = ref("");
const publicRegionId = ref(true);
const deleteSelectedPoints = () => {
  if (state.editGeoJSON && selectedPoints.value) {
    state.editGeoJSON.deleteSelectedPoints();
  }
};
const selectedPoints = computed(
  () => state.editGeoJSON && state.editGeoJSON.selectedPoints.length
);

const polygonExists = computed(() => state.editGeoJSON && state.editGeoJSON.getEditingGeoJSON());



const cancel = () => {
  state.editGeoJSON?.cancelGeoJSONEdit();
  state.filters.addingRegionPolygon = undefined;
};

const addRegion = async () => {
  // build up the SiteModel
  if (state.editGeoJSON) {
    const polyGeoJSON = state.editGeoJSON.getEditingGeoJSON();
    if (polyGeoJSON) {
        const regionUpload: RegionUpload = {
          type: "FeatureCollection",
          features: [
            {
              type: "Feature",
              properties: {
                type: "region",
                region_id: regionId.value,
                start_date: null,
                end_date: null,
                mgrs: "52SDG",
                originator: 'custom',
              },
              geometry: polyGeoJSON,
            },
          ],
        };
        await ApiService.addRegionModel(regionUpload);
        maplibregl.clearStorage();
        // We need to update the source to get information
        // This reloads the source vector-tile to color it properly after data has been changed.
        state.filters.randomKey = `?randomKey=randomKey_${Math.random() * 1000}`; 
        state.editGeoJSON.cancelGeoJSONEdit();
        state.filters.addingRegionPolygon = undefined;
        await updateRegionList();
        await updateRegionMap();
    }
  }
};
</script>

<template>
  <v-card>
    <v-card-title>
      <v-row>
        <h5>Add Region</h5>
        <v-spacer />
      </v-row>
    </v-card-title>
    <v-card-text class="pt-3">
      <v-row>
        <ul>
          <li>Begin by clicking on the screen to add a point.</li>
          <li>Complete the polygon by double clicking.</li>
          <li>Right click to Edit the polygon after complettion</li>
        </ul>
      </v-row>
      <v-row>
        <v-text-field
          v-model="regionId"
          label="Region Id"
          :rules="[v => v !== '' || 'Must contain Region Id']"
        />
      </v-row>
      <v-row>
        <v-checkbox
          v-model="publicRegionId"
          label="Public"
        />
      </v-row>
      <v-btn
        v-if="selectedPoints"
        size="small"
        color="error"
        class="mx-2"
        @click="deleteSelectedPoints()"
      >
        <v-icon>mdi-delete</v-icon>
        points
      </v-btn>
    </v-card-text>
    <v-card-actions>
      <v-row dense>
        <v-spacer />
        <v-btn
          color="error"
          variant="flat"
          class="mx-3"
          @click="cancel()"
        >
          Cancel
        </v-btn>
        <v-btn
          color="success"
          variant="flat"
          :disabled="!polygonExists"
          class="mx-3"
          @click="addRegion()"
        >
          Save
        </v-btn>
        <v-spacer />
      </v-row>
    </v-card-actions>
  </v-card>
</template>

