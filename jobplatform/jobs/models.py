
from django.db import models
from django.utils import timezone
from core.models import TimeStampedModel
from django.contrib.auth.models import User


# ------------- Category Class ----------------
class Category(TimeStampedModel):
    """
    Category Model creates a DB table Category.
    Used to store information about the job field or domain.
    """

    # --------- Fields -------------
    name = models.CharField(max_length=250, unique=True) # there no two categories with the same name
    slug = models.SlugField(max_length=250, unique=True) # same no two categories with the same slug

    # -------- Meta --------
    class Meta:
        ordering = ['name'] # Alphabetic ordering make sense for this
        verbose_name_plural = 'categories'

    # ------- Properties : Computed Fields------
    @property
    def active_jobs(self):
        """
        :param: nothing
        :return: int
        """
        return self.jobs.filter(status='A').count()

    def __str__(self):
        return  self.name



# ----------- Company Class ---------------------
class Company(TimeStampedModel):
    """
    Company Model creates a DB table Company
    """
    # --------- Fields ----------------
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="companies") # related name is relative to the class
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True) # slug must be always unique
    bio = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)

    # ---------- Meta ------------------
    class Meta:
        ordering = ['name']
        verbose_name_plural = "companies"

    # -------- Properties : Computed Fields ----------
    @property
    def number_posted_jobs(self):
        """
        Number of posted jobs by one company
        :return: int
        """
        return self.jobs.count()

    @property
    def active_jobs(self):
        """
        used to compute the total number of active jobs by this company
        :return: int
        """
        """
        Bug : filter(Status=Job.Status.ACTIVE) 
        Correct : status in lowercase it matches the actual field name on the model
        """
        return self.jobs.filter(status='A').count()

    def is_owned_by(self, user):
        """
        Used to check if a user is company owner
        :param user: user object
        :return: Boolean True of False
        """
        return self.owner == user


    def __str__(self):
        return self.name



# ---------- Job Class Manger -------------
class JobManager(models.Manager):
    """
    Responsible about the Job Queries
    """
    def active(self):
        """
        Getting number of jobs where status == Active
        :return: int
        """
        return self.get_queryset().filter(
            status=Job.Status.ACTIVE, expires_at__gt=timezone.now())

    def by_company(self, company):
        """
        Used to filter jobs offered by certain company
        :param company:
        :return: list
        """
        return  self.get_queryset().filter(company = company)

    def remote(self):
        """
        used to get remote active jobs
        :return:
        """
        return self.get_queryset().filter(
            location_type=Job.LocationType.REMOTE,
            status = Job.Status.ACTIVE,
            expires_at__gt=timezone.now()
        )
# ----------------------------------------------

# ------------  Job Class --------------------
class Job(TimeStampedModel):
    """
    Job model used to define the job requirements
    """

    # -------- Choices inner classes-----------
    class Status(models.TextChoices):
        ACTIVE = 'A', "Active"
        DRAFT = 'D', 'Draft'
        CLOSED = 'C' , 'Closed'

    class LocationType(models.TextChoices):
        REMOTE = 'R', 'Remote'
        ONSITE = 'O', 'Onsite'
        HYBRID = 'H', 'Hybrid'
    # ---------------------------------------------

    # ----------------- Fields --------------------
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

    # Overriding the default Manager
    objects = JobManager()

    # ----------- Meta -------------
    class Meta:
        ordering  = ["-created_at"]


    # ------------ Properties : Computed Fields -------
    @property
    def is_expired(self):
        """
        Tells you if a timestamp has passed
        :return: Boolean True or False
        """
        return  self.expires_at < timezone.now()

    @property
    def is_active(self):
        """
        Tells if the job is active and not expired
        :return: Boolean
        """
        return self.status == self.Status.ACTIVE and not self.is_expired

    @property
    def days_remaining(self):
        """
         how many full days until the job expires. if yes return 0
        :return: int
        """
        if self.is_expired:
            return 0
        delta = self.expires_at - timezone.now()
        return delta.days


    # -------------- Instance Methods-----------------
    def activate(self):
        """
        move status from Draft to Active, save only the changed field
        :return: Job object
        """
        self.status = self.Status.ACTIVE
        self.save(update_fields=['status','updated_at'])

    def close(self):
        """
        move status to Closed, save only the changed field
        :return: nothing
        """
        self.status = 'C'
        self.save(update_fields=['status'])

    def has_applied(self, user):
        pass

    @classmethod
    def create_for_company(cls, company, title, description, expires_at, slug):
        """
        This is a canonical factory pattern to create a job with this fields

        :param slug: auto-generated field
        :param company: company name
        :param title: job title
        :param description: job description
        :param expires_at: expiration date
        :return: Job object
        """
        return cls.objects.create(
            company=company,
            title=title,
            description=description,
            expires_at=expires_at,
            slug=slug
        )

    def __str__(self):
        return self.title + " at " + self.company.name

