<script setup lang="ts">
import { Ref, computed, defineProps, onMounted, ref, withDefaults } from "vue";
import { state } from "../../store";
import { getColorFromLabel, styles } from "../../mapstyle/annotationStyles";
import { useDate } from "vuetify/lib/framework.mjs";
import { ApiService, SiteModelUpload } from "../../client/services/ApiService";

interface Props {
  region?: string;
}
const props = withDefaults(defineProps<Props>(), {
  region: undefined,
});

onMounted(() => {
  if (state.editPolygon) {
    state.editPolygon.setPolygonNew();
  }
  siteId.value = `9999`;
  performer.value = state.modelRuns.length
    ? state.modelRuns[0].performer.short_code.toLocaleLowerCase()
    : "unknown";
});

const dateAdpter = useDate();

type EditModes =
  | "SiteEvaluationLabel"
  | "StartDate"
  | "EndDate"
  | "SiteObservationLabel"
  | "SiteEvaluationNotes"
  | "SiteObservationNotes";

const currentTimestamp = computed(
  () => new Date(state.timestamp * 1000).toISOString().split("T")[0]
);
const startDate: Ref<string | null> = ref(null);
const endDate: Ref<string | null> = ref(null);
const startDateTemp: Ref<string | null> = ref(
  new Date(state.timestamp * 1000).toISOString().split("T")[0]
);
const endDateTemp: Ref<string | null> = ref(
  new Date(state.timestamp * 1000).toISOString().split("T")[0]
);
const editDialog = ref(false);
const currentEditMode: Ref<null | EditModes> = ref(null);
const siteEvaluationList = computed(() =>
  Object.entries(styles)
    .filter(([, { type }]) => type === "sites")
    .map(([label]) => label)
);
const siteEvaluationLabel = ref("Positive Annotated");
const siteId = ref("");
const comments = ref("");
const performer = ref("");
const version = ref("0.0.0");
const deleteSelectedPoints = () => {
  if (state.editPolygon && selectedPoints.value) {
    state.editPolygon.deleteSelectedPoints();
  }
};
const selectedPoints = computed(
  () => state.editPolygon && state.editPolygon.selectedPoints.length
);

const setEditingMode = (mode: EditModes) => {
  if (["StartDate", "EndDate"].includes(mode)) {
    if (startDate.value !== null) {
      startDateTemp.value = startDate.value;
    } else {
      startDateTemp.value = new Date(state.timestamp * 1000)
        .toISOString()
        .split("T")[0];
    }
    if (endDate.value !== null) {
      endDateTemp.value = endDate.value;
    } else {
      endDateTemp.value = new Date(state.timestamp * 1000)
        .toISOString()
        .split("T")[0];
    }
  }
  editDialog.value = true;
  currentEditMode.value = mode;
};

const updateTime = (
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  time: any,
  date: "StartDate" | "EndDate" | "StartDateTemp" | "EndDateTemp"
) => {
  if (time === null) {
    if (date === "StartDate") {
      startDate.value = null;
    } else if (date === "EndDate") {
      endDate.value = null;
    } else if (date === "StartDateTemp") {
      startDateTemp.value = null;
    } else if (date === "EndDateTemp") {
      endDateTemp.value = null;
    }
    editDialog.value = false;
  } else {
    if (date === "StartDate") {
      startDate.value = new Date(time as string).toISOString().split("T")[0];
    } else if (date === "EndDate") {
      endDate.value = new Date(time as string).toISOString().split("T")[0];
    } else if (date === "StartDateTemp") {
      startDateTemp.value = new Date(time as string)
        .toISOString()
        .split("T")[0];
    } else if (date === "EndDateTemp") {
      endDateTemp.value = new Date(time as string).toISOString().split("T")[0];
    }
    editDialog.value = false;
  }
};

const cancel = () => {
  state.editPolygon?.cancelPolygonEdit();
  state.filters.addingSitePolygon = undefined;
};

