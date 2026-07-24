# AtlasAI

AtlasAI is an AI-powered market intelligence and company discovery platform designed to help users explore companies, industry sectors, business problems, and recent news through a Retrieval-Augmented Generation (RAG) interface.

The platform combines structured relational data in PostgreSQL with semantic retrieval using ChromaDB and Gemini-powered answer generation. It also includes automated news ingestion and a human-in-the-loop Company Discovery workflow for safely expanding the trusted knowledge base.

---

## Features

### AI-Powered RAG Search

AtlasAI provides a conversational interface for querying the platform's trusted knowledge base.

The RAG pipeline:

1. Accepts a natural-language question.
2. Generates semantic embeddings for the query.
3. Retrieves relevant documents from ChromaDB.
4. Builds grounded context from the retrieved documents.
5. Sends the context and question to Gemini.
6. Generates an answer based on the available AtlasAI context.
7. Returns supporting sources and metadata.

Example questions:

```text
What is Amazon Web Services?

What AI solutions does AWS provide?

Recommend AI companies for the Food and Beverage industry.

What recent news is available about Amazon Web Services?

Compare FOSS Analytics and Pixelfield GmbH.
```

When the available knowledge base does not contain sufficient information to answer a question, AtlasAI is designed to return an insufficient-information response instead of intentionally fabricating unsupported information.

---

## Company Intelligence

AtlasAI stores structured company information including fields such as:

- Company name
- Country
- Website
- Company type
- AI category
- Funding
- Estimated revenue
- Maturity
- Deployment evidence
- Associated sectors

Users can browse company information through the Company Directory and query the same trusted information through Ask AI.

---

## Sector Intelligence

AtlasAI supports sector-based company exploration and AI vendor recommendations.

Example queries:

```text
Recommend AI companies for the Food and Beverage industry.

Which AI companies would you recommend for food manufacturing?

Recommend AI vendors for Bakery and Confectionery Manufacturing.
```

The RAG pipeline retrieves relevant sector and company information before generating recommendations.

---

## News Intelligence

AtlasAI integrates with NewsAPI to collect recent company-related news.

The news pipeline:

```text
NewsAPI
   ↓
Company-Focused Article Search
   ↓
Relevance Filtering
   ↓
Duplicate Detection
   ↓
PostgreSQL
   ↓
ChromaDB
   ↓
Ask AI
```

The synchronization pipeline filters irrelevant and low-quality content before storing trusted news records.

News articles are persisted in PostgreSQL and indexed into ChromaDB, allowing users to ask questions such as:

```text
What recent news is available about Amazon Web Services?

What are the latest developments related to AWS?

What recent news is available about Microsoft?
```

News can be refreshed and reindexed through the backend API.

---

## Company Discovery (Admin Only)

AtlasAI includes an Admin-only, human-in-the-loop Company Discovery system for identifying potential new AI and technology companies via a dedicated discovery provider without using news articles as company records.

The workflow is:

```text
Admin Discovery Search
       ↓
Tavily Organization Search API
       ↓
Normalized Company Records & Metadata
       ↓
Verification
       ↓
Duplicate Detection
       ↓
Confidence Scoring
       ↓
Pending Admin Review
      ↙             ↘
  Reject           Approve
                       ↓
               Trusted PostgreSQL Data
                       ↓
            Incremental ChromaDB Indexing
                       ↓
                  Available to RAG
```

### Discovery Safety

External candidates are never automatically added to the trusted knowledge base.

Before entering the trusted AtlasAI data, candidates go through:

- Deterministic company-name extraction
- AI and technology relevance checks
- Evidence URL validation
- Source-domain extraction
- Duplicate detection
- Low-quality content filtering
- Confidence scoring
- Human approval or rejection

Only approved candidates are inserted into the trusted company database and indexed into ChromaDB.

This prevents unverified external information from directly contaminating the trusted RAG knowledge base.

### Incremental Knowledge Base Updates

When a discovered company is approved, AtlasAI indexes only the newly approved company into ChromaDB.

A complete vector database rebuild is not required.

The workflow was validated end-to-end:

```text
Discovery
→ Candidate Extraction
→ Pending Review
→ Human Approval
→ PostgreSQL
→ Incremental ChromaDB Indexing
→ Available to RAG
```

A newly approved Discovery candidate was successfully retrieved by the RAG retrieval pipeline after incremental indexing, validating dynamic knowledge base updates without a complete rebuild.

