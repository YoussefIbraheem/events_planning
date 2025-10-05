from django.db.models.signals import post_save
from logging import Logger
from django.dispatch import receiver
from .models import Event, Ticket
import datetime

logger = Logger(__name__)

# @receiver(post_save, sender=Event)
# def generate_tickets(sender, instance, created, **kwargs):
#     tickets_amounts = instance.tickets_available
    
#     for _ in range(tickets_amounts):
#         Ticket.objects.create(
#             ticket_code=f"{instance.id}-{instance.organiser.id}-{instance.date_time.strftime('%Y%m%d%H%M%S')}-{_+1}",
#             event=instance,
#         )
#     if created:
#         logger.info(f"Generated {tickets_amounts} tickets for event {instance.id}")


