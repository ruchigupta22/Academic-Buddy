# 🎓 Academic Chatbot

### AI-Powered Learning Assistant for Smarter Exam Preparation

> **Academic Buddy** is a full-stack AI-powered learning platform that transforms lecture notes and previous-year question papers (PYQs) into an interactive academic assistant for **question answering, quiz generation, answer evaluation, exam analytics, and personalized revision planning**.

---

## 🚀 Overview

Students often have hundreds of pages of lecture notes and previous-year question papers, making it difficult to:

* Find relevant information quickly
* Identify important and frequently repeated topics
* Understand which topics carry higher marks
* Practice questions effectively
* Track learning performance
* Plan revision efficiently before examinations

**Academic Buddy** addresses these problems by combining **Retrieval-Augmented Generation (RAG), semantic search, LLMs, vector databases, structured analytics, and personalized recommendations** into a single platform.

### ✨ Key Capabilities

| Feature                   | Description                                                              |
| ------------------------- | ------------------------------------------------------------------------ |
| 📚 **Lecture Notes Chat** | Ask questions directly from uploaded lecture material using RAG          |
| 📝 **Quiz Generation**    | Generate MCQs, short-answer, and numerical questions                     |
| 🎯 **Answer Evaluation**  | Evaluate student answers using an LLM-as-a-Judge approach                |
| 🧠 **PYQ Intelligence**   | Extract and analyze structured information from previous-year papers     |
| 📊 **Exam Analytics**     | Identify topic frequency, marks distribution, and repeated topics        |
| 🗓️ **Revision Planner**  | Generate personalized study priorities and daily revision plans          |
| 📈 **User Analytics**     | Track quiz performance, accuracy, topics attempted, and learning history |
| 🔄 **LLM Failover**       | Automatically switch from Gemini to Groq when the primary model fails    |

---

## 🖥️ Application Preview

> Screenshots
### 🎓 Dashboard
<img width="1891" height="878" alt="image" src="https://github.com/user-attachments/assets/40bedf07-6b0f-4774-be8e-25cc3b53a8d2" />

### 💬 Lecture Notes Chat
<img width="1896" height="875" alt="image" src="https://github.com/user-attachments/assets/be2d0ae5-752c-4122-b2c8-696a7c8d24ad" />



### 📊 PYQ Analytics
<img width="1879" height="873" alt="image" src="https://github.com/user-attachments/assets/44fe503c-36ff-4e8d-9879-fb23357deb28" />


### 📝 Quiz Generation

<img width="1888" height="874" alt="image" src="https://github.com/user-attachments/assets/34f65855-7824-4d70-9472-00be539f8792" />


### 🗓️ Personalized Revision

<img width="1905" height="871" alt="image" src="https://github.com/user-attachments/assets/413cfcdd-360d-48c4-9e15-2a316dea0149" />


---

# 🏗️ System Architecture

Academic Buddy follows a **full-stack AI architecture** consisting of four major layers:

```text
┌──────────────────────────────────────────────────────┐
│                    React Frontend                    │
│       Context API • Axios • React Router             │
└──────────────────────────┬───────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│                   FastAPI Backend                     │
│        REST APIs • Pydantic • Async Requests         │
└───────────────┬───────────────────┬───────────────────┘
                │                   │
                ▼                   ▼
      ┌─────────────────┐   ┌─────────────────┐
      │   AI / RAG      │   │  Data Storage   │
      │                 │   │                 │
      │ Gemini          │   │ ChromaDB        │
      │ Groq            │   │ SQLite          │
      │ Embeddings      │   │                 │
      │ Semantic Search │   │                 │
      └────────┬────────┘   └────────┬────────┘
               │                     │
               └──────────┬──────────┘
                          ▼
                  Academic Response
```

## 🧩 Architecture Components

### Frontend

* React.js
* Context API for global state management
* Axios for API communication
* React Router for navigation

