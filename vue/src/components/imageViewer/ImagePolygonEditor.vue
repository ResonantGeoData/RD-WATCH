<script setup lang="ts">
import { Ref, computed, ref, watch, withDefaults } from "vue";
import { ApiService } from "../../client";
import { state } from '../../store'

interface Props {
    siteEvalId: string;
    evalGeoJSON: GeoJSON.Polygon | null | GeoJSON.Point;
    samViewer: null | number;
}
const props = withDefaults(defineProps<Props>(), {
});

const emit = defineEmits<{
  (e: "clear-storage"): void;
  (e: "update-list"): void;
  (e: 'save'): void;
}>();


const editingGeoJSON = ref(false);
const evaluationGeoJSON: Ref<GeoJSON.Polygon | GeoJSON.Point |  null> = ref(props.evalGeoJSON); // holds the site geoJSON so it can be edited


watch([() => props.siteEvalId], () => {
  cancelEditingGeoJSON();
  evaluationGeoJSON.value = props.evalGeoJSON;
  
  
});
watch(() => props.evalGeoJSON, () => {
  evaluationGeoJSON.value = props.evalGeoJSON;
})

watch(() => state.filters.editingGeoJSONSiteId, () => {
  if (state.filters.editingGeoJSONSiteId !== null) {
    editingGeoJSON.value = true;
  } else {
    editingGeoJSON.value = false;
  }
});

const startEditingGeoJSON = () => {
  state.filters.editingGeoJSONSiteId = props.siteEvalId;
  if (state.editGeoJSON && evaluationGeoJSON.value) {
    state.editGeoJSON.setGeoJSONEdit(evaluationGeoJSON.value);
    editingGeoJSON.value = true;
  }
}

const cancelEditingGeoJSON = () => {
  state.filters.editingGeoJSONSiteId = null;
  if (state.editGeoJSON && evaluationGeoJSON.value) {
    state.editGeoJSON.cancelGeoJSONEdit();
    editingGeoJSON.value = false;
  }
}

const saveEditingGeoJSON = async () => {
  if (state.editGeoJSON) {
    const polyGeoJSON = state.editGeoJSON.getEditingGeoJSON();
    if (polyGeoJSON) {
      evaluationGeoJSON.value = polyGeoJSON;
      await ApiService.patchSiteEvaluation(props.siteEvalId, { geom: polyGeoJSON });
      cancelEditingGeoJSON();
      emit('clear-storage');
    }
  }
}
const selectedPoints = computed(() => state.editGeoJSON && (state.editGeoJSON.selectedPoints).length);

const deleteSelectedPoints = () => {
  if (state.editGeoJSON && selectedPoints.value) {
    state.editGeoJSON.deleteSelectedPoints();
  }
}

console.log(evaluationGeoJSON.value);
console.log(editingGeoJSON.value);
</script>

<template>
  <v-row class="pt-3">
    <v-spacer />
    <v-col>
      <v-btn
        size="small"
        :disabled="editingGeoJSON || !(evaluationGeoJSON)"
        @click="startEditingGeoJSON()"
      >
        Edit GeoJSON
      </v-btn>
    </v-col>
    <v-spacer />
  </v-row>
  <v-row
    v-if="editingGeoJSON"
    class="pt3"
  >
    <v-spacer />
    <h3 style="display:inline">
      GeoJSON:
    </h3>
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

    <v-btn
      size="small"
      color="error"
      class="mx-2"
      @click="cancelEditingGeoJSON()"
    >
      Cancel
    </v-btn>
    <v-btn
      size="small"
      color="success"
      class="mx-2"
      @click="saveEditingGeoJSON()"
    >
      Save
    </v-btn>
    <v-spacer />
  </v-row>
</template>
