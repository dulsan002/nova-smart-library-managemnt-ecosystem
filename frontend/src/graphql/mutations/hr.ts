/**
 * HR / Employee Management GraphQL mutations.
 */

import { gql } from '@apollo/client';

export const CREATE_DEPARTMENT = gql`
  mutation CreateDepartment($name: String!, $code: String!, $description: String) {
    createDepartment(name: $name, code: $code, description: $description) {
      id
      name
      code
    }
  }
`;

export const UPDATE_DEPARTMENT = gql`
  mutation UpdateDepartment($id: UUID!, $name: String, $description: String, $headId: UUID, $isActive: Boolean) {
    updateDepartment(id: $id, name: $name, description: $description, headId: $headId, isActive: $isActive) {
      id
      name
      description
      isActive
    }
  }
`;

export const CREATE_EMPLOYEE = gql`
  mutation CreateEmployee(
    $userId: UUID!
    $employeeId: String!
    $departmentId: UUID!
    $jobTitle: String!
    $hireDate: Date!
    $employmentType: String
    $status: String
    $salary: Float
    $reportsToId: UUID
  ) {
    createEmployee(
      userId: $userId
      employeeId: $employeeId
      departmentId: $departmentId
      jobTitle: $jobTitle
      hireDate: $hireDate
      employmentType: $employmentType
      status: $status
      salary: $salary
      reportsToId: $reportsToId
    ) {
      id
      employeeId
      fullName
    }
  }
`;

export const UPDATE_EMPLOYEE = gql`
  mutation UpdateEmployee(
    $id: UUID!
    $departmentId: UUID
    $jobTitle: String
    $employmentType: String
    $status: String
    $salary: Float
    $terminationDate: Date
    $reportsToId: UUID
  ) {
    updateEmployee(
      id: $id
      departmentId: $departmentId
      jobTitle: $jobTitle
      employmentType: $employmentType
      status: $status
      salary: $salary
      terminationDate: $terminationDate
      reportsToId: $reportsToId
    ) {
      id
      employeeId
      status
      jobTitle
    }
  }
`;

export const CREATE_JOB_VACANCY = gql`
  mutation CreateJobVacancy(
    $title: String!
    $departmentId: UUID!
    $description: String!
    $requirements: String!
    $responsibilities: String
    $experienceLevel: String
    $employmentType: String
    $positionsAvailable: Int
    $salaryRangeMin: Float
    $salaryRangeMax: Float
    $closingDate: Date
    $location: String
  ) {
    createJobVacancy(
      title: $title
      departmentId: $departmentId
      description: $description
      requirements: $requirements
      responsibilities: $responsibilities
      experienceLevel: $experienceLevel
      employmentType: $employmentType
      positionsAvailable: $positionsAvailable
      salaryRangeMin: $salaryRangeMin
      salaryRangeMax: $salaryRangeMax
      closingDate: $closingDate
      location: $location
    ) {
      id
      title
      status
    }
  }
`;

export const UPDATE_JOB_VACANCY = gql`
  mutation UpdateJobVacancy(
    $id: UUID!
    $title: String
    $description: String
    $requirements: String
    $status: String
    $closingDate: Date
    $positionsAvailable: Int
  ) {
    updateJobVacancy(
      id: $id
      title: $title
      description: $description
      requirements: $requirements
      status: $status
      closingDate: $closingDate
      positionsAvailable: $positionsAvailable
    ) {
      id
      title
      status
    }
  }
`;

export const UPDATE_APPLICATION_STATUS = gql`
  mutation UpdateApplicationStatus($id: UUID!, $status: String!, $reviewNotes: String, $interviewDate: DateTime) {
    updateApplicationStatus(id: $id, status: $status, reviewNotes: $reviewNotes, interviewDate: $interviewDate) {
      id
      status
      reviewNotes
    }
  }
`;
