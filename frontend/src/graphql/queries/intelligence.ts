/**
 * Intelligence GraphQL queries — search, recommendations, analytics,
 * notifications, reading behaviour.
 */

import { gql } from '@apollo/client';

// --- Recommendations ---

export const MY_RECOMMENDATIONS = gql`
  query MyRecommendations($limit: Int, $strategy: String) {
    myRecommendations(limit: $limit, strategy: $strategy) {
      id
      score
      strategy
      explanation
      isClicked
      isDismissed
      book {
        id
        title
        coverImageUrl
        averageRating
        authors {
          firstName
          lastName
        }
      }
    }
  }
`;

export const MY_PREFERENCES = gql`
  query MyPreferences {
    myPreferences {
      id
      preferredCategories
      preferredAuthors
      preferredLanguages
      dislikedCategories
      readingSpeed
    }
  }
`;

// --- Trending ---

export const TRENDING_BOOKS = gql`
  query TrendingBooks($period: String, $limit: Int) {
    trendingBooks(period: $period, limit: $limit) {
      id
      rank
      score
      borrowCount
      reviewCount
      book {
        id
        title
        coverImageUrl
        averageRating
        authors {
          firstName
          lastName
        }
      }
    }
  }
`;

export const TRENDING_SEARCHES = gql`
  query TrendingSearches($limit: Int, $days: Int) {
    trendingSearches(limit: $limit, days: $days) {
      queryText
      count
    }
  }
`;

// --- Hybrid Search ---

export const SEARCH_BOOKS = gql`
  query SearchBooks(
    $query: String!
    $page: Int
    $pageSize: Int
    $category: String
    $author: String
    $language: String
    $minRating: Float
    $yearFrom: Int
    $yearTo: Int
    $digitalOnly: Boolean
    $availableOnly: Boolean
  ) {
    searchBooks(
      query: $query
      page: $page
      pageSize: $pageSize
      category: $category
      author: $author
      language: $language
      minRating: $minRating
      yearFrom: $yearFrom
      yearTo: $yearTo
      digitalOnly: $digitalOnly
      availableOnly: $availableOnly
    ) {
      results {
        bookId
        title
        subtitle
        authorNames
        isbn
        score
        snippet
      }
      total
      page
      facets {
        name
        values {
          value
          count
        }
      }
      queryTimeMs
      correctedQuery
    }
  }
`;

export const AUTO_SUGGEST = gql`
  query AutoSuggest($prefix: String!, $limit: Int) {
    autoSuggest(prefix: $prefix, limit: $limit) {
      text
      source
    }
  }
`;

// --- AI-powered Search ---

export const AI_SEARCH = gql`
  query AiSearch($query: String!) {
    aiSearch(query: $query) {
      answer
      sources {
        bookId
        title
        subtitle
        authors
        categories
        isbn
        rating
        availableCopies
        totalCopies
        totalBorrows
      }
      modelUsed
      error
    }
  }
`;

// --- Notifications ---

export const MY_NOTIFICATIONS = gql`
  query MyNotifications($limit: Int, $unreadOnly: Boolean) {
    myNotifications(limit: $limit, unreadOnly: $unreadOnly) {
      id
      notificationType
      channel
      priority
      title
      body
      data
      isRead
      readAt
      createdAt
    }
  }
`;

export const NOTIFICATION_COUNT = gql`
  query NotificationCount {
    notificationCount {
      totalUnread
      byType
    }
  }
`;

// --- Reading Behaviour ---

export const MY_READING_SPEED = gql`
  query MyReadingSpeed {
    myReadingSpeed {
      wordsPerMinute
      category
      sessionsAnalyzed
    }
  }
`;

export const MY_SESSION_PATTERNS = gql`
  query MySessionPatterns {
    mySessionPatterns {
      peakHour
      peakDay
      avgSessionMinutes
      preferredTime
      sessionsPerWeek
      totalSessions
    }
  }
`;

export const MY_ENGAGEMENT_HEATMAP = gql`
  query MyEngagementHeatmap($days: Int) {
    myEngagementHeatmap(days: $days) {
      heatmap
      days
      hours
    }
  }
`;

export const MY_COMPLETION_PREDICTIONS = gql`
  query MyCompletionPredictions {
    myCompletionPredictions {
      assetId
      title
      completionProbability
      estimatedDays
      currentProgress
    }
  }
`;

// --- Admin: Predictive Analytics ---

export const OVERDUE_PREDICTIONS = gql`
  query OverduePredictions($limit: Int) {
    overduePredictions(limit: $limit) {
      borrowId
      userEmail
      bookTitle
      probability
      riskLevel
      contributingFactors
    }
  }
`;

export const DEMAND_FORECASTS = gql`
  query DemandForecasts($limit: Int) {
    demandForecasts(limit: $limit) {
      bookId
      bookTitle
      trend
      predictedBorrows
      recommendedCopies
    }
  }
`;

export const CHURN_PREDICTIONS = gql`
  query ChurnPredictions($limit: Int) {
    churnPredictions(limit: $limit) {
      userId
      userEmail
      churnProbability
      riskLevel
      weeksInactive
      recommendations
    }
  }
`;

export const COLLECTION_GAPS = gql`
  query CollectionGaps($minSeverity: String) {
    collectionGaps(minSeverity: $minSeverity) {
      categoryName
      gapSeverity
      currentCopies
      borrowDemand
      searchDemand
      waitlistCount
      suggestedAcquisitions
    }
  }
`;

// --- Admin: LLM Analytics ---

export const LLM_ANALYTICS = gql`
  query LLMAnalytics {
    llmAnalytics {
      summary
      overdueInsights
      demandInsights
      userInsights
      collectionInsights
      recommendations
      modelUsed
      error
    }
  }
`;

// --- Admin: AI Models ---

export const AI_MODELS = gql`
  query AIModels($modelType: String) {
    aiModels(modelType: $modelType) {
      id
      modelType
      version
      name
      description
      config
      metrics
      isActive
      createdAt
    }
  }
`;

export const RECOMMENDATION_METRICS = gql`
  query RecommendationMetrics($k: Int) {
    recommendationMetrics(k: $k) {
      precisionAtK
      recallAtK
      ndcgAtK
      mrr
      hitRate
      catalogCoverage
      diversity
      novelty
    }
  }
`;

// --- Admin: AI Provider Configs ---

export const AI_PROVIDER_CONFIGS = gql`
  query AIProviderConfigs($capability: String, $activeOnly: Boolean) {
    aiProviderConfigs(capability: $capability, activeOnly: $activeOnly) {
      id
      provider
      capability
      displayName
      modelName
      apiBaseUrl
      extraConfig
      isActive
      isHealthy
      lastHealthCheck
      lastError
      createdAt
      updatedAt
    }
  }
`;

export const MY_BROWSE_HISTORY = gql`
  query MyBrowseHistory($limit: Int) {
    myBrowseHistory(limit: $limit) {
      id
      book {
        id
        title
        coverImageUrl
      }
      viewedAt
      durationSeconds
      source
    }
  }
`;