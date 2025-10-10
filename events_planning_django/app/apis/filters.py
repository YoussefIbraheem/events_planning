from django_filters import FilterSet, DateTimeFilter, NumberFilter, BooleanFilter
from app.models import Event, Ticket

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
        field_name="event__id",
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
