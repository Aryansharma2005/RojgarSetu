# 🤝 Rojgar Setu (रोजगार सेतु)

<h3>Live Website</h3>
<a href="https://rojgarsetu-fisf.onrender.com/">Rojgar Setu</a>
> **Master Full-Stack Engineering Specification — Version 5.5 • Peer-to-Peer (P2P) Architecture**  
> *Dual-Actor Hyperlocal Platform for Direct Individual Hiring • Zero Agency Brokerage*

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5%2B-092E20?logo=django)](https://djangoproject.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?logo=postgresql)](https://supabase.com)
[![PostGIS](https://img.shields.io/badge/PostGIS-3.3.7-green)](https://postgis.net)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-Flash%20AI-orange?logo=google)](https://aistudio.google.com)
[![DigiLocker](https://img.shields.io/badge/DigiLocker-Aadhaar%20Verified-blue)](https://digilocker.gov.in)

---

## 📌 Executive Summary & Core Paradigm Shift

**Rojgar Setu** is an open, zero-brokerage, strictly **Individual-to-Individual (P2P / C2C)** workforce discovery platform. It eliminates traditional recruitment agencies (which charge ₹15,000–₹25,000 upfront non-refundable brokerage from homeowners) and establishes trust between individual homeowners and verified blue-collar karigars.

### 🌟 Core Architectural Pillars
1. **Zero Agencies / Companies:** Strictly individuals hiring individuals. No corporate, contractor, or agency profiles permitted.
2. **PostGIS Hyperlocal Radius:** Exact GPS location capture connecting employers to workers within walking/short radius (500m–10km).
3. **Dynamic AI Screening (Gemini Flash):** Dynamically generates 4–6 practical safety & tool MCQs across 1 to 4 selected trades in <1s with auto-scoring and AI profile bio synthesis.
4. **Pre-Signed Contract Handshake:** Employer signs dynamic contract at job creation! Sent intact in chat; personal phone numbers revealed **ONLY** when worker signs.

---

## 🔄 The 5-Stage Pre-Signed Contract Handshake & Phone Unlock Pipeline

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│     STAGE 1     │      │     STAGE 2     │      │     STAGE 3     │      │     STAGE 4     │      │     STAGE 5     │
│  Job Creation   │ ───► │  1-Click Apply  │ ───► │   Masked Chat   │ ───► │Forward Contract │ ───► │ PHONE UNLOCKED! │
│ 1st-Party Sign  │      │ 500m-10km Radius│      │ 100% Privacy    │      │ In-Chat Feed    │      │  Direct 1-Click │
└─────────────────┘      └─────────────────┘      └─────────────────┘      └─────────────────┘      └─────────────────┘
```

1. **Stage 1 (Job Creation & Pre-Sign):** Homeowner posts job with duties, duration, and pay. The system generates trade-specific contract terms. The employer digitally signs upfront with a 1st-party cryptographic stamp (`DIGITAL_SIGN_EMP_<id>_<timestamp>`).
2. **Stage 2 (Hyperlocal Discovery & Apply):** Worker browses jobs sorted by true spherical PostGIS distance (500m–10km). Worker applies in 1 click with their verified Gemini AI test score and Aadhaar badge.
3. **Stage 3 (Masked In-App Chat):** Employer reviews applicant's AI score and bio, and accepts them into chat. **Strict Privacy Shield:** Mobile numbers and emails remain 100% masked (`+91 98XXX-XX111`).
4. **Stage 4 (In-Chat Contract Forwarding):** Employer clicks "Forward Contract" in chat. The pre-signed contract appears directly in the worker's chat feed.
5. **Stage 5 (Worker Signature & Phone Reveal):** Worker inspects terms and clicks "Accept & Sign Contract" (2nd-party digital stamp). Contract status becomes `active` (Fully Executed). **Privacy shield is lifted:** Mutual telephone numbers are unlocked instantly with 1-click calling (`tel:`) and WhatsApp!

---

## 📂 Repository & Folder Structure

```text
Rojgar-Setu/
├── .env                              # Pre-configured local secrets (ignored by git)
├── .env.example                      # Production template for teammates
├── .gitignore                        # Python, Django, environment & OS exclusions
├── manage.py                         # Django root CLI
├── requirements.txt                  # Python dependencies (Django 5+, Psycopg2, Requests, Dotenv)
├── README.md                         # Master documentation & team implementation guide
├── run_rojgar_setu.bat               # 1-Click Windows launcher (migrates, seeds, and boots server)
│
├── docs/                             # Engineering Blueprints & Master Plans
│   ├── Rojgar_Setu_Master_Implementation_Plan.pdf  # Master Full-Stack Specification v5.5 (P2P)
│   ├── ROJGAR_SETU_MASTER_FULLSTACK_PLAN.html     # System Architecture & Swimlane Blueprint
│   └── ROJGAR_SETU_POSTGRESQL_IMPLEMENTATION_PLAN.html # PostGIS DDL, GiST Indexes & JSONB Schema
│
├── rojgar_setu/                      # Django Core Project Configuration
│   ├── __init__.py
│   ├── asgi.py
│   ├── wsgi.py
│   ├── settings.py                   # Supabase PostgreSQL + PostGIS + Gemini configuration
│   └── urls.py                       # Root route dispatcher
│
├── core/                             # Rojgar Setu P2P Application
│   ├── migrations/                   # Database schema migrations
│   │   ├── 0001_initial.py           # Initial PostgreSQL relational + JSONB models
│   │   └── __init__.py
│   ├── management/
│   │   └── commands/
│   │       ├── check_db.py           # Diagnostic command validating Supabase & Gemini API
│   │       ├── seed_p2p_data.py      # Populates realistic Delhi-NCR gigs, karigars & chat
│   │       └── seed_data.py          # Proxy command to seed_p2p_data
│   ├── ai_service.py                 # Gemini Flash dynamic 4-6 MCQ testing & AI bio engine
│   ├── spatial.py                    # PostGIS spherical distance & 500m-10km filter engine
│   ├── models.py                     # UserAccount, WorkerProfile, Job, Application, ChatRoom, Contract
│   ├── forms.py                      # Multi-trade registration, job post with digital signature
│   ├── views.py                      # 5-Stage Contract Handshake & Phone Unlock controllers
│   ├── urls.py                       # Sub-app URL routing
│   └── context_processors.py         # Bilingual dictionary (Hindi/English) & DB status badge
│
├── templates/                        # Responsive PWA-Ready Bilingual Templates
│   ├── base.html                     # Global navbar, Supabase status indicator, footer
│   ├── index.html                    # P2P Hero, 5-stage handshake diagram, Leaflet.js map
│   ├── auth/
│   │   ├── login.html                # Phone login with 1-click demo buttons
│   │   ├── register.html             # Dual-actor selector (Worker vs Homeowner)
│   │   ├── register_worker.html      # 1-to-4 trade selector & HTML5 GPS capture
│   │   └── register_employer.html    # Homeowner GPS capture & DigiLocker consent
│   ├── quiz/
│   │   └── assessment.html           # Gemini Flash dynamic MCQ screen with auto-grading
│   ├── jobs/
│   │   ├── list.html                 # Distance-sorted job feed with pre-signed badges
│   │   ├── detail.html               # Contract terms, price, and 1-click apply button
│   │   ├── create.html               # Dynamic contract terms generator & 1st-party signing
│   │   ├── my_jobs.html              # Employer dashboard tracking posted gigs
│   │   └── applicants.html           # Applicant review with AI test score, bio & chat button
│   ├── chat/
│   │   └── room.html                 # 1-on-1 In-App Masked Chat & In-Chat Contract Signature
│   ├── workers/
│   │   ├── list.html                 # Nearby Karigar directory sorted by proximity
│   │   ├── profile.html              # Karigar profile with AI Bio & Aadhaar badge
│   │   └── my_applications.html      # Worker tracking dashboard for applications
│   └── analytics/
│       └── dashboard.html            # P2P contracts executed & brokerage savings analytics
│
└── static/                           # Static assets, CSS, JavaScript & icons
```

---

## ⚡ Quickstart Guide (Run in 2 Minutes)

### Option 1: 1-Click Windows Launcher (Fastest)
Double-click `run_rojgar_setu.bat` or run:
```powershell
.\run_rojgar_setu.bat
```
This automatically applies Supabase database migrations, seeds demo karigars, and launches the server at `http://127.0.0.1:8000/`.

---

### Option 2: Manual Terminal Setup

#### 1. Clone & Navigate
```bash
git clone <your-github-repo-url>
cd Rojgar-Setu
```

#### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Configure Environment
Your `.env` is already configured with live Supabase PostgreSQL and Google Gemini API credentials.  
*(Teammates can customize using `.env.example` if connecting to separate instances).*

#### 5. Verify Database & APIs
Run the diagnostic test:
```bash
python manage.py check_db
```
Expected output:
```text
==================================================
   ROJGAR SETU SYSTEM & DATABASE DIAGNOSTIC
==================================================
1. Testing Database Connection...
   ✓ Database Connected: PostgreSQL 17.12 on aarch64-unknown-linux-gnu...
   ✓ PostGIS Extension Active: POSTGIS="3.3.7"...

2. Checking Core Table Records...
   ✓ Verified Karigars:    4
   ✓ Individual Employers: 4
   ✓ Pre-Signed Gigs:      4
   ✓ Handshake Contracts:  1

3. Checking Gemini AI Configuration...
   ✓ GEMINI_API_KEY detected
   ✓ Active AI Model: gemini-flash-latest
==================================================
```

#### 6. Apply Migrations & Seed Data
```bash
python manage.py migrate
python manage.py seed_p2p_data
```

#### 7. Launch Development Server
```bash
python manage.py runserver 8000
```
Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser.

---

## 🔑 Pre-Seeded Demo Credentials

| Role | Name | Phone | Password | Profile Highlights |
| :--- | :--- | :--- | :--- | :--- |
| **Worker (Karigar)** | Manoj Kumar Prajapati | `9870001111` | `password123` | Plumber & Electrician &bull; 100% AI Quiz Score &bull; Aadhaar Verified ✓ |
| **Worker (Domestic)** | Sunita Devi | `9870002222` | `password123` | House Maid & Cook &bull; 5 Yrs Exp &bull; Aadhaar Verified ✓ |
| **Employer (Homeowner)** | Anita Sharma | `9811223344` | `password123` | Noida Sector 62 &bull; Posted Plumbing Job (450m away) |
| **Employer (Homeowner)** | Vikram Malhotra | `9822334455` | `password123` | Indirapuram &bull; Posted House Maid Job (600m away) |

*(Quick-fill buttons are available on the Login page for instant one-click testing!)*

---

## 🧪 How to Test the 5-Stage Contract Handshake Live

1. **Step 1:** Log in as **Employer** (`Phone: 9811223344`, `Password: password123`).
2. **Step 2:** Click **"My Gigs"** &bull; select **"Urgent Plumber for Kitchen Pipe Leakage"** &bull; click **"Review Applicants"**.
3. **Step 3:** Notice applicant **Manoj Prajapati** (450m away, 100% AI test score). Click **"Accept & Start Chat"**.
4. **Step 4:** You enter the **In-App Masked Chat**. Notice phone numbers are shielded: `+91 98XXX-XX111`. Click **"Forward Pre-Signed Contract"**.
5. **Step 5:** In another browser tab/incognito window, log in as **Worker Manoj** (`Phone: 9870001111`, `Password: password123`).
6. **Step 6:** Click **"My Applications"** &bull; click **"Open Chat"**.
7. **Step 7:** Inspect the employer's pre-signed contract card. Click **"Accept Terms & Apply 2nd-Party Digital Signature"**!
8. **Step 8 (Magic Moment):** 🎉 The contract transitions to **"FULLY EXECUTED"**. The Privacy Shield is lifted! Both parties instantly see each other's full personal mobile number with direct **1-click `tel:` calling** and **WhatsApp** deep-links!

---

## 🛠️ GitHub Push Instructions for the Team

To push this codebase to your team's GitHub repository:

```bash
# 1. Initialize git (if not already initialized)
git init

# 2. Add remote repository
git remote add origin <your-github-repo-url>

# 3. Stage all files (.env is protected by .gitignore)
git add .

# 4. Commit master implementation
git commit -m "feat: complete Rojgar Setu P2P architecture v5.5 with Supabase PostgreSQL, PostGIS & Gemini Flash"

# 5. Push to GitHub
git branch -M main
git push -u origin main
```

---

## 📜 Specifications & Documentation Index

All foundational architectural PDFs and specifications are preserved in the [`docs/`](file:///c:/Users/hites/Downloads/Rojgar%20Setu/docs) folder:
- [Rojgar_Setu_Master_Implementation_Plan.pdf](file:///c:/Users/hites/Downloads/Rojgar%20Setu/docs/Rojgar_Setu_Master_Implementation_Plan.pdf): Master v5.5 Engineering Blueprint
- [ROJGAR_SETU_MASTER_FULLSTACK_PLAN.html](file:///c:/Users/hites/Downloads/Rojgar%20Setu/docs/ROJGAR_SETU_MASTER_FULLSTACK_PLAN.html): Comprehensive swimlane diagrams and system matrix
- [ROJGAR_SETU_POSTGRESQL_IMPLEMENTATION_PLAN.html](file:///c:/Users/hites/Downloads/Rojgar%20Setu/docs/ROJGAR_SETU_POSTGRESQL_IMPLEMENTATION_PLAN.html): PostGIS GiST spatial indexing & JSONB schemas
