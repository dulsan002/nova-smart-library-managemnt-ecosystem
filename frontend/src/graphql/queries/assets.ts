/**
 * Asset Management GraphQL queries.
 */

import { gql } from '@apollo/client';

export const GET_ASSETS = gql`
  query GetAssets($status: String, $categoryId: UUID, $search: String, $limit: Int) {
    assets(status: $status, categoryId: $categoryId, search: $search, limit: $limit) {
      id
      assetTag
      name
      description
      status
      condition
      floorNumber
      room
      purchaseDate
      purchasePrice
      supplier
      warrantyExpiry
      manufacturer
      modelNumber
      serialNumber
      currentValue
      isUnderWarranty
      maintenanceOverdue
      nextMaintenanceDate
      imageUrl
      createdAt
      category {
        id
        name
        slug
      }
      assignedTo {
        id
        firstName
        lastName
        email
      }
    }
  }
`;

export const GET_ASSET = gql`
  query GetAsset($id: UUID!) {
    asset(id: $id) {
      id
      assetTag
      name
      description
      status
      condition
      floorNumber
      room
      locationNotes
      purchaseDate
      purchasePrice
      supplier
      warrantyExpiry
      usefulLifeYears
      salvageValue
      serialNumber
      manufacturer
      modelNumber
      currentValue
      isUnderWarranty
      maintenanceOverdue
      nextMaintenanceDate
      maintenanceIntervalDays
      imageUrl
      createdAt
      updatedAt
      category {
        id
        name
      }
      assignedTo {
        id
        firstName
        lastName
      }
    }
  }
`;

export const GET_ASSET_CATEGORIES = gql`
  query GetAssetCategories {
    assetCategories {
      id
      name
      slug
      icon
      description
      assetCount
      parent {
        id
        name
      }
    }
  }
`;

export const GET_ASSET_STATS = gql`
  query GetAssetStats {
    assetStats {
      totalAssets
      activeCount
      underMaintenanceCount
      disposedCount
      totalValue
      maintenanceOverdueCount
      warrantyExpiringSoon
    }
  }
`;

export const GET_MAINTENANCE_LOGS = gql`
  query GetMaintenanceLogs($assetId: UUID, $limit: Int) {
    maintenanceLogs(assetId: $assetId, limit: $limit) {
      id
      maintenanceType
      description
      performedDate
      cost
      vendor
      notes
      conditionAfter
      createdAt
      asset {
        id
        name
        assetTag
      }
      performedBy {
        id
        firstName
        lastName
      }
    }
  }
`;
