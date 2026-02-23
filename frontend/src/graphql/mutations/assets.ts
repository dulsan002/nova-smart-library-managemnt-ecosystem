/**
 * Asset Management GraphQL mutations.
 */

import { gql } from '@apollo/client';

export const CREATE_ASSET_CATEGORY = gql`
  mutation CreateAssetCategory($name: String!, $slug: String!, $parentId: UUID, $description: String, $icon: String) {
    createAssetCategory(name: $name, slug: $slug, parentId: $parentId, description: $description, icon: $icon) {
      id
      name
      slug
    }
  }
`;

export const CREATE_ASSET = gql`
  mutation CreateAsset(
    $assetTag: String!
    $name: String!
    $categoryId: UUID!
    $description: String
    $status: String
    $condition: String
    $floorNumber: Int
    $room: String
    $purchaseDate: Date
    $purchasePrice: Float
    $supplier: String
    $warrantyExpiry: Date
    $usefulLifeYears: Int
    $serialNumber: String
    $manufacturer: String
    $modelNumber: String
    $nextMaintenanceDate: Date
    $maintenanceIntervalDays: Int
  ) {
    createAsset(
      assetTag: $assetTag
      name: $name
      categoryId: $categoryId
      description: $description
      status: $status
      condition: $condition
      floorNumber: $floorNumber
      room: $room
      purchaseDate: $purchaseDate
      purchasePrice: $purchasePrice
      supplier: $supplier
      warrantyExpiry: $warrantyExpiry
      usefulLifeYears: $usefulLifeYears
      serialNumber: $serialNumber
      manufacturer: $manufacturer
      modelNumber: $modelNumber
      nextMaintenanceDate: $nextMaintenanceDate
      maintenanceIntervalDays: $maintenanceIntervalDays
    ) {
      id
      assetTag
      name
      status
    }
  }
`;

export const UPDATE_ASSET = gql`
  mutation UpdateAsset(
    $id: UUID!
    $name: String
    $status: String
    $condition: String
    $floorNumber: Int
    $room: String
    $description: String
    $nextMaintenanceDate: Date
    $maintenanceIntervalDays: Int
  ) {
    updateAsset(
      id: $id
      name: $name
      status: $status
      condition: $condition
      floorNumber: $floorNumber
      room: $room
      description: $description
      nextMaintenanceDate: $nextMaintenanceDate
      maintenanceIntervalDays: $maintenanceIntervalDays
    ) {
      id
      name
      status
      condition
    }
  }
`;

export const DELETE_ASSET = gql`
  mutation DeleteAsset($id: UUID!) {
    deleteAsset(id: $id) {
      ok
    }
  }
`;

export const LOG_MAINTENANCE = gql`
  mutation LogMaintenance(
    $assetId: UUID!
    $maintenanceType: String!
    $description: String!
    $performedDate: Date!
    $cost: Float
    $vendor: String
    $notes: String
    $conditionAfter: String
  ) {
    logMaintenance(
      assetId: $assetId
      maintenanceType: $maintenanceType
      description: $description
      performedDate: $performedDate
      cost: $cost
      vendor: $vendor
      notes: $notes
      conditionAfter: $conditionAfter
    ) {
      id
      maintenanceType
      description
    }
  }
`;

export const DISPOSE_ASSET = gql`
  mutation DisposeAsset(
    $assetId: UUID!
    $method: String!
    $disposedDate: Date!
    $disposalValue: Float
    $reason: String!
    $notes: String
  ) {
    disposeAsset(
      assetId: $assetId
      method: $method
      disposedDate: $disposedDate
      disposalValue: $disposalValue
      reason: $reason
      notes: $notes
    ) {
      id
      method
    }
  }
`;
