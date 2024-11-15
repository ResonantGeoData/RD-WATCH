import { Ref, ShallowRef, ref } from "vue";
import { Map } from "maplibre-gl";

const mapReference: Ref<null | Map> = ref(null);


const addPattern = (diagonalLeftImage: HTMLImageElement, diagonalRightImage: HTMLImageElement, menuImg?: HTMLImageElement) => {
  if (mapReference.value) {
    if (!mapReference.value.hasImage("null")) {
      mapReference.value.addImage("null", {
        width: 0,
        height: 0,
        data: new Uint8Array(),
      });
    }

    if (mapReference.value.hasImage("diagonal-right")) {
      mapReference.value.removeImage("diagonal-right");
    }
    if (mapReference.value.hasImage("diagonal-left")) {
      mapReference.value.removeImage("diagonal-left");
    }
    mapReference.value.addImage("diagonal-right", diagonalRightImage );
    mapReference.value.addImage("diagonal-left", diagonalLeftImage);
    if (menuImg) {
      mapReference.value.addImage("diagonal-left", diagonalLeftImage)
    }
  }
}
const setReference = (map: ShallowRef<Map | null>) => {
  mapReference.value = map.value;
  if (mapReference.value) {
    if (!mapReference.value.hasImage("null")) {
      mapReference.value.addImage("null", {
        width: 0,
        height: 0,
        data: new Uint8Array(),
      });
    }
  }
}
export { setReference, addPattern };
