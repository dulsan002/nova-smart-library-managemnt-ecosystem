"""
Human Resources — GraphQL Schema
==================================
CRUD for departments, employees, job vacancies, and job applications.
"""

import graphene
from graphene_django import DjangoObjectType

from apps.common.decorators import require_authentication, require_roles, audit_action
from apps.common.permissions import Role
from apps.hr.domain.models import Department, Employee, JobVacancy, JobApplication


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class DepartmentType(DjangoObjectType):
    employee_count = graphene.Int()

    class Meta:
        model = Department
        fields = ('id', 'name', 'code', 'description', 'head', 'is_active', 'created_at')

    def resolve_employee_count(self, info):
        return self.employee_count


class EmployeeType(DjangoObjectType):
    full_name = graphene.String()
    years_of_service = graphene.Float()

    class Meta:
        model = Employee
        fields = (
            'id', 'user', 'employee_id', 'department', 'job_title',
            'employment_type', 'status', 'hire_date', 'termination_date',
            'probation_end_date', 'salary', 'salary_currency',
            'emergency_contact_name', 'emergency_contact_phone',
            'reports_to', 'direct_reports', 'notes', 'created_at', 'updated_at',
        )

    def resolve_full_name(self, info):
        return self.full_name

    def resolve_years_of_service(self, info):
        return self.years_of_service


class JobVacancyType(DjangoObjectType):
    application_count = graphene.Int()
    is_accepting_applications = graphene.Boolean()

    class Meta:
        model = JobVacancy
        fields = (
            'id', 'title', 'department', 'description', 'requirements',
            'responsibilities', 'experience_level', 'employment_type',
            'positions_available', 'salary_range_min', 'salary_range_max',
            'salary_currency', 'status', 'posted_by', 'posted_date',
            'closing_date', 'location', 'created_at', 'updated_at',
        )

    def resolve_application_count(self, info):
        return self.application_count

    def resolve_is_accepting_applications(self, info):
        return self.is_accepting_applications


class JobApplicationType(DjangoObjectType):
    class Meta:
        model = JobApplication
        fields = (
            'id', 'vacancy', 'applicant', 'applicant_name', 'applicant_email',
            'applicant_phone', 'resume_url', 'cover_letter', 'status',
            'reviewed_by', 'review_notes', 'interview_date', 'created_at', 'updated_at',
        )


class HRStatsType(graphene.ObjectType):
    total_employees = graphene.Int()
    active_employees = graphene.Int()
    on_leave_count = graphene.Int()
    departments_count = graphene.Int()
    open_vacancies = graphene.Int()
    pending_applications = graphene.Int()


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------