### Backend

* FastAPI
* RESTful APIs
* Pydantic validation
* Asynchronous request handling
* Modular router/service architecture

### Storage

* **ChromaDB** — vector storage and semantic retrieval
* **SQLite** — structured PYQ and user analytics

### AI Layer

* Gemini API
* Groq API as fallback
* Retrieval-Augmented Generation
* Vector embeddings
* Semantic similarity search
* Prompt engineering

---

# 📚 Feature 1 — Lecture Notes Chat

The Lecture Notes Chat is the core feature of Academic Buddy.

It uses a **Retrieval-Augmented Generation (RAG)** pipeline to answer questions using the student's uploaded academic material instead of relying solely on the LLM's internal knowledge.

## 🔄 RAG Pipeline

```text
                Upload Lecture Material
                         │
                         ▼
                PDF / PPT Processing
                         │
                         ▼
                  Text Extraction
                         │
                         ▼
                    Chunking
                         │
                         ▼
                Embedding Generation
                         │
                         ▼
                     ChromaDB
                         │
                         │
                  User asks a question
                         │
                         ▼
                  Query Embedding
                         │
                         ▼
                 Similarity Search
                         │
                         ▼
                Top-K Chunks Retrieved
                         │
                         ▼
                 Prompt Construction
                         │
                         ▼
                    Gemini
                         │
                    Failure?
                      /   \
                    No     Yes
                    │       │
                    ▼       ▼
                 Answer   Groq
                    │       │
                    └───┬───┘
                        ▼
               Answer + Citations
```

## 1️⃣ Upload Lecture Notes

Students can upload academic material such as:

* Lecture PDFs
* PPTs
* Course notes

The documents are processed before being stored in the vector database.

```text
PDF / PPT
   ↓
Text Extraction
   ↓
Document Chunking
   ↓
Embedding Generation
   ↓
ChromaDB
```

## 2️⃣ Document Chunking

Instead of sending an entire 100-page document to an LLM, the document is divided into smaller chunks.

| Parameter     |    Configuration |
| ------------- | ---------------: |
| Chunk Size    | ~1500 characters |
| Chunk Overlap |  ~200 characters |

Chunk overlap helps preserve contextual continuity between adjacent sections.

### Example

```text
Original Document
       │
       ├── Chunk 1
       ├── Chunk 2
       ├── Chunk 3
       ├── ...
       └── Chunk N
```

## 3️⃣ Embedding Generation

Each document chunk is converted into a dense vector representation.

For example:

```text
"Fick's First Law"
        ↓
[0.12, -0.45, 0.89, ...]
```

The resulting embeddings represent the semantic meaning of the text, allowing the system to retrieve conceptually relevant content rather than relying only on exact keyword matches.

## 4️⃣ Vector Storage

The generated embeddings are stored in **ChromaDB**.

Each stored chunk contains metadata such as:

* Text
* Page number
* Source file
* Chunk index
* Embedding vector

## 5️⃣ Question Answering

Suppose a student asks:

> **"What is Fick's First Law?"**

The system performs:

```text
User Query
    ↓
Query Embedding
    ↓
Semantic Similarity Search
    ↓
Top-K Relevant Chunks
    ↓
Context Construction
    ↓
LLM Prompt
    ↓
Gemini / Groq
    ↓
Final Answer
```

Only the most relevant retrieved content is provided as context to the model.

## 6️⃣ Source-Based Responses

The generated response includes source information such as:

* Source file
* Page number

This makes responses more traceable and helps reduce unsupported or hallucinated answers.

---

# 📝 Feature 2 — Quiz Generation

Academic Buddy can automatically generate quizzes from uploaded academic material.

## 🔄 Quiz Pipeline

```text
Selected Topic
      ↓
Retrieve Relevant Chunks
      ↓
Construct Context
      ↓
Prompt LLM
      ↓
Generate Questions
      ↓
Quiz Presented to Student
```

