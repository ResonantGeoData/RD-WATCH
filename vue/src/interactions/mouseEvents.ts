import { Ref, ref } from "vue";
import { Color, Map, MapLayerMouseEvent, Popup } from "maplibre-gl";
import { ShallowRef } from "vue";
import { getSiteObservationDetails, selectedObservationList, state } from "../store";

const checkBadge =
  '<svg style="display:inline;" width="20" height="20" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="replacementColor" aria-hidden="true"><path fill-rule="evenodd" d="M8.603 3.799A4.49 4.49 0 0112 2.25c1.357 0 2.573.6 3.397 1.549a4.49 4.49 0 013.498 1.307 4.491 4.491 0 011.307 3.497A4.49 4.49 0 0121.75 12a4.49 4.49 0 01-1.549 3.397 4.491 4.491 0 01-1.307 3.497 4.491 4.491 0 01-3.497 1.307A4.49 4.49 0 0112 21.75a4.49 4.49 0 01-3.397-1.549 4.49 4.49 0 01-3.498-1.306 4.491 4.491 0 01-1.307-3.498A4.49 4.49 0 012.25 12c0-1.357.6-2.573 1.549-3.397a4.49 4.49 0 011.307-3.497 4.49 4.49 0 013.497-1.307zm7.007 6.387a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z" clip-rule="evenodd"></path></svg>';

  const hoveredInfo: Ref<{region: string[], siteId: number[]}> = ref({region: [], siteId:[]});

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
      let html = "<div><ul>";
      const htmlMap: Record<string, boolean> = {};
      insideObservation = true;
      hoveredInfo.value.region = [];
      hoveredInfo.value.siteId = [];
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
            let fillString = "";
            if (!htmlMap[id]) {
              if (item.layer?.paint) {
                const fillColor = item.layer?.paint["fill-color"] as Color;
                if (fillColor) {
                  fillString = `style="background-color: rgba(${
                    fillColor.r * 255
                  }, ${fillColor.g * 255}, ${fillColor.b * 255}, ${
                    fillColor.a * 255
                  }); font-weight: bolder; opacity: 1.0 !important;"`;
                  ids.push(id);
                  htmlMap[id] = true;
                  let groundtruth = checkBadge;
                  if (item.properties.groundtruth) {
                    groundtruth = groundtruth.replace(
                      "replacementColor",
                      `rgba(${fillColor.r * 255}, ${fillColor.g * 255}, ${
                        fillColor.b * 255
                      }, ${fillColor.a * 255})`
                    );
                  } else {
                    groundtruth = groundtruth.replace(
                      "replacementColor",
                      `rgba(0,0,0,0)`
                    );
                  }
                  const area = Math.round(item.properties.area).toLocaleString('en-US');
                  const areaStr = `<div class='badge'>Area: ${area } m²`;
                  const scoreStyle = `style="background-color:${calculateScoreColor(
                    score.toFixed(2)
                  )};color: black; font-weight:bolder; opacity: 1.0 !important;"`;
                  html = `${html}<li>${groundtruth}<div class='badge' ${fillString}>SiteId:${regionName}_${String(id).padStart(4, '0')}</div> <div class='badge' ${scoreStyle}>Score:${score.toFixed(
                    2
                    )}</div> ${areaStr}</li>`;
                  }
              }
            }
          }
        }
      );
      html += "</ul></div>";
      popup.setLngLat(coordinates).setHTML(html).addTo(map.value);
    } else if (map.value) {
      hoveredInfo.value.region = [];
      hoveredInfo.value.siteId = [];
      insideObservation = false;
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
