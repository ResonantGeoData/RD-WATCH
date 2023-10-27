import { App, Ref,   nextTick, ref } from "vue";
import { Color, Map, MapLayerMouseEvent, Popup } from "maplibre-gl";
import { ShallowRef } from "vue";
import { getSiteObservationDetails, selectedObservationList, state } from "../store";
import  createPopup from '../main';
import { PopUpData } from '../interactions/popUpType';
import { styles } from "../mapstyle/annotationStyles";


  const hoveredInfo: Ref<{region: string[], siteId: string[]}> = ref({region: [], siteId:[]});

let app: App | null = null;
const calculateScoreColor = (score: number) => {
  if (score <= 0.25) {
    return "red";
  }
  if (score > 0.25 && score <= 0.5) {
    return "orange";
  }
  if (score > 0.5 && score <= 0.75) {
    return "yellowgreen";
  }
  if (score > 0.75 && score <= 1.0) {
    return "green";
  }
  return "black";
};
let popup: Popup;
const map:ShallowRef<null | Map> = ref(null)
const popupLogic = async (mapArg: ShallowRef<null | Map>) => {
  popup = new Popup({
    closeButton: false,
    closeOnClick: false,
    maxWidth: '700px',
  });
  map.value = mapArg.value;
};
const drawPopupObservation = async (e: MapLayerMouseEvent) => {
  if (e.features && e.features[0]?.properties && map.value) {
    console.log(e.features[0].properties);
    const coordinates = e.lngLat;
    const ids = [];
    const htmlMap: Record<string, boolean> = {};
    hoveredInfo.value.region = [];
    hoveredInfo.value.siteId = [];
    const popupData: PopUpData[] = [];
    e.features.forEach(
      (
        item: GeoJSON.GeoJsonProperties & {
          layer?: { paint?: { "fill-color"?: Color } };
        }
      ) => {
        if (item.properties && item.properties.id) {
          const id = item.properties.site_number;
          const region: string = item.properties.region;
          const score = item.properties.score;
          const siteId = item.properties.siteeval_id;
          const configName = item.properties.configuration_name;
          const performerName = item.properties.performer_name;
          const version = item.properties.version;
          const siteLabel = item.properties.site_label;
          hoveredInfo.value.region.push(
            `${item.properties.configuration_id}_${region}_${item.properties.performer_id}`
          );
          hoveredInfo.value.siteId.push(siteId);
          if (!htmlMap[id]) {
            if (item.layer?.paint) {
              const fillColor = item.layer?.paint["fill-color"] as Color;
              if (fillColor) {
                ids.push(id);
                htmlMap[id] = true;
                }
                const area = Math.round(item.properties.area).toLocaleString('en-US');
                popupData.push({
                  siteId: `${region}_${String(id).padStart(4, '0')}`,
                  score,
                  groundTruth: item.properties.groundtruth,
                  obsColor: `rgb(${fillColor.r *255}, ${fillColor.g * 255}, ${fillColor.b * 255})`,
                  siteColor: styles[siteLabel].color,
                  scoreColor: calculateScoreColor(score),
                  timestamp: item.properties.timestamp,
                  area,
                  version,
                  configName,
                  performerName,
                  siteLabel,
              })
            }
          }
        }
      }
    );
    popup.setLngLat(coordinates).setHTML('<div id="popup-content"></div>').addTo(map.value);
    nextTick(() => {
      if (app !== null) {
        app.unmount();
        app = null;
      }
      app = createPopup(popupData);
      app.mount('#popup-content');
    });
  } else if (map.value) {
    hoveredInfo.value.region = [];
    hoveredInfo.value.siteId = [];
    if (app !== null) {
      app.unmount();
      app = null;
    }
    map.value.getCanvas().style.cursor = "";
    popup.remove();
  }
};
const clickObservation = async (e: MapLayerMouseEvent) => {
  if (e.features && e.features[0]?.properties && map.value) {
    const feature = e.features[0];
    if (feature.properties) {
      const siteId = feature.properties.siteeval_id;
      const scoringBase = {
        region: feature.properties.region as string,
        configurationId: feature.properties.configuration_id as number,
        siteNumber: feature.properties.site_number as number,
        version: feature.properties.version,
      }

      if (siteId && !selectedObservationList.value.includes(siteId)) {
        await getSiteObservationDetails(siteId, scoringBase);
      }
    }
  }

}

let loadedFunctions: {
  id: string,
  mouseenter: (e: MapLayerMouseEvent) => Promise<void>;
  mouseleave: (e: MapLayerMouseEvent) => Promise<void>;
  clickObservation: (e: MapLayerMouseEvent) => Promise<void>;
}[] = []
const setPopupEvents = (map: ShallowRef<null | Map>) => {
  if (map.value) {
    for (let i = 0; i< loadedFunctions.length; i += 1){
      const data = loadedFunctions[i];
      map.value.off("mouseenter", `observations-fill-${data.id}`, data.mouseenter);
      map.value.off("mouseleave", `observations-fill-${data.id}`, data.mouseleave);
      map.value.off("click", `observations-fill-${data.id}`, data.clickObservation);
    }
    loadedFunctions = []
    for (const m of state.openedModelRuns) {
      const id = m.split('|')[0];
      map.value.on("mouseenter", `observations-fill-${id}`, drawPopupObservation);
      map.value.on("mouseleave", `observations-fill-${id}`, drawPopupObservation);
      map.value.on("click", `observations-fill-${id}`, clickObservation);
      loadedFunctions.push({id, mouseenter: drawPopupObservation, mouseleave: drawPopupObservation, clickObservation});
    }
  }
}

export { popupLogic, hoveredInfo, setPopupEvents };
