/**
 * Catalog GraphQL queries.
 */

import { gql } from '@apollo/client';

export const BOOK_FRAGMENT = gql`
  fragment BookFields on BookType {
    id
    title
    subtitle
    isbn13
    isbn10
    publisher
    publicationDate
    edition
    language
    pageCount
    description
    coverImageUrl
    averageRating
    ratingCount
    totalBorrows
    availableCopies
    totalCopies
    hasEbook
    hasAudiobook
    tags
    createdAt
    authors {
      id
      firstName
      lastName
    }
    categories {
      id
      name
      slug
    }
  }
`;

export const GET_BOOKS = gql`
  ${BOOK_FRAGMENT}
  query GetBooks(
    $first: Int
    $after: String
    $query: String
    $categoryId: UUID
    $authorId: UUID
    $language: String
    $availableOnly: Boolean
    $orderBy: String
  ) {
    books(
      first: $first
      after: $after
      query: $query
      categoryId: $categoryId
      authorId: $authorId
      language: $language
      availableOnly: $availableOnly
      orderBy: $orderBy
    ) {
      edges {
        node {
          ...BookFields
        }
        cursor
      }
      pageInfo {
        hasNextPage
        endCursor
      }
      totalCount
    }
  }
`;

export const GET_BOOK = gql`
  ${BOOK_FRAGMENT}
  query GetBook($id: UUID!) {
    book(id: $id) {
      ...BookFields
      copies {
        id
        barcode
        status
        condition
        floorNumber
        shelfNumber
        shelfLocation
        branch
      }
      reviews {
        id
        user {
          id
          firstName
          lastName
        }
        rating
        title
        content
        createdAt
      }
    }
  }
`;

export const GET_BOOK_BY_ISBN = gql`
  ${BOOK_FRAGMENT}
  query GetBookByISBN($isbn: String!) {
    bookByIsbn(isbn: $isbn) {
      ...BookFields
    }
  }
`;

export const GET_AUTHORS = gql`
  query GetAuthors($search: String, $limit: Int) {
    authors(search: $search, limit: $limit) {
      id
      firstName
      lastName
      biography
      birthDate
      deathDate
      nationality
      photoUrl
    }
  }
`;

export const GET_AUTHOR = gql`
  query GetAuthor($id: UUID!) {
    author(id: $id) {
      id
      firstName
      lastName
      biography
      birthDate
      deathDate
      nationality
      photoUrl
    }
  }
`;

export const GET_CATEGORIES = gql`
  query GetCategories($rootOnly: Boolean) {
    categories(rootOnly: $rootOnly) {
      id
      name
      slug
      description
      icon
      parent {
        id
      }
      sortOrder
      children {
        id
        name
        slug
      }
    }
  }
`;

export const GET_BOOK_COPIES = gql`
  query GetBookCopies($bookId: UUID!, $status: String) {
    bookCopies(bookId: $bookId, status: $status) {
      id
      barcode
      status
      condition
      floorNumber
      shelfNumber
      shelfLocation
      branch
      acquisitionDate
    }
  }
`;
