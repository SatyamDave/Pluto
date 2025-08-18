# AI Market Terminal

A production-ready AI-powered trading terminal with tiered access for learners, professionals, and quantitative traders.

## 🚀 Features

### Multi-Tier Access
- **Learner**: Free tier with AI tutor, paper trading, and basic backtesting
- **Pro**: Live trading access, advanced strategies, and real-time analytics
- **Quant**: Custom strategy builder, API access, and advanced analytics
- **Enterprise**: Team management, custom integrations, and SLA guarantees

### Core Capabilities
- 🤖 AI-powered trading strategies
- 📊 Real-time market data and analytics
- 🔬 Advanced backtesting engine
- 💳 Integrated payment processing (Stripe)
- 📈 Comprehensive monitoring and logging
- 🔐 JWT-based authentication with role-based access

## 🏗️ Architecture

```
ai-market-terminal/
├── apps/
│   ├── api/          # FastAPI backend
│   ├── web/          # React frontend
│   └── cli/          # Command-line interface
├── auth/             # Authentication module
├── infra/            # Infrastructure configs
│   ├── k8s/          # Kubernetes manifests
│   ├── monitoring/   # Prometheus + Grafana
│   └── db/           # Database configs
├── demos/            # Demo workflows
└── docs/             # Documentation
```

## 🛠️ Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- Kubernetes cluster (for production)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/ai-market-terminal.git
   cd ai-market-terminal
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. **Access the applications**
   - Web UI: http://localhost
   - API: http://localhost:8000
   - Grafana: http://localhost:3000 (admin/admin)
   - Prometheus: http://localhost:9090

### Manual Setup

#### API Backend
```bash
cd apps/api
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Web Frontend
```bash
cd apps/web
npm install
npm start
```

#### CLI Tool
```bash
cd apps/cli
pip install -r requirements.txt
python main.py --help
```

## 🚀 Production Deployment

### Kubernetes Deployment

1. **Build and push Docker images**
   ```bash
   docker build -t your-registry/ai-market-api:latest apps/api/
   docker build -t your-registry/ai-market-web:latest apps/web/
   docker push your-registry/ai-market-api:latest
   docker push your-registry/ai-market-web:latest
   ```

2. **Deploy to Kubernetes**
   ```bash
   kubectl apply -f infra/k8s/
   ```

3. **Set up ingress and SSL**
   ```bash
   # Configure your domain in infra/k8s/ingress.yaml
   kubectl apply -f infra/k8s/ingress.yaml
   ```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | JWT signing secret | `your-secret-key-change-in-production` |
| `STRIPE_SECRET_KEY` | Stripe secret key | - |
| `POSTGRES_PASSWORD` | Database password | `secure_password` |
| `POSTHOG_API_KEY` | PostHog analytics key | - |

## 📊 Monitoring

### Prometheus Metrics
- API request counts and latency
- Database connection metrics
- Custom business metrics

### Grafana Dashboards
- System health overview
- Trading performance metrics
- User activity analytics

### Logging
- Structured JSON logging
- Centralized log aggregation
- Error tracking and alerting

## 🧪 Testing

### Run Tests
```bash
# API tests
cd apps/api && pytest tests/ -v

# Web tests
cd apps/web && npm test

# CLI tests
cd apps/cli && python -m pytest tests/ -v
```

### Demo Workflows
```bash
# Learner demo
python demos/learner_demo.py

# Pro demo
python demos/pro_demo.py

# Quant demo
python demos/quant_demo.py
```

## 🔧 Development

### Code Quality
- **Python**: Black, Flake8, MyPy
- **JavaScript**: ESLint, Prettier
- **Pre-commit hooks** for automated formatting

### API Documentation
- Interactive docs: http://localhost:8000/docs
- OpenAPI spec: http://localhost:8000/openapi.json

### Database Migrations
```bash
cd apps/api
alembic upgrade head
```

## 📈 Analytics

### PostHog Integration
- User behavior tracking
- Feature usage analytics
- A/B testing capabilities

### Custom Events
- User signup/login
- Backtest execution
- Trading activity
- Subscription upgrades

## 🔐 Security

### Authentication
- JWT-based authentication
- Role-based access control
- Secure password hashing

### Data Protection
- Encrypted data at rest
- TLS for data in transit
- Regular security audits

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Guidelines
- Follow the existing code style
- Add tests for new features
- Update documentation
- Ensure all tests pass

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/ai-market-terminal/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/ai-market-terminal/discussions)

## 🗺️ Roadmap

- [ ] Advanced AI strategy builder
- [ ] Real-time market data feeds
- [ ] Mobile application
- [ ] Advanced risk management
- [ ] Social trading features
- [ ] Institutional features

---

**Built with ❤️ by the AI Market Terminal team**
