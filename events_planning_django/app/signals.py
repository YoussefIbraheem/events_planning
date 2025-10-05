from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Event, Ticket
import datetime


@receiver(post_save, sender=Event)
def generate_tickets(sender, instance, created, **kwargs):
    tickets_amounts = instance.available_tickets

    for _ in range(tickets_amounts):
        Ticket.objects.create(
            ticket_code=f"{instance.id}-{instance.organiser.id}-{instance.date_time.strftime('%Y%m%d%H%M%S')}-{_+1}",
            event=instance,
        )
    print(f"Generated {tickets_amounts} tickets for event {instance.title}")


