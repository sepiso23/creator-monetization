# 🇿🇲 Nthanda Monetization App - MVP

**Help creators in Zambia get paid reliably.**

A web-based creator monetization platform enabling fast, reliable mobile-money-based payments. Fans support creators using local payment methods, creators receive payouts to mobile money accounts.

---

## 🎯 Mission

Creators in Zambia lack reliable monetization tools because most global platforms don't support local payments. This forces creators to rely on foreign accounts, middlemen, or unsustainable partnerships. **Nthanda solves this by enabling direct mobile-money payments.**

---

## 📋 MVP Scope (2 Weeks)

**Core User Flows:**
- ✅ Creators sign up, create profiles, set up bank accounts
- ✅ Fans discover creators, send payments via mobile money
- ✅ Creators see balances, request payouts
- ✅ Admin approves payouts, reconciles transactions

**Tech Stack:**
- **Frontend:** React (modern UI, mobile-responsive)
- **Backend:** Django REST Framework or Node.js
- **Database:** PostgreSQL (immutable ledger)
- **Cache/Queue:** Redis
- **Auth:** JWT tokens
- **Payments:** Local mobile money provider APIs
- **Hosting:** Cloud VPS (AWS, DigitalOcean, etc.)

---

## 📁 Project Structure

```
creator-monetization/
├── backend/                    ← Django/Node.js API
│   ├── README.md              ← Backend setup & API docs
│   ├── requirements.txt        ← Python dependencies
│   ├── manage.py              ← Django CLI
│   ├── config/                ← Settings, URLs, WSGI
│   ├── apps/
│   │   ├── auth/              ← User auth & JWT
│   │   ├── creators/          ← Creator profiles
│   │   ├── wallets/           ← Wallet & ledger
│   │   ├── payments/          ← Payment processing
│   │   ├── payouts/           ← Payout management
│   │   └── admin/             ← Admin endpoints
│   └── tests/                 ← Unit & integration tests
├── frontend/                  ← React app
│   ├── README.md              ← Frontend setup & guide
│   ├── package.json           ← Dependencies
│   ├── public/
│   ├── src/
│   │   ├── components/        ← React components
│   │   ├── pages/             ← Page components
│   │   ├── services/          ← API client
│   │   ├── store/             ← Redux/Context state
│   │   ├── styles/            ← CSS/Tailwind
│   │   └── App.js
│   └── tests/                 ← Unit & integration tests
├── ISSUE_TEMPLATE_GUIDE.md    ← Complete issue template docs
├── ISSUE_TEMPLATES_QUICK_REF.md ← 1-page cheat sheet
├── EXAMPLE_WEEK1_ISSUES.md    ← Real example issues
├── QUICK_START.md             ← Getting started
└── README.md                  ← This file
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+ (backend)
- Node.js 16+ (frontend)
- PostgreSQL 12+
- Redis 6+

### Setup Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

→ API runs at `http://localhost:8000`

### Setup Frontend
```bash
cd frontend
npm install
npm start
```

→ App runs at `http://localhost:3000`

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────┐
│                    Fans / Creators                 │
│              (Web Browser + Mobile)                │
└────────────────────┬────────────────────────────────┘
                     │
         ┌───────────┴────────────┐
         │   Frontend (React)     │
         │  - Auth screens        │
         │  - Creator profiles    │
         │  - Payment UI          │
         │  - Wallet dashboard    │
         └───────────┬────────────┘
                     │ (HTTPS)
         ┌───────────┴────────────┐
         │  Backend API (Django)  │
         │  - Auth & JWT          │
         │  - Creator profiles    │
         │  - Wallet & ledger     │
         │  - Payment logic       │
         │  - Admin endpoints     │
         └───────────┬────────────┘
         ┌───────────┼────────────┐
         │           │            │
    ┌────┴────┐  ┌──┴────┐  ┌──┴─────┐
    │ Postgres │  │ Redis │  │Mobile  │
    │ Ledger   │  │ Cache │  │Money   │
    └──────────┘  └───────┘  └────────┘
