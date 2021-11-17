import json
import logging

from django.contrib import messages
from django.contrib.gis.db.models import Collect, Extent
from rgd import permissions
from rgd.views import PermissionListView, query_params

from . import filters, models

logger = logging.getLogger(__name__)


class _OutlineFieldListView(PermissionListView):
    paginate_by = 15

    def _get_extent_summary(self, object_list):
        ids = [o.pk for o in object_list]
        queryset = self.get_queryset().filter(pk__in=ids, outline__isnull=False)
        summary = queryset.aggregate(
            Collect('outline'),
            Extent('outline'),
        )
        extents = {
            'count': queryset.count(),
        }
        logger.info(summary)
        if queryset.count():
            extents.update(
                {
                    'collect': json.loads(summary['outline__collect'].geojson),
                    'convex_hull': json.loads(summary['outline__collect'].convex_hull.geojson),
                    'extent': {
                        'xmin': summary['outline__extent'][0],
                        'ymin': summary['outline__extent'][1],
                        'xmax': summary['outline__extent'][2],
                        'ymax': summary['outline__extent'][3],
                    },
                }
            )
        return extents

    def get_context_data(self, *args, **kwargs):
        # Pagination happens here
        context = super().get_context_data(*args, **kwargs)
        summary = self._get_extent_summary(context['object_list'])
        context['extents'] = json.dumps(summary)
        # Have a smaller dict of meta fields to parse for menu bar
        # This keeps us from parsing long GeoJSON fields twice
        meta = {
            'count': self.get_queryset().count(),  # This is the amount in the full results
        }
        context['extents_meta'] = json.dumps(meta)
        context['search_params'] = json.dumps(self.request.GET)
        context['query_params'] = query_params(self.request.GET)
        return context


class STACFileListView(_OutlineFieldListView):
    model = models.STACFile
    filter = filters.STACFileFilter
    context_object_name = 'objects'
    template_name = 'core/stacfile_list.html'

    def get_queryset(self):
        filterset = self.filter(data=self.request.GET)
        queryset = self.model.objects.order_by('pk')
        if not filterset.is_valid():
            message = 'Filter parameters illformed. Full results returned.'
            all_error_messages_content = [
                msg.message
                for msg in list(messages.get_messages(self.request))
                if msg.level_tag == 'error'
            ]
            if message not in all_error_messages_content:
                messages.add_message(self.request, messages.ERROR, message)
            return queryset
        queryset = filterset.filter_queryset(queryset)
        return permissions.filter_read_perm(self.request.user, queryset)
