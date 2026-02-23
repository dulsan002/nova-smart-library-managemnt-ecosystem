/**
 * Digital Content GraphQL queries.
 */

import { gql } from '@apollo/client';

export const GET_DIGITAL_ASSET = gql`
  query GetDigitalAsset($id: UUID!) {
    digitalAsset(id: $id) {
      id
      assetType
      mimeType
      fileSizeBytes
      totalPages
      durationSeconds
      narrator
      createdAt
      book {
        id
        title
        subtitle
        coverImageUrl
        authors {
          id
          firstName
          lastName
        }
      }
    }
  }
`;

export const DIGITAL_ASSETS_FOR_BOOK = gql`
  query DigitalAssetsForBook($bookId: UUID!) {
    digitalAssetsForBook(bookId: $bookId) {
      id
      assetType
      mimeType
      fileSizeBytes
      totalPages
      durationSeconds
      narrator
      createdAt
    }
  }
`;

export const MY_LIBRARY = gql`
  query MyLibrary($favoritesOnly: Boolean) {
    myLibrary(favoritesOnly: $favoritesOnly) {
      id
      isFavorite
      isFinished
      lastAccessedAt
      overallProgress
      totalTimeSeconds
      lastPosition
      digitalAsset {
        id
        assetType
        totalPages
        durationSeconds
        narrator
        mimeType
        book {
          id
          title
          coverImageUrl
          authors {
            firstName
            lastName
          }
        }
      }
    }
  }
`;

export const MY_READING_SESSIONS = gql`
  query MyReadingSessions($status: String, $limit: Int) {
    myReadingSessions(status: $status, limit: $limit) {
      id
      sessionType
      status
      progressPercent
      startedAt
      endedAt
      durationSeconds
      digitalAsset {
        id
        book {
          id
          title
        }
      }
    }
  }
`;

export const ACTIVE_SESSION = gql`
  query ActiveSession($digitalAssetId: UUID) {
    activeSession(digitalAssetId: $digitalAssetId) {
      id
      sessionType
      progressPercent
      lastPosition
      digitalAsset {
        id
        assetType
        totalPages
        durationSeconds
        book {
          id
          title
        }
      }
    }
  }
`;

export const MY_BOOKMARKS = gql`
  query MyBookmarks($digitalAssetId: UUID) {
    myBookmarks(digitalAssetId: $digitalAssetId) {
      id
      title
      position
      note
      color
      createdAt
    }
  }
`;

export const MY_HIGHLIGHTS = gql`
  query MyHighlights($digitalAssetId: UUID) {
    myHighlights(digitalAssetId: $digitalAssetId) {
      id
      text
      positionStart
      positionEnd
      color
      note
      createdAt
    }
  }
`;

export const ALL_DIGITAL_ASSETS = gql`
  query AllDigitalAssets($assetType: String) {
    allDigitalAssets(assetType: $assetType) {
      id
      assetType
      filePath
      mimeType
      fileSizeBytes
      totalPages
      durationSeconds
      narrator
      isDrmProtected
      createdAt
      book {
        id
        title
        coverImageUrl
        authors {
          id
          firstName
          lastName
        }
      }
    }
  }
`;