---

## Discovery Interface

The frontend includes a dedicated Company Discovery interface.

The interface supports:

- External company discovery searches
- Discovery summary metrics
- Candidate review
- Confidence score display
- Confidence reasons
- Evidence inspection
- Pending candidate management
- Human approval
- Human rejection with rejection reason
- Incremental indexing status
- Provider extraction diagnostics

The frontend acts as the human review interface.

Verification, confidence scoring, duplicate detection, trusted database insertion, and ChromaDB indexing remain backend responsibilities.

---

## Architecture

AtlasAI follows a layered backend architecture.

```text
Frontend
   │
   ▼
FastAPI REST API
   │
   ├── API Endpoints
   │
   ├── Services
   │
   ├── Repositories
   │
   ├── SQLAlchemy Models
   │
   └── AI / RAG Layer
          │
          ├── Document Ingestion
          ├── Chunking
          ├── Embeddings
          ├── ChromaDB Vector Store
          ├── Semantic Retrieval
          ├── Prompt Construction
          └── Gemini Generation

Structured Data
   │
   ▼
PostgreSQL
   │
   ▼
Document Transformation
   │
   ▼
ChromaDB
   │
   ▼
Semantic Retrieval
   │
   ▼
Gemini
   │
   ▼
Grounded Answer + Sources
```

---

## Technology Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- LangChain
- ChromaDB
- Gemini API
- NewsAPI

### Frontend

- React
- TypeScript
- Vite

### AI / RAG

- Retrieval-Augmented Generation
- Semantic embeddings
- ChromaDB vector search
- Metadata-aware retrieval
- Gemini LLM
- Incremental vector indexing

---

## Project Structure

```text
AtlasAI/
│
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   │   ├── chat.py
│   │   │   ├── chunking.py
│   │   │   ├── embeddings.py
│   │   │   ├── ingest.py
│   │   │   ├── prompts.py
│   │   │   ├── retriever.py
│   │   │   └── vector_store.py
│   │   │
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── endpoints/
│   │   │
│   │   ├── clients/
│   │   ├── config/
│   │   ├── evaluation/
│   │   │   ├── __init__.py
│   │   │   └── rag.py
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   │
│   ├── migrations/
│   ├── scripts/
│   │   └── evaluate_rag.py
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── routes/
│   │   ├── services/
│   │   └── types/
│   │
│   └── package.json
│
└── README.md
```

---

## Data Flow

### Trusted Dataset Ingestion

```text
Source CSV Data
      ↓
Validation / Transformation
      ↓
PostgreSQL
      ↓
Document Generation
      ↓
Chunking
      ↓
Embeddings
      ↓
ChromaDB
```

PostgreSQL acts as the structured source of truth, while ChromaDB provides semantic retrieval for the RAG pipeline.

---

## RAG Query Flow

```text
User Question
      ↓
SemanticRetrieverService
      ↓
ChromaDB Similarity Search
      ↓
Relevant Chunks
      ↓
Context Construction
      ↓
Gemini
      ↓
Grounded Answer
      ↓
Sources + Metadata
```

Retrieved documents remain available in the API response for transparency, source attribution, and debugging.

---

## RAG Evaluation

AtlasAI includes a retrieval evaluation harness for systematically testing the quality of the RAG retrieval pipeline.

The evaluation suite covers:

- Company retrieval
- News retrieval
- Sector-based recommendations
- Multi-entity retrieval
- Retrieval of newly approved Discovery companies
- Out-of-scope query cases

### Retrieval Evaluation Results

The retrieval-only evaluation was executed against the AtlasAI knowledge base using the production semantic retrieval pipeline.

| Metric | Result |
| --- | --- |
| Evaluation Cases | 17 |
| Passed | 17 |
| Retrieval Test Pass Rate | 100% |
| Hit@K | 100% |
| Source Type Accuracy | 100% |
| Entity Coverage | 100% |

### Results by Category

| Category | Result |
| --- | --- |
| Company Retrieval | 4/4 |
| News Retrieval | 3/3 |
| Sector Recommendations | 3/3 |
| Multi-Entity Retrieval | 3/3 |
| Discovery Knowledge Base Update | 1/1 |

The evaluation verified that relevant companies, news articles, sectors, and multiple entities could be found within the configured top-K retrieval results.

