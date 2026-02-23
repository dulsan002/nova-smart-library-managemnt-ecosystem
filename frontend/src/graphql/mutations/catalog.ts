/**
 * Catalog GraphQL mutations.
 */

import { gql } from '@apollo/client';
import { BOOK_FRAGMENT } from '@/graphql/queries/catalog';

export const CREATE_BOOK = gql`
  ${BOOK_FRAGMENT}
  mutation CreateBook($input: CreateBookInput!) {
    createBook(input: $input) {
      ...BookFields
    }
  }
`;

export const UPDATE_BOOK = gql`
  ${BOOK_FRAGMENT}
  mutation UpdateBook($bookId: UUID!, $input: UpdateBookInput!) {
    updateBook(bookId: $bookId, input: $input) {
      ...BookFields
    }
  }
`;

export const ADD_BOOK_COPY = gql`
  mutation AddBookCopy($input: AddBookCopyInput!) {
    addBookCopy(input: $input) {
      id
      barcode
      status
      condition
      shelfLocation
      branch
    }
  }
`;

export const CREATE_AUTHOR = gql`
  mutation CreateAuthor($input: CreateAuthorInput!) {
    createAuthor(input: $input) {
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

export const UPDATE_AUTHOR = gql`
  mutation UpdateAuthor($authorId: UUID!, $input: UpdateAuthorInput!) {
    updateAuthor(authorId: $authorId, input: $input) {
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

export const DELETE_AUTHOR = gql`
  mutation DeleteAuthor($authorId: UUID!) {
    deleteAuthor(authorId: $authorId) {
      ok
    }
  }
`;

export const DELETE_BOOK = gql`
  mutation DeleteBook($bookId: UUID!) {
    deleteBook(bookId: $bookId) {
      ok
    }
  }
`;

export const CREATE_CATEGORY = gql`
  mutation CreateCategory($input: CreateCategoryInput!) {
    createCategory(input: $input) {
      id
      name
      slug
    }
  }
`;

export const SUBMIT_BOOK_REVIEW = gql`
  mutation SubmitBookReview(
    $bookId: UUID!
    $rating: Int!
    $title: String
    $content: String
  ) {
    submitBookReview(
      bookId: $bookId
      rating: $rating
      title: $title
      content: $content
    ) {
      id
      rating
      title
      content
      createdAt
    }
  }
`;
