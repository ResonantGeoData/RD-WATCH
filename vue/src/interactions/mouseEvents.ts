import { App, Ref,   nextTick, ref } from "vue";
import { Color, Map, MapLayerMouseEvent, Popup } from "maplibre-gl";
import { ShallowRef } from "vue";
import { getSiteObservationDetails, selectedObservationList, state } from "../store";
import  createPopup from '../main';
import { PopUpData } from '../interactions/popUpType';


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

const popupLogic = async (map: ShallowRef<null | Map>) => {
  const popup = new Popup({
    closeButton: false,
    closeOnClick: false,
    maxWidth: '700px',
  });
  const drawPopup = async (e: MapLayerMouseEvent) => {
    if (e.features && e.features[0]?.properties && map.value) {
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
                  popupData.push({
                    siteId: `${regionName}_${String(id).padStart(4, '0')}`,
                    score,
                    groundTruth: item.properties.groundtruth,
                    siteColor: `rgb(${fillColor.r *255}, ${fillColor.g * 255}, ${fillColor.b * 255})`,
                    scoreColor: calculateScoreColor(score),
                    timestamp: item.properties.timestamp,
                    area,                  
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
          regionId: feature.properties.region_id as number,
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

  if (map.value) {
    map.value.on("mouseenter", "observations-fill", function (e) {
      drawPopup(e);
    });
    map.value.on("mouseleave", "observations-fill", function (e) {
      drawPopup(e);
    });
    // map.value.on("mousemove", "observations-fill", function (e) {
    //   if (insideObservation) {
    //     drawPopup(e);
    //   }
    // });
    map.value.on("click", "observations-fill", function (e) {
      clickObservation(e);
    });
  }
};

export { popupLogic, hoveredInfo };
