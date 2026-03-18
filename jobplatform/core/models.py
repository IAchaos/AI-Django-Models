from django.db import models


class TimeStampedModel(models.Model):
    """
    - Abstract Base Class - Never creates a table.
    - Every Model inherits from this class will have
    this fields automatically.
    - Helps to encapsulate the logic and isolate reusable parts for use.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True