### Supported Question Types

* Multiple Choice Questions
* Short Answer Questions
* Numerical Questions

### Difficulty Levels

* 🟢 Easy
* 🟡 Medium
* 🔴 Hard

Students can also generate multiple questions for a selected topic.

---

# 🎯 Feature 3 — Answer Evaluation

Academic Buddy implements an **LLM-as-a-Judge** architecture for evaluating student answers.

## Evaluation Process

The evaluator receives:

```text
Question
   +
Model Answer
   +
Student Answer
   +
Maximum Marks
```

The LLM then:

1. Compares the student's answer with the expected answer
2. Checks conceptual correctness
3. Identifies missing concepts or assumptions
4. Assigns marks
5. Generates feedback

### Example

**Input**

```text
Question:
Explain Fick's First Law.

Maximum Marks:
5

Student Answer:
...
```

**Output**

```json
{
  "score": 4,
  "feedback": "Good explanation but missing assumptions."
}
```

This provides students with immediate feedback rather than only a numerical score.

---

# 🧠 Feature 4 — PYQ Intelligence Engine

The **PYQ Intelligence Engine** converts unstructured previous-year examination papers into structured exam intelligence.

This allows the system to identify what topics are repeatedly asked and how marks are distributed across a course.

## 📄 Upload PYQs

Students can upload:

* Midsem papers
* Endsem papers
* Quiz papers
* Previous examination papers

## 🔄 Question Processing Pipeline

```text
PYQ Paper
    ↓
Question Extraction
    ↓
LLM-based Metadata Extraction
    ↓
Structured Question Records
    ↓
SQLite
    ↓
Exam Analytics
```

## 🏷️ Extracted Metadata

For every question, the system extracts structured information such as:

| Field         | Example          |
| ------------- | ---------------- |
| Topic         | Diffusion        |
| Subtopic      | Fick's First Law |
| Marks         | 5                |
| Question Type | Theory           |
| Difficulty    | Easy             |
| Year          | 2022             |

### Example

**Original Question**

```text
Explain Fick's First Law. [5]
```

**Structured Record**

```text
Topic       → Diffusion
Subtopic    → Fick's First Law
Marks       → 5
Type        → Theory
Difficulty  → Easy
Year        → 2022
```

---

# 📊 PYQ Analytics

Once questions from multiple papers are stored, Academic Buddy can generate meaningful exam-level analytics.

### Analytics Generated

* Topic frequency
* Marks distribution
* Average marks per topic
* Frequently repeated topics
* High-weightage topics
* Exam trends
* Emerging topics

### Example

| Topic          | Frequency |
| -------------- | --------: |
| Diffusion      |        15 |
| Phase Diagram  |        12 |
| Heat Treatment |         9 |

This transforms a collection of PDFs into a structured database of exam patterns.

---

# 🗓️ Feature 5 — Personalized Revision Planner

Academic Buddy combines academic content, exam trends, and student progress to generate personalized revision recommendations.

The planner considers:

```text
Uploaded Lecture Notes
        +
PYQ Statistics
        +
Student Performance
        +
Days Remaining
        ↓
Priority Calculation
        ↓
Personalized Revision Plan
```

## 📌 Priority Factors

Topics can be prioritized based on:

* High PYQ frequency
* High marks weightage
* Weak student performance
* Exam relevance

### Example Plan

```text
Day 1 → Diffusion
Day 2 → Phase Diagram
Day 3 → Heat Treatment
Day 4 → Revision + Practice
```

---

# 📈 Feature 6 — User Analytics

Academic Buddy tracks learning activity to provide personalized recommendations.

### Tracked Data

#### Quiz Performance

* Quiz history
* Scores
* Accuracy
* Topics attempted

#### Learning Activity

* Chat history
* Questions asked
* Topics covered

### Recommendations

The collected information can be used to identify:

