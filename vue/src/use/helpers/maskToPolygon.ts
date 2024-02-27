import * as turf from "@turf/turf";
import cv from "@techstark/opencv-js";

export function convertImageToPoly(
  image: HTMLImageElement,
  smoothing = 3,
  combine = false
) {
  // Create an OpenCV mat from the image
  const src = cv.imread(image);
  // Convert the image to grayscale
  const gray = new cv.Mat();
  cv.cvtColor(src, gray, cv.COLOR_RGBA2GRAY);
  // Apply threshold to identify visible pixels
  const threshold = 0;
  cv.threshold(gray, gray, threshold, 255, cv.THRESH_BINARY);
  // Find contours in the image
  const contours = new cv.MatVector();
  const hierarchy = new cv.Mat();
  cv.findContours(
    gray,
    contours,
    hierarchy,
    cv.RETR_EXTERNAL,
    cv.CHAIN_APPROX_SIMPLE
  );
  // Get the contour with the largest area
  let maxArea = -1;
  let maxContour;

  const polygonList: GeoJSON.Feature<
    GeoJSON.Polygon,
    GeoJSON.GeoJsonProperties
  >[] = [];
  for (let i = 0; i < contours.size(); i++) {
    const contour = contours.get(i);
    const area = cv.contourArea(contour);
    if (area > maxArea) {
      maxArea = area;
      maxContour = contours.get(i);
    }
    if (combine) {
      const tempPoly = contourToGeoJSON(contours.get(i), smoothing);
      if (tempPoly) {
        polygonList.push(tempPoly);
      }
    }
  }
  // Convert contour points to GeoJSON polygon
  if (combine) {
    if (maxContour) {
      maxContour.delete();
    }
    src.delete();
    gray.delete();
    contours.delete();
    hierarchy.delete();
    return polygonList;
  }
  if (maxContour) {
    const geoJSONPolygon = contourToGeoJSON(maxContour, smoothing);
    if (geoJSONPolygon) {
      maxContour.delete();
      src.delete();
      gray.delete();
      contours.delete();
      hierarchy.delete();
      return [geoJSONPolygon];
    }
  }
  // Release memory
  src.delete();
  gray.delete();
  contours.delete();
  hierarchy.delete();
  return null;
}

function contourToGeoJSON(contour: cv.Mat, smoothing = 3) {
  const tmp = new cv.Mat();
  const cnt = contour;
  // You can try more different parameters
  if (smoothing < 0) {
    smoothing = 0;
  }
  cv.approxPolyDP(cnt, tmp, smoothing, true);
  //tmp = contour;
  const coordinates = [];
  for (let i = 0; i < tmp.data32S.length; i += 2) {
    const x = tmp.data32S[i];
    const y = tmp.data32S[i + 1];
    coordinates.push([x, y]);
  }
  if (coordinates.length >= 3) {
    coordinates.push(coordinates[0]); // Close the polygon
    const polygon = turf.polygon([coordinates]);
    return polygon;
  }
  return null;
}

export function drawGeoJSONPolygon(
  ctx: CanvasRenderingContext2D,
  geoJSONPolygon: GeoJSON.Polygon
) {
  if (
    !ctx ||
    !geoJSONPolygon ||
    geoJSONPolygon.type !== "Polygon" ||
    !geoJSONPolygon.coordinates
  ) {
    console.error("Invalid input parameters.");
    return;
  }
  // Extract coordinates from GeoJSON
  const coordinates = geoJSONPolygon.coordinates[0];
  // Draw circles at each coordinate
  ctx.fillStyle = "blue"; // Circle fill color
  for (const coord of coordinates) {
    const [x, y] = coord;
    const radius = 8; // Circle radius
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, 2 * Math.PI);
    ctx.fill();
  }
  // Draw lines connecting the circles
  ctx.strokeStyle = "red"; // Line color
  ctx.lineWidth = 2; // Line width
  ctx.beginPath();
  const firstCoord = coordinates[0];
  ctx.moveTo(firstCoord[0], firstCoord[1]);
  for (let i = 1; i < coordinates.length; i++) {
    const coord = coordinates[i];
    ctx.lineTo(coord[0], coord[1]);
  }
  ctx.closePath();
  ctx.stroke();
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function flattenCoordinates(coordinates: any[]): number[] {
  return coordinates.reduce<number[]>((acc, coord) => {
    if (Array.isArray(coord[0])) {
      return acc.concat(flattenCoordinates(coord));
    } else {
      return acc.concat(coord);
    }
  }, []);
}

export function combinePolygons(
  polygons: GeoJSON.Feature<GeoJSON.Polygon, GeoJSON.GeoJsonProperties>[]
): GeoJSON.Feature<GeoJSON.Polygon, GeoJSON.GeoJsonProperties> | null {
  if (polygons.length === 0) {
    return null; // Return null if the array is empty
  }
  const combinedPolygon = turf.union(turf.featureCollection(polygons));
  let outputPolygon = combinedPolygon;
  // Check if the result is a MultiPolygon
  if (combinedPolygon && combinedPolygon.geometry.type === "Polygon") {
    return outputPolygon as GeoJSON.Feature<
      GeoJSON.Polygon,
      GeoJSON.GeoJsonProperties
    >;
  } else if (
    combinedPolygon &&
    combinedPolygon.geometry.type === "MultiPolygon"
  ) {
    // If it's a MultiPolygon, convert it to a single Polygon by merging the coordinates

    const combinedCoordinates = flattenCoordinates(
      combinedPolygon.geometry.coordinates
    );
    const newCoordinates: GeoJSON.Position[] = [];
    const turfPoints: GeoJSON.Feature<
      GeoJSON.Point,
      GeoJSON.GeoJsonProperties
    >[] = [];
    for (let i = 0; i < combinedCoordinates.length; i += 2) {
      newCoordinates.push([combinedCoordinates[i], combinedCoordinates[i + 1]]);
      turfPoints.push(
        turf.point([combinedCoordinates[i], combinedCoordinates[i + 1]])
      );
    }
    const pointCollection = turf.featureCollection(turfPoints);
    const filteredTurfPoints = turf.concave(pointCollection);
    // Create a single Polygon feature
    if (filteredTurfPoints) {
      outputPolygon = {
        type: "Feature",
        geometry: {
          type: "Polygon",
          coordinates: filteredTurfPoints?.geometry
            .coordinates as GeoJSON.Position[][],
        },
        properties: {}, // You can copy properties from any of the input polygons if needed
      };
      return outputPolygon as GeoJSON.Feature<
        GeoJSON.Polygon,
        GeoJSON.GeoJsonProperties
      >;
    }
  }
  return null;
}