It also verified that a newly approved Company Discovery candidate could be retrieved from the knowledge base after incremental ChromaDB indexing, demonstrating the workflow:

```text
External Discovery
→ Human Approval
→ Trusted PostgreSQL Data
→ Incremental ChromaDB Indexing
→ RAG Retrieval
```

### Evaluation Scope

The reported 100% result represents the current **retrieval-only evaluation criteria** and should not be interpreted as 100% overall RAG or LLM answer accuracy.

Retrieval evaluation measures whether expected entities and source types are present in the retrieved context.

The following generation-level behaviors require separate answer-level evaluation:

- Final answer groundedness
- Citation correctness
- Citation-to-source alignment
- Hallucination detection
- Honest insufficient-information responses
- Out-of-scope refusal behavior

Out-of-scope queries are included in the retrieval evaluation suite for visibility, but final `"I don't know"` behavior must be validated at the generation layer.

### Running the Evaluation

From the backend directory:

```bash
python scripts/evaluate_rag.py
```

The evaluation runs against the existing AtlasAI ChromaDB knowledge base and uses the same semantic retrieval pipeline as the application.

---

## Backend Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd AtlasAI/backend
```

### 2. Create a Virtual Environment

Windows:

```bash
py -3.10 -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file using the project's `.env.example` as a reference.

Configure the required environment variables, including:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/atlasai

SECRET_KEY=your_secret_key

GOOGLE_API_KEY=your_google_api_key

NEWS_API_KEY=your_newsapi_key

TAVILY_API_KEY=your_tavily_api_key

INITIAL_ADMIN_EMAIL=admin@yourdomain.com
INITIAL_ADMIN_PASSWORD=your_secure_admin_password
INITIAL_ADMIN_USERNAME=admin
```

Additional configuration values should be copied from `.env.example` where required.

Never commit API keys, database passwords, or production credentials.

### 5. Configure PostgreSQL

Create the AtlasAI PostgreSQL database and ensure the database service is running.

Apply database migrations:

```bash
alembic upgrade head
```

### 6. Start the Backend

From the `backend` directory:

```bash
uvicorn app.main:app --reload
```

The API will normally be available at:

```text
http://127.0.0.1:8000
```

Interactive FastAPI Swagger documentation is available at:

```text
http://127.0.0.1:8000/docs
```

---

## Frontend Setup

Open another terminal:

```bash
cd AtlasAI/frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend will normally be available at:

```text
http://127.0.0.1:5173
```

Create a production build with:

```bash
npm run build
```

---

## Main API Capabilities

AtlasAI exposes APIs for:

- Company directory access
- Sector information
- Business problem information
- News retrieval
- News synchronization
- News reindexing
- RAG-based Ask AI
- External company discovery
- Pending discovery review
- Candidate approval
- Candidate rejection

Interactive API documentation is available through FastAPI Swagger at `/docs`.

---

## Company Discovery API

### Search for Candidates

```text
POST /api/v1/discovery/search
```

Example request:

```json
{
  "query": "AI startup food technology",
  "sector": "Food and Beverage",
  "country": "Germany",
  "limit": 10
}
```

The response includes candidate counts, created candidates, skipped candidates, provider extraction metrics, and optional extraction diagnostics.

### List Pending Candidates

```text
GET /api/v1/discovery/pending
```

### View Candidate

```text
GET /api/v1/discovery/{candidate_id}
```

### Approve Candidate

```text
POST /api/v1/discovery/{candidate_id}/approve
```

Approval inserts the company into trusted PostgreSQL data and incrementally indexes the company into ChromaDB.

### Reject Candidate

```text
POST /api/v1/discovery/{candidate_id}/reject
```

Example request:

```json
{
  "rejection_reason": "False positive: extracted entity is not a company."
}
```

Rejected candidates are never added to the trusted knowledge base.

---

## News API

### List Recent News

```text
GET /api/v1/news
```

### Get Company News

```text
GET /api/v1/news/company/{company_id}
```

### Refresh News

```text
POST /api/v1/news/refresh
```

### Reindex Persisted News

```text
POST /api/v1/news/reindex
```

The news reindex workflow can be used to rebuild persisted news vectors and remove stale news retrieval results.

---

## Testing

Backend unit tests can be run with:

```bash
python -m unittest discover -s tests/unit
```

During development, the Company Discovery unit test suite covered scenarios including:

