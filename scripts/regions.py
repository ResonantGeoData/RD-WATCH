from watch_helpers import post_region_items_from_s3_iter

if __name__ == '__main__':
    # s3://kitware-smart-watch-data/scratch/kw/proposed_annotations_sample/
    post_region_items_from_s3_iter(
        bucket='kitware-smart-watch-data',
        prefix='scratch/kw/proposed_annotations_sample/regions',
        dry_run=False,
        sites=False,
    )
    post_region_items_from_s3_iter(
        bucket='kitware-smart-watch-data',
        prefix='scratch/kw/proposed_annotations_sample/sites',
        dry_run=False,
        sites=True,
    )
