import { App, Ref, createApp, defineComponent, nextTick, ref } from "vue";
import { Color, Map, MapLayerMouseEvent, Popup } from "maplibre-gl";
import { ShallowRef } from "vue";
import { getSiteObservationDetails, selectedObservationList, state } from "../store";
import PopUpComponent from '../components/PopUpComponent.vue'

import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css' // Ensure you are using css-loader

const vuetify = createVuetify({
  components,
  directives,
})

interface PopUpData {
  siteId: string;
  siteColor: string;
  score: number;
  groundTruth: boolean;
  scoreColor: string;
  area: string;
}

  const hoveredInfo: Ref<{region: string[], siteId: number[]}> = ref({region: [], siteId:[]});

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

const popupLogic = (map: ShallowRef<null | Map>) => {
  const popup = new Popup({
    closeButton: false,
    closeOnClick: false,
    maxWidth: '600px',
  });
  let insideObservation = false;
  const drawPopup = (e: MapLayerMouseEvent) => {
    if (e.features && e.features[0]?.properties && map.value) {
      const coordinates = e.lngLat;
      const ids = [];
      const htmlMap: Record<string, boolean> = {};
      insideObservation = true;
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
            const regionName = state.regionMap[item.properties.region_id]
            const score = item.properties.score;
            const siteId = item.properties.siteeval_id;
            hoveredInfo.value.region.push(
              `${item.properties.configuration_id}_${item.properties.region_id}_${item.properties.performer_id}`
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
                  console.log(item.properties);
                  popupData.push({
                    siteId: `${regionName}_${String(id).padStart(4, '0')}`,
                    score,
                    groundTruth: item.properties.groundtruth,
                    siteColor: `rgb(${fillColor.r *255}, ${fillColor.g * 255}, ${fillColor.b * 255})`,
                    scoreColor: calculateScoreColor(score),
                    area,
                  })    
              }
            }
          }
        }
      );
      popup.setLngLat(coordinates).setHTML('<div id="popup-content"></div>').addTo(map.value);
      const MyNewPopup = defineComponent({
        extends: PopUpComponent,
        setup() {
          return { data: popupData }
        },
      })
      nextTick(() => {
        if (app !== null) {
          app.unmount();
          app = null;
        }
        app = createApp(MyNewPopup).use(vuetify)
        app.mount('#popup-content');
      })
      
    } else if (map.value) {
      hoveredInfo.value.region = [];
      hoveredInfo.value.siteId = [];
      insideObservation = false;
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
        if (siteId && !selectedObservationList.value.includes(siteId)) {
          await getSiteObservationDetails(siteId);
        }
      }
    }

  }

  if (map.value) {
    map.value.on("mouseenter", "observations-fill", function (e) {
      drawPopup(e);
    });
    map.value.on("mouseleave", "observations-fill", function (e) {
      drawPopup(e);
    });
    map.value.on("mousemove", "observations-fill", function (e) {
      if (insideObservation) {
        drawPopup(e);
      }
    });
    map.value.on("click", "observations-fill", function (e) {
      clickObservation(e);
    });
  }
};

export { popupLogic, hoveredInfo };