- Candidate extraction
- False-positive filtering
- Generic headline rejection
- AI relevance validation
- Duplicate detection
- Confidence scoring
- Human approval
- Human rejection
- Incremental indexing
- Provider diagnostics
- Description-assisted extraction
- Generic publication/newsletter filtering

The latest validated Company Discovery development checkpoint completed 32 unit tests successfully.

The RAG retrieval evaluation can be run separately with:

```bash
python scripts/evaluate_rag.py
```

The frontend production build can be verified with:

```bash
npm run build
```

---

## Design Decisions

### PostgreSQL as the Source of Truth

Structured AtlasAI entities are stored in PostgreSQL.

ChromaDB is treated as the semantic retrieval layer rather than the primary source of truth.

This separation allows structured data to remain consistent while enabling semantic search over the same trusted information.

### Human-in-the-Loop Discovery

Externally discovered companies are never automatically promoted into trusted data.

A human reviewer must approve each candidate before it becomes part of the trusted knowledge base.

This protects the RAG pipeline from automatically ingesting false-positive or unverified external entities.

### Incremental Indexing

Knowledge base updates do not require rebuilding the entire vector database.

Newly approved companies can be indexed individually, allowing the RAG knowledge base to evolve incrementally.

### Deterministic Discovery Extraction

Company extraction and initial verification use deterministic rules rather than an LLM.

The system intentionally prefers skipping ambiguous entities instead of guessing company identities.

### Grounded RAG Responses

AtlasAI uses retrieved knowledge base documents as context for answer generation and exposes supporting sources alongside generated responses.

When sufficient information is unavailable, the system is designed to acknowledge the limitation rather than intentionally generate unsupported information.

### Retrieval Evaluation

The evaluation harness tests the production retrieval pipeline rather than maintaining a separate evaluation-specific retrieval implementation.

This ensures evaluation results reflect the same semantic retrieval behavior used by AtlasAI.

---

## Known Limitations

- Company Discovery depends on the quality and coverage of external NewsAPI results.
- Deterministic company extraction may intentionally skip ambiguous company mentions rather than guessing.
- Discovery may occasionally produce false-positive candidates, which are protected from entering trusted data by the human approval workflow.
- External candidate metadata requires human verification before approval.
- Semantic retrieval quality depends on the content available in the trusted AtlasAI knowledge base.
- News coverage depends on the availability and relevance of NewsAPI articles.
- Retrieval-only evaluation does not measure final LLM answer accuracy or hallucination rate.
- Out-of-scope `"I don't know"` behavior requires answer-level evaluation.
- Full production authentication and authorization are outside the current assignment scope.

---

## Future Improvements

Potential future improvements include:

- Answer-level RAG evaluation
- Automated groundedness evaluation
- Citation correctness evaluation
- Hybrid semantic and keyword search
- Retrieval re-ranking
- Retrieval confidence scoring
- More advanced metadata filtering
- Expanded company discovery providers
- Improved official company website verification
- Scheduled background news synchronization
- More advanced RAG observability and tracing
- Authentication and role-based access control

---

## Assignment Focus

AtlasAI was developed with emphasis on:

- AI and RAG capabilities
- Grounded semantic retrieval
- Structured data engineering
- Company intelligence
- Sector-based recommendations
- Company Discovery
- Human-in-the-loop verification
- News automation
- Incremental knowledge base updates
- Backend engineering
- Transparent source attribution
- Retrieval evaluation
- Clean architecture

The project demonstrates a complete workflow where structured data, external intelligence, semantic retrieval, human verification, and generative AI work together within a controlled knowledge system.

---

## Evaluation Summary

AtlasAI was evaluated against the following core retrieval capabilities:

```text
✓ Company Retrieval
✓ News Retrieval
✓ Sector-Based Recommendations
✓ Multi-Entity Retrieval
✓ Source-Type Matching
✓ Entity Coverage
✓ Newly Approved Discovery Company Retrieval
```

The current retrieval-only evaluation achieved:

```text
17 / 17 retrieval tests passed

Retrieval Test Pass Rate: 100%
Hit@K:                   100%
Source Type Accuracy:    100%
Entity Coverage:         100%
```

These results represent retrieval performance under the current evaluation criteria and do not claim 100% end-to-end LLM answer accuracy.

---

## License

This project was developed as part of a technical assignment and evaluation process.