import { getColorFromLabel } from "../../mapstyle/annotationStyles";
import { EvaluationGeoJSON, EvaluationImage, EvaluationImageResults } from "../../types";

export interface PixelPoly {
    coords: {x:number; y:number}[][];
    label: string;
}

const getClosestPoly = (timestamp: number, polys: EvaluationGeoJSON[], evaluationPoly: EvaluationGeoJSON['geoJSON'], siteEvalLabel: string) => {
    if (polys.length === 0) {
      return {geoJSON: evaluationPoly, label:siteEvalLabel};
    }
      let found = polys[0];
      for (let i = 0; i < polys.length; i += 1) {
          if (timestamp > polys[i].timestamp) {
              if (i > 0) {
                  found = polys[i -1]
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
      const { coords } = poly;
      const renderFunction = () => {
          if (context) {
          canvas.width = overrideWidth === -1 ? image.image_dimensions[0]: overrideWidth;
          canvas.height = overrideHeight === -1 ? image.image_dimensions[1]: overrideHeight;
          // draw the offscreen canvas
          if ((overrideWidth !== -1 || overrideHeight !== -1) && background) {
            context.drawImage(background, 0, 0, image.image_dimensions[0], image.image_dimensions[1], 0, 0, overrideWidth, overrideHeight);
          } else if (background) {
            context.drawImage(background, 0, 0);
          }
          const widthRatio = overrideWidth / image.image_dimensions[0];
          const heightRatio = overrideHeight / image.image_dimensions[1];
  
          // We draw the ground truth
          if (groundTruthPoly && drawGroundTruth) {
            groundTruthPoly.coords.forEach((ring) => {
              const xPos = overrideWidth === -1 ? ring[0].x : ring[0].x * widthRatio ;
              const yPos = overrideHeight === -1 ? image.image_dimensions[1] - ring[0].y : overrideHeight - (ring[0].y * overrideHeight);
              context.moveTo(xPos, yPos);
              context.beginPath();
              ring.forEach(({x, y}) => {
                const yPosEnd =  overrideHeight === -1 ? image.image_dimensions[1] - y : overrideHeight - (y * heightRatio);
                const xPos = overrideWidth === -1 ? x : x * widthRatio;
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
  
          coords.forEach((ring) => {
            const xPos = overrideWidth === -1 ? ring[0].x : ring[0].x * widthRatio ;
            const yPos = overrideHeight === -1 ? image.image_dimensions[1] - ring[0].y : overrideHeight - (ring[0].y * overrideHeight);
            
            context.moveTo(xPos, yPos);
            context.beginPath();
            ring.forEach(({x, y}) => {
              const yPosEnd =  overrideHeight === -1 ? image.image_dimensions[1] - y : overrideHeight - (y * heightRatio);
              const xPos = overrideWidth === -1 ? x : x * widthRatio;
              if (context){
                  context.lineTo(xPos, yPosEnd);
              }
            });
            const lineDivisor = Math.max(canvas.width, canvas.height);
            context.lineWidth = lineDivisor/ 100.0;
            context.strokeStyle = getColorFromLabel(poly.label);
            context.stroke();
          });
          // Now scale the canvas to the proper size
          if (overrideHeight === -1  && overrideWidth === -1) {
            const ratio = image.image_dimensions[1] / image.image_dimensions[0];
            const maxHeight = document.documentElement.clientHeight * 0.30;
            const maxWidth = document.documentElement.clientWidth - 550;
            let width = maxWidth
            let height = width * ratio;
            if (height > maxHeight) {
              height = maxHeight;
              width = height / ratio;
            }
            context.canvas.style.width = `${width}px`
            context.canvas.style.height = `${height}px`;
          } else { // We draw a label for downloaded GIFs
            const fontSize = canvas.height / 15;
            context.font = `${fontSize}px Arial`;
            // Source Satellite
            if (image.source) {
              const drawText = image.siteobs_id !== null ? `*${image.source}` : image.source;
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
              background.width = image.image_dimensions[0];
              background.height = image.image_dimensions[1];
              background.ctx.drawImage(imageObj, 0, 0, image.image_dimensions[0], image.image_dimensions[1]);
              renderFunction();
          }
      }
    };


const processImagePoly = (
    image: EvaluationImage,
    polygons: EvaluationGeoJSON[],
    evaluationGeoJSON: EvaluationImageResults['evaluationGeoJSON'],
    label: string,
    hasGroundTruth: boolean,
    groundTruth: EvaluationImageResults['groundTruth'] | null,
    ) => {
    const closestPoly = getClosestPoly(image.timestamp, polygons, evaluationGeoJSON, label);
        // Now we convert the coordinates to
        const bboxWidth = image.bbox.xmax - image.bbox.xmin;
        const bboxHeight = image.bbox.ymax - image.bbox.ymin;
        const imageWidth = image.image_dimensions[0];
        const imageHeight = image.image_dimensions[1];
        const imageNormalizePoly: {x: number, y: number}[][] = []
        closestPoly.geoJSON.coordinates.forEach((ring) => {
          imageNormalizePoly.push([]);
            ring.forEach((coord) => {
                const normalize_x = (coord[0] - image.bbox.xmin) / bboxWidth;
            const normalize_y = (coord[1] - image.bbox.ymin) / bboxHeight;
            const image_x = normalize_x * imageWidth;
            const image_y = normalize_y * imageHeight;
            imageNormalizePoly[imageNormalizePoly.length -1].push({x: image_x, y: image_y});

            })
        })
        let groundTruthPoly;
        if (hasGroundTruth && groundTruth) {
          const gtNormalizePoly: {x: number, y: number}[][] = []
          groundTruth.geoJSON.coordinates.forEach((ring) => {
            gtNormalizePoly.push([]);
            ring.forEach((coord) => {
                const normalize_x = (coord[0] - image.bbox.xmin) / bboxWidth;
              const normalize_y = (coord[1] - image.bbox.ymin) / bboxHeight;
              const image_x = normalize_x * imageWidth;
              const image_y = normalize_y * imageHeight;
              gtNormalizePoly[imageNormalizePoly.length -1].push({x: image_x, y: image_y});
              })
              groundTruthPoly = { coords: gtNormalizePoly, label: groundTruth.label}
          })

        }
        return { image: image, poly: {coords: imageNormalizePoly, label: closestPoly.label}, groundTruthPoly };
}
export {
    drawData,
    createCanvas,
    getClosestPoly,
    processImagePoly,
}