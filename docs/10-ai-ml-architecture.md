# 10 — AI/ML Architecture

> AI/ML pipeline, hybrid search engine, recommendation engine, predictive analytics, LLM integration, and model management

---

## 1. AI/ML System Overview

```mermaid
graph TB
    subgraph "AI/ML Capabilities"
        direction LR
        Search["Hybrid Search<br/>Full-text + Semantic + Fuzzy"]
        Recommend["Recommendation Engine<br/>Collaborative + Content-based"]
        Predict["Predictive Analytics<br/>Overdue, Demand, Churn"]
        Content["Content Analysis<br/>Auto-tagging, Reading Level"]
        LLMSearch["AI Search<br/>Conversational LLM"]
        LLMAnalytics["LLM Analytics<br/>Natural Language Insights"]
        ReadBehavior["Reading Behavior<br/>Speed, Patterns, Heatmap"]
        Verify["Identity Verification<br/>OCR + Face Recognition"]
        Notify["Smart Notifications<br/>Multi-channel, Dedup"]
    end

    subgraph "AI Infrastructure"
        Embeddings["Embedding Model<br/>all-MiniLM-L6-v2<br/>384 dimensions"]
        PGVector[("pgvector<br/>Embedding Storage")]
        Ollama["Ollama LLM Server<br/>llama3.1"]
        SKLearn["scikit-learn<br/>ML Models"]
        OCR["pytesseract<br/>OCR Engine"]
        FaceRec["face-recognition<br/>Face Encoding"]
    end

    subgraph "Provider Abstraction"
        Factory["AI Provider Factory"]
        OllamaP["Ollama Provider"]
        OpenAIP["OpenAI Provider"]
        GeminiP["Gemini Provider"]
        LocalP["Local Transformers"]
    end

    Search --> Embeddings
    Search --> PGVector
    Recommend --> PGVector
    Recommend --> SKLearn
    Predict --> SKLearn
    Content --> Embeddings
    LLMSearch --> Factory
    LLMAnalytics --> Factory
    Factory --> OllamaP --> Ollama
    Factory --> OpenAIP
    Factory --> GeminiP
    Factory --> LocalP
    Verify --> OCR
    Verify --> FaceRec
```

---

## 2. Hybrid Search Engine

### 2.1 Architecture

```mermaid
graph TB
    Query["User Query"] --> Engine["SearchEngine"]

    subgraph "Search Strategies (Parallel)"
        FT["Full-Text Search<br/>PostgreSQL tsvector<br/>ts_rank scoring<br/>Weight: 0.45"]
        SM["Semantic Search<br/>Sentence Transformers<br/>pgvector cosine similarity<br/>Weight: 0.35"]
        FZ["Fuzzy Search<br/>pg_trgm extension<br/>Trigram similarity<br/>Weight: 0.20"]
    end

    Engine --> FT
    Engine --> SM
    Engine --> FZ

    FT --> Merge["Result Merger"]
    SM --> Merge
    FZ --> Merge

    Merge --> Dedup["Deduplication"]
    Dedup --> Rank["Weighted Ranking"]
    Rank --> Filters["Apply Filters<br/>category, author, language,<br/>rating, year, availability"]
    Filters --> Facets["Build Facets"]
    Facets --> Results["SearchResponseType"]
```

### 2.2 Search Weights Configuration

| Strategy | Weight | Best For |
|----------|--------|----------|
| **Full-text** | 0.45 | Exact keyword matches, title searches |
| **Semantic** | 0.35 | Conceptual similarity, natural language queries |
| **Fuzzy** | 0.20 | Typo tolerance, partial matches |

### 2.3 Embedding Pipeline

```mermaid
graph LR
    subgraph "Embedding Computation"
        Book["Book Record<br/>title + description + authors"]
        Concat["Text Concatenation"]
        Model["all-MiniLM-L6-v2<br/>Sentence Transformer"]
        Vector["384-dim Vector"]
        Store[("pgvector column<br/>Book.embedding")]
    end

    subgraph "Similarity Search"
        QueryText["Query Text"]
        QueryEmbed["Query Embedding"]
        Cosine["Cosine Similarity<br/>1 - cosine_distance"]
        TopK["Top-K Results"]
    end

    Book --> Concat --> Model --> Vector --> Store
    QueryText --> Model --> QueryEmbed --> Cosine
    Store --> Cosine --> TopK
```

### 2.4 Auto-Suggest

| Feature | Implementation |
|---------|---------------|
| **Prefix matching** | PostgreSQL `LIKE` with index |
| **Popular searches** | SearchLog aggregation |
| **Debouncing** | 300ms client-side debounce |

---

## 3. Recommendation Engine

### 3.1 Strategy Architecture

