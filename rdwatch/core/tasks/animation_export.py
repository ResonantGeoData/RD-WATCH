import logging
import os
import tempfile
import time
import zipfile
from datetime import datetime
from typing import Literal

import cv2
import numpy as np
from celery import group, shared_task, states
from celery.result import GroupResult
from PIL import Image, ImageDraw, ImageFont
from pydantic import UUID4, BaseModel, Field
from pyproj import Transformer

from django.contrib.auth.models import User
from django.core.files import File
from django.db.models import Q

from rdwatch.celery import app
from rdwatch.core.models import (
    AnimationModelRunExport,
    AnimationSiteExport,
    ModelRun,
    SiteEvaluation,
    SiteImage,
)

logger = logging.getLogger(__name__)

label_mapping = {
    'active_construction': {
        'color': (192, 0, 0),
        'label': 'Active Construction',
    },
    'post_construction': {
        'color': (91, 155, 213),
        'label': 'Post Construction',
    },
    'site_preparation': {
        'color': (255, 217, 102),
        'label': 'Site Preparation',
    },
    'unknown': {
        'color': (112, 48, 160),
        'label': 'Unknown',
    },
    'no_activity': {
        'color': (166, 166, 166),
        'label': 'No Activity',
    },
    'positive_annotated': {
        'color': (127, 0, 0),
        'label': 'Positive Annotated',
    },
    'positive': {
        'color': (127, 0, 0),
        'label': 'Positive Annotated',
    },
    'positive_partial': {
        'color': (0, 0, 139),
        'label': 'Positive Partial',
    },
    'positive_annotated_static': {
        'color': (255, 140, 0),
        'label': 'Positive Annotated Static',
    },
    'positive_partial_static': {
        'color': (255, 255, 0),
        'label': 'Positive Partial Static',
    },
    'positive_pending': {
        'color': (30, 144, 255),
        'label': 'Positive Pending',
    },
    'positive_excluded': {
        'color': (0, 255, 255),
        'label': 'Positive Excluded',
    },
    'negative': {
        'color': (255, 0, 255),
        'label': 'Negative',
    },
    'ignore': {
        'color': (0, 255, 0),
        'label': 'Ignore',
    },
    'transient_positive': {
        'color': (255, 105, 180),
        'label': 'Transient Positive',
    },
    'transient_negative': {
        'color': (255, 228, 196),
        'label': 'Transient Negative',
    },
    'system_proposed': {
        'color': (31, 119, 180),
        'label': 'System Proposed',
    },
    'system_confirmed': {
        'color': (31, 119, 180),
        'label': 'System Confirmed',
    },
    'system_rejected': {
        'color': (31, 119, 180),
        'label': 'System Rejected',
    },
}


def rescale_bbox(bbox, scale):
    """
    Rescales a bounding box by a given scaling factor.

    Parameters:
    bbox (list): A list containing [minx, miny, maxx, maxy].
    scale (float): The scaling factor to apply to the bounding box.

    Returns:
    list: A list containing the rescaled [minx, miny, maxx, maxy].
    """
    minx, miny, maxx, maxy = bbox

    center_x = (minx + maxx) / 2
    center_y = (miny + maxy) / 2

    width = (maxx - minx) * scale / 2
    height = (maxy - miny) * scale / 2

    return [center_x - width, center_y - height, center_x + width, center_y + height]


