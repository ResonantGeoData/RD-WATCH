import { getColorFromLabel } from "../../mapstyle/annotationStyles";
import { ImageBBox } from "../../store";
import { BaseBBox, EvaluationGeoJSON, EvaluationImage, EvaluationImageResults } from "../../types";

export interface PixelPoly {
    coords: {x:number; y:number}[][];
    type: 'Polygon' | 'Point';
    label: string;
    scaled?: {
      crop: {x: number, y:number, width: number, height: number}
      scaledPoly: {x: number; y:number}[][];
      groundTruth?: {x: number; y:number}[][];
    } | false;
}


const getClosestPoly = (timestamp: number, polys: EvaluationGeoJSON[], evaluationPoly: EvaluationGeoJSON['geoJSON'], siteEvalLabel: string, baseBBox: BaseBBox, defaultSitePoly = false) => {
    if (polys.length === 0 || defaultSitePoly) {
      return {geoJSON: evaluationPoly, label:siteEvalLabel, bbox: baseBBox};
    }
      let found = polys[0];
      for (let i = 0; i < polys.length; i += 1) {
          if (timestamp > polys[i].timestamp) {
              if (i > 0) {
                  found = polys[i - 1]
              }
          }
      }
      return found;
  }


const createCanvas = (width: number, height: number) => {
    const myOffScreenCanvas: HTMLCanvasElement & { ctx?: CanvasRenderingContext2D | null } = document.createElement("canvas");
    myOffScreenCanvas.width = width;
    myOffScreenCanvas.height = height;
    // attach the context to the canvas for easy access and to reduce complexity.
    myOffScreenCanvas.ctx = myOffScreenCanvas.getContext("2d");
    return myOffScreenCanvas;
 }


