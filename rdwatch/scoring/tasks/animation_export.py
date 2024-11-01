import logging
import os
import tempfile
import time
import zipfile
from datetime import datetime
from typing import Any

import cv2
import numpy as np
from celery import group, shared_task, states
from celery.result import GroupResult
from PIL import Image, ImageDraw
from pydantic import UUID4

from django.contrib.auth.models import User
from django.contrib.gis.geos import Point, Polygon
from django.core.files import File
from django.db.models import Q

from rdwatch.celery import app
from rdwatch.core.tasks import ToMeters
from rdwatch.core.tasks.animation_export import (
    GenerateAnimationSchema,
    draw_text_in_box,
    paste_image_with_bbox,
    rescale_bbox,
    to_pixel_coords,
)
from rdwatch.scoring.models import (
    AnimationModelRunExport,
    AnimationSiteExport,
    AnnotationProposalObservation,
    AnnotationProposalSite,
    EvaluationRun,
    Observation,
    Site,
    SiteImage,
)

logger = logging.getLogger(__name__)

label_mapping = {
    'Active Construction': {
        'color': (192, 0, 0),
        'label': 'Active Construction',
    },
    'Post Construction': {
        'color': (91, 155, 213),
        'label': 'Post Construction',
    },
    'Site Preparation': {
        'color': (255, 217, 102),
        'label': 'Site Preparation',
    },
    'Unknown': {
        'color': (112, 48, 160),
        'label': 'Unknown',
    },
    'No Activity': {
        'color': (166, 166, 166),
        'label': 'No Activity',
    },
    'Positive Annotated': {
        'color': (127, 0, 0),
        'label': 'Positive Annotated',
    },
    'Positive Partial': {
        'color': (0, 0, 139),
        'label': 'Positive Partial',
    },
    'Positive Annotated Static': {
        'color': (255, 140, 0),
        'label': 'Positive Annotated Static',
    },
    'Positive Partial Static': {
        'color': (255, 255, 0),
        'label': 'Positive Partial Static',
    },
    'Positive Pending': {
        'color': (30, 144, 255),
        'label': 'Positive Pending',
    },
    'Positive Excluded': {
        'color': (0, 255, 255),
        'label': 'Positive Excluded',
    },
    'Negative': {
        'color': (255, 0, 255),
        'label': 'Negative',
    },
    'Ignore': {
        'color': (0, 255, 0),
        'label': 'Ignore',
    },
    'Transient Positive': {
        'color': (255, 105, 180),
        'label': 'Transient Positive',
    },
    'Transient Negative': {
        'color': (255, 228, 196),
        'label': 'Transient Negative',
    },
    'System Proposed': {
        'color': (31, 119, 180),
        'label': 'System Proposed',
    },
    'System Confirmed': {
        'color': (31, 119, 180),
        'label': 'System Confirmed',
    },
    'System Rejected': {
        'color': (31, 119, 180),
        'label': 'System Rejected',
    },
}


def find_closest_observation(site_uuid, timestamp, model='Observation'):
    if model == 'Observation':
        observation_model = Observation
    elif model == 'AnnotationProposalObservation':
        observation_model = AnnotationProposalObservation
    else:
        raise ValueError(
            "Invalid model. Choose either 'Observation' or 'AnnotationProposalObservation'."
        )

    # Fetch the closest observation where the date is before the SiteImage timestamp
    closest_observation = (
        observation_model.objects.filter(site_uuid=site_uuid, date__lte=timestamp)
        .order_by('-date')
        .first()
    )

    return closest_observation


