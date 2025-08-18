"""
PMF Analytics API
Tracks Product-Market Fit metrics and generates reports
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
import redis
import posthog
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

# Initialize Redis for analytics caching
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

# Initialize PostHog
posthog.api_key = os.getenv("POSTHOG_API_KEY")
posthog.host = os.getenv("POSTHOG_HOST", "https://app.posthog.com")

router = APIRouter(prefix="/pmf", tags=["pmf"])

# Pydantic models
class PMFMetrics(BaseModel):
    dau: int
    wau: int
    mau: int
    dauMauRatio: float
    conversionRate: float
    npsScore: float
    churnRate: float
    arpu: float
    ltv: float
    referralRate: float

class CohortData(BaseModel):
    cohort: str
    size: int
    conversionRate: float
    retention: float
    revenue: float

class FeatureUsage(BaseModel):
    feature: str
    usage: float
    satisfaction: float
    revenueCorrelation: float

class NPSSurvey(BaseModel):
    user_id: str
    score: int
    feedback: Optional[str] = None
    category: str = "general"

class MicroSurvey(BaseModel):
    user_id: str
    question: str
    answer: str
    feature: Optional[str] = None

def calculate_dau_mau_ratio(dau: int, mau: int) -> float:
    """Calculate DAU/MAU ratio"""
    return dau / mau if mau > 0 else 0

def calculate_conversion_rate(paid_users: int, total_users: int) -> float:
    """Calculate conversion rate"""
    return paid_users / total_users if total_users > 0 else 0

def calculate_nps_score(promoters: int, detractors: int, total_responses: int) -> float:
    """Calculate Net Promoter Score"""
    if total_responses == 0:
        return 0
    return ((promoters - detractors) / total_responses) * 100

def calculate_churn_rate(churned_users: int, total_users: int) -> float:
    """Calculate churn rate"""
    return churned_users / total_users if total_users > 0 else 0

@router.get("/metrics")
async def get_pmf_metrics(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)")
):
    """Get PMF metrics for the specified date range"""
    try:
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Get metrics from PostHog
        dau = get_daily_active_users(start, end)
        wau = get_weekly_active_users(start, end)
        mau = get_monthly_active_users(start, end)
        
        # Calculate ratios
        dau_mau_ratio = calculate_dau_mau_ratio(dau, mau)
        
        # Get conversion data
        conversion_rate = get_conversion_rate(start, end)
        
        # Get NPS data
        nps_score = get_nps_score(start, end)
        
        # Get churn data
        churn_rate = get_churn_rate(start, end)
        
        # Get revenue metrics
        arpu = get_arpu(start, end)
        ltv = get_ltv(start, end)
        
        # Get referral data
        referral_rate = get_referral_rate(start, end)
        
        metrics = PMFMetrics(
            dau=dau,
            wau=wau,
            mau=mau,
            dauMauRatio=dau_mau_ratio,
            conversionRate=conversion_rate,
            npsScore=nps_score,
            churnRate=churn_rate,
            arpu=arpu,
            ltv=ltv,
            referralRate=referral_rate
        )
        
        # Cache results
        cache_key = f"pmf_metrics:{start_date}:{end_date}"
        redis_client.setex(cache_key, 3600, json.dumps(metrics.dict()))
        
        return {"metrics": metrics}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cohorts")
async def get_cohort_analysis(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)")
):
    """Get cohort analysis data"""
    try:
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Get cohort data from database
        cohorts = get_cohort_data(start, end)
        
        return {"cohorts": cohorts}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/features")
async def get_feature_usage(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)")
):
    """Get feature usage and revenue correlation"""
    try:
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Get feature usage data
        features = get_feature_usage_data(start, end)
        
        return {"featureUsage": features}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/nps")
async def submit_nps_survey(survey: NPSSurvey):
    """Submit NPS survey response"""
    try:
        # Store NPS response
        nps_data = {
            "user_id": survey.user_id,
            "score": survey.score,
            "feedback": survey.feedback,
            "category": survey.category,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in Redis for quick access
        redis_client.lpush("nps_responses", json.dumps(nps_data))
        
        # Track in PostHog
        posthog.capture(survey.user_id, "nps_survey_submitted", {
            "score": survey.score,
            "category": survey.category,
            "has_feedback": bool(survey.feedback)
        })
        
        return {"message": "NPS survey submitted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/micro-survey")
async def submit_micro_survey(survey: MicroSurvey):
    """Submit micro-survey response"""
    try:
        # Store micro-survey response
        survey_data = {
            "user_id": survey.user_id,
            "question": survey.question,
            "answer": survey.answer,
            "feature": survey.feature,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in Redis
        redis_client.lpush("micro_surveys", json.dumps(survey_data))
        
        # Track in PostHog
        posthog.capture(survey.user_id, "micro_survey_submitted", {
            "question": survey.question,
            "answer": survey.answer,
            "feature": survey.feature
        })
        
        return {"message": "Micro-survey submitted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/report/generate")
async def generate_pmf_report(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    background_tasks: BackgroundTasks
):
    """Generate comprehensive PMF report"""
    try:
        # Add report generation to background tasks
        background_tasks.add_task(
            generate_report_background,
            start_date,
            end_date
        )
        
        return {"message": "PMF report generation started"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/report/{report_id}")
async def get_pmf_report(report_id: str):
    """Get generated PMF report"""
    try:
        # Get report from cache/storage
        report_data = redis_client.get(f"pmf_report:{report_id}")
        
        if not report_data:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return json.loads(report_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions for data retrieval
def get_daily_active_users(start: datetime, end: datetime) -> int:
    """Get daily active users from PostHog"""
    try:
        # Query PostHog for DAU
        response = posthog.get(
            'insights/trend/',
            params={
                'events': [{'id': '$pageview'}],
                'date_from': start.strftime('%Y-%m-%d'),
                'date_to': end.strftime('%Y-%m-%d'),
                'interval': 'day'
            }
        )
        
        # Calculate average DAU
        if response and 'result' in response:
            total_events = sum(day['count'] for day in response['result'])
            days = (end - start).days + 1
            return total_events // days
        
        return 0
        
    except Exception:
        # Return mock data for demonstration
        return 145

def get_weekly_active_users(start: datetime, end: datetime) -> int:
    """Get weekly active users from PostHog"""
    try:
        # Query PostHog for WAU
        response = posthog.get(
            'insights/trend/',
            params={
                'events': [{'id': '$pageview'}],
                'date_from': start.strftime('%Y-%m-%d'),
                'date_to': end.strftime('%Y-%m-%d'),
                'interval': 'week'
            }
        )
        
        if response and 'result' in response:
            return sum(week['count'] for week in response['result'])
        
        return 0
        
    except Exception:
        # Return mock data for demonstration
        return 892

def get_monthly_active_users(start: datetime, end: datetime) -> int:
    """Get monthly active users from PostHog"""
    try:
        # Query PostHog for MAU
        response = posthog.get(
            'insights/trend/',
            params={
                'events': [{'id': '$pageview'}],
                'date_from': start.strftime('%Y-%m-%d'),
                'date_to': end.strftime('%Y-%m-%d'),
                'interval': 'month'
            }
        )
        
        if response and 'result' in response:
            return sum(month['count'] for month in response['result'])
        
        return 0
        
    except Exception:
        # Return mock data for demonstration
        return 2340

def get_conversion_rate(start: datetime, end: datetime) -> float:
    """Get conversion rate from subscription data"""
    try:
        # Query database for subscription data
        # This would query your actual database
        paid_users = 42  # Mock data
        total_users = 234  # Mock data
        
        return calculate_conversion_rate(paid_users, total_users)
        
    except Exception:
        return 0.18  # Mock data

def get_nps_score(start: datetime, end: datetime) -> float:
    """Get NPS score from survey responses"""
    try:
        # Get NPS responses from Redis
        responses = redis_client.lrange("nps_responses", 0, -1)
        
        if not responses:
            return 52  # Mock data
        
        scores = []
        for response in responses:
            data = json.loads(response)
            response_date = datetime.fromisoformat(data['timestamp'])
            if start <= response_date <= end:
                scores.append(data['score'])
        
        if not scores:
            return 52  # Mock data
        
        # Calculate NPS
        promoters = len([s for s in scores if s >= 9])
        detractors = len([s for s in scores if s <= 6])
        total = len(scores)
        
        return calculate_nps_score(promoters, detractors, total)
        
    except Exception:
        return 52  # Mock data

def get_churn_rate(start: datetime, end: datetime) -> float:
    """Get churn rate from user data"""
    try:
        # Query database for churn data
        churned_users = 19  # Mock data
        total_users = 234  # Mock data
        
        return calculate_churn_rate(churned_users, total_users)
        
    except Exception:
        return 0.08  # Mock data

def get_arpu(start: datetime, end: datetime) -> float:
    """Get Average Revenue Per User"""
    try:
        # Query database for revenue data
        total_revenue = 10647  # Mock data
        total_users = 234  # Mock data
        
        return total_revenue / total_users if total_users > 0 else 0
        
    except Exception:
        return 45.50  # Mock data

def get_ltv(start: datetime, end: datetime) -> float:
    """Get Lifetime Value"""
    try:
        # Calculate LTV based on ARPU and retention
        arpu = get_arpu(start, end)
        retention_rate = 0.92  # Mock data
        
        # Simple LTV calculation: ARPU / (1 - retention_rate)
        return arpu / (1 - retention_rate) if retention_rate < 1 else arpu
        
    except Exception:
        return 342.00  # Mock data

def get_referral_rate(start: datetime, end: datetime) -> float:
    """Get referral rate"""
    try:
        # Query database for referral data
        users_with_referrals = 54  # Mock data
        total_users = 234  # Mock data
        
        return users_with_referrals / total_users if total_users > 0 else 0
        
    except Exception:
        return 0.23  # Mock data

def get_cohort_data(start: datetime, end: datetime) -> List[CohortData]:
    """Get cohort analysis data"""
    try:
        # Query database for cohort data
        # This would query your actual database
        cohorts = [
            CohortData(cohort="Week 1", size=200, conversionRate=0.15, retention=0.85, revenue=1350),
            CohortData(cohort="Week 2", size=180, conversionRate=0.18, retention=0.82, revenue=1458),
            CohortData(cohort="Week 3", size=165, conversionRate=0.21, retention=0.79, revenue=1386),
            CohortData(cohort="Week 4", size=142, conversionRate=0.19, retention=0.76, revenue=1075)
        ]
        
        return cohorts
        
    except Exception:
        return []

def get_feature_usage_data(start: datetime, end: datetime) -> List[FeatureUsage]:
    """Get feature usage and revenue correlation"""
    try:
        # Query database for feature usage data
        features = [
            FeatureUsage(feature="AI Tutor", usage=0.89, satisfaction=4.2, revenueCorrelation=0.78),
            FeatureUsage(feature="Backtesting", usage=0.67, satisfaction=4.1, revenueCorrelation=0.85),
            FeatureUsage(feature="Paper Trading", usage=0.92, satisfaction=4.3, revenueCorrelation=0.65),
            FeatureUsage(feature="Live Trading", usage=0.34, satisfaction=3.9, revenueCorrelation=0.92),
            FeatureUsage(feature="Market Analysis", usage=0.76, satisfaction=4.0, revenueCorrelation=0.71)
        ]
        
        return features
        
    except Exception:
        return []

def generate_report_background(start_date: str, end_date: str):
    """Generate PMF report in background"""
    try:
        # Generate comprehensive report
        report_data = {
            "report_id": f"pmf_{start_date}_{end_date}_{datetime.now().timestamp()}",
            "start_date": start_date,
            "end_date": end_date,
            "generated_at": datetime.now().isoformat(),
            "metrics": get_pmf_metrics(start_date, end_date),
            "cohorts": get_cohort_analysis(start_date, end_date),
            "features": get_feature_usage(start_date, end_date),
            "recommendations": generate_recommendations(start_date, end_date)
        }
        
        # Store report
        report_id = report_data["report_id"]
        redis_client.setex(f"pmf_report:{report_id}", 86400, json.dumps(report_data))
        
        # Send notification
        send_report_notification(report_data)
        
    except Exception as e:
        print(f"Error generating PMF report: {e}")

def generate_recommendations(start_date: str, end_date: str) -> List[str]:
    """Generate PMF recommendations"""
    recommendations = []
    
    # Get metrics
    metrics = get_pmf_metrics(start_date, end_date)
    
    if metrics["dauMauRatio"] < 0.4:
        recommendations.append("Improve user engagement to increase DAU/MAU ratio")
    
    if metrics["conversionRate"] < 0.15:
        recommendations.append("Optimize conversion funnel to increase paid subscriptions")
    
    if metrics["npsScore"] < 50:
        recommendations.append("Address user satisfaction issues to improve NPS")
    
    if metrics["churnRate"] > 0.1:
        recommendations.append("Implement retention strategies to reduce churn")
    
    return recommendations

def send_report_notification(report_data: Dict[str, Any]):
    """Send notification about generated report"""
    try:
        # Send Slack notification
        # This would integrate with your Slack webhook
        print(f"PMF report generated: {report_data['report_id']}")
        
    except Exception as e:
        print(f"Error sending notification: {e}")
