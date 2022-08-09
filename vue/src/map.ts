import maplibregl from "maplibre-gl";

export const map = new maplibregl.Map({
  container: "map", // HTML element with ID "map" defined in index.html
  style: "https://demotiles.maplibre.org/style.json",
});