```text
Weak Areas
     ↓
Topics to Revise
     ↓
Recommended Practice
     ↓
Improved Preparation
```

---

# ⚙️ Engineering Challenges & Solutions

## 1. Reducing LLM Hallucinations

A major challenge with LLM-based academic systems is generating answers that are not grounded in the student's study material.

### Solution

Academic Buddy uses:

* Retrieval-Augmented Generation
* Semantic retrieval
* Source citations
* Context-aware prompting
* Strict response instructions

```text
Student Question
       ↓
Retrieve Relevant Material
       ↓
Provide Retrieved Context
       ↓
Generate Grounded Answer
       ↓
Attach Source Citation
```

This reduces dependence on the model's parametric knowledge.

---

## 2. LLM Quota & Availability Failures

External LLM APIs can encounter quota limits, temporary failures, or availability issues.

To improve reliability, Academic Buddy implements a fallback strategy:

```text
                User Request
                     │
                     ▼
                Gemini API
                     │
             ┌───────┴───────┐
             │               │
          Success          Failure
             │               │
             ▼               ▼
          Response         Groq API
                             │
                             ▼
                          Response
```

This provides an alternative model path when the primary provider cannot process the request.

---

## 3. Hybrid Storage Architecture

Different parts of the application require different types of storage.

### ChromaDB

Used for:

* Embedding storage
* Semantic similarity search
* Retrieval of relevant document chunks

### SQLite

Used for:

* PYQ metadata
* Question records
* Marks
* Years
* Topic analytics
* User performance data

| Storage  | Primary Purpose           |
| -------- | ------------------------- |
| ChromaDB | Semantic/vector retrieval |
| SQLite   | Structured analytics      |

This separation allows each database to handle the workload it is designed for.

---

# 📈 Processing Scale

The system is designed to process:

* Lecture PDFs
* PPTs
* PYQ papers
* Multiple questions across examination papers

### Example: 100-Page Lecture PDF

```text
100-page PDF
      ↓
Text Extraction
      ↓
~300 Chunks
      ↓
~300 Embeddings
      ↓
ChromaDB
```

The chunk-based architecture allows large academic documents to be processed without passing the entire document to the LLM for every query.

---

# 🔌 REST API

The backend exposes **15+ REST APIs** covering the major application workflows.

### API Categories

| Category           | Operations                            |
| ------------------ | ------------------------------------- |
| 📚 Lecture         | Upload, retrieval, academic chat      |
| 📝 Quiz            | Generate quiz, evaluate answers       |
| 📄 PYQ             | Upload and process question papers    |
| 📊 Analytics       | Topic and exam analytics              |
| 🗓️ Revision       | Generate revision plans               |
| 👤 Profile         | User profile management               |
| 🎯 Recommendations | Personalized academic recommendations |

### Major Endpoints

```text
/api/v1/upload/lecture
/api/v1/chat

/api/v1/pyq/upload
/api/v1/pyq/ask
/api/v1/pyq/report
/api/v1/pyq/analytics

/api/v1/quiz/generate
/api/v1/quiz/check

/api/v1/revision/...
```

The API layer separates frontend interaction from business logic and AI processing.

---

# 🛠️ Technology Stack

## Frontend

| Technology   | Purpose                 |
| ------------ | ----------------------- |
| React.js     | User interface          |
| Context API  | Global state management |
| Axios        | API communication       |
| React Router | Client-side navigation  |

## Backend

| Technology       | Purpose                       |
| ---------------- | ----------------------------- |
| FastAPI          | Backend framework             |
| Pydantic         | Data validation               |
| REST APIs        | Client-server communication   |
| Async Processing | Non-blocking request handling |

## Databases

| Technology | Purpose                                   |
| ---------- | ----------------------------------------- |
| ChromaDB   | Vector database and semantic retrieval    |
| SQLite     | Structured application and analytics data |

## AI / ML

