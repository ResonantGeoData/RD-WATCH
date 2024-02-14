import * as turf from "@turf/turf";
import cv from "@techstark/opencv-js";

export function convertImageToPoly(image: HTMLImageElement, smoothing = 3) {
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
    cv.findContours(gray, contours, hierarchy, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE);
    // Get the contour with the largest area
    let maxArea = -1;
    let maxContour;
    for (let i = 0; i < contours.size(); i++) {
      const contour = contours.get(i);
      const area = cv.contourArea(contour);
      if (area > maxArea) {
        maxArea = area;
        maxContour = contours.get(i);
      }
    }
    // Convert contour points to GeoJSON polygon
    if (maxContour) {
    const geoJSONPolygon = contourToGeoJSON(maxContour, smoothing);
    maxContour.delete();
    return geoJSONPolygon;
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
      const x = tmp.data32S[i]
      const y = tmp.data32S[i+1]
      coordinates.push([x, y]);
    }
    coordinates.push(coordinates[0]); // Close the polygon
    const polygon = turf.polygon([coordinates]);
    return polygon.geometry;
  }


  export function drawGeoJSONPolygon(ctx: CanvasRenderingContext2D, geoJSONPolygon: GeoJSON.Polygon) {
    if (!ctx || !geoJSONPolygon || geoJSONPolygon.type !== 'Polygon' || !geoJSONPolygon.coordinates) {
      console.error('Invalid input parameters.');
      return;
    }
    // Extract coordinates from GeoJSON
    const coordinates = geoJSONPolygon.coordinates[0];
    // Draw circles at each coordinate
    ctx.fillStyle = 'blue'; // Circle fill color
    for (const coord of coordinates) {
      const [x, y] = coord;
      const radius = 8; // Circle radius
      ctx.beginPath();
      ctx.arc(x, y, radius, 0, 2 * Math.PI);
      ctx.fill();
    }
    // Draw lines connecting the circles
    ctx.strokeStyle = 'red'; // Line color
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