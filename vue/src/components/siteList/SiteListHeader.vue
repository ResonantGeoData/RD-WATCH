<script setup lang="ts">
import { ref, watch } from "vue";

defineProps<{
    modelValue: string;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", filter: string): void;
}>();

const filter = ref('');

watch(filter, () => {
    emit("update:modelValue", filter.value);
});
</script>

<template>
  <v-row
    class="pa-2 search"
    align="center"
  >
    <v-text-field
      v-model="filter"
      label="Search"
      variant="outlined"
      class="text-field"
      hide-details
      density="compact"
      single-line
    />
    <div
      class="search-icon"
      size="small"
    >
      <v-icon
        size="25"
        color="#01579B"
        class="pt-3 pl-3"
      >
        mdi-magnify
      </v-icon>
    </div>
  </v-row>
</template>
<style scoped>
.search {
    background-color: #01579B;
    width: 250px ;
    margin: 0px;
}
.text-field {
    margin: 10px;
    max-height: 35px;
    background-color: white;
}
.search-icon {
  min-width: 35px;
  min-height: 35px;
  background-color: white;
}

</style>
