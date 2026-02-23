/**
 * Engagement GraphQL queries.
 */

import { gql } from '@apollo/client';

export const MY_ENGAGEMENT = gql`
  query MyEngagement {
    myEngagement {
      id
      totalKp
      level
      levelTitle
      currentStreak
      longestStreak
      lastActivityDate
      explorerKp
      scholarKp
      connectorKp
      achieverKp
      dedicatedKp
      kpEarnedToday
      streakMultiplier
      rank
      rankPercentile
    }
  }
`;

export const MY_ACHIEVEMENTS = gql`
  query MyAchievements {
    myAchievements {
      id
      earnedAt
      achievement {
        id
        name
        description
        category
        icon
        kpReward
        criteria
      }
    }
  }
`;

export const MY_DAILY_ACTIVITY = gql`
  query MyDailyActivity($days: Int) {
    myDailyActivity(days: $days) {
      id
      date
      kpEarned
      booksBorrowed
      pagesRead
      sessionsCompleted
      readingMinutes
    }
  }
`;

export const MY_RANK = gql`
  query MyRank {
    myRank {
      rank
      totalKp
      level
      levelTitle
      percentile
    }
  }
`;

export const ALL_ACHIEVEMENTS = gql`
  query AllAchievements($category: String) {
    allAchievements(category: $category) {
      id
      name
      description
      category
      icon
      kpReward
      rarity
      criteria
      isActive
      sortOrder
    }
  }
`;

export const LEADERBOARD = gql`
  query Leaderboard($limit: Int) {
    leaderboard(limit: $limit) {
      rank
      userId
      fullName
      email
      avatarUrl
      totalKp
      level
      levelTitle
    }
  }
`;
