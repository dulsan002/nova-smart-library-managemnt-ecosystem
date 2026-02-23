/**
 * Intelligence GraphQL mutations.
 */

import { gql } from '@apollo/client';

export const GENERATE_RECOMMENDATIONS = gql`
  mutation GenerateRecommendations {
    generateRecommendations {
      taskId
    }
  }
`;

export const CLICK_RECOMMENDATION = gql`
  mutation ClickRecommendation($recommendationId: UUID!) {
    clickRecommendation(recommendationId: $recommendationId) {
      success
    }
  }
`;

export const DISMISS_RECOMMENDATION = gql`
  mutation DismissRecommendation($recommendationId: UUID!) {
    dismissRecommendation(recommendationId: $recommendationId) {
      success
    }
  }
`;

export const UPDATE_PREFERENCES = gql`
  mutation UpdatePreferences(
    $preferredCategories: [String]
    $preferredAuthors: [String]
    $preferredLanguages: [String]
    $dislikedCategories: [String]
  ) {
    updatePreferences(
      preferredCategories: $preferredCategories
      preferredAuthors: $preferredAuthors
      preferredLanguages: $preferredLanguages
      dislikedCategories: $dislikedCategories
    ) {
      preferences {
        id
        preferredCategories
        preferredAuthors
        preferredLanguages
        dislikedCategories
      }
    }
  }
`;

export const MARK_NOTIFICATION_READ = gql`
  mutation MarkNotificationRead($notificationId: UUID!) {
    markNotificationRead(notificationId: $notificationId) {
      success
    }
  }
`;

export const MARK_ALL_NOTIFICATIONS_READ = gql`
  mutation MarkAllNotificationsRead {
    markAllNotificationsRead {
      count
    }
  }
`;

export const LOG_SEARCH_CLICK = gql`
  mutation LogSearchClick($searchLogId: UUID!, $clickedBookId: UUID!) {
    logSearchClick(searchLogId: $searchLogId, clickedBookId: $clickedBookId) {
      success
    }
  }
`;

export const TRIGGER_MODEL_TRAINING = gql`
  mutation TriggerModelTraining($pipeline: String) {
    triggerModelTraining(pipeline: $pipeline) {
      taskId
    }
  }
`;

export const TRIGGER_EMBEDDING_COMPUTATION = gql`
  mutation TriggerEmbeddingComputation($batchSize: Int) {
    triggerEmbeddingComputation(batchSize: $batchSize) {
      taskId
    }
  }
`;

export const ACTIVATE_AI_MODEL = gql`
  mutation ActivateAIModel($modelId: UUID!) {
    activateAiModel(modelId: $modelId) {
      success
      model {
        id
        version
        isActive
      }
    }
  }
`;

// --- AI Provider Configuration ---

export const CREATE_AI_PROVIDER_CONFIG = gql`
  mutation CreateAIProviderConfig(
    $provider: String!
    $capability: String!
    $displayName: String!
    $modelName: String!
    $apiBaseUrl: String
    $apiKey: String
    $extraConfig: JSONString
  ) {
    createAiProviderConfig(
      provider: $provider
      capability: $capability
      displayName: $displayName
      modelName: $modelName
      apiBaseUrl: $apiBaseUrl
      apiKey: $apiKey
      extraConfig: $extraConfig
    ) {
      config {
        id
        provider
        capability
        displayName
        modelName
        apiBaseUrl
        isActive
        isHealthy
      }
    }
  }
`;

export const UPDATE_AI_PROVIDER_CONFIG = gql`
  mutation UpdateAIProviderConfig(
    $configId: UUID!
    $displayName: String
    $modelName: String
    $apiBaseUrl: String
    $apiKey: String
    $extraConfig: JSONString
  ) {
    updateAiProviderConfig(
      configId: $configId
      displayName: $displayName
      modelName: $modelName
      apiBaseUrl: $apiBaseUrl
      apiKey: $apiKey
      extraConfig: $extraConfig
    ) {
      config {
        id
        provider
        capability
        displayName
        modelName
        apiBaseUrl
        isActive
        isHealthy
      }
    }
  }
`;

export const DELETE_AI_PROVIDER_CONFIG = gql`
  mutation DeleteAIProviderConfig($configId: UUID!) {
    deleteAiProviderConfig(configId: $configId) {
      success
    }
  }
`;

export const ACTIVATE_AI_PROVIDER_CONFIG = gql`
  mutation ActivateAIProviderConfig($configId: UUID!) {
    activateAiProviderConfig(configId: $configId) {
      config {
        id
        capability
        isActive
      }
    }
  }
`;

export const TEST_AI_PROVIDER_CONFIG = gql`
  mutation TestAIProviderConfig($configId: UUID!) {
    testAiProviderConfig(configId: $configId) {
      healthy
      message
      config {
        id
        isHealthy
        lastHealthCheck
        lastError
      }
    }
  }
`;

export const GENERATE_AI_RESPONSE = gql`
  mutation GenerateAIResponse($prompt: String!, $systemPrompt: String, $capability: String) {
    generateAiResponse(prompt: $prompt, systemPrompt: $systemPrompt, capability: $capability) {
      text
      model
      error
    }
  }
`;

export const LOG_BOOK_VIEW = gql`
  mutation LogBookView($bookId: UUID!, $source: String, $durationSeconds: Int) {
    logBookView(bookId: $bookId, source: $source, durationSeconds: $durationSeconds) {
      success
      viewId
    }
  }
`;