@shared_task
def create_animation(self, site_evaluation_id: UUID4, settings: dict[str, Any]):
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
        site_evaluation = Site.objects.get(uuid=site_evaluation_id)
        site_label = site_evaluation.status_annotated or site_evaluation.point_status
    except Site.DoesNotExist:
        site_evaluation = AnnotationProposalSite.objects.get(
            annotation_proposal_set_uuid=site_evaluation_id
        )
        site_label = site_evaluation.status
    except AnnotationProposalSite.DoesNotExist:
        return False, False

    # Determine the largest dimensions
    images_data = []

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
            query &= Q(
                observation__isnull=False
            )  # TODO Check if it needs to change _isempty or something like that
        if 'nonobs' in filters['include'] and len(filters['include']) == 1:
            query &= Q(
                observation__isnull=True
            )  # TODO check if it needs to change _isempty or something like taht

    images = SiteImage.objects.filter(query).order_by('timestamp')

    if len(images) == 0:
        logger.debug('No Images found returning')
        return False, False
    total_images = len(images)
    max_image_record = None
    max_width_px, max_height_px = 0, 0
    for image_record in images.iterator():
        if image_record.image:
            img = Image.open(image_record.image)
            width, height = image_record.image_dimensions
            images_data.append((img, width, height, image_record))

            # Check if the current image has the maximum width and height
            if width >= max_width_px and height >= max_height_px:
                max_width_px = width
                max_height_px = height
                max_image_record = image_record

    while max_width_px < 500 or max_height_px < 500:
        max_width_px *= 2
        max_height_px *= 2

    # using the max_image_bbox we apply the rescale_border
    if rescale:
        # Need the geometry base site evaluation bbox plus 20% around it for rescaling
        if site_evaluation.union_geometry:
            max_image_bbox = Polygon.from_ewkt(site_evaluation.union_geometry).extent
        if site_evaluation.point_geometry:
            tempbox: tuple[float, float, float, float] = Polygon.from_ewkt(
                site_evaluation.point_geometry
            ).extent
            if (
                tempbox[2] == tempbox[0] and tempbox[3] == tempbox[1]
            ):  # create bbox based on point
                size_diff = (500 * 0.5) / ToMeters
                tempbox = [
                    tempbox[0] - size_diff,
                    tempbox[1] - size_diff,
                    tempbox[2] + size_diff,
                    tempbox[3] + size_diff,
                ]
            max_image_bbox = tempbox

        # SCORING GEOMETRY IS STORED IN 4326
        max_image_bbox = rescale_bbox(max_image_bbox, 1.2)

        # Rescale the large box larger based on the rescale border
        output_bbox_size = rescale_bbox(max_image_bbox, rescale_border)
        rescaled_image_bbox_width = output_bbox_size[2] - output_bbox_size[0]
        rescaled_image_bbox_height = output_bbox_size[3] - output_bbox_size[1]

        # Determine pixels per unit for the rescaled image
        # This is used to determine the size of the output image
        max_image_record_bbox = max_image_record.image_bbox.extent
        x_pixel_per_unit = max_width_px / (
            max_image_record_bbox[2] - max_image_record_bbox[0]
        )
        y_pixel_per_unit = max_height_px / (
            max_image_record_bbox[3] - max_image_record_bbox[1]
        )
        # Update the rescaled max dimensions
        rescaled_max_width = int(rescaled_image_bbox_width * x_pixel_per_unit)
        rescaled_max_height = int(rescaled_image_bbox_height * y_pixel_per_unit)
        upscaled = False
        base_rescaled_max_width = rescaled_max_width
        base_rescaled_max_height = rescaled_max_height
        if rescaled_max_width < 500 or rescaled_max_height < 500:
            while rescaled_max_width < 500 or rescaled_max_height < 500:
                rescaled_max_width *= 2
                rescaled_max_height *= 2
                x_pixel_per_unit = rescaled_max_width / rescaled_image_bbox_width
                y_pixel_per_unit = rescaled_max_height / rescaled_image_bbox_height
            upscaled = True

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
            img = img.resize((max_width_px, max_height_px), Image.Resampling.NEAREST)
        draw = ImageDraw.Draw(img)

        # Extract image dimensions and bounding box
        if not image_record.image_dimensions or not image_record.image_bbox:
            continue

        bbox = image_record.image_bbox.extent  # minx, miny, maxx, maxy
        # bbox = transformer_other.transform_bounds(bbox[0], bbox[1], bbox[2], bbox[3])

        widthScale = max_width_px / width
        heightScale = max_height_px / height
        xScale = (width / (bbox[2] - bbox[0])) * widthScale
        yScale = (height / (bbox[3] - bbox[1])) * heightScale

        if rescale:
            # We draw the max_image_record bbox polygon on the center of the screen
            bbox = max_image_record.image_bbox.extent

            bbox_transform = bbox
            xScale = max_width_px / (bbox_transform[2] - bbox_transform[0])
            yScale = max_height_px / (bbox_transform[3] - bbox_transform[1])
            if upscaled:
                xScale = xScale * (rescaled_max_width / base_rescaled_max_width)
                yScale = yScale * (rescaled_max_height / base_rescaled_max_height)

            x_offset = (bbox_transform[0] - output_bbox_size[0]) * xScale
            y_offset = (bbox_transform[1] - output_bbox_size[1]) * yScale
            bbox = bbox_transform

        # Draw geometry or point on the image
        # observation is a string we need the object for it
        try:
            observation = find_closest_observation(
                site_evaluation_id, image_record.timestamp
            )
        except Observation.DoesNotExist:
            try:
                observation = find_closest_observation(
                    site_evaluation_id,
                    image_record.timestamp,
                    'AnnotationProposalObservation',
                )
            except AnnotationProposalObservation.DoesNotExist:
                observation = None
        if observation:
            polygon = Polygon.from_ewkt(observation.geometry)
            label = observation.phase
            label_mapped = label_mapping.get(label, {})
        elif not polygon:
            if site_evaluation.union_geometry:
                polygon = Polygon.from_ewkt(site_evaluation.union_geometry)
            if site_evaluation.point_geometry:
                point = Point.from_ewkt(site_evaluation.point_geometry)

            label_mapped = label_mapping.get(site_label.replace(' ', '_'), {})
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
                color = label_mapped.get('color', (255, 255, 255))
                draw.polygon(pixel_coords, outline=color)
            elif polygon.geom_type == 'MultiPolygon':
                # Handle MultiPolygon by iterating over each polygon
                for poly in polygon:
                    base_coords = poly.coords[
                        0
                    ]  # Get the exterior coordinates of the Polygon
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
                    color = label_mapped.get('color', (255, 255, 255))
                    draw.polygon(pixel_coords, outline=color)
        if not polygon and observation:
            # Probably an error because I don't think we
            # support observation points in the scoring DB
            raise ValueError(
                "Polygon not found in Observation and Points aren't supported"
            )
        if point and 'geom' in labels:
            transformed_point = (point.x, point.y)
            pixel_point = to_pixel_coords(
                transformed_point[0],
                transformed_point[1],
                bbox,
                xScale,
                yScale,
                x_offset,
                y_offset,
            )
            color = label_mapped.get('color', (255, 255, 255))
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
                label_mapped.get('color', (255, 255, 255)),
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
                site_label_mapped.get('color', (255, 255, 255)),
            )

        frames.append(img)
        np_array.append(np.array(img))  # Convert PIL image to NumPy array
        count += 1

    # Save frames as an animated GIF
    evaluation_run = site_evaluation.evaluation_run_uuid
    base_str = f'Eval_{evaluation_run.evaluation_number}_{evaluation_run.evaluation_run_number}_{evaluation_run.performer}'  # noqa: E501
    prefix = f'{base_str}_{str(site_evaluation.site_id)}'
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
    self, site_evaluation_id: UUID4, settings: dict[str, Any], userId: int
):
    task_id = self.request.id
    try:
        site_evaluation = Site.objects.get(pk=site_evaluation_id)
    except Site.DoesNotExist:
        site_evaluation = AnnotationProposalSite.object.get(pk=site_evaluation_id)
    user = User.objects.get(pk=userId)
    site_export = AnimationSiteExport(
        name='',
        created=datetime.now(),
        site_evaluation=site_evaluation.uuid,
        user=user,
        celery_id=task_id,
        arguments=settings,
    )
    # try:
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
    # except Exception as e:
    #     logger.warning(f'Error when processing Animation: {e}')
    #     if site_export:
    #         site_export.delete()


@app.task(bind=True)
def create_modelrun_animation_export(
    self, modelrun_id: UUID4, settings: dict[str, Any], userId: int
):
    task_id = self.request.id
    model_run = EvaluationRun.objects.get(pk=modelrun_id)
    user = User.objects.get(pk=userId)
    title = f'Eval_{model_run.evaluation_number}_{model_run.evaluation_run_number}_{model_run.performer}'  # noqa: E501
    modelrun_export, created = AnimationModelRunExport.objects.get_or_create(
        name=title,
        created=datetime.now(),
        configuration=modelrun_id,
        user=user,
        celery_id=task_id,
        arguments=settings,
    )

    # Now we create a task for each site in the image that has information
    site_tasks = []
    for site in Site.objects.filter(evaluation_run_uuid=modelrun_id).iterator():
        if SiteImage.objects.filter(site=site.pk).exists():
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
    with zipfile.ZipFile(zip_filepath, 'w') as zip_file:
        for export in exports.iterator():
            if export.export_file and export.export_file.name:
                site_evaluation = Site.objects.get(uuid=export.site_evaluation)
                # Open the file and write its content to the zip archive
                format = export.arguments['output_format']
                site_number = str(site_evaluation.site_id)
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