```mermaid
graph TB
    subgraph "Strategies"
        Collab["Collaborative Filtering<br/>User-User similarity"]
        ContentBased["Content-Based<br/>Embedding similarity"]
        Trending["Trending<br/>Popular by period"]
        Popular["Popular<br/>Most borrowed overall"]
    end

    subgraph "Hybrid Merger"
        Weights["Strategy Weights"]
        Merge["Score Combination"]
        PostFilter["Post-Filtering<br/>- Already read<br/>- Previously dismissed<br/>- Already recommended"]
        Rank["Final Ranking<br/>Top N"]
    end

    Collab --> Weights
    ContentBased --> Weights
    Trending --> Weights
    Popular --> Weights
    Weights --> Merge --> PostFilter --> Rank

    subgraph "Output"
        RecTable[("Recommendation<br/>user, book, score,<br/>strategy, reason")]
    end

    Rank --> RecTable
```

### 3.2 Collaborative Filtering

```mermaid
graph LR
    subgraph "Input"
        UserHistory["Target User<br/>Borrow History"]
        AllHistory["All Users<br/>Borrow History"]
    end

    subgraph "Processing"
        CoOccurrence["Co-occurrence Matrix<br/>Books borrowed together"]
        UserSimilarity["User Similarity<br/>Jaccard / Cosine"]
        SimilarUsers["Top Similar Users"]
        TheirBooks["Their Unread Books"]
    end

    UserHistory --> CoOccurrence
    AllHistory --> CoOccurrence
    CoOccurrence --> UserSimilarity
    UserSimilarity --> SimilarUsers
    SimilarUsers --> TheirBooks
```

### 3.3 Content-Based Filtering

```mermaid
graph LR
    subgraph "User Profile"
        Prefs["UserPreference<br/>preferred_categories<br/>preferred_authors"]
        PrefVector["preference_vector<br/>(384-dim embedding)"]
    end

    subgraph "Book Space"
        BookEmbeddings[("Book Embeddings<br/>pgvector")]
    end

    subgraph "Matching"
        Cosine["Cosine Similarity"]
        TopMatches["Top-K Similar Books"]
    end

    PrefVector --> Cosine
    BookEmbeddings --> Cosine
    Cosine --> TopMatches
```

### 3.4 Periodic Refresh Schedule

| Task | Schedule | Description |
|------|----------|-------------|
| `refresh_stale_recommendations` | Every 6 hours | Regenerate recommendations for users with stale data |
| `compute_book_embeddings` | Every 6 hours | Compute embeddings for new/updated books |
| `compute_trending_books` | Every 3 hours | Recompute trending scores |
| `weekly_model_training` | Weekly | Retrain recommendation models |

---

## 4. Predictive Analytics

### 4.1 Overdue Prediction

```mermaid
graph LR
    subgraph "Features"
        BorrowHistory["User borrow history<br/>past overdue rate"]
        BookPopularity["Book popularity<br/>demand level"]
        UserActivity["User activity<br/>last login, streak"]
        SeasonalPatterns["Seasonal patterns<br/>time of year"]
    end

    subgraph "Model"
        SKLearn["scikit-learn<br/>Classifier"]
    end

    subgraph "Output"
        Risk["Overdue Risk Score<br/>0.0 - 1.0"]
        Prediction["OverduePredictionType<br/>borrowId, riskScore,<br/>predictedReturnDate,<br/>riskFactors"]
    end

    BorrowHistory --> SKLearn
    BookPopularity --> SKLearn
    UserActivity --> SKLearn
    SeasonalPatterns --> SKLearn
    SKLearn --> Risk --> Prediction
```

### 4.2 Demand Forecasting

| Feature | Description |
|---------|-------------|
| **Input** | Historical borrow counts, trends, seasonal patterns |
| **Model** | Time series analysis with scikit-learn |
| **Output** | `DemandForecastType` — book, predicted demand, confidence, period |
| **Schedule** | Every 4 hours via Celery |

### 4.3 Churn Prediction

| Feature | Description |
|---------|-------------|
| **Input** | Last activity date, borrow frequency, reading time, engagement |
| **Model** | Classification model (logistic regression / random forest) |
| **Output** | `ChurnPredictionType` — user, churn probability, risk factors, last activity |
| **Schedule** | Weekly via Celery |

### 4.4 Collection Gap Analysis

| Feature | Description |
|---------|-------------|
| **Input** | Search queries with zero results, reservation queues, popular categories |
| **Analysis** | Identifies categories/topics with high demand but low supply |
| **Output** | `CollectionGapType` — category, severity, recommendation |
| **Schedule** | Part of weekly analysis |

---

## 5. LLM Integration

### 5.1 AI Provider Architecture

