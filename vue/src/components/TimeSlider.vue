<script setup lang="ts">
import { computed } from "vue";
import { state } from "../store";

interface Props {
  min: number | null;
  max: number;
  compact?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  compact: false,
});


const convertUnixToDate = (timestamp:number) => {
  const date = new Date(timestamp * 1000);


  const year = date.getFullYear();
const month = ('0' + (date.getMonth() + 1)).slice(-2);
const day = ('0' + date.getDate()).slice(-2);

// Concatenate to get the desired format
const formattedDate = year + '-' + month + '-' + day;
return formattedDate;

}

const date = computed(() => convertUnixToDate(state.timestamp));
const minDate = computed(() => convertUnixToDate(props.min || 0));
const maxDate = computed(() => convertUnixToDate(props.max));
</script>

<template>
  <v-container class="mr-2 time-slider">
    <v-row
      align="center"
      justify="center"
    >
      <v-col>
        <v-row v-if="!compact">
          <v-spacer />
          <span>{{ date }}</span>
          <v-spacer />
        </v-row>
        <v-row>
          <v-col>
            <v-row>
              <v-slider
                v-model.number="state.timestamp"
                :min="min || 0"
                :max="max"
                :disabled="min == max"
                class="date-slider w-100 mb-0 pb-0"
                type="range"
                color="primary"
                :track-size="compact ? 5 : 10"
                track-color="#E0E0E0"
                density="compact"
                hide-details
                @click.stop
              />
            </v-row>
            <v-row v-if="!compact">
              <span>{{ minDate }}</span>
              <v-spacer />
              <span>{{ maxDate }}</span>
            </v-row>
          </v-col>
        </v-row>
      </v-col>
      <v-col
        cols="1"
      >
        <v-icon
          :size="compact ? 'small' : 'large'"
          color="primary"
          class="calender"
        >
          mdi-calendar-today-outline
        </v-icon>
      </v-col>
    </v-row>
  </v-container>
</template>

<style scoped>
.calendar {
  opacity: 1.0;
}

.time-slider {
  /* avoid getting cut off due to parent overflow: hidden */
  padding: 24px;
}
</style>