def paste_image_with_bbox(
    source_image,
    bbox,
    pixel_per_unit_x,
    pixel_per_unit_y,
    output_width,
    output_height,
    output_bbox,
    output_pixel_per_unit_x,
    output_pixel_per_unit_y,
):
    """
    Pastes a source image into an output image based on matching bounding box coordinates,
    with different pixel-per-unit scales for the X and Y axes.

    Parameters:
    source_image_path (Image): source image.
    bbox (list): Bounding box of the source image in the format [minx, miny, maxx, maxy].
    pixel_per_unit_x (float): Pixels per unit for the X-axis of the source image.
    pixel_per_unit_y (float): Pixels per unit for the Y-axis of the source image.
    output_width (int): Width of the output image.
    output_height (int): Height of the output image.
    output_bbox (list): Bounding box of the output image in the format [minx, miny, maxx, maxy].
    output_pixel_per_unit_x (float): Pixels per unit for the X-axis of the output image.
    output_pixel_per_unit_y (float): Pixels per unit for the Y-axis of the output image.

    Returns:
    Image: The output image with the source image pasted in.
    """

    # Calculate the dimensions of the source image in pixels
    source_width_px = int((bbox[2] - bbox[0]) * pixel_per_unit_x)
    source_height_px = int((bbox[3] - bbox[1]) * pixel_per_unit_y)

    rescale_x_factor = output_pixel_per_unit_y / pixel_per_unit_y
    rescale_y_factor = output_pixel_per_unit_x / pixel_per_unit_x
    rescale_x = int(rescale_x_factor * source_width_px)
    rescale_y = int(rescale_y_factor * source_height_px)
    # logger.warning(f'\tRescaling Source: {source_width_px} {source_height_px}')
    # logger.warning(f'\tRescale Size: {rescale_x} {rescale_y}')
    # logger.warning(f'\tRescaling Factor: {rescale_x_factor} {rescale_y_factor}')
    rescaled_source_image = source_image.resize((rescale_x, rescale_y))

    # determine what section of the new image to grab based on the output_bbox_size
    # this requires finding the difference between the source and output
    crop = (
        (output_bbox[0] - bbox[0]) * output_pixel_per_unit_x,
        (output_bbox[1] - bbox[1]) * output_pixel_per_unit_y,
        (output_bbox[2] - bbox[0]) * output_pixel_per_unit_x,
        (output_bbox[3] - bbox[1]) * output_pixel_per_unit_y,
    )
    # logger.warning(f'\tCrop: {crop}')
    cropped_img = rescaled_source_image.crop(
        (crop[0], crop[1], crop[2], crop[3])
    )  # left, top, right, bottom
    # image needs to be recentered
    gray_value = 128
    gray_color = (gray_value, gray_value, gray_value, 0)
    output_image = Image.new('RGBA', (output_width, output_height), gray_color)

    # Paste the source image into the output image
    output_image.paste(cropped_img)

    return output_image


def to_pixel_coords(lon, lat, bbox, xScale, yScale, xOffset=0, yOffset=0):
    x = (lon - bbox[0]) * xScale + xOffset
    y = (bbox[3] - lat) * yScale + yOffset
    return x, y


def draw_text_in_box(
    draw,
    text,
    position,
    box_size,
    box_color=(80, 80, 80),
    text_color=(255, 255, 255),
    font_path=None,
    initial_font_size=30,
):
    """
    Draws text within a given box with adjustable font size and a background square.
    If the text is larger than the box, the box size is adjusted to fit the text.

    :param draw: ImageDraw object to draw on the image.
    :param text: Text to draw.
    :param position: Position (x, y) to start drawing the box and text.
    :param box_size: Tuple (width, height) specifying the initial box size.
    :param box_color: Background color of the box (R, G, B).
    :param text_color: Color of the text (R, G, B).
    :param font_path: Path to a .ttf font file, or None to use default font.
    :param initial_font_size: Starting font size.
    """
    max_width, max_height = box_size

    # Load font
    def get_font(size):
        return (
            ImageFont.truetype(font_path, size)
            if font_path
            else ImageFont.load_default(size)
        )

    # Binary search for the optimal font size
    low, high = 10, initial_font_size
    best_font_size = low
    best_text_bbox = None

    while low <= high:
        mid = (low + high) // 2
        font = get_font(mid)
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        if text_width <= max_width and text_height <= max_height:
            best_font_size = mid
            best_text_bbox = text_bbox
            low = mid + 1
        else:
            high = mid - 1

    # Use the best font size found
    font = get_font(best_font_size)
    best_text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = best_text_bbox[2] - best_text_bbox[0]
    text_height = best_text_bbox[3] - best_text_bbox[1]

    # Adjust the box size if the text is larger
    box_width = max(text_width, max_width)
    box_height = max(text_height, max_height)

    # Draw background box
    text_x = position[0] + (box_width - text_width) / 2
    text_y = position[1] + (box_height - text_height) / 2

    draw.rectangle(
        [position, (text_x + box_width, text_y + box_height)], fill=box_color
    )
    # Draw text
    draw.text((text_x, text_y), text, font=font, fill=text_color)


