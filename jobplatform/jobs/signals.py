from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Application, Job


# ------ Signal One: Application Class --------------------
@receiver(post_save, sender=Application)
def on_application_saved(sender, instance, created, **kwargs):
    """
        Fires every time an Application is saved.
        created=True  → new application just submitted
        created=False → existing application was updated
        """
    if created:
        instance.job.total_applications = F('total_applications') + 1
        instance.job.save(update_fields=['total_applications'])

    if not created and instance.status == Application.Status.HIRED:
        instance.job.status = Job.Status.CLOSED
        instance.job.save(update_fields=['status', 'updated_at'])


# ------ Signal Two : Job Class ---------------------

@receiver(post_save, sender=Job)
def on_job_activated(sender, instance, created, **kwargs):
    """
        Fires every time a Job is saved.
    """
    from django.utils.text import slugify
    if not instance.slug:
        instance.slug = slugify(instance.title)
        Job.objects.filter(pk=instance.pk).update(
            slug=instance.slug
        )
