# 🌍 AI Identity Platform

**Modular AI Identity System** - Your AI-native identity isn't one big blob, it's modular cards you pull out depending on the situation.

## 🎴 Vision

An **AI-native modular identity system** where users can create context-specific "identity cards":
- **Work Identity Card** → replaces resumes (skills, verified work history, AI-scored credibility)
- **Financial Identity Card** → replaces credit score (income proof, spending consistency, risk score)
- **Creator Identity Card** → replaces follower screenshots (authenticity, engagement quality)
- **Civic Identity Card** → human verification + community reputation

Each card is **AI-generated, verifiable, portable, and privacy-controlled**.

## 🚀 MVP: Work Identity Card

We're launching with the **Work Identity Card** - a dynamic, auto-updating profile that shows your skills, credibility, and proof.

### Key Features
- **AI-Verified Skills**: "Python — 2,134 lines committed in 2024, 5 production projects, verified by GitHub"
- **Dynamic Updates**: Always fresh, unlike static resumes
- **Interactive Cards**: Recruiters can chat with your AI agent about your work
- **Trust Score**: AI confidence meter (0-100) for credibility
- **Portable**: Share as link, QR code, or embed in signatures

## 🏗️ Architecture

```
ai-market-terminal/
├── apps/
│   ├── web/                 # Next.js frontend
│   └── api/                 # FastAPI backend
├── packages/
│   ├── ui/                  # Shared UI components
│   ├── database/            # Prisma schema & migrations
│   └── ai-engine/           # AI processing & verification
├── docs/                    # Documentation
└── scripts/                 # Development scripts
```

## 🛠️ Tech Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.11+
- **Database**: PostgreSQL, Redis
- **AI**: OpenAI API, LangChain
- **Auth**: OAuth (Google, LinkedIn, GitHub)
- **Deployment**: Docker, Vercel, Railway

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL
- Redis

### Development Setup

1. **Clone & Install**
```bash
git clone <repo-url>
cd ai-market-terminal
npm install
```

2. **Environment Setup**
```bash
cp .env.example .env.local
# Fill in your API keys and database URLs
```

3. **Database Setup**
```bash
cd packages/database
npx prisma generate
npx prisma db push
```

4. **Start Development**
```bash
# Terminal 1: Frontend
npm run dev:web

# Terminal 2: Backend
npm run dev:api

# Terminal 3: AI Engine
npm run dev:ai
```

5. **Open Application**
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📋 User Flow

1. **Sign Up** → OAuth with Google/LinkedIn/GitHub
2. **Create Work Card** → Connect data sources (GitHub, LinkedIn)
3. **AI Processing** → Extracts skills, experience, proof
4. **Customize** → Control visibility and presentation
5. **Share** → Unique URL (identity.me/username/work)
6. **Auto-Update** → Always fresh with new data

## 🔐 Verification System

- **Source-Based Proof**: GitHub commits, LinkedIn endorsements
- **AI Background Check**: Cross-references multiple sources
- **Human Verification**: Manager/colleague endorsements
- **Trust Score**: Dynamic credibility rating (0-100)

## 🎯 Roadmap

### Phase 1: Work Identity Card MVP ✅
- [x] Basic auth & dashboard
- [x] GitHub/LinkedIn integration
- [x] AI skill extraction
- [x] Card generation & sharing

### Phase 2: Enhanced Features
- [ ] Financial Identity Card
- [ ] Creator Identity Card
- [ ] Advanced AI verification
- [ ] Mobile app

### Phase 3: Platform Expansion
- [ ] Civic Identity Card
- [ ] Enterprise integrations
- [ ] Blockchain verification
- [ ] Global identity layer

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

---

**Built with ❤️ for the future of AI-native identity**
