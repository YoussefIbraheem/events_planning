from django_filters import (
    FilterSet,
    DateTimeFilter,
    NumberFilter,
    BooleanFilter,
    TypedChoiceFilter,
)
from app.models import Event, Ticket, Order


class EventFilter(FilterSet):

    date_from = DateTimeFilter(
        field_name="date_time",
        lookup_expr="gte",
        label="Filter events starting from this date",
    )

    date_to = DateTimeFilter(
        field_name="date_time",
        lookup_expr="lte",
        label="Filter events before this date",
    )


class TicketFilter(FilterSet):
    # Use custom names for parameters
    date_from = DateTimeFilter(
        field_name="event__date_time",
        lookup_expr="gte",
        label="Filter events starting from this date",
    )
    date_to = DateTimeFilter(
        field_name="event__date_time",
        lookup_expr="lte",
        label="Filter events before this date",
    )
    event_id = NumberFilter(
        field_name="event_id",
        lookup_expr="exact",
        label="Filter by event ID",
    )
    available_only = BooleanFilter(
        method="filter_available", label="Show only available (unsold) tickets"
    )

    def filter_available(self, queryset, name, value):
        if value:
            return queryset.filter(attendee__isnull=True)
        return queryset

    class Meta:
        model = Ticket
        fields = ["event_id", "date_from", "date_to"]


class OrderFilter(FilterSet):

    # Use custom names for parameters
    date_from = DateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
        label="Filter orders created starting from this date",
    )
    date_to = DateTimeFilter(
        field_name="created_at",
        lookup_expr="lte",
        label="Filter orders created before this date",
    )
    order_status = TypedChoiceFilter(
        field_name="order_status", choices=Order.Status.choices
    )

    def filter_available(self, queryset, name, value):
        if value:
            return queryset.filter(attendee__isnull=True)
        return queryset

    class Meta:
        model = Order
        fields = ["date_from", "date_to", "order_status"]