const drawData = (
    canvas: HTMLCanvasElement,
    image: EvaluationImage,
    poly: PixelPoly,
    groundTruthPoly?: PixelPoly,
    overrideWidth = -1,
    overrideHeight = -1,
    background: HTMLCanvasElement & { ctx?: CanvasRenderingContext2D | null } | null = null,
    drawGroundTruth = false,
    rescale = false,
    fullscreen = false,
    canvasScale = 1,
    radiusMultiplier = 1,
    ) => {
      const context = canvas.getContext('2d');
      const imageObj = new Image();
      imageObj.src = image.image;
      imageObj.crossOrigin = "Anonymous";
      if (!background) {
          background = createCanvas(image.image_dimensions[0], image.image_dimensions[1]);
      }
      background.width = image.image_dimensions[0];
      background.height = image.image_dimensions[1];
      const coords = rescale && poly.scaled ? poly.scaled.scaledPoly : poly.coords;
      const renderFunction = (imageDim: [number, number]) => {
          if (context) {
          canvas.width = overrideWidth === -1 ? imageDim[0] : overrideWidth;
          canvas.height = overrideHeight === -1 ? imageDim[1] : overrideHeight;
          const canvasWidth = canvas.width;
          const canvasHeight = canvas.height;
          if (rescale) {
            canvas.width = canvas.width * canvasScale;
            canvas.height = canvas.height * canvasScale;
          }
          // draw the offscreen canvas
            let destWidth = canvasWidth;
            let destHeight = canvasHeight;
            const offsetX = rescale ? (canvas.width - destWidth) / 2.0 : 0;
            const offsetY = rescale ? (canvas.height - destHeight) / 2.0 : 0;
            let destOffsetX = offsetX;
            let destOffsetY = offsetY
            let computedX =  rescale && poly.scaled ? poly.scaled.crop.x : 0;
            let computedY = rescale && poly.scaled ? poly.scaled.crop.y: 0;
            let imageWidth = rescale && poly.scaled ? poly.scaled.crop.width: imageDim[0];
            let imageHeight = rescale && poly.scaled ? poly.scaled.crop.height: imageDim[1];
            //Now if we have more image data than the scaled width and height are available we can take additional pixel information
            if (rescale && poly.scaled) { //Implies S2/L8/PL data where more pixel data can be taken
              computedX = poly.scaled.crop.x - (((poly.scaled.crop.width  * canvasScale) - poly.scaled.crop.width ) / 2.0);
              computedY = poly.scaled.crop.y - (((poly.scaled.crop.height * canvasScale) - poly.scaled.crop.height) / 2.0);
              imageWidth = poly.scaled.crop.width * canvasScale;
              imageHeight = poly.scaled.crop.height * canvasScale;
              destWidth = canvasWidth * canvasScale;
              destHeight = canvasHeight * canvasScale;
              destOffsetX = (canvas.width - destWidth) / 2.0;
              destOffsetY = (canvas.height - destHeight) / 2.0;
            }
          context.fillStyle = 'lightgray';
          context.fillRect(0,0, canvas.width, canvas.height);
          if (background) {
            context.drawImage(background, computedX, computedY, imageWidth, imageHeight, destOffsetX, destOffsetY, destWidth, destHeight);
          }
          const standardPoly = (overrideHeight === -1 && !rescale) || !(poly.scaled || (overrideHeight !== -1 && overrideHeight !== imageDim[1]));
          let widthRatio = rescale && poly.scaled ? imageDim[0] / poly.scaled.crop.width  : overrideWidth / imageDim[0];
          let heightRatio = rescale && poly.scaled  ? imageDim[1] / poly.scaled.crop.height : overrideHeight / imageDim[1];

          let computedImageHeight = rescale && poly.scaled ? poly.scaled.crop.height: imageDim[1];
          let computedOverrideHeight = rescale && poly.scaled ? imageDim[1] : overrideHeight;
          if (overrideHeight !== -1 || overrideWidth !== -1) {
            computedImageHeight = imageDim[1];
            computedOverrideHeight = overrideHeight
            if (poly.scaled) {
              widthRatio = !rescale ? overrideWidth / imageDim[0] : overrideWidth / poly.scaled.crop.width;
              heightRatio = !rescale ? overrideHeight / imageDim[1] : overrideHeight / poly.scaled.crop.height;
            }
          }

          // We draw the ground truth
          if (groundTruthPoly && drawGroundTruth) {
            let gtPoly  = groundTruthPoly.coords;
            if (poly.scaled && rescale && poly.scaled.groundTruth) {
              gtPoly = poly.scaled.groundTruth
            }
            gtPoly.forEach((ring) => {
              const xPos = standardPoly ? ring[0].x : ring[0].x * widthRatio ;
              const yPos = standardPoly ? computedImageHeight - ring[0].y : computedOverrideHeight - (ring[0].y * heightRatio);
              context.moveTo(xPos, yPos);
              context.beginPath();
              ring.forEach(({x, y}) => {
                const yPosEnd =  standardPoly ? computedImageHeight - y : computedOverrideHeight - (y * heightRatio);
                const xPos = standardPoly ? x : x * widthRatio;
                  if (context){
                    context.lineTo(xPos, yPosEnd);
                }
              });
              const lineDivisor = Math.max(canvas.width, canvas.height)
              context.lineWidth = lineDivisor/ 50.0;
              context.strokeStyle = getColorFromLabel(groundTruthPoly.label);
              context.stroke();
            });
          }
          if (poly.type === 'Polygon') {
            coords.forEach((ring) => {
              const xPos = (standardPoly ? ring[0].x : ring[0].x * widthRatio) + offsetX;
              const yPos = (standardPoly ? computedImageHeight - ring[0].y : computedOverrideHeight - (ring[0].y * heightRatio)) + offsetY;
              context.moveTo(xPos, yPos);
              context.beginPath();
              ring.forEach(({x, y}) => {
                const yPosEnd =  (standardPoly ? computedImageHeight - y : computedOverrideHeight - (y * heightRatio)) + offsetY;
                const xPos = (standardPoly ? x : x * widthRatio) + offsetX;
                if (context){
                    context.lineTo(xPos, yPosEnd);
                }
              });
              const lineDivisor = Math.max(canvas.width, canvas.height);
              context.lineWidth = lineDivisor/ 100.0;
              context.strokeStyle = getColorFromLabel(poly.label);
              context.stroke();
            });
          } else { // Drawing a Point
            const xPos = (standardPoly ? coords[0][0].x : coords[0][0].x * widthRatio) + offsetX;
            const yPos = (standardPoly ? computedImageHeight - coords[0][0].y : computedOverrideHeight - (coords[0][0].y * heightRatio)) + offsetY;
            const lineDivisor = Math.max(canvas.width, canvas.height);
            context.arc(xPos, yPos, (lineDivisor/ 100.0) * 2 * radiusMultiplier, 0, 2 * Math.PI, false);
            context.lineWidth = lineDivisor/ 100.0;
            context.strokeStyle = getColorFromLabel(poly.label);
            context.stroke();
          }
          // Now scale the canvas to the proper size
          if (overrideHeight === -1  && overrideWidth === -1) {
            let ratio = imageDim[1] / imageDim[0];
            if (poly.scaled && rescale) {
              ratio  = poly.scaled.crop.height / poly.scaled.crop.width;
            }
            let heightAdjustment = 0.30;
            let widthAdjustment = - 550;
            if (fullscreen) {
              heightAdjustment = 0.70;
              widthAdjustment = 100;
            }
            const maxHeight = document.documentElement.clientHeight * heightAdjustment;
            const maxWidth = document.documentElement.clientWidth - widthAdjustment;
            let width = maxWidth
            let height = width * ratio;
            if (height > maxHeight) {
              height = maxHeight;
              width = height / ratio;
            }

            context.canvas.style.width = `${width}px`
            context.canvas.style.height = `${height}px`;
          } else { // We draw a label for downloaded GIFs
            const fontSize = canvas.height / 25;
            context.font = `${fontSize}px Arial`;
            // Source Satellite
            if (image.source) {
              const drawText = image.observation_id !== null ? `*${image.source}` : image.source;
              const calc = context.measureText(drawText);
              context.fillStyle = 'rgba(255, 255, 255, 0.5)';
              const fontHeight =  (calc.actualBoundingBoxAscent + calc.actualBoundingBoxDescent) * 1.10;
              context.fillRect(0, 0, calc.width*1.10, fontHeight * 1.10);
              context.fillStyle = 'black';
              context.fillText(drawText, 0, fontHeight);
            }
            // Date Drawing
            if (image.timestamp) {
              const date = new Date(image.timestamp * 1000).toISOString().split('T')[0]
              const calc = context.measureText(date);
              context.fillStyle = 'rgba(255, 255, 255, 0.5)';
              const fontHeight =  (calc.actualBoundingBoxAscent + calc.actualBoundingBoxDescent) * 1.10;
              const xPos = (canvas.width * 0.5) - (calc.width * 1.10 * 0.5);
              context.fillRect(xPos, 0, calc.width*1.10, fontHeight * 1.10);
              context.fillStyle = 'black';
              context.fillText(date, xPos, fontHeight);
            }
            // Label Drawing
            if (image.timestamp) {
              const calc = context.measureText(poly.label);
              context.fillStyle = 'rgba(255, 255, 255, 0.5)';
              const fontHeight =  (calc.fontBoundingBoxAscent + calc.fontBoundingBoxDescent) * 1.10;
              const xPos = (canvas.width) - (calc.width * 1.10);
              context.fillRect(xPos, 0, calc.width*1.10, fontHeight * 1.10);
              context.fillStyle = getColorFromLabel(poly.label);
              context.fillText(poly.label, xPos, fontHeight * 0.90);
            }
            context.stroke();
          }
        }
      }

      imageObj.onload = () => {
          if (background && background.ctx) {
              background.width = imageObj.width;
              background.height = imageObj.height;
              background.ctx.drawImage(imageObj, 0, 0, imageObj.width, imageObj.height);
              renderFunction([imageObj.width, imageObj.height]);
          }
      }
    };

