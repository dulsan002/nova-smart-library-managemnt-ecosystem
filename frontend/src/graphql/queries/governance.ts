/**
 * Governance GraphQL queries.
 */

import { gql } from '@apollo/client';

export const AUDIT_LOGS = gql`
  query AuditLogs(
    $first: Int
    $after: String
    $action: String
    $resourceType: String
    $actorId: UUID
  ) {
    auditLogs(
      first: $first
      after: $after
      action: $action
      resourceType: $resourceType
      actorId: $actorId
    ) {
      edges {
        node {
          id
          action
          resourceType
          resourceId
          actorId
          actorEmail
          description
          ipAddress
          createdAt
        }
        cursor
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
`;

export const SECURITY_EVENTS = gql`
  query SecurityEvents(
    $severity: String
    $eventType: String
    $resolved: Boolean
    $limit: Int
  ) {
    securityEvents(
      severity: $severity
      eventType: $eventType
      resolved: $resolved
      limit: $limit
    ) {
      id
      eventType
      severity
      description
      ipAddress
      userId
      resolved
      resolvedAt
      createdAt
    }
  }
`;

export const KP_LEDGER = gql`
  query KPLedger($userId: UUID, $action: String, $limit: Int) {
    kpLedger(userId: $userId, action: $action, limit: $limit) {
      id
      userId
      action
      dimension
      points
      description
      balanceAfter
      createdAt
    }
  }
`;

export const MY_KP_HISTORY = gql`
  query MyKPHistory($limit: Int) {
    myKpHistory(limit: $limit) {
      id
      action
      dimension
      points
      description
      balanceAfter
      createdAt
    }
  }
`;
