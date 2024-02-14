// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.

// This source code is licensed under the license found in the
// LICENSE file in the root directory of this source tree.

// Convert the onnx model mask prediction to ImageData
export function arrayToImageData(input: any, width: number, height: number, color: [number, number, number, number] = [0, 114, 189, 255]) {
  const [r, g, b, a] = color; // the masks's blue color
  const arr = new Uint8ClampedArray(4 * width * height).fill(0);
  for (let i = 0; i < input.length; i++) {
    // Threshold the onnx model mask prediction at 0.0
    // This is equivalent to thresholding the mask using predictor.model.mask_threshold
    // in python
    if (input[i] > 0.0) {
      arr[4 * i + 0] = r;
      arr[4 * i + 1] = g;
      arr[4 * i + 2] = b;
      arr[4 * i + 3] = a;
    }
  }
  return new ImageData(arr, height, width);
}

// Use a Canvas element to produce an image from ImageData
export function imageDataToImage(imageData: ImageData) {
  const canvas = imageDataToCanvas(imageData);
  const image = new Image();
  image.src = canvas.toDataURL();
  return image;
}

// Canvas elements can be created from ImageData
export function imageDataToCanvas(imageData: ImageData) {
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  canvas.width = imageData.width;
  canvas.height = imageData.height;
  ctx?.putImageData(imageData, 0, 0);
  return canvas;
}

// Convert the onnx model mask output to an HTMLImageElement
export function onnxMaskToImage(input: any, width: number, height: number) {
  return imageDataToImage(arrayToImageData(input, width, height));
}

export function changeImageColor(
  imageElement: HTMLImageElement,
  newColor: [number, number, number] = [0, 1, 0]
) {
  // Create a hidden canvas element
  const canvas = document.createElement("canvas");
  canvas.id = "hiddenCanvas";
  document.body.appendChild(canvas);

  // Get the image dimensions
  const width = imageElement.width;
  const height = imageElement.height;

  // Set canvas dimensions
  canvas.width = width;
  canvas.height = height;

  // Get the 2D context of the canvas
  const context = canvas.getContext("2d");

  // Draw the image onto the canvas
  if (context) {
    context.drawImage(imageElement, 0, 0, width, height);

    // Get the image data
    const imageData = context.getImageData(0, 0, width, height);
    const data = imageData.data;

    // Loop through each pixel and change the color
    for (let i = 0; i < data.length; i += 4) {
      // Change the color of each pixel to the new color
      data[i] = newColor[0]; // Red component
      data[i + 1] = newColor[1]; // Green component
      data[i + 2] = newColor[2]; // Blue component
      // Alpha component (transparency) remains unchanged
    }

    // Put the modified image data back onto the canvas
    context.putImageData(imageData, 0, 0);
  }

  // Replace the original image with the modified image
  const newImg = new Image(imageElement.width, imageElement.height);
  newImg.src = canvas.toDataURL();

  // Remove the hidden canvas
  document.body.removeChild(canvas);
  return newImg;

}