const rescale = (baseBBox: BaseBBox, scale=1.2) => {
  const baseWidth =  baseBBox.xmax - baseBBox.xmin;
  const baseHeight =  baseBBox.ymax - baseBBox.ymin;
  const newWidth = (baseWidth * scale) ;
  const newHeight = (baseHeight * scale);

  return {
    xmin: baseBBox.xmin - ((newWidth - baseWidth) / 2),
    ymin: baseBBox.ymin - ((newHeight - baseHeight) / 2),
    xmax: baseBBox.xmax + ((newWidth - baseWidth) / 2),
    ymax: baseBBox.ymax + ((newHeight - baseHeight) / 2),
  }
}

// Convert Image-Space GeoJSON.Polygon to GeoSpatial Polygon
const denormalizePolygon = (bbox: BaseBBox, imageWidth: number, imageHeight: number, polygon: GeoJSON.Polygon ): GeoJSON.Polygon | null => {
  const bboxWidth = bbox.xmax - bbox.xmin;
  const bboxHeight = bbox.ymax - bbox.ymin;

  const geoSpatialPoly: GeoJSON.Position[][] = [];

  polygon.coordinates.forEach((ring) => {
    geoSpatialPoly.push([]);
    ring.forEach((coord) => {
      const normalize_x = coord[0] / imageWidth;
      const normalize_y = coord[1] / imageHeight;
      const geo_x = normalize_x * bboxWidth + bbox.xmin;
      const geo_y = normalize_y * bboxHeight + bbox.ymin;
      geoSpatialPoly[geoSpatialPoly.length - 1].push([geo_x, geo_y]);
    });
  });

  if (geoSpatialPoly.length === 1) {
    return { type: "Polygon", coordinates: geoSpatialPoly } as GeoJSON.Polygon;
  }
  return null;
};


