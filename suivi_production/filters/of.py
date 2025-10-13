import django_filters
from django import forms
from django.utils import timezone
from ..models import OrdreFabrication


class OrdreFabricationFilter(django_filters.FilterSet):
    numero = django_filters.CharFilter(field_name='numero_of', lookup_expr='icontains', label='Numéro OF')
    date = django_filters.DateFilter(field_name='date_premiere_finalisation', label='Date (YYYY-MM-DD)',
                                     widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = OrdreFabrication
        fields = ['numero', 'date']
