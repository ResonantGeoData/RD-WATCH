from django.contrib.gis.db.models.functions import GeometryDistance
from django.contrib.gis.measure import D
from django_filters import rest_framework as filters
from rgd.filters import GeometryFilter

from .models import Observation, Region, Site, STACFile


class BaseOutlineFieldFilter(filters.FilterSet):

    q = GeometryFilter(
        help_text='A Well-known text (WKT) representation of a geometry or a GeoJSON.',
        label='WKT/GeoJSON',
        method='filter_q',
    )
    predicate = filters.ChoiceFilter(
        choices=(
            ('contains', 'contains'),
            ('crosses', 'crosses'),
            ('disjoint', 'disjoint'),
            ('equals', 'equals'),
            ('intersects', 'intersects'),
            ('overlaps', 'overlaps'),
            ('touches', 'touches'),
            ('within', 'within'),
        ),
        help_text=(
            'A named spatial predicate based on the DE-9IM. This spatial predicate will be used '
            'to filter data such that `predicate(a, b)` where `b` is the queried geometry.'
        ),
        label='Spatial predicate',
        method='filter_predicate',
    )
    distance = filters.RangeFilter(
        help_text='The minimum/maximum distance around the queried geometry in meters.',
        label='Distance',
        method='filter_distance',
    )

    @property
    def _geometry(self):
        return self.form.cleaned_data['q']

    @property
    def _has_geom(self):
        return self._geometry is not None

    def filter_q(self, queryset, name, value):
        """Sort the queryset by distance to queried geometry.

        Annotates the queryset with `distance`.
        This uses the efficient KNN operation:
        https://postgis.net/docs/geometry_distance_knn.html
        """
        queryset = queryset.filter(outline__isnull=False)
        if value:
            queryset = queryset.annotate(distance=GeometryDistance('outline', value)).order_by(
                'distance'
            )
        return queryset

    def filter_predicate(self, queryset, name, value):
        """Filter the polygon by the chosen predicate."""
        if value and self._has_geom:
            queryset = queryset.filter(**{f'outline__{value}': self._geometry})
        return queryset

    def filter_distance(self, queryset, name, value):
        """Filter the queryset by distance to the queried geometry.

        We may wish to use the distance in degrees later on. This is
        very taxing on the DBMS right now. The distance in degrees
        can be provided by the initial geometry query.
        """
        if value and self._has_geom:
            geom = self._geometry
            if value.start is not None:
                queryset = queryset.filter(outline__distance_gte=(geom, D(m=value.start)))
            if value.stop is not None:
                queryset = queryset.filter(outline__distance_lte=(geom, D(m=value.stop)))
        return queryset

    class Meta:
        fields = [
            'q',
            'predicate',
            'distance',
        ]


class STACFileFilter(BaseOutlineFieldFilter):
    server_modified = filters.IsoDateTimeFromToRangeFilter(
        field_name='server_modified',
        help_text='The ISO 8601 formatted date and time when data was modified on the server.',
        label='Acquired',
    )
    processed = filters.IsoDateTimeFromToRangeFilter(
        field_name='processed',
        help_text='The ISO 8601 formatted date and time when data was processed.',
        label='Acquired',
    )

    class Meta:
        model = STACFile
        fields = [
            'q',
            'predicate',
            'distance',
            'server_modified',
            'processed',
        ]


class RegionFilter(BaseOutlineFieldFilter):
    region_id = filters.CharFilter(
        field_name='region_id',
        help_text='The region_id.',
        label='Region ID',
        lookup_expr='icontains',
    )
    date = filters.DateFilter(method='date_filter')

    def date_filter(self, queryset, name, value):
        if value:
            queryset = queryset.filter(start_date__lte=value)
            queryset = queryset.filter(end_date__gte=value)
        return queryset

    class Meta:
        model = Region
        fields = [
            'q',
            'predicate',
            'distance',
            'region_id',
            'date',
        ]


class SiteFilter(BaseOutlineFieldFilter):
    site_id = filters.CharFilter(
        field_name='site_id',
        help_text='The site_id.',
        label='Site ID',
        lookup_expr='icontains',
    )
    region_id = filters.CharFilter(
        field_name='parent_region__region_id',
        help_text='The region_id.',
        label='Region ID',
        lookup_expr='icontains',
    )
    date = filters.DateFilter(method='date_filter')
    originator = filters.CharFilter(method='originator_filter')

    def date_filter(self, queryset, name, value):
        if value:
            queryset = queryset.filter(start_date__lte=value)
            queryset = queryset.filter(end_date__gte=value)
        return queryset

    def originator_filter(self, queryset, name, value):
        return queryset.filter(properties__originator__iexact=value.lower())

    class Meta:
        model = Site
        fields = [
            'q',
            'predicate',
            'distance',
            'site_id',
            'region_id',
            'date',
            'originator',
        ]


class ObservationFilter(BaseOutlineFieldFilter):
    site_id = filters.CharFilter(
        field_name='parent_site__site_id',
        help_text='The site_id.',
        label='Site ID',
        lookup_expr='icontains',
    )
    region_id = filters.CharFilter(
        field_name='parent_site__parent_region__region_id',
        help_text='The region_id.',
        label='Region ID',
        lookup_expr='icontains',
    )
    observation_date = filters.DateFromToRangeFilter(
        field_name='observation_date',
        label='Observation Date',
    )
    current_phase = filters.CharFilter(method='current_phase_filter')

    def current_phase_filter(self, queryset, name, value):
        return queryset.filter(properties__current_phase__icontains=value.lower())

    class Meta:
        model = Observation
        fields = [
            'q',
            'predicate',
            'distance',
            'site_id',
            'region_id',
            'observation_date',
            'current_phase',
        ]
