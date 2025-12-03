SUNY AI Advising Demo - Feature Build Plan (Updated) 

Owner : Manish Sharma 

Date : 2nd Dec, 2025 

1. STUDENT PERSONA 

Feature 1: Academic Guidance Chat (RAG-Powered) 

Covers: Section A - Academic Guidance 

What it does: Students ask questions about courses, prerequisites, graduation requirements, major/minor requirements, and academic planning. The AI answers using actual SUNY course catalogs and degree requirement documents, providing citations for every response. 

Specific capabilities: 

Ask about course options for upcoming semester 

Check prerequisites and co-requisites 

Understand graduation requirements 

Get a suggested academic plan for the next few semesters 

Explore majors and minors and their requirements 

Understand which courses fulfill multiple requirements 

How it's built: 

Frontend: React/Tailwind or Streamlit [Mock] 

LLM: Google Gemini for generating responses - GCP 

Vector Database: Pinecone (cloud-hosted) or ChromaDB (open-source, local) 

Document Processing: LangChain / LlamaIndex / AWS 

 

 

 

Feature 2: Productivity and Learning Support Tools 

Covers: Section F - Productivity and Learning Support (Gemini strengths) 

What it does: Students upload course materials (notes, syllabi, readings) and get AI-generated study aids including flashcards, study schedules, content summaries, concept explanations, and practice quizzes. This demonstrates Gemini's teaching and content generation capabilities. 

Specific capabilities: 

Generate flashcards based on course material 

Create study schedules based on upcoming exams 

Summarize uploaded course notes 

Get help understanding difficult topics or assignments 

Generate practice quizzes or test questions on the fly 

 

--------- 

 

2. ADVISOR PERSONA 

Feature 1: Escalation Queue Dashboard 

Covers: Advisor Use Cases - Section A (Summary and Context) + Section B (Escalation Handling) 

What it does: Displays all student questions that were escalated to human advisors. Shows full conversation history, student profile snapshot (major, GPA, completed courses, risk indicators), and allows advisors to mark questions as "resolved" or "in progress". Advisors can leave notes for follow-up and see which students repeatedly need help. 

 

 

Specific capabilities: 

Advisor receives summary of student's AI interactions 

View flagged or escalated questions 

Student snapshot: performance, history, risk indicators 

See which queries need human intervention 

Reply with context and next steps 

Leave notes for future follow-up 

How it's built: 

Frontend: React + shadcn/ui components (data tables, cards, status badges, tabs) 

Backend: Next.js API routes with SQLite for storing escalations and advisor notes 

Data Storage: SQLite database or in-memory JSON array for demo purposes 

Status Management: Simple state updates when advisor marks items resolved or in-progress 

Risk Indicators: Mock data showing student GPA, course load, previous escalations 

 

Feature 2: AI-Generated Advisor Assist Tools 

Covers: Advisor Use Cases - Section C (Advisor Assist Tools) 

What it does: Advisor selects an escalated student question and uses AI to generate helpful artifacts: outreach emails, meeting invitations, advising session summaries, academic recovery plans, or personalized guidance notes. All generated content is based on the conversation context, student profile, and SUNY policies. 

Specific capabilities: 

Generate outreach emails or meeting invitations 

Create advising session summaries : audio samples maybe [.mp4 -> MoM ] 

Prepare academic recovery plans 

Draft personalized guidance notes based on policies 

 

How it's built: 

Frontend: React buttons/dropdown menu to select artifact type, modal to display and edit generated content 

LLM: Google Gemini with specific prompts for professional writing (emails, plans, summaries) 

Content Types: Different Gemini prompts for emails (empathetic, action-oriented), recovery plans (structured, goal-based), session summaries (concise, factual) 

 

------------ 

3. ADMINISTRATOR PERSONA 

Feature 1: Analytics Dashboard [ plotly  / matplotlib / seaborn ] 

Covers: Administrator Use Cases - Section B (Analytics and Reporting) 