class CreateDepartment(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        code = graphene.String(required=True)
        description = graphene.String()

    Output = DepartmentType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    @audit_action(action='CREATE', resource_type='Department')
    def mutate(self, info, name, code, description=''):
        return Department.objects.create(name=name, code=code, description=description)


class UpdateDepartment(graphene.Mutation):
    class Arguments:
        id = graphene.UUID(required=True)
        name = graphene.String()
        description = graphene.String()
        head_id = graphene.UUID()
        is_active = graphene.Boolean()

    Output = DepartmentType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    @audit_action(action='UPDATE', resource_type='Department')
    def mutate(self, info, id, **kwargs):
        dept = Department.objects.get(pk=id)
        for field in ['name', 'description', 'is_active']:
            if field in kwargs and kwargs[field] is not None:
                setattr(dept, field, kwargs[field])
        if 'head_id' in kwargs:
            if kwargs['head_id']:
                dept.head = Employee.objects.get(pk=kwargs['head_id'])
            else:
                dept.head = None
        dept.save()
        return dept


class CreateEmployee(graphene.Mutation):
    class Arguments:
        user_id = graphene.UUID(required=True)
        employee_id = graphene.String(required=True)
        department_id = graphene.UUID(required=True)
        job_title = graphene.String(required=True)
        hire_date = graphene.Date(required=True)
        employment_type = graphene.String()
        status = graphene.String()
        salary = graphene.Float()
        salary_currency = graphene.String()
        reports_to_id = graphene.UUID()
        emergency_contact_name = graphene.String()
        emergency_contact_phone = graphene.String()
        notes = graphene.String()

    Output = EmployeeType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    @audit_action(action='CREATE', resource_type='Employee')
    def mutate(self, info, user_id, employee_id, department_id, job_title, hire_date, **kwargs):
        from apps.identity.domain.models import User
        data = {
            'user': User.objects.get(pk=user_id),
            'employee_id': employee_id,
            'department': Department.objects.get(pk=department_id),
            'job_title': job_title,
            'hire_date': hire_date,
        }
        simple_fields = [
            'employment_type', 'status', 'salary', 'salary_currency',
            'emergency_contact_name', 'emergency_contact_phone', 'notes',
        ]
        for field in simple_fields:
            if field in kwargs and kwargs[field] is not None:
                data[field] = kwargs[field]
        if kwargs.get('reports_to_id'):
            data['reports_to'] = Employee.objects.get(pk=kwargs['reports_to_id'])
        return Employee.objects.create(**data)


class UpdateEmployee(graphene.Mutation):
    class Arguments:
        id = graphene.UUID(required=True)
        department_id = graphene.UUID()
        job_title = graphene.String()
        employment_type = graphene.String()
        status = graphene.String()
        salary = graphene.Float()
        termination_date = graphene.Date()
        reports_to_id = graphene.UUID()
        emergency_contact_name = graphene.String()
        emergency_contact_phone = graphene.String()
        notes = graphene.String()

    Output = EmployeeType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    @audit_action(action='UPDATE', resource_type='Employee')
    def mutate(self, info, id, **kwargs):
        emp = Employee.objects.get(pk=id)
        simple_fields = [
            'job_title', 'employment_type', 'status', 'salary',
            'termination_date', 'emergency_contact_name',
            'emergency_contact_phone', 'notes',
        ]
        for field in simple_fields:
            if field in kwargs and kwargs[field] is not None:
                setattr(emp, field, kwargs[field])
        if 'department_id' in kwargs and kwargs['department_id']:
            emp.department = Department.objects.get(pk=kwargs['department_id'])
        if 'reports_to_id' in kwargs:
            if kwargs['reports_to_id']:
                emp.reports_to = Employee.objects.get(pk=kwargs['reports_to_id'])
            else:
                emp.reports_to = None
        emp.save()
        return emp


class CreateJobVacancy(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        department_id = graphene.UUID(required=True)
        description = graphene.String(required=True)
        requirements = graphene.String(required=True)
        responsibilities = graphene.String()
        experience_level = graphene.String()
        employment_type = graphene.String()
        positions_available = graphene.Int()
        salary_range_min = graphene.Float()
        salary_range_max = graphene.Float()
        salary_currency = graphene.String()
        location = graphene.String()
        closing_date = graphene.Date()

    Output = JobVacancyType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    @audit_action(action='CREATE', resource_type='JobVacancy')
    def mutate(self, info, title, department_id, description, requirements, **kwargs):
        data = {
            'title': title,
            'department': Department.objects.get(pk=department_id),
            'description': description,
            'requirements': requirements,
            'posted_by': info.context.user,
            'status': 'DRAFT',
        }
        simple_fields = [
            'responsibilities', 'experience_level', 'employment_type',
            'positions_available', 'salary_range_min', 'salary_range_max',
            'salary_currency', 'location', 'closing_date',
        ]
        for field in simple_fields:
            if field in kwargs and kwargs[field] is not None:
                data[field] = kwargs[field]
        return JobVacancy.objects.create(**data)


class UpdateJobVacancy(graphene.Mutation):
    class Arguments:
        id = graphene.UUID(required=True)
        title = graphene.String()
        description = graphene.String()
        requirements = graphene.String()
        status = graphene.String()
        closing_date = graphene.Date()
        positions_available = graphene.Int()

    Output = JobVacancyType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    @audit_action(action='UPDATE', resource_type='JobVacancy')
    def mutate(self, info, id, **kwargs):
        from datetime import date as date_cls
        vacancy = JobVacancy.objects.get(pk=id)
        for field in ['title', 'description', 'requirements', 'status',
                       'closing_date', 'positions_available']:
            if field in kwargs and kwargs[field] is not None:
                setattr(vacancy, field, kwargs[field])
        # Auto-set posted_date when publishing
        if kwargs.get('status') == 'OPEN' and not vacancy.posted_date:
            vacancy.posted_date = date_cls.today()
        vacancy.save()
        return vacancy


class SubmitJobApplication(graphene.Mutation):
    """Public mutation — any authenticated user can apply."""

    class Arguments:
        vacancy_id = graphene.UUID(required=True)
        applicant_name = graphene.String(required=True)
        applicant_email = graphene.String(required=True)
        applicant_phone = graphene.String()
        resume_url = graphene.String()
        cover_letter = graphene.String()

    Output = JobApplicationType

    @require_authentication
    def mutate(self, info, vacancy_id, applicant_name, applicant_email, **kwargs):
        vacancy = JobVacancy.objects.get(pk=vacancy_id)
        if not vacancy.is_accepting_applications:
            raise Exception('This vacancy is no longer accepting applications.')
        return JobApplication.objects.create(
            vacancy=vacancy,
            applicant=info.context.user,
            applicant_name=applicant_name,
            applicant_email=applicant_email,
            applicant_phone=kwargs.get('applicant_phone', ''),
            resume_url=kwargs.get('resume_url', ''),
            cover_letter=kwargs.get('cover_letter', ''),
        )


class UpdateApplicationStatus(graphene.Mutation):
    class Arguments:
        id = graphene.UUID(required=True)
        status = graphene.String(required=True)
        review_notes = graphene.String()
        interview_date = graphene.DateTime()

    Output = JobApplicationType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    @audit_action(action='UPDATE', resource_type='JobApplication')
    def mutate(self, info, id, status, **kwargs):
        app = JobApplication.objects.get(pk=id)
        app.status = status
        app.reviewed_by = info.context.user
        if kwargs.get('review_notes'):
            app.review_notes = kwargs['review_notes']
        if kwargs.get('interview_date'):
            app.interview_date = kwargs['interview_date']
        app.save()
        return app


# ---------------------------------------------------------------------------
# Query & Mutation roots
# ---------------------------------------------------------------------------

class HRQuery(graphene.ObjectType):
    departments = graphene.List(DepartmentType, is_active=graphene.Boolean())
    department = graphene.Field(DepartmentType, id=graphene.UUID(required=True))
    employees = graphene.List(
        EmployeeType,
        department_id=graphene.UUID(),
        status=graphene.String(),
        search=graphene.String(),
        limit=graphene.Int(default_value=50),
    )
    employee = graphene.Field(EmployeeType, id=graphene.UUID(required=True))
    job_vacancies = graphene.List(
        JobVacancyType,
        status=graphene.String(),
        department_id=graphene.UUID(),
        limit=graphene.Int(default_value=20),
    )
    job_vacancy = graphene.Field(JobVacancyType, id=graphene.UUID(required=True))
    job_applications = graphene.List(
        JobApplicationType,
        vacancy_id=graphene.UUID(),
        status=graphene.String(),
        limit=graphene.Int(default_value=50),
    )
    hr_stats = graphene.Field(HRStatsType)

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_departments(self, info, is_active=None):
        qs = Department.objects.all()
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        return qs

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_department(self, info, id):
        return Department.objects.get(pk=id)

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_employees(self, info, department_id=None, status=None, search=None, limit=50):
        qs = Employee.objects.select_related('user', 'department', 'reports_to').all()
        if department_id:
            qs = qs.filter(department_id=department_id)
        if status:
            qs = qs.filter(status=status)
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(employee_id__icontains=search) |
                Q(job_title__icontains=search)
            )
        return qs[:limit]

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_employee(self, info, id):
        return Employee.objects.select_related('user', 'department', 'reports_to').get(pk=id)

    @require_authentication
    def resolve_job_vacancies(self, info, status=None, department_id=None, limit=20):
        qs = JobVacancy.objects.select_related('department', 'posted_by').all()
        if status:
            qs = qs.filter(status=status)
        if department_id:
            qs = qs.filter(department_id=department_id)
        return qs[:limit]

    @require_authentication
    def resolve_job_vacancy(self, info, id):
        return JobVacancy.objects.select_related('department', 'posted_by').get(pk=id)

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_job_applications(self, info, vacancy_id=None, status=None, limit=50):
        qs = JobApplication.objects.select_related('vacancy', 'applicant', 'reviewed_by').all()
        if vacancy_id:
            qs = qs.filter(vacancy_id=vacancy_id)
        if status:
            qs = qs.filter(status=status)
        return qs[:limit]

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_hr_stats(self, info):
        from django.db.models import Count, Q
        emp_agg = Employee.objects.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status='ACTIVE')),
            on_leave=Count('id', filter=Q(status='ON_LEAVE')),
        )
        return HRStatsType(
            total_employees=emp_agg['total'],
            active_employees=emp_agg['active'],
            on_leave_count=emp_agg['on_leave'],
            departments_count=Department.objects.filter(is_active=True).count(),
            open_vacancies=JobVacancy.objects.filter(status='OPEN').count(),
            pending_applications=JobApplication.objects.filter(status='SUBMITTED').count(),
        )


class HRMutation(graphene.ObjectType):
    create_department = CreateDepartment.Field()
    update_department = UpdateDepartment.Field()
    create_employee = CreateEmployee.Field()
    update_employee = UpdateEmployee.Field()
    create_job_vacancy = CreateJobVacancy.Field()
    update_job_vacancy = UpdateJobVacancy.Field()
    submit_job_application = SubmitJobApplication.Field()
    update_application_status = UpdateApplicationStatus.Field()
