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
  <v-text-field
    v-model="filter"
    label="Search"
    variant="solo"
    class="text-field"
    hide-details
    density="compact"
    append-inner-icon="mdi-magnify"
    single-line
  />
</template>
<style scoped>
.search {
    background-color: #3267BA;
    margin: 0px;
}
.text-field {
    border: 5px solid #3267BA
}

</style>
