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


const editingPolygon = ref(false);
const evaluationGeoJSON: Ref<GeoJSON.Polygon | GeoJSON.Point |  null> = ref(props.evalGeoJSON); // holds the site geoJSON so it can be edited


watch([() => props.siteEvalId], () => {
  cancelEditingPolygon();
  evaluationGeoJSON.value = props.evalGeoJSON;
  
  
});
watch(() => props.evalGeoJSON, () => {
  evaluationGeoJSON.value = props.evalGeoJSON;
})

watch(() => state.filters.editingPolygonSiteId, () => {
  if (state.filters.editingPolygonSiteId !== null) {
    editingPolygon.value = true;
  } else {
    editingPolygon.value = false;
  }
});

const startEditingPolygon = () => {
  state.filters.editingPolygonSiteId = props.siteEvalId;
  if (state.editPolygon && evaluationGeoJSON.value && evaluationGeoJSON.value.type === 'Polygon') {
    state.editPolygon.setPolygonEdit(evaluationGeoJSON.value);
    editingPolygon.value = true;
  }
}

const cancelEditingPolygon = () => {
  state.filters.editingPolygonSiteId = null;
  if (state.editPolygon && evaluationGeoJSON.value) {
    state.editPolygon.cancelPolygonEdit();
    editingPolygon.value = false;
  }
}

const saveEditingPolygon = async () => {
  if (state.editPolygon) {
    const polyGeoJSON = state.editPolygon.getEditingPolygon();
    if (polyGeoJSON) {
      evaluationGeoJSON.value = polyGeoJSON;
      await ApiService.patchSiteEvaluation(props.siteEvalId, { geom: polyGeoJSON });
      cancelEditingPolygon();
      emit('clear-storage');
    }
  }
}
const selectedPoints = computed(() => state.editPolygon && (state.editPolygon.selectedPoints).length);

const deleteSelectedPoints = () => {
  if (state.editPolygon && selectedPoints.value) {
    state.editPolygon.deleteSelectedPoints();
  }
}
</script>

<template>
  <v-row class="pt-3">
    <v-spacer />
    <v-col>
      <v-btn
        size="small"
        :disabled="editingPolygon || !!(evaluationGeoJSON && evaluationGeoJSON.type !== 'Polygon')"
        @click="startEditingPolygon()"
      >
        Edit Polygon
      </v-btn>
    </v-col>
    <v-spacer />
  </v-row>
  <v-row
    v-if="editingPolygon"
    class="pt3"
  >
    <v-spacer />
    <h3 style="display:inline">
      Polygon:
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
      @click="cancelEditingPolygon()"
    >
      Cancel
    </v-btn>
    <v-btn
      size="small"
      color="success"
      class="mx-2"
      @click="saveEditingPolygon()"
    >
      Save
    </v-btn>
    <v-spacer />
  </v-row>
</template>