class GenerateAnimationSchema(BaseModel):
    output_format: Literal['mp4', 'gif'] = 'mp4'
    fps: int = Field(1, ge=1)  # FPS should be an integer >= 1
    point_radius: int = Field(5, ge=1)  # Point radius should be an integer >= 1
    sources: list[Literal['WV', 'S2', 'L8', 'PL']] = ['WV', 'S2', 'L8', 'PL']
    labels: list[Literal['geom', 'date', 'source', 'obs', 'obs_label']] = [
        'geom',
        'date',
        'source',
        'obs',
        'obs_label',
    ]
    cloudCover: float | None = 100
    noData: float | None = 100
    include: list[Literal['obs', 'nonobs']] = ['obs', 'nonobs']
    rescale: bool = False
    rescale_border: int = Field(1, ge=0)  # Border rescale should be an integer >= 0


@shared_task
def create_animation(
    self, site_evaluation_id: UUID4, settings: GenerateAnimationSchema
):
    settingsSchema = GenerateAnimationSchema(**settings)
    output_format = settingsSchema.output_format
    fps = settingsSchema.fps
    point_radius = settingsSchema.point_radius
    sources = settingsSchema.sources
    labels = settingsSchema.labels
    rescale = settingsSchema.rescale
    rescale_border = settingsSchema.rescale_border
    filters = {
        'cloudCover': settingsSchema.cloudCover,
        'noData': settingsSchema.noData,
        'include': settingsSchema.include,
    }

    # Fetch the SiteEvaluation instance
    try:
        site_evaluation = SiteEvaluation.objects.get(id=site_evaluation_id)
    except SiteEvaluation.DoesNotExist:
        return False, False

    # Determine the largest dimensions
    images_data = []
    # Create a transformer from EPSG:3857 to EPSG:4326
    transformer_other = Transformer.from_crs('epsg:4326', 'epsg:3857', always_xy=True)

    site_label = site_evaluation.label.slug
    site_label_mapped = label_mapping.get(site_label, False)

    query = Q(site=site_evaluation_id, source__in=sources)

    # Apply cloudCover filter if provided
    if filters.get('cloudCover') is not None:
        query &= Q(cloudcover__lt=filters['cloudCover'])

    # Apply noData filter (percent_black) if provided
    if filters.get('noData') is not None:
        query &= Q(percent_black__lt=filters['noData'])

    # Apply include filter for observation
    if filters.get('include'):
        if 'obs' in filters['include'] and len(filters['include']) == 1:
            query &= Q(observation__isnull=False)
        if 'nonobs' in filters['include'] and len(filters['include']) == 1:
            query &= Q(observation__isnull=True)

    images = SiteImage.objects.filter(query).order_by('timestamp')

    if len(images) == 0:
        logger.warning('No Images found returning')
        return False, False
    total_images = len(images)
    max_image_record = None
    max_width_px, max_height_px = 0, 0
    for image_record in images:
        if image_record.image:
            img = Image.open(image_record.image)
            width, height = image_record.image_dimensions
            images_data.append((img, width, height, image_record))

            # Check if the current image has the maximum width and height
            if width >= max_width_px and height >= max_height_px:
                max_width_px = width
                max_height_px = height
                max_image_record = image_record

    if max_width_px < 500 or max_height_px < 500:
        new_height = (max_height_px / max_width_px) * 500
        max_width_px = int(500)
        max_height_px = int(new_height)

    # using the max_image_bbox we apply the rescale_border
    if rescale:
        # Need the geometry base site evaluation bbox plus 20% around it for rescaling
        max_image_bbox = site_evaluation.geom.extent
        max_image_bbox = rescale_bbox(max_image_bbox, 1.2)

        # Rescale the large box larger based on the rescale border
        output_bbox_size = rescale_bbox(max_image_bbox, rescale_border)
        rescaled_image_bbox_width = output_bbox_size[2] - output_bbox_size[0]
        rescaled_image_bbox_height = output_bbox_size[3] - output_bbox_size[1]

        # Determine pixels per unit for the rescaled image
        # This is used to determine the size of the output image
        max_image_record_bbox = max_image_record.image_bbox.extent
        max_image_record_bbox = transformer_other.transform_bounds(
            max_image_record_bbox[0],
            max_image_record_bbox[1],
            max_image_record_bbox[2],
            max_image_record_bbox[3],
        )

        x_pixel_per_unit = max_width_px / (
            max_image_record_bbox[2] - max_image_record_bbox[0]
        )
        y_pixel_per_unit = max_height_px / (
            max_image_record_bbox[3] - max_image_record_bbox[1]
        )
        logger.warning('PixelPerUnit : {x_pixel_perunit}, {y_pixel_per_unit}')
        logger.warning(
            f'Rescaled: {rescaled_image_bbox_width} {rescaled_image_bbox_height}'
        )
        # Update the rescaled max dimensions
        rescaled_max_width = int(rescaled_image_bbox_width * x_pixel_per_unit)
        rescaled_max_height = int(rescaled_image_bbox_height * y_pixel_per_unit)
    else:
        x_offset = 0
        y_offset = 0
    frames = []
    np_array = []
    polygon = None
    point = None
    count = 0
    for img, width, height, image_record in images_data:
        if img.mode in ('L', 'LA'):  # 'L' for grayscale, 'LA' for grayscale with alpha
            # Convert grayscale to RGB
            img = img.convert('RGB')

        self.update_state(
            state='PROGRESS',
            meta={
                'current': count,
                'total': total_images,
                'mode': 'Rendering Images',
                'siteEvalId': site_evaluation_id,
            },
        )
        if rescale:
            bbox = image_record.image_bbox.extent  # minx, miny, maxx, maxy
            # place into the same pixel coordinate system
            bbox = transformer_other.transform_bounds(
                bbox[0], bbox[1], bbox[2], bbox[3]
            )
            local_bbox_width = bbox[2] - bbox[0]
            local_bbox_height = bbox[3] - bbox[1]
            # get the local pixel per unit
            local_x_pixel_scale = width / local_bbox_width
            local_y_pixel_scale = height / local_bbox_height
            img = paste_image_with_bbox(
                img,
                bbox,
                local_x_pixel_scale,
                local_y_pixel_scale,
                rescaled_max_width,
                rescaled_max_height,
                output_bbox_size,
                x_pixel_per_unit,
                y_pixel_per_unit,
            )
            x_offset = 0
            y_offset = 0
        else:
            img = img.resize((max_width_px, max_height_px))
        draw = ImageDraw.Draw(img)

        # Extract image dimensions and bounding box
        if not image_record.image_dimensions or not image_record.image_bbox:
            continue

        bbox = image_record.image_bbox.extent  # minx, miny, maxx, maxy
        bbox = transformer_other.transform_bounds(bbox[0], bbox[1], bbox[2], bbox[3])

        widthScale = max_width_px / width
        heightScale = max_height_px / height
        xScale = (width / (bbox[2] - bbox[0])) * widthScale
        yScale = (height / (bbox[3] - bbox[1])) * heightScale

        if rescale:
            # We draw the max_image_record bbox polygon on the center of the screen
            bbox = max_image_record.image_bbox.extent
            xScale = max_width_px / (bbox[2] - bbox[0])
            yScale = max_height_px / (bbox[3] - bbox[1])
            # We need the bbox offset size based on the transform bounds difference
            bbox_transform = transformer_other.transform_bounds(
                bbox[0], bbox[1], bbox[2], bbox[3]
            )
            xScale = max_width_px / (bbox_transform[2] - bbox_transform[0])
            yScale = max_height_px / (bbox_transform[3] - bbox_transform[1])

            x_offset = (bbox_transform[0] - output_bbox_size[0]) * xScale
            y_offset = (bbox_transform[1] - output_bbox_size[1]) * yScale
            bbox = bbox_transform

        # Draw geometry or point on the image
        observation = image_record.observation
        if observation:
            polygon = observation.geom
            label = observation.label
            label_mapped = label_mapping.get(label.slug, {})
        elif not polygon:
            polygon = site_evaluation.geom
            label_mapped = label_mapping.get(site_evaluation.label.slug, {})
            site_evaluation.label
        if polygon and 'geom' in labels:
            if polygon.geom_type == 'Polygon':
                base_coords = polygon.coords[0]
                transformed_coords = [(lon, lat) for lon, lat in base_coords]

                pixel_coords = [
                    to_pixel_coords(
                        lon,
                        lat,
                        bbox,
                        xScale,
                        yScale,
                        x_offset,
                        y_offset,
                    )
                    for lon, lat in transformed_coords
                ]
                color = label_mapped.get('color', (256, 256, 256))
                draw.polygon(pixel_coords, outline=color)
        if not polygon and observation:
            point = observation.point
        if not point:
            point = site_evaluation.point
        if point and 'geom' in labels:
            transformed_point = (point.x, point.y)
            pixel_point = to_pixel_coords(
                transformed_point[0], transformed_point[1], bbox, xScale, yScale
            )
            color = label_mapped.get('color', (256, 256, 256))
            draw.ellipse(
                (
                    pixel_point[0] - point_radius,
                    pixel_point[1] - point_radius,
                    pixel_point[0] + point_radius,
                    pixel_point[1] + point_radius,
                ),
                outline=color,
            )

        # Drawing labels of timestamp
        ui_max_width = max_width_px
        ui_max_height = max_height_px
        if rescale:
            ui_max_width = rescaled_max_width
            ui_max_height = rescaled_max_height
        center = (ui_max_width / 2.0, ui_max_height / 2.0)
        # Draw date as 1/3 of the center of the image at the top
        date_width = ui_max_width / 3.0
        date_height = max(ui_max_height / 15.0, 10)
        date_box_point = (center[0] - (date_width / 2.0), 0)
        date_box_size = (date_width, date_height)
        if 'date' in labels:
            draw_text_in_box(
                draw,
                image_record.timestamp.strftime('%Y-%m-%d'),
                date_box_point,
                date_box_size,
            )
        # Draw Source
        source_point = (0, 0)
        source_size = (ui_max_width / 10.0, date_height)
        if 'source' in labels:
            draw_text_in_box(
                draw,
                image_record.source,
                source_point,
                source_size,
            )
        # Draw Observation
        obs_width = ui_max_width / 10.0
        obs_point = (ui_max_width - obs_width, 0)
        obs_size = (ui_max_width / 10.0, date_height)
        obs_text = '+obs'
        if image_record.observation is None:
            obs_text = '-obs'
        if 'obs' in labels:
            draw_text_in_box(
                draw,
                obs_text,
                obs_point,
                obs_size,
            )
        # Draw Label
        label_width = ui_max_width / 3.0
        label_height = max(ui_max_height / 15.0, 10)

        label_point = (center[0] - (label_width / 2.0), ui_max_height - label_height)
        label_size = (label_width, label_height)
        if 'obs_label' in labels and label_mapped:
            draw_text_in_box(
                draw,
                label_mapped['label'],
                label_point,
                label_size,
                label_mapped.get('color', (256, 256, 256)),
            )
        if 'site_label' in labels and site_label_mapped:
            site_label_point = (
                center[0] - (label_width / 2.0),
                ui_max_height - (label_height * 2),
            )
            draw_text_in_box(
                draw,
                site_label_mapped['label'],
                site_label_point,
                label_size,
                site_label_mapped.get('color', (256, 256, 256)),
            )

        frames.append(img)
        np_array.append(np.array(img))  # Convert PIL image to NumPy array
        count += 1

    # Save frames as an animated GIF
    prefix = f'{site_evaluation.configuration.title.strip()}\
        _{site_evaluation.configuration.region.name}\
            _{str(site_evaluation.number).zfill(4)}'
    if frames:
        # Create a temporary directory
        self.update_state(
            state='Progress',
            meta={
                'current': count,
                'total': total_images,
                'mode': f'Generating {output_format.upper()}',
                'siteEvalId': site_evaluation_id,
            },
        )

        output_dir = '/tmp/animation'
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        if output_format == 'gif':
            # Create a temporary file for GIF
            temp_file = tempfile.NamedTemporaryFile(
                prefix=prefix, suffix='.gif', dir=output_dir, delete=False
            )
            with open(temp_file.name, 'w') as tmp_file:
                output_file_path = tmp_file.name
                frames[0].save(
                    output_file_path,
                    save_all=True,
                    append_images=frames[1:],
                    duration=1000.0 / fps,
                    loop=0,
                    optimize=False,
                    quality=100,
                )
        else:  # 'mp4'
            # Create a temporary file for MP4
            temp_file = tempfile.NamedTemporaryFile(
                prefix=prefix, suffix='.mp4', dir=output_dir, delete=False
            )
            with open(temp_file.name, 'w') as tmp_file:
                output_file_path = tmp_file.name

                # Initialize video writer
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                video_width = max_width_px
                video_height = max_height_px
                if rescale:
                    video_width = rescaled_max_width
                    video_height = rescaled_max_height
                video_writer = cv2.VideoWriter(
                    output_file_path, fourcc, fps, (video_width, video_height)
                )

                # Write each frame to the video
                for frame in np_array:
                    frame_bgr = cv2.cvtColor(
                        frame, cv2.COLOR_RGB2BGR
                    )  # Convert RGB to BGR for OpenCV
                    video_writer.write(frame_bgr)

                video_writer.release()  # Close the video writer
        name = f'{prefix}.{output_format}'
        self.update_state(
            state='SUCCESS',
            meta={
                'current': count,
                'total': total_images,
                'mode': 'Rendering Complete',
                'siteEvalId': site_evaluation_id,
            },
        )

        return output_file_path, name
    return False, False


