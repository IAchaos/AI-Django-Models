from django.contrib import admin
from .models import Application, Job, Company, Category


# ------ -----------------Actions ----------------------
@admin.action(description='Activate Selected Jobs')
def active_jobs(modeladmin, request,queryset):
    queryset.update(status=Job.Status.ACTIVE)

@admin.action(description='Reject Selected Applications')
def reject_applications(modeladmin, request, queryset):
    queryset.update(status=Application.Status.REJECTED)

# -------------- ModelAdmin Classes -----------------

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug','created_at']
    search_fields = ['name']
    ordering =  ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name','owner','is_verified','created_at']
    search_fields = ['name','owner__username']
    list_filter = ['is_verified']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title','slug','company','status','location_type','expires_at','created_at']
    list_filter = ['status','location_type','category','is_featured']
    search_fields = ['title','company__name','description']
    readonly_fields = ['created_at','updated_at','total_applications']
    ordering = ['-created_at']
    actions = [active_jobs]

    fieldsets = [
        ('Basic Info', {
            'fields': ['title', 'slug', 'company', 'category', 'description']
        }),
        ('Classification', {
            'fields': ['status', 'location_type', 'is_featured']
        }),
        ('Compensation', {
            'fields': ['salary_min', 'salary_max']
        }),
        ('Dates & Stats', {
            'fields': ['expires_at', 'created_at', 'updated_at','total_applications'],
        }),
    ]


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['candidate','job','status','get_days_since_application']

    @admin.display(description='Days since applied')
    def get_days_since_application(self, obj):
        return obj.days_since_applied

    list_filter = ['status']
    search_fields = ['candidate__username','job__title']
    ordering = ['-created_at']
    readonly_fields = ['created_at','updated_at']
    actions = [reject_applications]
