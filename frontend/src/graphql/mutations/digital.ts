/**
 * Digital Content GraphQL mutations.
 */

import { gql } from '@apollo/client';

export const START_READING_SESSION = gql`
  mutation StartReadingSession(
    $digitalAssetId: UUID!
    $sessionType: String!
    $deviceType: String
  ) {
    startReadingSession(
      digitalAssetId: $digitalAssetId
      sessionType: $sessionType
      deviceType: $deviceType
    ) {
      id
      sessionType
      status
      startedAt
    }
  }
`;

export const END_READING_SESSION = gql`
  mutation EndReadingSession($sessionId: UUID!) {
    endReadingSession(sessionId: $sessionId) {
      id
      status
      endedAt
      durationSeconds
    }
  }
`;

export const UPDATE_READING_PROGRESS = gql`
  mutation UpdateReadingProgress(
    $sessionId: UUID!
    $progressPercent: Float!
    $position: JSONString
  ) {
    updateReadingProgress(
      sessionId: $sessionId
      progressPercent: $progressPercent
      position: $position
    ) {
      id
      progressPercent
    }
  }
`;

export const ADD_BOOKMARK = gql`
  mutation AddBookmark(
    $digitalAssetId: UUID!
    $title: String
    $position: JSONString!
    $note: String
    $color: String
  ) {
    addBookmark(
      digitalAssetId: $digitalAssetId
      title: $title
      position: $position
      note: $note
      color: $color
    ) {
      id
      title
      position
    }
  }
`;

export const ADD_HIGHLIGHT = gql`
  mutation AddHighlight(
    $digitalAssetId: UUID!
    $text: String!
    $positionStart: JSONString!
    $positionEnd: JSONString!
    $color: String
    $note: String
  ) {
    addHighlight(
      digitalAssetId: $digitalAssetId
      text: $text
      positionStart: $positionStart
      positionEnd: $positionEnd
      color: $color
      note: $note
    ) {
      id
      text
      color
    }
  }
`;

export const TOGGLE_FAVORITE = gql`
  mutation ToggleFavorite($digitalAssetId: UUID!) {
    toggleFavorite(digitalAssetId: $digitalAssetId) {
      id
      isFavorite
    }
  }
`;

export const UPLOAD_DIGITAL_ASSET = gql`
  mutation UploadDigitalAsset(
    $bookId: UUID!
    $assetType: String!
    $filePath: String!
    $fileSizeBytes: Int!
    $mimeType: String
    $durationSeconds: Int
    $narrator: String
    $totalPages: Int
  ) {
    uploadDigitalAsset(
      bookId: $bookId
      assetType: $assetType
      filePath: $filePath
      fileSizeBytes: $fileSizeBytes
      mimeType: $mimeType
      durationSeconds: $durationSeconds
      narrator: $narrator
      totalPages: $totalPages
    ) {
      id
      assetType
      book {
        id
        title
      }
    }
  }
`;

export const DELETE_DIGITAL_ASSET = gql`
  mutation DeleteDigitalAsset($digitalAssetId: UUID!) {
    deleteDigitalAsset(digitalAssetId: $digitalAssetId) {
      ok
    }
  }
`;

export const UPDATE_DIGITAL_ASSET = gql`
  mutation UpdateDigitalAsset(
    $digitalAssetId: UUID!
    $assetType: String
    $filePath: String
    $fileSizeBytes: Int
    $mimeType: String
    $durationSeconds: Int
    $narrator: String
    $totalPages: Int
  ) {
    updateDigitalAsset(
      digitalAssetId: $digitalAssetId
      assetType: $assetType
      filePath: $filePath
      fileSizeBytes: $fileSizeBytes
      mimeType: $mimeType
      durationSeconds: $durationSeconds
      narrator: $narrator
      totalPages: $totalPages
    ) {
      id
      assetType
      filePath
      fileSizeBytes
      mimeType
      durationSeconds
      narrator
      totalPages
      book {
        id
        title
      }
    }
  }
`;