What it does: Displays key metrics about system usage and student engagement: total questions asked, escalation rate, most asked topics, peak usage hours, student satisfaction ratings, and patterns indicating at-risk cohorts. Provides visual charts and trends to help administrators make data-driven decisions about advising resources. 

Specific capabilities: 

Dashboard for system usage and engagement 

Accuracy monitoring: common flagged responses 

Completion and retention patterns signaling at-risk cohorts 

Identification of students who repeatedly seek help (from Advisor Insights section) 

Most common areas of confusion 

Trends in student questions 

How it's built: 

Frontend: React + Tremor (dashboard UI library) or Recharts for visualizations or Plotly or PowerBI or Tableau  

Charts: Bar chart (top topics), line chart (questions over time), pie chart (escalation vs. resolved), heat map (peak hours), risk cohort indicators 

Data Storage: Mock data in JSON format or SQLite with sample queries and timestamps 

UI Library: Tremor provides pre-built dashboard components (KPI cards, charts, tables, metrics) 

Metrics Tracked: Question count, escalation percentage, common topics, satisfaction scores, response accuracy, at-risk student flags 

Risk Detection: Mock algorithm identifying students with multiple escalations, low engagement, or concerning question patterns 

 

Feature 2: Knowledge Base Document Upload & Management 

Covers: Administrator Use Cases - Section A (Content Management) 

What it does: Administrators upload PDF or TXT files (course catalogs, FAFSA guides, transfer policies, academic rules, program changes). The system automatically processes these documents, chunks them, embeds them, and adds them to the vector database so students can immediately ask questions about the new content. Shows list of currently indexed documents with upload date and version control. 

Specific capabilities: 

Update knowledge base for curriculum changes 

Upload new academic rules or program changes 

Manage policy documents that the AI draws from 

View which documents are currently active 

Delete or replace outdated documents 

How it's built: 

Frontend: React Dropzone for drag-and-drop file upload, table displaying uploaded documents with metadata 

Backend Processing: Next.js API route receives files and processes them 

Document Parsing: pdf-parse library extracts text from PDFs, native fs module for TXT files 

Document Processing: LangChain.js chunks documents into 500-token segments with overlap 

Vector Database: Pinecone or ChromaDB stores embeddings of new documents with metadata (filename, upload date, category) 

Version Control: Track document versions and allow replacement of outdated policies 

 

Complete Tech Stack Summary 

Component 

Technology 

Frontend Framework 

Next.js 14 (React App Router) 

UI Styling 

Tailwind CSS 

UI Components 

shadcn/ui 

LLM 

Google Gemini  

Vector Database 

Pinecone (cloud) or ChromaDB (open-source) 

Document Processing 

LangChain / LlamaIndex 

Charts/Visualization 

Tremor or Recharts or Tableau or Plotly 

File Upload 

React Dropzone or Files 

PDF Parsing 

pdf-parse, pdfplumber, pdfminer 

Data Storage 

SQLite or in-memory JSON 

Deployment 

Vercel, Netlify 

 

 

 

 

 

Coverage Verification 

Student Persona 

Section 

Feature 1 (Academic Chat) 

Feature 2 (Learning Tools) 

A. Academic Guidance 

✅ Full Coverage 

➖ 

F. Productivity/Learning 

➖ 

✅ Full Coverage 

Advisor Persona 

Use Case Section 

Feature 1 (Escalation Queue) 

Feature 2 (AI Assist Tools) 

A. Summary and Context 

✅ Full Coverage 

➖ 

B. Escalation Handling 

✅ Full Coverage 

➖ 

C. Advisor Assist Tools 

➖ 

✅ Full Coverage 

D. Insights 

✅ Partial (trends shown in queue) 

➖ 

Administrator Persona 

Use Case Section 

Feature 1 (Analytics) 

Feature 2 (Document Upload) 

A. Content Management 

➖ 

✅ Full Coverage 

B. Analytics and Reporting 

✅ Full Coverage 