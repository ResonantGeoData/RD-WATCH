<script setup lang="ts">
import { Ref, ref } from "vue";
import { debounce } from 'lodash';
import { VDatePicker } from 'vuetify/labs/VDatePicker'
import { Constellation, DownloadSettings } from "../client/services/ApiService";


const emit = defineEmits<{
    (e: "download", data: DownloadSettings): void;
    (e: "cancel"): void;
}>();

const baseList = ref(['S2', 'WV', 'L8'])
const selectedSource: Ref<Constellation[]> = ref(['WV']);
const dayRange = ref(14);
const noData = ref(50)
const overrideDates: Ref<[string, string]> = ref(['2013-01-01', new Date().toISOString().split('T')[0]])
const showAdvanced = ref(false);
const force =ref(false);
const customDateRange = ref(false);
const scaleOptions = ref(['default', 'bits', 'custom'])
const scale: Ref<'default' | 'bits' | 'custom'> = ref('default')
const scaleNums: Ref<[number, number]> = ref([0, 10000])
const bboxScale: Ref<number> = ref(1.2);
const validForm = ref(true);

const download = debounce(
  () => {
    emit('download', {
      constellation: selectedSource.value,
      dayRange: dayRange.value,
      noData: noData.value,
      overrideDates: customDateRange.value ? overrideDates.value : undefined,
      force: force.value,
      scale: scale.value,
      scaleNum: scale.value === 'custom' ? scaleNums.value : undefined,
      bboxScale: bboxScale.value,
    });
  },
  2000,
);

const cancel = debounce(() => emit('cancel'), 2000);

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const updateTime = (time: any, date: 'StartDate' | 'EndDate') => {
    if (date === 'StartDate') {
      overrideDates.value[0] = new Date(time as string).toISOString().split('T')[0];
    } else if (date === 'EndDate') {
        overrideDates.value[1] = new Date(time as string).toISOString().split('T')[0];
    }
}

const display = ref(true);

</script>

<template>
  <v-dialog
    v-model="display"
    width="400"
  >
    <v-card>
      <v-card-title>Download Model-Run Images</v-card-title>
      <v-form v-model="validForm">
        <v-card-text>
          <v-row
            dense
            align="center"
          >
            <v-select
              v-model="selectedSource"
              multiple
              :items="baseList"
              label="Source"
              class="mr-2"
            />
            <v-icon
              :color="showAdvanced ? 'primary' : ''"
              @click="showAdvanced = !showAdvanced"
            >
              mdi-cog
            </v-icon>
          </v-row>
          <div v-if="showAdvanced">
            <v-row
              dense
              align="center"
              class="pb-5"
            >
              <v-checkbox
                v-model="force"
                density="compact"
                label="Force"
                hint="Force redownloading all images"
                persistent-hint
              />
            </v-row>
            <v-row
              dense
              align="center"
              class="pb-5"
            >
              <v-select
                v-model="scale"
                :items="scaleOptions"
                density="compact"
                label="Bit Scaling"
                persistent-hint
              />
            </v-row>
            <v-row
              v-if="scale==='custom'"
              dense
              align="center"
              class="pb-5"
            >
              <v-text-field
                v-model.number="scaleNums[0]"
                type="number"
                label="low"
                :rules="[v => v >= 0 || 'Must be >= 0']"
                class="mx-2"
              />
              <v-text-field
                v-model.number="scaleNums[1]"
                type="number"
                label="high"
                class="mx-2"
              />
            </v-row>
            <v-row
              dense
              align="center"
              class="pb-5"
            >
              <v-text-field
                v-model.number="bboxScale"
                :rules="[ v => v >= 1.2 || 'Must be >= 1.2', v => v <= 2 || 'Must be <= 2']"
                type="number"
                step="0.1"
                label="Box Scaling"
              />
              <v-tooltip
                open-delay="50"
                bottom
              >
                <template #activator="{ props:subProps }">
                  <v-icon
                    v-bind="subProps"
                  >
                    mdi-information
                  </v-icon>
                </template>
                <span>
                  Adds a scaling factor to the calculating bounding box to provide more image area around site
                </span>
              </v-tooltip>
            </v-row>

            <v-row
              dense
              align="center"
            >
              <v-text-field
                v-model="dayRange"
                type="number"
                label="Day Limit"
                :rules="[ v => v >= 0 || 'Must be >= 0', v => v <= 365 || 'Must be <= 365']"
                class="m4"
              />
              <v-tooltip
                open-delay="50"
                bottom
              >
                <template #activator="{ props:subProps }">
                  <v-icon
                    v-bind="subProps"
                  >
                    mdi-information
                  </v-icon>
                </template>
                <span>
                  Day Limit applies to S2/L8 imagery to grab one image every X days.  This is to prevent loading hundreds of images
                </span>
              </v-tooltip>
            </v-row>
            <v-row
              dense
              align="center"
            >
              <v-text-field
                v-model="noData"
                type="number"
                label="NODATA %"
              />
              <v-tooltip
                open-delay="50"
                bottom
              >
                <template #activator="{ props:subProps }">
                  <v-icon
                    v-bind="subProps"
                  >
                    mdi-information
                  </v-icon>
                </template>
                <span>
                  When utilizing the DayRange limit this will attmept to filter out images that have more that X% NODATA
                </span>
              </v-tooltip>
            </v-row>
            <v-row dense>
              <v-checkbox
                v-model="customDateRange"
                label="Custom Date Range"
              />
            </v-row>
            <div v-if="customDateRange">
              <v-row dense>
                <v-menu
                  open-delay="20"
                  :close-on-content-click="false"
                >
                  <template #activator="{ props }">
                    <v-btn
                      color="primary"
                      v-bind="props"
                      class="mr-2"
                    >
                      <b>Start:</b>
                      <span> {{ overrideDates[0] }}</span>
                    </v-btn>
                  </template>
                  <v-date-picker
                    :model-value="[overrideDates[0]]"
                    hide-actions
                    @update:model-value="updateTime($event, 'StartDate')"
                  />
                </v-menu>
                <v-menu
                  open-delay="20"
                  :close-on-content-click="false"
                >
                  <template #activator="{ props }">
                    <v-btn
                      color="primary"
                      v-bind="props"
                      class="ml-2"
                    >
                      <b>End:</b>
                      <span> {{ overrideDates[1] }}</span>
                    </v-btn>
                  </template>
                  <v-date-picker
                    :model-value="[overrideDates[1]]"
                    hide-actions
                    @update:model-value="updateTime($event, 'EndDate')"
                  />
                </v-menu>
              </v-row>
            </div>
          </div>
        </v-card-text>
      </v-form>
      <v-card-actions>
        <v-row>
          <v-spacer />
          <v-btn
            color="error"
            class="mx-3"
            @click="cancel()"
          >
            Cancel
          </v-btn>
          <v-btn
            color="success"
            class="mx-3"
            :disabled="!validForm"
            @click="download()"
          >
            Download
          </v-btn>
        </v-row>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.modelRunCard{
  border: 3px solid transparent;
}
.modelRunCard:hover {
  cursor: pointer;
  border: 3px solid blue;
}
.selectedCard{
  background-color: lightblue;
}
.model-title {
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