const addProposal = async () => {
  // build up the SiteModel
  if (state.editPolygon) {
    const polyGeoJSON = state.editPolygon.getEditingPolygon();
    console.log(polyGeoJSON);
    if (polyGeoJSON) {
      const found = Object.entries(styles).find(([, item]) => (item.label === siteEvaluationLabel.value));
      console.log(found);

      if (found) {
        const label = found[0];
        const siteModel: SiteModelUpload = {
          type: "FeatureCollection",
          features: [
            {
              type: "Feature",
              properties: {
                type: "site",
                site_id: `${props.region}_${siteId.value}`,
                region_id: props.region || "unknown",
                originator: performer.value,
                version: version.value,
                mgrs: "52SDG",
                model_content: "proposed",
                start_date: startDate.value,
                end_date: endDate.value,
                comments: comments.value,
                status: label,
              },
              geometry: polyGeoJSON,
            },
          ],
        };
        if (state.modelRuns.length) {
          const modelRunId = state.modelRuns[0].id;
          await ApiService.addSiteModel(modelRunId, siteModel);
        }
      }
    }
  }
};
</script>

<template>
  <v-card>
    <v-card-title>
      <v-row>
        <h5>Add Proposal</h5>
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
        <div class="label">
          <b>Label:</b>
          <v-chip
            size="small"
            :color="getColorFromLabel(siteEvaluationLabel)"
            class="ml-2"
          >
            {{ siteEvaluationLabel }}
          </v-chip>
          <v-icon @click="setEditingMode('SiteEvaluationLabel')">
            mdi-pencil
          </v-icon>
        </div>
      </v-row>
      <v-row>
        <div class="label">
          <b class="mr-1">Start Date:</b>
          <span>
            {{ startDate ? startDate : "null" }}
            <v-icon
              class="ma-0"
              @click="setEditingMode('StartDate')"
            >
              mdi-pencil
            </v-icon>
          </span>
        </div>
      </v-row>
      <v-row>
        <div class="label">
          <b class="mr-1">End Date:</b>
          <span>
            {{ endDate ? endDate : "null" }}
            <v-icon
              class="ma-0"
              @click="setEditingMode('EndDate')"
            >
              mdi-pencil
            </v-icon>
          </span>
        </div>
      </v-row>
      <v-row>
        <v-text-field
          v-model="siteId"
          label="SiteId"
        />
      </v-row>
      <v-row>
        <v-text-field
          v-model="performer"
          label="Performer"
        />
      </v-row>
      <v-row>
        <v-text-field
          v-model="version"
          label="Version"
        />
      </v-row>
      <v-row>
        <v-textarea
          v-model="comments"
          label="Comments"
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
          class="mx-3"
          @click="addProposal()"
        >
          Save
        </v-btn>
      </v-row>
    </v-card-actions>
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
              @click="
                editDialog = false;
                siteEvaluationUpdated = true;
              "
            >
              Save
            </v-btn>
          </v-row>
        </v-card-actions>
      </v-card>
      <v-card v-if="currentEditMode === 'StartDate'">
        <v-card>
          <v-card-title>Site Start Time</v-card-title>
          <v-card-text>
            <v-row
              dense
              justify="center"
            >
              <v-btn
                color="error"
                class="mb-2 mx-1"
                size="small"
                @click="
                  updateTime(null, 'StartDate');
                  editDialog = false;
                "
              >
                Set Time to Null
              </v-btn>
            </v-row>
            <v-date-picker
              v-if="startDateTemp !== null"
              :model-value="
                dateAdpter.parseISO(
                  startDateTemp ? startDateTemp : currentTimestamp
                )
              "
              @update:model-value="updateTime($event, 'StartDate')"
              @click:cancel="editDialog = false"
              @click:save="editDialog = false"
            />
          </v-card-text>
        </v-card>
      </v-card>
      <v-card v-if="currentEditMode === 'EndDate'">
        <v-card>
          <v-card-title>Site End Time</v-card-title>
          <v-card-text>
            <v-row
              dense
              justify="center"
            >
              <v-btn
                color="error"
                class="mb-2 mx-1"
                size="small"
                @click="
                  updateTime(null, 'EndDate');
                  editDialog = false;
                "
              >
                Set Time to Null
              </v-btn>
            </v-row>
            <v-date-picker
              v-if="endDateTemp !== null"
              :model-value="
                dateAdpter.parseISO(
                  endDateTemp ? endDateTemp : currentTimestamp
                )
              "
              @update:model-value="updateTime($event, 'EndDate')"
              @click:cancel="editDialog = false"
              @click:save="editDialog = false"
            />
          </v-card-text>
        </v-card>
      </v-card>
    </v-dialog>
  </v-card>
</template>

