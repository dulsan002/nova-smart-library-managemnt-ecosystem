/**
 * HR / Employee Management GraphQL queries.
 */

import { gql } from '@apollo/client';

export const GET_DEPARTMENTS = gql`
  query GetDepartments($isActive: Boolean) {
    departments(isActive: $isActive) {
      id
      name
      code
      description
      isActive
      employeeCount
      head {
        id
        fullName
        jobTitle
      }
    }
  }
`;

export const GET_EMPLOYEES = gql`
  query GetEmployees($departmentId: UUID, $status: String, $search: String, $limit: Int) {
    employees(departmentId: $departmentId, status: $status, search: $search, limit: $limit) {
      id
      employeeId
      fullName
      jobTitle
      employmentType
      status
      hireDate
      yearsOfService
      createdAt
      user {
        id
        email
        firstName
        lastName
        avatarUrl
      }
      department {
        id
        name
        code
      }
      reportsTo {
        id
        fullName
      }
    }
  }
`;

export const GET_EMPLOYEE = gql`
  query GetEmployee($id: UUID!) {
    employee(id: $id) {
      id
      employeeId
      fullName
      jobTitle
      employmentType
      status
      hireDate
      terminationDate
      probationEndDate
      salary
      salaryCurrency
      emergencyContactName
      emergencyContactPhone
      yearsOfService
      notes
      createdAt
      updatedAt
      user {
        id
        email
        firstName
        lastName
        avatarUrl
        role
      }
      department {
        id
        name
        code
      }
      reportsTo {
        id
        fullName
        jobTitle
      }
      directReports {
        id
        fullName
        jobTitle
      }
    }
  }
`;

export const GET_JOB_VACANCIES = gql`
  query GetJobVacancies($status: String, $departmentId: UUID, $limit: Int) {
    jobVacancies(status: $status, departmentId: $departmentId, limit: $limit) {
      id
      title
      description
      requirements
      experienceLevel
      employmentType
      positionsAvailable
      salaryRangeMin
      salaryRangeMax
      salaryCurrency
      status
      postedDate
      closingDate
      location
      applicationCount
      isAcceptingApplications
      createdAt
      department {
        id
        name
      }
      postedBy {
        id
        firstName
        lastName
      }
    }
  }
`;

export const GET_JOB_APPLICATIONS = gql`
  query GetJobApplications($vacancyId: UUID, $status: String, $limit: Int) {
    jobApplications(vacancyId: $vacancyId, status: $status, limit: $limit) {
      id
      applicantName
      applicantEmail
      applicantPhone
      resumeUrl
      coverLetter
      status
      reviewNotes
      interviewDate
      createdAt
      vacancy {
        id
        title
      }
      applicant {
        id
        firstName
        lastName
      }
      reviewedBy {
        id
        firstName
        lastName
      }
    }
  }
`;

export const GET_HR_STATS = gql`
  query GetHRStats {
    hrStats {
      totalEmployees
      activeEmployees
      onLeaveCount
      departmentsCount
      openVacancies
      pendingApplications
    }
  }
`;