```

---

## 📋 Core Components

### Auth & User Service
- User registration (email + password)
- JWT authentication & refresh tokens
- Role-based access (creator, fan, admin)

### Creator Profiles Service
- Public creator profiles (discoverable)
- Creator dashboard (balance, transactions)
- Profile editing & bank account setup

### Wallet & Ledger Service
- Immutable transaction ledger (append-only)
- Wallet balance calculated from ledger
- No manual balance editing (audit trail)

### Payments Integration
- Initiate mobile money payments
- Webhook handling from mobile money provider
- Payment state machine (pending → success/failed)
- Idempotency (prevent duplicate charges)

### Payouts & Admin
- Creator payout requests
- Admin approval/rejection
- Automatic weekly payout processing
- Admin reconciliation dashboard

---

## 📱 API Endpoints

### Authentication
```
POST   /api/v1/auth/register          Create user account
POST   /api/v1/auth/login             User login
POST   /api/v1/auth/refresh           Refresh JWT token
```

### Creator Profiles
```
GET    /api/v1/creators/{id}          Get public profile
PUT    /api/v1/creators/me            Update own profile
```

### Wallet & Payments
```
GET    /api/v1/wallets/me             Get wallet balance
GET    /api/v1/wallets/me/transactions Get transaction history
POST   /api/v1/payments/initiate      Start payment
POST   /api/v1/payments/webhook       Receive payment status (mobile money provider)
```

### Payouts
```
POST   /api/v1/payouts/request        Request payout
GET    /api/v1/payouts/me             Get payout history
```

### Admin
```
GET    /api/v1/admin/transactions     View all transactions
GET    /api/v1/admin/payouts          View all payouts
POST   /api/v1/admin/payouts/{id}/approve    Approve payout
POST   /api/v1/admin/payouts/{id}/reject     Reject payout
```

---

## 📅 2-Week Sprint

### Week 1: Foundation & Integration
- **Day 1-2:** Auth setup, user models, JWT
- **Day 3-5:** Creator profiles, wallet setup, first integrations
- **Day 6-7:** Payment flow, webhooks, end-to-end testing

### Week 2: Polish & Launch
- **Day 8:** UI polish, admin features, styling
- **Day 9:** Bug fixes, integration issues, final testing
- **Day 10:** Security review, deployment, go-live

**Integration Windows:**
- Days 3-5: First backend-frontend integrations
- Days 6-7: Full payment & payout flows
- Days 9-10: Stabilization & go-live

---

## 📖 Documentation

### Getting Started
- **[QUICK_START.md](QUICK_START.md)** - 30-second overview
- **[backend/README.md](backend/README.md)** - Backend setup & development
- **[frontend/README.md](frontend/README.md)** - Frontend setup & development

### Issue Templates & Workflow
- **[ISSUE_TEMPLATES_README.md](ISSUE_TEMPLATES_README.md)** - Complete guide
- **[ISSUE_TEMPLATES_QUICK_REF.md](ISSUE_TEMPLATES_QUICK_REF.md)** - 1-page cheat sheet
- **[ISSUE_TEMPLATE_GUIDE.md](ISSUE_TEMPLATE_GUIDE.md)** - Detailed reference
- **[EXAMPLE_WEEK1_ISSUES.md](EXAMPLE_WEEK1_ISSUES.md)** - Real example issues

### Checklists
- **[ISSUE_CREATION_CHECKLIST.md](ISSUE_CREATION_CHECKLIST.md)** - Pre-submit verification
- **[INDEX.md](INDEX.md)** - File navigation

---

## 👥 Team

| Role | Name | Responsibility |
|------|------|-----------------|
| **Project Lead** | Peter Zyambo | Overall MVP delivery, Backend lead, integration owner |
| **Frontend Lead** | George Mugale | Core UI, state management |
| **Frontend Support** | Barnabas Mwaipaya | Styling, responsiveness, polish |
| **Backend Support** | George Mugale | services, database, polish |
| **QA** | Team | Testing, verification |

---

## 🔗 Daily Workflow

### Before Code
1. **Create Issue** - Use appropriate template (backend, frontend, integration, etc.)
2. **Define API Contract** - Backend & frontend agree on request/response
3. **Assign Owner** - Clear ownership
4. **Link Dependencies** - Track blockers

### During Code
1. **Implement Feature** - Follow acceptance criteria
2. **Test Locally** - Unit + integration tests
3. **Request Review** - Code review before merge
4. **Merge to Main** - Squash commits

### Daily Sync (Days 3-10)
1. **Backend-Frontend Handshake** - 15 min standup
2. **Verify Real Endpoints** - Frontend uses actual API (no mocks)
3. **Log Blockers** - Same day resolution
4. **Integration Owner Sign-Off** - API contracts approved

---

## ✅ Definition of Done

Feature is **Done** when:
- ✅ Code meets acceptance criteria
- ✅ Tests written (unit + integration)
- ✅ No console errors or warnings
- ✅ Real backend integration (no mocks)
- ✅ QA verified on mobile & desktop
- ✅ Integration owner approved
- ✅ Merged to main

---

## 🚀 Deployment

### Staging
```bash
git push origin feature-branch
# Creates automatic staging deployment
```

### Production
```bash
git push origin main
# Creates automatic production deployment
```

**Pre-Deployment Checklist:**
- [ ] All tests passing
- [ ] Code reviewed & approved
- [ ] Migrations tested
- [ ] Environment variables set
- [ ] Monitoring configured
- [ ] Rollback plan ready

---

## 🐛 Bug Reports

Found a bug? Create issue with `[BUG]` template:

```
Title: [BUG] Brief description
Steps to reproduce
Expected vs actual result
Screenshots/videos
Browser & OS info
```

---

## 📞 Support

**Questions?**
- Read [ISSUE_TEMPLATES_README.md](ISSUE_TEMPLATES_README.md)
- Check [EXAMPLE_WEEK1_ISSUES.md](EXAMPLE_WEEK1_ISSUES.md) for examples
- Ask in team chat or standup

**Having trouble?**
- Backend issues → Contact Peter
- Frontend issues → Contact George or Barnabas
- Integration issues → Contact Peter

---

## 📄 License

MIT License - See LICENSE file

---

## 🎯 Mission Statement

> **"If it doesn't help a creator get paid within 2 weeks, don't ship it."**

Every decision, every line of code, every feature should move us toward this goal. Keep this focus and we will succeed.

---

## 🤝 Contributing

Want to contribute? Start here:

- **Read [CONTRIBUTION.md](CONTRIBUTION.md)** for:
  - Branching strategy (`feature/`, `fix/`, `docs/`, etc.)
  - Commit message conventions
  - Pull request guidelines with examples
  - Code style for backend & frontend
  - Testing requirements
  - Code review process
  - Common issues & solutions

- **Create issues** using templates in [.github/ISSUE_TEMPLATE](https://github.com/zyambo/creator-monetization/tree/main/.github/ISSUE_TEMPLATE/)

- **Review examples** in [EXAMPLE_WEEK1_ISSUES.md](EXAMPLE_WEEK1_ISSUES.md)

**Project Lead:** Peter Zyambo (reviews API/backend changes)  
**Frontend Lead:** George Mugale (reviews frontend/integration)  
**Frontend Support:** Barnabas Mwaipaya (styling/responsive design)

---

**Created:** January 27, 2026  
**Status:** MVP In Development  
**Timeline:** 2-week sprint  
**Goal:** Enable Zambian creators to get paid reliably. 🇿🇲
