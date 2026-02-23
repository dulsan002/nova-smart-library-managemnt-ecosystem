/**
 * Apollo Client configuration for Nova GraphQL API.
 *
 * Features:
 * - Automatic JWT token injection via auth link
 * - Token refresh on 401 via error link
 * - In-memory cache with type policies
 * - Retry logic for network errors
 */

import {
  ApolloClient,
  InMemoryCache,
  createHttpLink,
  from,
  type NormalizedCacheObject,
} from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import { onError } from '@apollo/client/link/error';
import { useAuthStore } from '@/stores/authStore';

/**
 * Custom field policy for our flat-edge pagination (not Relay-style).
 * Our backend returns `{ edges: [BookType], pageInfo, totalCount }` where
 * edges are flat objects — NOT wrapped in `{ node, cursor }`.
 * relayStylePagination expects Relay-style edges and filters ours out.
 */
function flatConnectionPagination(keyArgs: string[] | false) {
  return {
    keyArgs,
    merge: false as const, // Each page is standalone; replace, don't merge
  };
}

const GRAPHQL_URL =
  import.meta.env.VITE_GRAPHQL_URL || '/graphql/';

// --- HTTP Link ---
const httpLink = createHttpLink({
  uri: GRAPHQL_URL,
  credentials: 'include',
});

// --- Auth Link: inject JWT bearer token ---
const authLink = setContext((_, { headers }) => {
  const token = useAuthStore.getState().accessToken;
  return {
    headers: {
      ...headers,
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  };
});

// --- Error Link: handle auth errors, trigger refresh ---
const errorLink = onError(({ graphQLErrors, networkError, operation, forward }) => {
  if (graphQLErrors) {
    for (const err of graphQLErrors) {
      // JWT expired or permission denied
      if (
        err.message.includes('Signature has expired') ||
        err.message.includes('Error decoding signature')
      ) {
        const { refreshTokens, logout } = useAuthStore.getState();
        refreshTokens()
          .then((success) => {
            if (success) {
              // Retry the failed operation
              const oldHeaders = operation.getContext().headers;
              const newToken = useAuthStore.getState().accessToken;
              operation.setContext({
                headers: {
                  ...oldHeaders,
                  Authorization: `Bearer ${newToken}`,
                },
              });
              return forward(operation);
            } else {
              logout();
            }
          })
          .catch(() => logout());
      }
    }
  }

  if (networkError) {
    console.error(`[Network error]: ${networkError.message}`);
  }
});

// --- Cache with type policies ---
const cache = new InMemoryCache({
  typePolicies: {
    Query: {
      fields: {
        books: flatConnectionPagination(['query', 'categoryId', 'authorId', 'language']),
        users: flatConnectionPagination(['role', 'isActive', 'search']),
        allBorrows: flatConnectionPagination(['status', 'userId']),
        auditLogs: flatConnectionPagination(['action', 'resourceType', 'actorId']),
      },
    },
    BookType: {
      keyFields: ['id'],
    },
    UserType: {
      keyFields: ['id'],
    },
    BorrowRecordType: {
      keyFields: ['id'],
    },
    RecommendationType: {
      keyFields: ['id'],
    },
  },
});

// --- Client ---
export const apolloClient: ApolloClient<NormalizedCacheObject> = new ApolloClient({
  link: from([errorLink, authLink, httpLink]),
  cache,
  defaultOptions: {
    watchQuery: {
      fetchPolicy: 'cache-and-network',
      errorPolicy: 'all',
    },
    query: {
      fetchPolicy: 'cache-first',
      errorPolicy: 'all',
    },
    mutate: {
      errorPolicy: 'all',
    },
  },
});
