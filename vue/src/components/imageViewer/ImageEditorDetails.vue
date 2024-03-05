<script setup lang="ts">
import { Ref, computed, ref, watch, withDefaults } from "vue";
import { ApiService } from "../../client";
import { SiteModelStatus } from "../../client/services/ApiService";
import { getColorFromLabel, styles } from '../../mapstyle/annotationStyles';
import { state } from '../../store'
import { EvaluationImageResults } from "../../types";

type EditModes = 'SiteEvaluationLabel' | 'StartDate' | 'EndDate' | 'SiteObservationLabel' | 'SiteEvaluationNotes' | 'SiteObservationNotes'

interface Props {
    siteEvalId: string;
    editable: boolean;
    dateRange?: number[] | null;
    groundTruth: EvaluationImageResults['groundTruth'] | null;
    hasGroundTruth: boolean;
    evaluationLabel: string;
    evaluationNotes: string;
    evalCurrentDate: string;
    status: string | null;
    evalGeoJSON: GeoJSON.Polygon | null;
    currentTimestamp: string;
    samViewer: null | number;
}
const props = withDefaults(defineProps<Props>(), {
  dateRange: null,
});

const emit = defineEmits<{
  (e: "clear-storage"): void;
  (e: "update-list"): void;
  (e: 'cancel'): void;
  (e: 'save'): void;
}>();

const editMode = ref(props.editable);

const editDialog = ref(false);
const currentEditMode: Ref<null | EditModes> = ref(null);
const siteEvaluationLabel = ref(props.evaluationLabel);
const startDate: Ref<string|null> = ref(props.dateRange && props.dateRange[0] ? new Date(props.dateRange[0] * 1000).toISOString().split('T')[0] : null);
const endDate: Ref<string|null> = ref(props.dateRange && props.dateRange[1] ? new Date(props.dateRange[1] * 1000).toISOString().split('T')[0] : null);
const siteEvaluationList = computed(() => Object.entries(styles).filter(([, { type }]) => type === 'sites').map(([label]) => label));
const siteEvaluationNotes = ref(props.evaluationNotes);
const siteEvaluationUpdated = ref(false)
const siteStatus: Ref<string | null> = ref(null);
const startDateTemp: Ref<string | null> = ref(null);
const endDateTemp: Ref<string | null> = ref(null);
const currentDate = ref(props.evalCurrentDate);
const editingPolygon = ref(false);
const evaluationGeoJSON: Ref<GeoJSON.Polygon | null> = ref(props.evalGeoJSON); // holds the site geoJSON so it can be edited

watch(() => props.editable, () => {
  editMode.value = props.editable;
})