```mermaid
classDiagram
    class BaseAIProvider {
        <<abstract>>
        +String provider_name
        +generate_text(prompt, system_prompt, config) String
        +generate_embedding(text, config) List~float~
        +health_check(config) Boolean
    }

    class OllamaProvider {
        +generate_text() String
        +health_check() Boolean
        -_call_ollama_api(endpoint, payload) Dict
    }

    class OpenAIProvider {
        +generate_text() String
        +generate_embedding() List~float~
        +health_check() Boolean
    }

    class GeminiProvider {
        +generate_text() String
        +health_check() Boolean
    }

    class LocalTransformersProvider {
        +generate_embedding() List~float~
    }

    class AIProviderFactory {
        +get_provider(capability) BaseAIProvider
        -_load_config(capability) AIProviderConfig
    }

    class AIProviderConfig {
        +String provider
        +String capability
        +String model_name
        +String api_endpoint
        +String api_key
        +Boolean is_active
        +Integer max_tokens
        +Float temperature
    }

    BaseAIProvider <|-- OllamaProvider
    BaseAIProvider <|-- OpenAIProvider
    BaseAIProvider <|-- GeminiProvider
    BaseAIProvider <|-- LocalTransformersProvider
    AIProviderFactory --> BaseAIProvider : creates
    AIProviderFactory --> AIProviderConfig : reads
```

### 5.2 LLM-Powered Search

```mermaid
graph TB
    subgraph "Input"
        UserQuery["Natural Language Query<br/>'Recommend a good sci-fi book'"]
    end

    subgraph "Context Building"
        SearchEngine["Hybrid Search Engine<br/>(or DB fallback)"]
        TopBooks["Top 10 matching books"]
        ContextString["Context String<br/>Title, authors, categories,<br/>rating, availability, description"]
    end

    subgraph "LLM Processing"
        SystemPrompt["System Prompt<br/>'You are NovaLib AI,<br/>a helpful librarian assistant'"]
        UserPrompt["User prompt + book context"]
        Ollama["Ollama llama3.1<br/>POST /api/generate"]
    end

    subgraph "Output"
        Answer["Conversational Answer"]
        Sources["Referenced Books<br/>AISearchSourceType"]
    end

    UserQuery --> SearchEngine --> TopBooks --> ContextString
    SystemPrompt --> Ollama
    ContextString --> UserPrompt --> Ollama
    Ollama --> Answer
    TopBooks --> Sources
```

### 5.3 LLM Analytics

```mermaid
graph LR
    subgraph "Data Aggregation"
        BookStats["Book statistics"]
        BorrowStats["Circulation metrics"]
        UserStats["User engagement"]
        SearchStats["Search patterns"]
    end

    subgraph "LLM Processing"
        Prompt["Analytics prompt<br/>'Analyze this library data<br/>and provide insights'"]
        Ollama["Ollama llama3.1"]
    end

    subgraph "Output"
        Summary["Natural Language Summary<br/>Key insights, trends,<br/>recommendations for librarians"]
    end

    BookStats --> Prompt
    BorrowStats --> Prompt
    UserStats --> Prompt
    SearchStats --> Prompt
    Prompt --> Ollama --> Summary
```

---

## 6. Identity Verification Pipeline

### 6.1 OCR + Face Recognition

```mermaid
graph TB
    subgraph "Input"
        NICPhoto["NIC/ID Document Photo"]
        Selfie["User Selfie"]
    end

    subgraph "OCR Pipeline"
        Preprocess["Image Preprocessing<br/>Pillow"]
        Tesseract["pytesseract OCR"]
        Parse["NIC Parser<br/>Extract: name, NIC number,<br/>DOB, address"]
    end

    subgraph "Face Pipeline"
        FaceDetect["Face Detection<br/>face_recognition library"]
        FaceEncode["Face Encoding<br/>128-dim vector"]
        FaceCompare["Face Comparison<br/>Euclidean distance<br/>Tolerance: 0.6"]
    end

    subgraph "Decision"
        Confidence["Confidence Score"]
        AutoApprove["Auto-Approve<br/>(high confidence)"]
        ManualReview["Manual Review<br/>(low confidence)"]
    end

    NICPhoto --> Preprocess --> Tesseract --> Parse
    NICPhoto --> FaceDetect --> FaceEncode
    Selfie --> FaceDetect
    FaceEncode --> FaceCompare --> Confidence
    Parse --> Confidence
    Confidence -->|">= threshold"| AutoApprove
    Confidence -->|"< threshold"| ManualReview
```

---

## 7. Content Analysis

### 7.1 Auto-Tagging Pipeline

| Step | Description |
|------|-------------|
| 1. Text extraction | Combine title + description + author names |
| 2. NLP processing | NLTK tokenization, stemming, stop-word removal |
| 3. Topic modeling | TF-IDF feature extraction |
| 4. Category suggestion | Match against existing category embeddings |
| 5. Tag assignment | Auto-assign top matching categories |

### 7.2 Reading Level Assessment

