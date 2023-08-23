<script setup lang="ts">
import { Ref, ref } from "vue";
import { VDatePicker } from 'vuetify/labs/VDatePicker'
import { DownloadSettings } from "../client/services/ApiService";


const emit = defineEmits<{
    (e: "download", data: DownloadSettings): void;
    (e: "cancel"): void;
}>();

const baseList = ref(['S2', 'WV', 'L8'])
const selectedSource: Ref<'S2' | 'WV' | 'L8'> = ref('WV');
const dayRange = ref(14);
const noData = ref(50)
const overrideDates: Ref<[string, string]> = ref(['2013-01-01', new Date().toISOString().split('T')[0]])
const showAdvanced = ref(false);
const customDateRange = ref(false);

const download = () => {
    emit('download', {
        constellation: selectedSource.value,
        dayRange: dayRange.value,
        noData: noData.value,
        customDateRange: customDateRange.value ? overrideDates.value : undefined,
    })
}

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
      <v-card-text>
        <v-row
          dense
          align="center"
        >
          <v-select
            v-model="selectedSource"
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
          >
            <v-text-field
              v-model="dayRange"
              type="number"
              label="Day Limit"
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
      <v-card-actions>
        <v-row>
          <v-spacer />
          <v-btn
            color="error"
            class="mx-3"
            @click="emit('cancel')"
          >
            Cancel
          </v-btn>
          <v-btn
            color="success"
            class="mx-3"
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