| Technology      | Purpose                              |
| --------------- | ------------------------------------ |
| RAG             | Grounded question answering          |
| Embeddings      | Semantic representation of documents |
| Semantic Search | Relevant context retrieval           |
| Gemini API      | Primary LLM                          |
| Groq API        | Fallback LLM                         |
| LLM-as-a-Judge  | Answer evaluation                    |

## Other

* PDF/PPT parsing
* Prompt engineering
* Metadata extraction
* REST API design
* Structured data processing

---

# 📂 Project Structure

> Update this section to exactly match your repository structure if your folders differ.

```text
Academic-Buddy/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── context/
│   │   └── ...
│   ├── package.json
│   └── ...
│
├── backend/
│   ├── routers/
│   ├── services/
│   ├── models/
│   ├── schemas/
│   ├── ...
│   ├── requirements.txt
│   └── ...
│
├── docs/
│   ├── architecture.png
│   ├── lecture-chat.png
│   ├── quiz.png
│   ├── pyq-analytics.png
│   └── revision.png
│
└── README.md
```

---

# 🚀 Getting Started

## Prerequisites

Make sure the following are installed:

* Python 3.x
* Node.js
* npm
* Gemini API key
* Groq API key

---

## 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd Academic-Buddy
```

---

## 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file inside the backend directory:

```env
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
```

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

The backend will be available at:

```text
http://127.0.0.1:8000
```

FastAPI's interactive API documentation can be accessed through:

```text
http://127.0.0.1:8000/docs
```

---

## 3. Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend will then be available at the local development address provided by Vite.

---

# 🔐 Environment Variables

The application requires API credentials for the LLM providers.

```env
GEMINI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
```

> **Never commit API keys or `.env` files to GitHub.**

Add the following to `.gitignore`:

```text
.env
__pycache__/
node_modules/
*.db
```

---

# 🔮 Future Improvements

Potential extensions to Academic Buddy include:

* [ ] Multilingual academic support
* [ ] Improved personalized recommendation models
* [ ] Automated exam timetable integration
* [ ] More advanced learning analytics
* [ ] Streaming LLM responses
* [ ] Improved question difficulty classification
* [ ] More advanced adaptive learning strategies
* [ ] Deployment with scalable cloud infrastructure

---

# 💡 Why Academic Buddy?

Academic Buddy is designed around a simple idea:

```text
              Academic Material
                     ↓
              ┌─────────────┐
              │ Academic    │
              │   Buddy     │
              └──────┬──────┘
                     ↓
       ┌─────────────┼─────────────┐
       ↓             ↓             ↓
    Understand     Practice      Analyze
       ↓             ↓             ↓
      RAG          Quizzes        PYQs
       │             │             │
       └─────────────┼─────────────┘
                     ↓
              Personalized
                 Revision
```

Instead of treating lecture notes, PYQs, quizzes, and student performance as separate resources, the system connects them into a single learning workflow.

---

# 📌 Key Highlights

* 🚀 Full-stack **React + FastAPI** application
* 🧠 **RAG-powered** academic question answering
* 🔎 Semantic search using **vector embeddings**
* 📚 Lecture PDF/PPT processing
* 📝 AI-generated quizzes
* 🎯 **LLM-as-a-Judge** answer evaluation
* 🧠 Automated **PYQ metadata extraction**
* 📊 Exam trend and topic analytics
* 🗓️ Personalized revision planning
* 🔄 Gemini → Groq LLM failover
* 🗄️ Hybrid **ChromaDB + SQLite** architecture
* 🔌 **15+ REST APIs**

---

# 👩‍💻 Author

### Khushi Srivastava

**IIT Kharagpur**

Interested in:

`Software Engineering` • `Machine Learning` • `Generative AI` • `Data Science`

---

## ⭐ If you found this project interesting

Feel free to explore the repository, try the application, or use the architecture as inspiration for building AI-powered educational systems.
