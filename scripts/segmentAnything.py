import os

import click
import cv2
import numpy as np
from segment_anything import SamPredictor, sam_model_registry


@click.command()
@click.argument('input_path', type=click.Path(exists=True, dir_okay=False))
@click.argument(
    'output_path', type=click.Path(dir_okay=False), required=False, default=None
)
def main(input_path, output_path):
    checkpoint = 'sam_vit_h_4b8939.pth'
    model_type = 'vit_h'

    # Load the SAM model
    sam = sam_model_registry[model_type](checkpoint=checkpoint)
    sam.to(device='cpu')

    # Create a predictor
    predictor = SamPredictor(sam)

    # Read the input image
    image = cv2.imread(input_path)

    # Set the image for prediction
    predictor.set_image(image)

    # Get image embedding
    image_embedding = predictor.get_image_embedding().cpu().numpy()

    # Determine the output path
    if output_path is None:
        input_dir = os.path.dirname(input_path)
        input_filename = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(input_dir, f'{input_filename}.npy')

    # Save the output npy file
    np.save(output_path, image_embedding)


if __name__ == '__main__':
    main()
