from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel
import uvicorn
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')

app = FastAPI(
    title="AI Market Terminal API",
    description="Production-ready API for AI-powered trading terminal",
    version="0.9.0-beta"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

# Pydantic models
class User(BaseModel):
    id: str
    email: str
    tier: str = "learner"
    subscription_status: str = "active"

class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class BacktestRequest(BaseModel):
    symbol: str
    strategy: str
    start_date: str
    end_date: str
    initial_capital: float = 10000

class BacktestResult(BaseModel):
    id: str
    symbol: str
    strategy: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    status: str

# Mock database (replace with real database)
users_db = {}
backtests_db = {}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_user(user_id: str = Depends(verify_token)):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]

def check_tier_access(user: User, required_tier: str):
    tier_hierarchy = {"learner": 0, "pro": 1, "quant": 2, "enterprise": 3}
    user_tier_level = tier_hierarchy.get(user.tier, 0)
    required_tier_level = tier_hierarchy.get(required_tier, 0)
    
    if user_tier_level < required_tier_level:
        raise HTTPException(
            status_code=403, 
            detail=f"Tier {required_tier} required. Current tier: {user.tier}"
        )

@app.middleware("http")
async def prometheus_middleware(request, call_next):
    start_time = datetime.utcnow()
    response = await call_next(request)
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_LATENCY.observe(duration)
    
    return response

@app.get("/")
async def root():
    return {"message": "AI Market Terminal API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/auth/signup", response_model=dict)
async def signup(user_data: UserCreate):
    user_id = f"user_{len(users_db) + 1}"
    users_db[user_id] = User(
        id=user_id,
        email=user_data.email,
        tier="learner"
    )
    
    access_token = create_access_token(data={"sub": user_id})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/login", response_model=dict)
async def login(user_data: UserLogin):
    # Mock authentication - replace with real auth
    for user_id, user in users_db.items():
        if user.email == user_data.email:
            access_token = create_access_token(data={"sub": user_id})
            return {"access_token": access_token, "token_type": "bearer"}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/user/profile", response_model=User)
async def get_profile(user: User = Depends(get_user)):
    return user

@app.post("/backtest", response_model=BacktestResult)
async def create_backtest(
    request: BacktestRequest,
    user: User = Depends(get_user)
):
    check_tier_access(user, "learner")
    
    # Mock backtest execution
    backtest_id = f"backtest_{len(backtests_db) + 1}"
    result = BacktestResult(
        id=backtest_id,
        symbol=request.symbol,
        strategy=request.strategy,
        total_return=0.15,
        sharpe_ratio=1.2,
        max_drawdown=-0.05,
        status="completed"
    )
    
    backtests_db[backtest_id] = result
    return result

@app.get("/backtest/{backtest_id}", response_model=BacktestResult)
async def get_backtest(
    backtest_id: str,
    user: User = Depends(get_user)
):
    check_tier_access(user, "learner")
    
    if backtest_id not in backtests_db:
        raise HTTPException(status_code=404, detail="Backtest not found")
    
    return backtests_db[backtest_id]

@app.get("/backtests", response_model=List[BacktestResult])
async def list_backtests(user: User = Depends(get_user)):
    check_tier_access(user, "learner")
    return list(backtests_db.values())

@app.post("/trading/paper-trade")
async def paper_trade(user: User = Depends(get_user)):
    check_tier_access(user, "learner")
    return {"message": "Paper trading endpoint - Learner tier only"}

@app.post("/trading/live-trade")
async def live_trade(user: User = Depends(get_user)):
    check_tier_access(user, "pro")
    return {"message": "Live trading endpoint - Pro tier and above"}

@app.post("/billing/portal")
async def billing_portal(user: User = Depends(get_user)):
    return {"portal_url": f"https://billing.example.com/user/{user.id}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
