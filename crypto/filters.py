from typing import Any

import django_filters
from django import forms

from .models import CoinPrice


class CoinPriceFilterForm(forms.Form):
    def clean(self) -> dict[str, Any]:
        super().clean()
        start = self.cleaned_data.get("min_price")
        end = self.cleaned_data.get("max_price")
        if start is not None and end is not None and start > end:
            raise forms.ValidationError("min_price не может быть больше max_price.")
        return self.cleaned_data


class CoinPriceFilter(django_filters.FilterSet):
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")

    symbol = django_filters.CharFilter(field_name="symbol", lookup_expr="iexact")

    class Meta:
        model = CoinPrice
        fields = ["symbol", "min_price", "max_price"]
        form = CoinPriceFilterForm
