"""
Human Resources — Domain Models
=================================
Manages library staff: departments, employees, job vacancies, and applications.

Models:
    Department     — organizational unit (e.g., Circulation, Reference, IT)
    Employee       — staff member linked to a User account
    JobVacancy     — open position posting
    JobApplication — candidate's application for a vacancy
"""

from __future__ import annotations

import uuid
from datetime import date

from django.conf import settings
from django.db import models

from apps.common.base_models import TimeStampedModel


# ---------------------------------------------------------------------------
# Department
# ---------------------------------------------------------------------------

class Department(TimeStampedModel):
    """Organizational unit within the library."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=20, unique=True, help_text='Short identifier, e.g. CIRC, REF')
    description = models.TextField(blank=True, default='')
    head = models.ForeignKey(
        'Employee', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='headed_departments',
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'hr_departments'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def employee_count(self) -> int:
        return self.employees.filter(status='ACTIVE').count()


# ---------------------------------------------------------------------------
# Employee
# ---------------------------------------------------------------------------

class Employee(TimeStampedModel):
    """Library staff member linked to a system user account."""

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        ON_LEAVE = 'ON_LEAVE', 'On Leave'
        SUSPENDED = 'SUSPENDED', 'Suspended'
        TERMINATED = 'TERMINATED', 'Terminated'
        PROBATION = 'PROBATION', 'Probation'

    class EmploymentType(models.TextChoices):
        FULL_TIME = 'FULL_TIME', 'Full Time'
        PART_TIME = 'PART_TIME', 'Part Time'
        CONTRACT = 'CONTRACT', 'Contract'
        INTERN = 'INTERN', 'Intern'
        VOLUNTEER = 'VOLUNTEER', 'Volunteer'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link to User
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='employee_profile',
    )

    # Employment details
    employee_id = models.CharField(max_length=30, unique=True, help_text='Staff ID, e.g. EMP-001')
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name='employees',
    )
    job_title = models.CharField(max_length=150)
    employment_type = models.CharField(
        max_length=20, choices=EmploymentType.choices, default=EmploymentType.FULL_TIME,
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    # Dates
    hire_date = models.DateField()
    termination_date = models.DateField(null=True, blank=True)
    probation_end_date = models.DateField(null=True, blank=True)

    # Compensation (optional, for summary/stats)
    salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=3, default='USD')

    # Contact / emergency
    emergency_contact_name = models.CharField(max_length=200, blank=True, default='')
    emergency_contact_phone = models.CharField(max_length=30, blank=True, default='')

    # Reporting
    reports_to = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='direct_reports',
    )

    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'hr_employees'
        ordering = ['employee_id']

    def __str__(self):
        return f'{self.employee_id} — {self.user.first_name} {self.user.last_name}'

    @property
    def full_name(self) -> str:
        return f'{self.user.first_name} {self.user.last_name}'

    @property
    def years_of_service(self) -> float:
        end = self.termination_date or date.today()
        return round((end - self.hire_date).days / 365.25, 1)


# ---------------------------------------------------------------------------
# Job Vacancy
# ---------------------------------------------------------------------------

class JobVacancy(TimeStampedModel):
    """Open position posting for recruitment."""

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        OPEN = 'OPEN', 'Open'
        CLOSED = 'CLOSED', 'Closed'
        ON_HOLD = 'ON_HOLD', 'On Hold'
        FILLED = 'FILLED', 'Filled'

    class ExperienceLevel(models.TextChoices):
        ENTRY = 'ENTRY', 'Entry Level'
        MID = 'MID', 'Mid Level'
        SENIOR = 'SENIOR', 'Senior Level'
        LEAD = 'LEAD', 'Lead / Supervisor'
        MANAGER = 'MANAGER', 'Manager'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=200)
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name='vacancies',
    )
    description = models.TextField()
    requirements = models.TextField(help_text='Qualifications and skills required')
    responsibilities = models.TextField(blank=True, default='')
    experience_level = models.CharField(
        max_length=20, choices=ExperienceLevel.choices, default=ExperienceLevel.MID,
    )
    employment_type = models.CharField(
        max_length=20, choices=Employee.EmploymentType.choices,
        default=Employee.EmploymentType.FULL_TIME,
    )
    positions_available = models.PositiveIntegerField(default=1)
    salary_range_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_range_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=3, default='USD')

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='posted_vacancies',
    )
    posted_date = models.DateField(null=True, blank=True)
    closing_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True, default='Library Main Campus')

    class Meta:
        db_table = 'hr_job_vacancies'
        ordering = ['-created_at']
        verbose_name_plural = 'Job vacancies'

    def __str__(self):
        return f'{self.title} ({self.department.name})'

    @property
    def application_count(self) -> int:
        return self.applications.count()

    @property
    def is_accepting_applications(self) -> bool:
        if self.status != 'OPEN':
            return False
        if self.closing_date and self.closing_date < date.today():
            return False
        return True


# ---------------------------------------------------------------------------
# Job Application
# ---------------------------------------------------------------------------

class JobApplication(TimeStampedModel):
    """A candidate's application for a job vacancy."""

    class Status(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'Submitted'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        SHORTLISTED = 'SHORTLISTED', 'Shortlisted'
        INTERVIEW = 'INTERVIEW', 'Interview Scheduled'
        OFFERED = 'OFFERED', 'Offer Made'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        REJECTED = 'REJECTED', 'Rejected'
        WITHDRAWN = 'WITHDRAWN', 'Withdrawn'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    vacancy = models.ForeignKey(
        JobVacancy, on_delete=models.CASCADE, related_name='applications',
    )
    # Applicant can be an existing user or an external candidate
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='job_applications',
    )
    applicant_name = models.CharField(max_length=200)
    applicant_email = models.EmailField()
    applicant_phone = models.CharField(max_length=30, blank=True, default='')

    resume_url = models.URLField(max_length=500, blank=True, default='')
    cover_letter = models.TextField(blank=True, default='')

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SUBMITTED,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_applications',
    )
    review_notes = models.TextField(blank=True, default='')
    interview_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'hr_job_applications'
        ordering = ['-created_at']
        unique_together = [('vacancy', 'applicant_email')]

    def __str__(self):
        return f'{self.applicant_name} → {self.vacancy.title}'
