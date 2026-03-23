
from datetime import timedelta

from django.core.exceptions import ValidationError
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

        # Bug : filter(Status=Job.Status.ACTIVE)
        # Correct : status in lowercase it matches the actual field name on the model

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
    """
    def active(self):
        
        NB. moved to ActiveJobManager
        Getting number of jobs where status == Active not expired
        :return: int

        return self.get_queryset().filter(
            status=Job.Status.ACTIVE, expires_at__gt=timezone.now())
        """
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
"""
    . This is class is going to have three level .
    . Using Proxy Models to achieve reusability and code readibilty .
    . Proxy models : ActiveJobProxy
                     ExpiredJobProxy
                     FeaturedJobProxy
"""
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
    is_featured = models.BooleanField(default=False)
    total_applications = models.PositiveIntegerField(default=0)

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

    @property
    def salary_range(self):
        from .utils import format_salary
        return format_salary(self.salary_min, self.salary_max)

    @property
    def reading_time(self):
        from .utils import calculate_reading_time
        return calculate_reading_time(self.description)

    # Model Validation
    def clean(self):
        errors = {}

        # Rule One : salary_min cannot be greater than salary_max if both are provided
        if self.salary_min and self.salary_max:
            if self.salary_max > self.salary_min:
                errors['salary_min'] = 'Salary min cannot exceed Max Salary'


        # Rule Two: expires_at cannot be set to a date in the past
        if self.expires_at and self.expires_at < timezone.now():
            errors['expires_at'] = 'Expiry date cannot be in the past.'

        if errors:
            raise ValidationError(errors)


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
        self.status = self.Status.CLOSED
        self.save(update_fields=['status','updated_at'])

    def has_applied(self, user):
        return self.applications.filter(candidate=user).exists()

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

# -------- Custom Mangers For Proxy Models -------------------
# --------- ActiveJobManger-------------------
class ActiveJobManager(models.Manager):
    def get_queryset(self):
        """
        Filters active and not expired jobs
        :return: list
        """
        return super().get_queryset().filter(
            status=Job.Status.ACTIVE, expires_at__gt=timezone.now())

# -------- ExpiredJobManager ----------------
class ExpiredJobManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(expires_at__lte=timezone.now())

# ------- FeaturedJobManager -----------------
class FeaturedJobManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            status=Job.Status.ACTIVE, expires_at__gt=timezone.now(), is_featured=True
        )


# ---------- Proxy models for Job --------------
# ---------- ActiveJobProxy -------------------

class ActiveJob(Job):
    class Meta:
        proxy = True
        ordering = ['-is_featured', '-created_at']

    objects = ActiveJobManager()

    def get_similar(self):
        return ActiveJob.objects.filter(
            category=self.category,
        ).exclude(pk=self.pk)[:5]

class ExpiredJob(Job):
    class Meta:
        proxy = True

    objects = ExpiredJobManager()

    @property
    def days_since_expiry(self):
        return (timezone.now() - self.expires_at).days

    def renew(self, days=30):
        self.status = self.Status.ACTIVE
        self.expires_at = timezone.now() + timedelta(days=days)

        self.save(update_fields=['status', 'expires_at', 'updated_at'])



class FeaturedJob(Job):
    class Meta:
        proxy = True

    objects = FeaturedJobManager()

    def unfeature(self):
        self.is_featured = False
        self.save(update_fields=['is_featured', 'updated_at'])





#---------- Application Custom Manager ----------------------
class ApplicationManager(models.Manager):
    def for_job(self, job):
        """
        Returning all applications for specific job
        :return: list
        """
        return  self.get_queryset().filter(job=job)

    def for_candidate(self, user):
        """
        all applications for a specific candidate
        :param user: user pk
        :return: list of  applications
        """
        return self.get_queryset().filter(candidate=user)

    def pending(self):
        """
        all applications currently in Pending status
        :return: list
        """
        return self.get_queryset().filter(status=Application.Status.PENDING)



# ------------------- Application  Class --------------------
class Application(TimeStampedModel):
    """
    This class used to handle the application logic
    """

    # ------------ Class inner choices-----------------------
    class Status(models.TextChoices):
        PENDING = 'P', 'Pending'
        REVIEWING = 'R', 'Reviewing'
        SHORTLISTED = 'S', 'Shortlisted'
        REJECTED = 'J', 'Rejected'
        HIRED = 'H', 'Hired'

    # -------------------- Fields------------------------
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    cover_letter = models.TextField(blank=True)
    resume = models.FileField(upload_to='resumes/')
    status = models.CharField(max_length=1, choices=Status.choices, default=Status.PENDING)

    # ------ Properties: Computed Fields -------------------
    @property
    def is_active(self):
        """
        returns True if the application has not been rejected or hired yet
        :return: Boolean
        """
        return self.status not in [self.Status.HIRED , self.Status.REJECTED]

    @property
    def days_since_applied(self):
        """
        how many days since the candidate applied
        :return: int (number of days)
        """
        return (timezone.now() - self.created_at).days

    # Model Validation
    def clean(self):
        errors = {}

        # Rule One: A candidate cannot apply to their own company's job
        if self.candidate == self.job.company.owner:
            errors['candidate'] = 'You cannot apply to your own company \'s job.'

    # --------------- Instance Methods --------------------
    def shortlist(self):
        """
        move to Shortlisted, save only changed fields
        :return: nothing
        """
        self.status = self.Status.SHORTLISTED
        self.save(update_fields=['status','updated_at'])

    def reject(self):
        self.status = self.Status.REJECTED
        self.save(update_fields=['status', 'updated_at'])

    def hire(self):
        self.status = self.Status.HIRED
        self.save(update_fields=['status', 'updated_at'])

    # --------------- Class methods ------------------------
    @classmethod
    def submit(cls, job, candidate, cover_letter, resume):
        if job.has_applied(candidate):
            raise ValueError("You can only apply one to this Job.")
        if not  job.is_active:
            raise ValueError("Cannot apply to a closed or expired job.")
        return cls.objects.create(
                job=job,
                candidate=candidate,
                cover_letter=cover_letter,
                resume=resume,
            )

    #------------- Meta ----------------------
    class Meta:
        ordering = ['-created_at']
        unique_together = ['job', 'candidate']

    # Overriding the default manager
    objects = ApplicationManager()

    def __str__(self):
        return f"{self.candidate.username} → {self.job.title}"
