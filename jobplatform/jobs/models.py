from django.db import models
from core.models import TimeStampedModel
from django.contrib.auth.models import User

class Category(TimeStampedModel):
    """
    Category Model creates a DB table Category.
    Used to store information about the job field or domain.
    """

    name = models.CharField(max_length=250, unique=True) # there no two categories with the same name
    slug = models.SlugField(max_length=250, unique=True) # same no two categories with the same slug

    class Meta:
        ordering = ['name'] # Alphabetic ordering make sense for this
        verbose_name_plural = 'Categories'

    def __str__(self):
        return  self.name



class Company(TimeStampedModel):
    """
    Comapny Model creates a DB table Company
    """

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="companies") # related name is relative to the class
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True) # slug must be always unique
    bio = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "companies"

    def __str__(self):
        return self.name + " " + self.owner.username


class Job(TimeStampedModel):
    """
    Job model used to define the job requirements
    """
    class Status(models.TextChoices):
        ACTIVE = 'A', "Active"
        DRAFT = 'D', 'Draft'
        CLOSED = 'C' , 'Closed'

    class LocationType(models.TextChoices):
        REMOTE = 'R', 'Remote'
        ONSITE = 'O', 'Onsite'
        HYBRID = 'H', 'Hybrid'

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name="jobs", null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="jobs")

    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True)
    description = models.TextField()
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=1, choices=Status.choices, default=Status.DRAFT , null=False)
    location_type = models.CharField(max_length=1, choices=LocationType.choices, default=LocationType.ONSITE, null=False)


    class Meta:
        ordering  = ["-created_at"]

    def __str__(self):
        return self.title + " at " + self.company.name