const normalizePolygon = (bbox: BaseBBox, imageWidth: number, imageHeight: number, polygon: GeoJSON.Polygon | GeoJSON.MultiPolygon  | GeoJSON.Point) => {
  const bboxWidth = bbox.xmax - bbox.xmin;
  const bboxHeight = bbox.ymax - bbox.ymin;

  const imageNormalizePoly: {x: number, y: number}[][] = []
  if (['Polygon', 'MultiPolygon'].includes(polygon.type)) {
    polygon.coordinates.forEach((ring) => {
      imageNormalizePoly.push([]);
      if (polygon.type === 'Polygon') {
      (ring as GeoJSON.Position[]).forEach((baseCoord) => {
          const coord = baseCoord as GeoJSON.Position;
          const normalize_x = (coord[0] - bbox.xmin) / bboxWidth;
          const normalize_y = (coord[1] - bbox.ymin) / bboxHeight;
          const image_x = normalize_x * imageWidth;
          const image_y = normalize_y * imageHeight;
          imageNormalizePoly[imageNormalizePoly.length -1].push({x: image_x, y: image_y});
        });
      }else if (polygon.type === 'MultiPolygon') {
        (ring as GeoJSON.Position[][]).forEach((baseCoord) => {
          const coordList = baseCoord as GeoJSON.Position[];
          coordList.forEach((coord) => {
          const normalize_x = (coord[0] - bbox.xmin) / bboxWidth;
          const normalize_y = (coord[1] - bbox.ymin) / bboxHeight;
          const image_x = normalize_x * imageWidth;
          const image_y = normalize_y * imageHeight;
          imageNormalizePoly[imageNormalizePoly.length -1].push({x: image_x, y: image_y});
          });
        });
      } 
    });
  } else if (polygon.type === 'Point') {
        imageNormalizePoly.push([]);
        const coordList = polygon.coordinates;
        const normalize_x = (coordList[0] - bbox.xmin) / bboxWidth;
        const normalize_y = (coordList[1] - bbox.ymin) / bboxHeight;
        const image_x = normalize_x * imageWidth;
        const image_y = normalize_y * imageHeight;
        imageNormalizePoly[imageNormalizePoly.length -1].push({x: image_x, y: image_y});
    }
  return imageNormalizePoly;
}


