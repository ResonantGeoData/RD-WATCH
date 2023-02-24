import django_filters
import iso3166

from django.db import transaction
from django.db.models import (
    Avg,
    Case,
    Count,
    F,
    JSONField,
    Max,
    Min,
    OuterRef,
    Q,
    Subquery,
    When,
)
from django.db.models.functions import JSONObject  # type: ignore
from rest_framework import viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.utils.urls import replace_query_param

from rdwatch.db.functions import (
    AggregateArraySubquery,
    BoundingBoxGeoJSON,
    ExtractEpoch,
    TimeRangeJSON,
)
from rdwatch.models import HyperParameters, Region, lookups
from rdwatch.serializers import (
    HyperParametersDetailSerializer,
    HyperParametersListSerializer,
    HyperParametersWriteSerializer,
)


class ModelRunFilter(django_filters.FilterSet):
    performer = django_filters.CharFilter(method='filter_performer')
    region = django_filters.CharFilter(method='filter_region')
    groundtruth = django_filters.BooleanFilter(method='filter_groundtruth')

    class Meta:
        model = HyperParameters
        fields: list[str] = []

    def filter_performer(self, queryset, name, value):
        if self.form.cleaned_data.get('groundtruth', False):
            queryset = queryset.alias(
                min_score=Min('evaluations__score'),
                performer_slug=F('performer__slug'),
            )
            return queryset.filter(
                (Q(performer_slug='TE') & Q(min_score=1)) | Q(performer_slug=value)
            )
        else:
            queryset = queryset.alias(performer_slug=F('performer__slug'))
            return queryset.filter(performer_slug__iexact=value)

    def filter_groundtruth(self, queryset, name, value):
        if self.form.cleaned_data['performer'] is None:
            queryset = queryset.alias(
                min_score=Min('evaluations__score'),
                performer_slug=F('performer__slug'),
            )
            if value:
                return queryset.filter(performer_slug__iexact='TE', min_score=1)
            else:
                return queryset.exclude(performer_slug__iexact='TE', min_score=1)
        else:
            return queryset

    def filter_region(self, queryset, name, value):
        countrystr, numstr = value.split('_')
        country = iso3166.countries_by_alpha2[countrystr].numeric
        classification_slug = numstr[0]
        number = None if numstr[1:] == 'xxx' else int(numstr[1:])
        return queryset.alias(
            region_country=F('evaluations__region__country'),
            region_class_slug=F('evaluations__region__classification__slug'),
            region_number=F('evaluations__region__number'),
        ).filter(
            region_country=country,
            region_class_slug=classification_slug,
            region_number=number,
        )


def get_queryset():
    return (
        HyperParameters.objects.select_related('evaluations', 'performer')
        # Get minimum score and performer so that we can tell which runs
        # are ground truth
        .alias(min_score=Min('evaluations__score'), performer_slug=F('performer__slug'))
        # Label ground truths as such. A ground truth is defined as a model run
        # with a min_score of 1 and a performer of "TE"
        .alias(
            groundtruth=Case(
                When(min_score=1, performer_slug__iexact='TE', then=True),
                default=False,
            )
        )
        # Order queryset so that ground truths are first
        .order_by('-groundtruth', '-id')
        .alias(region_id=F('evaluations__region_id'))
        .annotate(
            json=JSONObject(
                id='pk',
                title='title',
                performer=Subquery(  # prevents including "performer" in slow GROUP BY
                    lookups.Performer.objects.filter(
                        pk=OuterRef('performer_id')
                    ).values(
                        json=JSONObject(
                            id='id',
                            team_name='description',
                            short_code='slug',
                        )
                    ),
                    output_field=JSONField(),
                ),
                region=Subquery(  # prevents including "region" in slow GROUP BY
                    Region.objects.filter(pk=OuterRef('region_id')).values(
                        json=JSONObject(
                            id='id',
                            country='country',
                            classification=JSONObject(slug='classification__slug'),
                            number='number',
                        )
                    ),
                    output_field=JSONField(),
                ),
                parameters='parameters',
                numsites=Count('evaluations__pk', distinct=True),
                score=Avg('evaluations__score'),
                timestamp=ExtractEpoch(Max('evaluations__timestamp')),
                timerange=TimeRangeJSON('evaluations__observations__timestamp'),
                bbox=BoundingBoxGeoJSON('evaluations__observations__geom'),
            )
        )
    )


class ModelRunViewSet(viewsets.ViewSet):
    @transaction.atomic
    def create(self, request: Request):
        write_serializer = HyperParametersWriteSerializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        hyper_parameters = HyperParameters.objects.create(
            title=write_serializer.validated_data['title'],
            performer=write_serializer.validated_data['performer'],
            parameters=write_serializer.validated_data['parameters'],
        )
        detail_serializer = HyperParametersDetailSerializer(
            {
                'id': hyper_parameters.pk,
                'title': hyper_parameters.title,
                'performer': {
                    'id': hyper_parameters.performer.pk,
                    'team_name': hyper_parameters.performer.description,
                    'short_code': hyper_parameters.performer.slug,
                },
                'parameters': hyper_parameters.parameters,
                'numsites': 0,
            }
        )
        return Response(data=detail_serializer.data, status=200)

    def retrieve(self, request: Request, pk: int):
        values = get_queryset().filter(pk=pk).values_list('json', flat=True)
        if not values:
            raise NotFound()
        serializer = HyperParametersDetailSerializer(values[0])
        return Response(data=serializer.data)

    def list(self, request: Request):
        queryset = ModelRunFilter(
            request.query_params,
            queryset=get_queryset(),
        ).qs

        limit = request.query_params.get('limit', api_settings.PAGE_SIZE or 25)
        if isinstance(limit, str):
            if not limit.isdigit():
                raise ValidationError({'limit': f"Invalid limit '{limit}'"})
            limit = int(limit)
        page = request.query_params.get('page', 1)
        if isinstance(page, str):
            if (
                not page.isdigit()
                or page == '0'
                or (not limit and not (page == 1 or page == '1'))
            ):
                raise ValidationError({'page': f"Invalid page '{page}'"})
            page = int(page)

        # Calculate total number of model runs prior to paginating queryset
        total_model_run_count = queryset.count()

        subquery = queryset[(page - 1) * limit : page * limit] if limit else queryset
        aggregate = queryset.defer('json').aggregate(
            timerange=TimeRangeJSON('evaluations__observations__timestamp'),
            results=AggregateArraySubquery(subquery.values('json')),
        )

        aggregate['count'] = total_model_run_count

        # Only bother calculating the entire bounding box of this model run
        # list if the user has specified a region. We don't want to overload
        # PostGIS by making it calculate a bounding box for every polygon in
        # the database.
        if 'region' in request.query_params:
            aggregate |= queryset.defer('json').aggregate(
                bbox=BoundingBoxGeoJSON('evaluations__geom')
            )

        if aggregate['count'] > 0 and not aggregate['results']:
            raise NotFound({'page': f"Invalid page '{page}'"})
        aggregate['next'] = (
            replace_query_param(request.build_absolute_uri(), 'page', page + 1)
            if limit and page * limit < aggregate['count']
            else None
        )
        aggregate['previous'] = (
            replace_query_param(request.build_absolute_uri(), 'page', page - 1)
            if limit and page > 1
            else None
        )

        serializer = HyperParametersListSerializer(aggregate)
        return Response(data=serializer.data)