@app.task(bind=True)
def create_site_animation_export(
    self, site_evaluation_id: UUID4, settings: GenerateAnimationSchema, userId: int
):
    task_id = self.request.id
    site_evaluation = SiteEvaluation.objects.get(pk=site_evaluation_id)
    user = User.objects.get(pk=userId)
    site_export = AnimationSiteExport(
        name='',
        created=datetime.now(),
        site_evaluation=site_evaluation,
        user=user,
        celery_id=task_id,
        arguments=settings,
    )
    try:
        site_export.celery_id = task_id
        site_export.save()
        file_path, name = create_animation(self, site_evaluation_id, settings)
        if file_path is False and name is False:
            logger.warning('No Images were found')
            site_export.delete()
            return
        site_export.name = name
        with open(file_path, 'rb') as file:
            site_export.export_file.save(name, File(file))
        site_export.save()
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.warning(f'Error when processing Animation: {e}')
        if site_export:
            site_export.delete()


@app.task(bind=True)
def create_modelrun_animation_export(
    self, modelrun_id: UUID4, settings: GenerateAnimationSchema, userId: int
):
    task_id = self.request.id
    model_run = ModelRun.objects.get(pk=modelrun_id)
    user = User.objects.get(pk=userId)
    modelrun_export, created = AnimationModelRunExport.objects.get_or_create(
        name='',
        created=datetime.now(),
        configuration=model_run,
        user=user,
        celery_id=task_id,
        arguments=settings,
    )
    # Now we create a task for each site in the image that has information
    site_evals = SiteEvaluation.objects.filter(configuration_id=modelrun_id)
    site_tasks = []
    for site in site_evals:
        if SiteImage.objects.filter(
            site=site.pk
        ).exists():  # Has images add it to the tasks
            site_tasks.append(create_site_animation_export.s(site.pk, settings, userId))

    subtasks = group(site_tasks)

    result: GroupResult = subtasks.apply_async()

    total = len(site_tasks)

    while not result.ready():
        completed_count = result.completed_count()
        # Update the main task state with the overall progress
        self.update_state(
            state=states.STARTED,
            meta={
                'mode': 'Processing Site Animations',
                'current': completed_count,
                'total': total,
            },
        )

        # Optionally, sleep for a while to avoid too frequent updates
        time.sleep(5)
    task_ids = [res.id for res in result.results]
    self.update_state(
        state=states.STARTED,
        meta={
            'mode': 'Generating Zip file',
            'current': completed_count,
            'total': total,
        },
    )
    # now we take each AnimationModelRunExport file and create a zip file for it
    exports = AnimationSiteExport.objects.filter(celery_id__in=task_ids)

    # Prepare to create a zip file
    zip_filename = f'modelrun_export_{modelrun_id}.zip'
    zip_filepath = os.path.join('/tmp', zip_filename)

    title = model_run.title
    with zipfile.ZipFile(zip_filepath, 'w') as zip_file:
        for export in exports:
            if export.export_file and export.export_file.name:
                # Open the file and write its content to the zip archive
                format = export.arguments['output_format']
                site_number = str(export.site_evaluation.number).zfill(4)
                output_name = f'{title}_{site_number}.{format}'
                with export.export_file.open('rb') as f:
                    file_data = f.read()
                    zip_file.writestr(output_name, file_data)

    # Save the zip file to the AnimationModelRunExport instance
    with open(zip_filepath, 'rb') as file:
        modelrun_export.export_file.save(zip_filename, File(file))

    modelrun_export.save()

    # Clean up temporary zip file
    if os.path.exists(zip_filepath):
        os.remove(zip_filepath)

    self.update_state(state=states.SUCCESS)
    return {'status': 'Completed', 'zip_file': modelrun_export.export_file.url}