watch([() => props.siteEvalId], () => {
  cancelEditingPolygon();
  siteEvaluationLabel.value = props.evaluationLabel;
  siteEvaluationNotes.value = props.evaluationNotes;
  startDate.value = props.dateRange && props.dateRange[0] ? new Date(props.dateRange[0] * 1000).toISOString().split('T')[0] : null;
  endDate.value = props.dateRange && props.dateRange[1] ? new Date(props.dateRange[1] * 1000).toISOString().split('T')[0] : null;
  currentDate.value = props.evalCurrentDate;
  siteStatus.value = props.status;
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


  // eslint-disable-next-line @typescript-eslint/no-explicit-any
const updateTime = (time: any, date: 'StartDate' | 'EndDate'| 'StartDateTemp' | 'EndDateTemp') => {
  if (time === null) {
    if (date === 'StartDate') {
      startDate.value = null;
    } else if (date === 'EndDate') {
      endDate.value = null
    } else if (date === 'StartDateTemp') {
      startDateTemp.value = null;
    }  else if (date === 'EndDateTemp') {
      endDateTemp.value = null;
    }
    editDialog.value = false;
  } else {
    if (date === 'StartDate') {
      startDate.value = new Date(time as string).toISOString().split('T')[0];
    } else if (date === 'EndDate') {
      endDate.value = new Date(time as string).toISOString().split('T')[0];
    } else if (date === 'StartDateTemp') {
      startDateTemp.value = new Date(time as string).toISOString().split('T')[0];
    } else if (date === 'EndDateTemp') {
      endDateTemp.value = new Date(time as string).toISOString().split('T')[0];
    }
  }
  siteEvaluationUpdated.value = true;
}

const setEditingMode = (mode: EditModes) => {
  if (['StartDate', 'EndDate'].includes(mode)){
    if (startDate.value === null) {
      startDateTemp.value = currentDate.value;
    } else {
      startDateTemp.value = startDate.value;
    }
    if (endDate.value === null) {
      endDateTemp.value = currentDate.value;
    } else {
      endDateTemp.value = endDate.value;
    }
  }
  editDialog.value = true;
  currentEditMode.value = mode;
}


const saveSiteEvaluationChanges = async () => {
 await  ApiService.patchSiteEvaluation(props.siteEvalId, {
    label: siteEvaluationLabel.value,
    start_date: startDate.value,
    end_date: endDate.value,
    notes: siteEvaluationNotes.value ? siteEvaluationNotes.value : undefined,
  });
  siteEvaluationUpdated.value = false;
  emit('clear-storage');
  // reset cache after changing siteEvals for vector tiles
  emit('update-list');
}

const setSiteModelStatus = async (status: SiteModelStatus) => {
  if (status) {
    await ApiService.patchSiteEvaluation(props.siteEvalId, {
      status
    });
    siteStatus.value = status;
    emit('update-list');
  }
}

const startEditingPolygon = () => {
  state.filters.editingPolygonSiteId = props.siteEvalId;
  if (state.editPolygon && evaluationGeoJSON.value) {
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
  <v-col>
    <div>
      <b class="mr-1">Date Range:</b>
      <span> {{ startDate ? startDate : 'null' }}
        <v-icon
          v-if="editMode && samViewer === null"
          class="ma-0"
          @click="setEditingMode('StartDate')"
        >
          mdi-pencil
        </v-icon>

      </span>
      <span class="mx-1"> to</span>
      <span> {{ endDate ? endDate : 'null' }}
        <v-icon
          v-if="editMode && samViewer === null"
          class="ma-0"
          @click="setEditingMode('EndDate')"
        >
          mdi-pencil
        </v-icon>

      </span>
    </div>
    <div v-if="groundTruth && hasGroundTruth">
      <b class="mr-1">Date Range:</b>
      <span> {{ new Date(groundTruth.timerange.min * 1000).toISOString().split('T')[0] }}
        <v-icon
          class="ma-0"
          color="white"
        />
      </span>
      <span class="mx-1"> to</span>
      <span> {{ new Date(groundTruth.timerange.max * 1000).toISOString().split('T')[0] }}</span>
    </div>
  </v-col>
  <v-col>
    <div class="ml-5">
      <b>Label:</b>
      <v-chip
        size="small"
        :color="getColorFromLabel(siteEvaluationLabel)"
        class="ml-2"
      >
        {{ siteEvaluationLabel }}
      </v-chip>
      <v-icon
        v-if="editMode && samViewer === null"
        @click="setEditingMode('SiteEvaluationLabel')"
      >
        mdi-pencil
      </v-icon>
    </div>
    <div
      v-if="hasGroundTruth && groundTruth"
      class="ml-5"
    >
      <b>Label:</b>
      <v-chip
        size="small"
        :color="getColorFromLabel(groundTruth.label)"
        class="ml-2"
      >
        {{ groundTruth.label }}
      </v-chip>
    </div>
  </v-col>
  <v-col>
    <div class="notesPreview">
      <b>Notes:</b>
      <v-icon
        v-if="editMode && samViewer === null"
        @click="setEditingMode('SiteEvaluationNotes')"
      >
        mdi-pencil
      </v-icon>
      <v-tooltip
        :text="siteEvaluationNotes"
        location="bottom center"
      >
        <template #activator="{ props }">
          <span v-bind="props"> {{ siteEvaluationNotes }}</span>
        </template>
      </v-tooltip>
    </div>
  </v-col>
  <v-spacer />
  <v-col v-if="!siteEvaluationUpdated && editMode ">
    <v-btn
      v-if="!editingPolygon && samViewer === null"
      size="small"
      :disabled="editingPolygon"
      @click="startEditingPolygon()"
    >
      Edit Polygon
    </v-btn>
    <span
      v-if="editingPolygon"
    >
      <h3 style="display:inline">Polygon:</h3>
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
    </span>
  </v-col>
  <v-col v-if="!editingPolygon && editMode && samViewer === null">
    <v-btn
      v-if="siteEvaluationUpdated"
      size="small"
      color="success"
      @click="saveSiteEvaluationChanges"
    >
      Save Changes
    </v-btn>
    <v-btn
      v-if="siteStatus !== 'APPROVED'"
      size="small"
      class="mx-1"
      color="success"
      @click="setSiteModelStatus('APPROVED')"
    >
      Approve
    </v-btn>
    <v-btn
      v-if="siteStatus === 'APPROVED'"
      size="small"
      class="mx-1"
      color="warning"
      @click="setSiteModelStatus('PROPOSAL')"
    >
      Un-Approve
    </v-btn>
    <v-btn
      v-if="siteStatus !== 'REJECTED'"
      size="small"
      class="mx-1"
      color="error"
      @click="setSiteModelStatus('REJECTED')"
    >
      Reject
    </v-btn>
    <v-btn
      v-if="siteStatus === 'REJECTED'"
      size="small"
      class="mx-1"
      color="warning"
      @click="setSiteModelStatus('PROPOSAL')"
    >
      Un-Reject
    </v-btn>
  </v-col>
  <v-dialog
    v-model="editDialog"
    width="400"
  >
    <v-card v-if="currentEditMode === 'SiteEvaluationLabel'">
      <v-card-title>Edit Site Model Label</v-card-title>
      <v-card-text>
        <v-select
          v-model="siteEvaluationLabel"
          :items="siteEvaluationList"
          label="Label"
          class="mx-2"
        />
      </v-card-text>
      <v-card-actions>
        <v-row dense>
          <v-btn
            color="error"
            class="mx-3"
            @click="editDialog = false"
          >
            Cancel
          </v-btn>
          <v-btn
            color="success"
            class="mx-3"
            @click="editDialog = false; siteEvaluationUpdated = true"
          >
            Save
          </v-btn>
        </v-row>
      </v-card-actions>
    </v-card>
    <v-card v-if="currentEditMode === 'StartDate'">
      <v-card>
        <v-card-title>Observation Time</v-card-title>
        <v-card-text>
          <v-row
            dense
            justify="center"
          >
            <v-btn
              color="error"
              class="mb-2 mx-1"
              size="small"
              @click="updateTime(null, 'StartDate'); editDialog=false"
            >
              Set Time to Null
            </v-btn>
            <v-btn
              color="primary"
              class="mb-2 mx-1"
              size="small"
              @click="updateTime(currentDate, 'StartDate'); editDialog=false"
            >
              Current: {{ currentDate }}
            </v-btn>
          </v-row>
          <v-date-picker
            v-if="startDateTemp !== null"
            :model-value="[startDateTemp ? startDateTemp : currentTimestamp]"
            @update:model-value="updateTime($event, 'StartDate')"
            @click:cancel="editDialog = false"
            @click:save="editDialog = false"
          />
        </v-card-text>
      </v-card>
    </v-card>
    <v-card v-if="currentEditMode === 'EndDate'">
      <v-card>
        <v-card-title>Observation Time</v-card-title>
        <v-card-text>
          <v-row
            dense
            justify="center"
          >
            <v-btn
              color="error"
              class="mb-2 mx-1"
              size="small"
              @click="updateTime(null, 'EndDate'); editDialog=false"
            >
              Set Time to Null
            </v-btn>
            <v-btn
              color="primary"
              class="mb-2 mx-1"
              size="small"
              @click="updateTime(currentDate, 'EndDate'); editDialog=false"
            >
              Current: {{ currentDate }}
            </v-btn>
          </v-row>
          <v-date-picker
            v-if="endDateTemp !== null"
            :model-value="[endDateTemp ? endDateTemp : currentTimestamp]"
            @update:model-value="updateTime($event, 'EndDate')"
            @click:cancel="editDialog = false"
            @click:save="editDialog = false"
          />
        </v-card-text>
      </v-card>
    </v-card>
    <v-card v-if="currentEditMode === 'SiteEvaluationNotes'">
      <v-card-title>Edit Site Model Notes</v-card-title>
      <v-card-text>
        <v-textarea
          v-model="siteEvaluationNotes"
          label="Notes"
        />
      </v-card-text>
      <v-card-actions>
        <v-row dense>
          <v-spacer />
          <v-btn
            color="error"
            class="mx-3"
            @click="editDialog = false"
          >
            Cancel
          </v-btn>
          <v-btn
            color="success"
            class="mx-3"
            @click="editDialog = false; siteEvaluationUpdated = true"
          >
            Save
          </v-btn>
        </v-row>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.notesPreview {
  min-width: 150px;
  max-width: 150px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>