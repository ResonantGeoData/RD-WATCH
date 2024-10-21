<script setup lang="ts">
import { Ref, computed, ref, watch } from "vue";
import { ApiService } from "../../client";
import { state, updateRegionList } from "../../store";



const scoringApp = computed(()=> ApiService.getApiPrefix().includes('scoring'));





const toggleRegion = () => {
  const val = !state.filters.drawRegionPoly;
  state.filters = { ...state.filters, drawRegionPoly: val };
}

const addRegion = () => {
  state.filters.addingRegionPolygon = true;
}

const deleteRegion = async () => {
  if (state.filters.regions?.length) {
    const regionDetails = state.regionMap[state.filters.regions[0]];
    if (regionDetails !== undefined) {
      const result = await ApiService.deleteRegionModel(regionDetails.id)
      if (result.success) {
        state.filters = { ...state.filters, regions: undefined };
      }
      await updateRegionList();
    }
  }
}

const downloadRegionModel = () => {
  if (state.filters.regions?.length) {
    const regionDetails = state.regionMap[state.filters.regions[0]];
    if (regionDetails !== undefined) {
    const url = `/api/regions/${regionDetails.id}/download`;
    window.location.assign(url);
    }
  }
};


const getRegionInfo: Ref<false | {id: number, deleteBlock?: string; hasGeom?: boolean}> = ref(false);
watch(() => state.filters.regions?.length, () => {
  if (state.filters.regions && state.filters.regions.length) {
    const regionData = state.regionMap[state.filters.regions[0]]
    if (regionData) {
      getRegionInfo.value = regionData;
      return;
    }
  }
  getRegionInfo.value = false;
});

</script>

<template>
  <v-menu
    open-on-hover
  >
    <template #activator="{ props }">
      <v-btn
        v-bind="props"
        class="px-2 mx-2"
        :color="state.filters.drawRegionPoly ? 'primary' : ''"
        @click="getRegionInfo && getRegionInfo.hasGeom && toggleRegion()"
      >
        <v-icon
          :color="state.filters.drawRegionPoly ? 'white' : ''"
          size="x-large"
        >
          mdi-select
        </v-icon>
        <v-icon
          :color="state.filters.drawRegionPoly ? 'white' : 'black'"
          size="large"
        >
          mdi-menu-down
        </v-icon>
      </v-btn>
    </template>
    <v-card outlined>
      <v-list>
        <v-list-item
          value="Region"
          :class="{'disabled-item': !getRegionInfo || !getRegionInfo.hasGeom }"
          :disabled="!getRegionInfo || !getRegionInfo.hasGeom"
          @click="toggleRegion()"
        >
          <div
            class="layer-text"
          >
            Region
          </div>
          <v-checkbox-btn
            :model-value="state.filters.drawRegionPoly "
            density="compact"
            :disabled="!getRegionInfo || !getRegionInfo.hasGeom"
            hide-details
            readonly
            class="item-checkbox"
          />
        </v-list-item>
        <v-tooltip v-if="!scoringApp">
          <template #activator="{ props }">
            <v-list-item
              value="deleteRegion"
              v-bind="props"
              :class="{'disabled-item': !getRegionInfo || !getRegionInfo.hasGeom || !!getRegionInfo.deleteBlock }"
              :disabled="!getRegionInfo || !getRegionInfo.hasGeom || !!getRegionInfo.deleteBlock "
              @click="deleteRegion()"
            >
              <v-row dense>
                <div
                  class="layer-text"
                >
                  Delete
                </div>
                <v-spacer />
                <v-icon color="error">
                  mdi-delete
                </v-icon>
              </v-row>
            </v-list-item>
          </template>
          <v-alert v-if="getRegionInfo && getRegionInfo.deleteBlock">
            {{ getRegionInfo.deleteBlock }}
          </v-alert>
          <v-alert v-if="getRegionInfo && !getRegionInfo.hasGeom">
            Cannot Delete the region because there is no geometry
          </v-alert>
          <span>Delete the region</span>
        </v-tooltip>
        <v-tooltip v-if="!scoringApp">
          <template #activator="{ props }">
            <v-list-item
              value="downloadRegion"
              v-bind="props"
              :class="{'disabled-item': !getRegionInfo || !getRegionInfo.hasGeom }"
              :disabled="!getRegionInfo || !getRegionInfo.hasGeom"
              @click="downloadRegionModel()"
            >
              <v-row dense>
                <div
                  class="layer-text"
                >
                  Download
                </div>
                <v-spacer />
                <v-icon>
                  mdi-download
                </v-icon>
              </v-row>
            </v-list-item>
          </template>

          <v-alert v-if="getRegionInfo && !getRegionInfo.hasGeom">
            Cannot Download the region because there is no geometry
          </v-alert>
          <span>Download the region geometry</span>
        </v-tooltip>
        <v-list-item
          v-if="!scoringApp"
          value="addRegion"
          @click="addRegion()"
        >
          <v-row dense>
            <div
              class="layer-text"
            >
              Add Region
            </div>
            <v-spacer />
            <v-icon>
              mdi-plus
            </v-icon>
          </v-row>
        </v-list-item>
      </v-list>
    </v-card>
  </v-menu>
</template>

<style scoped>
.base {
    position: absolute;
    left: 650px;
    top:8px;
    margin-left: 10px;
}
.button-label {
    font-size: 8px;
}

.layer-text {
  text-transform: uppercase;
  font-size: 16px;
  display: inline;
  margin-left: 5px;
}

.layer-icon {
  color: #FFFFFF !important;
  background-color: #37474F;
  min-width: 30px !important;
  width:30px !important;
  height: 30px !important;
  min-height: 30px !important;
  max-width: 30px !important;
  max-height: 30px !important;
  border-radius: 5px !important;
  font-size: 20px !important;
  text-align: center !important;
  font-weight: 800 !important;
  line-height: 30px !important;
  display: inline;
}

.rootItem {
  border-bottom: 1px solid gray;
  height: 35px;
}

.item-checkbox {
  display:inline;
  float:right;
}

.disabled-item {
  background-color: gray;
  color: lightgray;
  cursor:not-allowed;
}
</style>