const oneMeterWGS84 = 0.000008983; // This is 1m distance in WGS84
const areaAroundPoint = 200
const rescalePoly = (image:EvaluationImage, baseBBox: BaseBBox, polygon: GeoJSON.Polygon | GeoJSON.Point) => {
  let rescaled = rescale(baseBBox);
  if (polygon.type === 'Point') {  // for points the bbox area grabbed is 200m around the point.
    const pointBBox = {
      xmin: baseBBox.xmin - (oneMeterWGS84 * 0.5 * areaAroundPoint),
      xmax: baseBBox.xmax + (oneMeterWGS84 * 0.5 * areaAroundPoint),
      ymin: baseBBox.ymin - (oneMeterWGS84 * 0.5 * areaAroundPoint) ,
      ymax: baseBBox.ymax + (oneMeterWGS84 * 0.5 * areaAroundPoint),
    };
    rescaled = rescale(pointBBox);
  }
  const baseWidth = rescaled.xmax - rescaled.xmin;
  const baseHeight = rescaled.ymax - rescaled.ymin;
  const imageBBoxWidth = image.bbox.xmax - image.bbox.xmin;
  const imageBBoxHeight = image.bbox.ymax - image.bbox.ymin;

  // If not equal we need to rescale them
  const diffX  = ((imageBBoxWidth - baseWidth) / imageBBoxWidth) * 100;
  const diffY  = ((imageBBoxHeight - baseHeight) / imageBBoxHeight) * 100;
  if (diffX > 7 || diffY > 7) {
    // Now we calculate a crop value for the larger imageBBox
    const relativeWidth = baseWidth / imageBBoxWidth;
    const relativeHeight = baseHeight / imageBBoxHeight;
    const newImageWidth = image.image_dimensions[0] * relativeWidth;
    const newImageHeight = image.image_dimensions[1] * relativeHeight;
    const widthDiff = image.image_dimensions[0] - newImageWidth;
    const heightDiff = image.image_dimensions[1] - newImageHeight;
    const crop = {
      x: widthDiff / 2.0,
      y: heightDiff / 2.0,
      width: newImageWidth,
      height: newImageHeight,
    }
    // Next we need to reposition all of the pixels to fit the new image;
    const imageWidth = newImageWidth;
    const imageHeight = newImageHeight;
    // Lets check if we need a scaled verison:
    const scaledPoly: {x: number, y: number}[][] = normalizePolygon(rescaled, imageWidth, imageHeight, polygon)
    return { crop, scaledPoly };
  }
  return false;

}

const processImagePoly = (
    image: EvaluationImage,
    polygons: EvaluationGeoJSON[],
    evaluationGeoJSON: EvaluationImageResults['evaluationGeoJSON'],
    evaluationBBox: BaseBBox,
    label: string,
    hasGroundTruth: boolean,
    groundTruth: EvaluationImageResults['groundTruth'] | null,
    defaultSitePoly = false,
    ) => {
    const closestPoly = getClosestPoly(image.timestamp, polygons, evaluationGeoJSON, label, evaluationBBox, defaultSitePoly );
        // Now we convert the coordinates to image space
        const imageWidth = image.image_dimensions[0];
        const imageHeight = image.image_dimensions[1];
        const imageNormalizePoly: {x: number, y: number}[][] = normalizePolygon(image.bbox, imageWidth, imageHeight, closestPoly.geoJSON);
        let groundTruthPoly;
        if (hasGroundTruth && groundTruth) {
          const gtNormalizePoly: {x: number, y: number}[][] = normalizePolygon(image.bbox, imageWidth, imageHeight, groundTruth.geoJSON);
          groundTruthPoly = { coords: gtNormalizePoly, label: groundTruth.label};
        }
        const poly: PixelPoly = {coords: imageNormalizePoly, label: closestPoly.label, scaled: false, type: closestPoly.geoJSON.type};
        const rescaled = rescalePoly(image, closestPoly.bbox, closestPoly.geoJSON);
        if (rescaled) {
          poly['scaled'] =  rescaled;
        }
        if (hasGroundTruth && groundTruth) {
          const rescaleGT = rescalePoly(image, closestPoly.bbox, groundTruth.geoJSON);
          if (rescaleGT && poly.scaled) {
            poly['scaled']['groundTruth'] = rescaleGT.scaledPoly;
          }
        }
        return { image: image, baseBBox: closestPoly.bbox, poly, groundTruthPoly };
}



function scaleBoundingBox(bbox: ImageBBox, scale: number) {
  // Get the width and height of the bounding box
  const width = bbox[2][0] - bbox[0][0];
  const height = bbox[2][1] - bbox[0][1];

  // Calculate the new width and height based on the scaling factor
  const newWidth = width * scale;
  const newHeight = height * scale;

  // Calculate the new coordinates of the bounding box
  const newX1 = bbox[0][0] - ((newWidth - width) / 2);
  const newY1 = bbox[0][1] - ((newHeight - height) / 2);
  const newX2 = bbox[2][0] + ((newWidth - width) / 2);
  const newY2 = bbox[2][1] + ((newHeight - height) / 2);

  // Return the new bounding box
  return [[newX1, newY1], [newX2, newY1], [newX2, newY2],  [newX1, newY2]] as ImageBBox;
}
export {
    drawData,
    createCanvas,
    getClosestPoly,
    processImagePoly,
    scaleBoundingBox,
    normalizePolygon,
    denormalizePolygon,
}