| Level | Criteria |
|-------|---------|
| **Beginner** | Short sentences, simple vocabulary, < 200 pages |
| **Intermediate** | Moderate complexity, 200-400 pages |
| **Advanced** | Complex vocabulary, technical content, > 400 pages |

---

## 8. Reading Behavior Analytics

### 8.1 Components

```mermaid
graph TB
    subgraph "Analyzers"
        Speed["ReadingSpeedAnalyzer<br/>Pages per minute<br/>Words per minute"]
        Patterns["SessionPatternAnalyzer<br/>Preferred times<br/>Session duration"]
        Heatmap["EngagementHeatmapGenerator<br/>Activity by hour/day"]
        Completion["CompletionPredictor<br/>Days to finish<br/>Probability of completion"]
    end

    subgraph "Data Sources"
        Sessions[("ReadingSession")]
        DailyAct[("DailyActivity")]
        Library[("UserLibrary")]
    end

    subgraph "Outputs"
        SpeedType["ReadingSpeedType<br/>avgPagesPerMinute,<br/>avgWordsPerMinute,<br/>totalPagesRead"]
        PatternType["SessionPatternType<br/>preferredHours,<br/>avgSessionDuration,<br/>mostActiveDay"]
        HeatmapType["EngagementHeatmapType<br/>data matrix (7x24)"]
        PredType["CompletionPredictionType<br/>book, daysToComplete,<br/>probability, currentProgress"]
    end

    Sessions --> Speed --> SpeedType
    Sessions --> Patterns --> PatternType
    DailyAct --> Heatmap --> HeatmapType
    Library --> Completion --> PredType
    Sessions --> Completion
```

---

## 9. Model Training Pipeline

### 9.1 Training Workflow

```mermaid
graph TB
    Trigger["Trigger<br/>(Celery Beat weekly<br/>or Admin manual)"]

    subgraph "Training Pipeline"
        DataCollection["1. Data Collection<br/>Borrow history, reviews,<br/>sessions, preferences"]
        FeatureEngineering["2. Feature Engineering<br/>User-item matrix,<br/>interaction features"]
        ModelTraining["3. Model Training<br/>scikit-learn models"]
        Evaluation["4. Model Evaluation<br/>Precision@K, Recall@K,<br/>NDCG, MRR, Hit Rate"]
        Versioning["5. Model Versioning<br/>AIModelVersion record"]
    end

    subgraph "Evaluation Metrics"
        Precision["Precision@K"]
        Recall["Recall@K"]
        NDCG["NDCG<br/>Normalized Discounted<br/>Cumulative Gain"]
        MRR["MRR<br/>Mean Reciprocal Rank"]
        HitRate["Hit Rate"]
        Coverage["Catalog Coverage"]
        Diversity["Diversity"]
        Novelty["Novelty"]
    end

    Trigger --> DataCollection --> FeatureEngineering --> ModelTraining --> Evaluation --> Versioning

    Evaluation --> Precision
    Evaluation --> Recall
    Evaluation --> NDCG
    Evaluation --> MRR
    Evaluation --> HitRate
    Evaluation --> Coverage
    Evaluation --> Diversity
    Evaluation --> Novelty
```

### 9.2 Model Version Management

```mermaid
stateDiagram-v2
    [*] --> Training : Trigger pipeline
    Training --> Trained : Model trained
    Trained --> Evaluated : Run evaluation metrics
    Evaluated --> Versioned : Save AIModelVersion
    Versioned --> Inactive : Default state
    Inactive --> Active : Admin activates
    Active --> Inactive : New model activated
```

---

## 10. AI Configuration

### 10.1 AIProviderConfig Settings

| Field | Description |
|-------|-------------|
| `provider` | OLLAMA, OPENAI, GEMINI, LOCAL_TRANSFORMERS |
| `capability` | TEXT_GENERATION, EMBEDDING, CLASSIFICATION |
| `model_name` | e.g., "llama3.1", "gpt-4", "gemini-pro" |
| `api_endpoint` | e.g., "http://localhost:11434" |
| `api_key` | Encrypted API key (nullable for local) |
| `is_active` | Only one active per capability |
| `priority` | Selection priority when multiple available |
| `max_tokens` | Max response tokens (default 2048) |
| `temperature` | Creativity parameter (default 0.7) |

### 10.2 Embedding Configuration

```yaml
EMBEDDING_MODEL: "all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS: 384
EMBEDDING_BATCH_SIZE: 100
EMBEDDING_SCHEDULE: "Every 6 hours"
BOOK_TEXT_FORMAT: "{title} {description} by {authors}"
```

### 10.3 Search Configuration

```yaml
SEARCH_WEIGHTS:
  FULLTEXT: 0.45
  SEMANTIC: 0.35
  FUZZY: 0.20

SEARCH_FIELD_COSTS:
  searchBooks: 10
  semanticSearch: 15
  default: 1
```
