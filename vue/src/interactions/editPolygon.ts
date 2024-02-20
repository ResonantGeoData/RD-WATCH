import MapboxDraw, { DrawSelectionChangeEvent } from "@mapbox/mapbox-gl-draw";
import { IControl, Map } from "maplibre-gl";
import { Ref, ShallowRef, ref, shallowRef } from "vue";

export interface EditPolygonType {
  initialize: () => void;
  setPolygonEdit: (polygon: GeoJSON.Polygon) => void;
  getEditingPolygon: () => GeoJSON.Polygon | null;
  cancelPolygonEdit: () => void;
  deleteSelectedPoints: () => void;
  selectedPoints: Ref<DrawSelectionChangeEvent['points']>;
}

export default function useEditPolygon(mapObj: Map): EditPolygonType {
  const map: ShallowRef<Map> = shallowRef(mapObj);
  const draw: Ref<MapboxDraw | null> = ref(null);
  const editingPolygon: Ref<GeoJSON.Polygon | null> = ref(null);
  const selectedPoints: Ref<DrawSelectionChangeEvent['points']> = ref([] as DrawSelectionChangeEvent['points']);

  const updated = (e: MapboxDraw.DrawUpdateEvent) => {
    if (e.features.length) {
      editingPolygon.value = e.features[0].geometry as GeoJSON.Polygon;
    }
  };

  const initialize = () => {
    if (draw.value) {
      map.value.removeControl(draw.value as unknown as IControl);
    }
    const styles =  [
      // ACTIVE (being drawn)
      // line stroke
      {
        id: "gl-draw-line",
        type: "line",
        filter: [
          "all",
          ["==", "$type", "LineString"],
          ["!=", "mode", "static"],
        ],
        layout: {
          "line-cap": "round",
          "line-join": "round",
        },
        paint: {
          "line-color": "#D20C0C",
          "line-dasharray": [0.2, 2],
          "line-width": 2,
        },
      },
      // polygon fill
      {
        id: "gl-draw-polygon-fill",
        type: "fill",
        filter: ["all", ["==", "$type", "Polygon"], ["!=", "mode", "static"]],
        paint: {
          "fill-color": "#D20C0C",
          "fill-outline-color": "#D20C0C",
          "fill-opacity": 0.1,
        },
      },
      // polygon mid points
      {
        id: "gl-draw-polygon-midpoint",
        type: "circle",
        filter: ["all", ["==", "$type", "Point"], ["==", "meta", "midpoint"]],
        paint: {
          "circle-radius": 3,
          "circle-color": "#fbb03b",
        },
      },
      // polygon outline stroke
      // This doesn't style the first edge of the polygon, which uses the line stroke styling instead
      {
        id: "gl-draw-polygon-stroke-active",
        type: "line",
        filter: ["all", ["==", "$type", "Polygon"], ["!=", "mode", "static"]],
        layout: {
          "line-cap": "round",
          "line-join": "round",
        },
        paint: {
          "line-color": "#D20C0C",
          "line-dasharray": [0.2, 2],
          "line-width": 2,
        },
      },
      // vertex point halos
      {
        id: "gl-draw-polygon-and-line-vertex-halo-active",
        type: "circle",
        filter: [
          "all",
          ["==", "meta", "vertex"],
          ["==", "$type", "Point"],
          ["!=", "mode", "static"],
        ],
        paint: {
          "circle-radius": 5,
          "circle-color": "#FFF",
        },
      },
      // vertex points
      {
        id: "gl-draw-polygon-and-line-vertex-active",
        type: "circle",
        filter: [
          "all",
          ["==", "meta", "vertex"],
          ["==", "$type", "Point"],
          ["!=", "mode", "static"],
        ],
        paint: {
          "circle-radius": 3,
          "circle-color": "#D20C0C",
        },
      },

      // INACTIVE (static, already drawn)
      // line stroke
      {
        id: "gl-draw-line-static",
        type: "line",
        filter: [
          "all",
          ["==", "$type", "LineString"],
          ["==", "mode", "static"],
        ],
        layout: {
          "line-cap": "round",
          "line-join": "round",
        },
        paint: {
          "line-color": "#000",
          "line-width": 3,
        },
      },
      // polygon fill
      {
        id: "gl-draw-polygon-fill-static",
        type: "fill",
        filter: ["all", ["==", "$type", "Polygon"], ["==", "mode", "static"]],
        paint: {
          "fill-color": "#000",
          "fill-outline-color": "#000",
          "fill-opacity": 0.1,
        },
      },
      // polygon outline
      {
        id: "gl-draw-polygon-stroke-static",
        type: "line",
        filter: ["all", ["==", "$type", "Polygon"], ["==", "mode", "static"]],
        layout: {
          "line-cap": "round",
          "line-join": "round",
        },
        paint: {
          "line-color": "#000",
          "line-width": 3,
        },
      },
    ];
    draw.value = new MapboxDraw({
      displayControlsDefault: true,
      controls: {
        polygon: true,
        trash: true,
      },
      //styles,
    });
    map.value.addControl(draw.value as unknown as IControl, "top-right");

    const selectionChange = (e: MapboxDraw.DrawSelectionChangeEvent) => {
      if (e.points.length) {
        selectedPoints.value = e.points;
      } else {
        selectedPoints.value = [];
      }
    }
    map.value.on("draw.update", updated);
    map.value.on("draw.selectionchange", selectionChange);
  };

  const setPolygonEdit = (polygon: GeoJSON.Polygon) => {
    if (draw.value) {
      const featureIds = draw.value.add(polygon);
      editingPolygon.value = polygon;
      selectedPoints.value = [];
      draw.value.changeMode("direct_select", { featureId: featureIds[0] });
    }
  };

  const deleteSelectedPoints = () => {
    if (draw.value) {
      selectedPoints.value = [];
      draw.value.trash();
    }
  }

  const cancelPolygonEdit = () => {
    if (draw.value) {
      draw.value.deleteAll();
    }
  };
  const getEditingPolygon = () => {
    return editingPolygon.value;
  };

  return {
    initialize,
    setPolygonEdit,
    getEditingPolygon,
    cancelPolygonEdit,
    deleteSelectedPoints,
    selectedPoints,
  };
}
