#!/usr/bin/env python3
"""
Learner Demo Workflow
AI Tutor + Paper Trading for new users
"""

import requests
import json
import time
from datetime import datetime, timedelta
import os

class LearnerDemo:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.session = requests.Session()
        self.user_token = None
        
    def signup_learner(self, email, password):
        """Sign up a new learner user"""
        print("🎓 Creating new learner account...")
        
        response = self.session.post(f"{self.api_url}/auth/signup", json={
            "email": email,
            "password": password
        })
        
        if response.status_code == 200:
            data = response.json()
            self.user_token = data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.user_token}"})
            print(f"✅ Learner account created: {email}")
            return True
        else:
            print(f"❌ Signup failed: {response.text}")
            return False
    
    def get_ai_tutor_lesson(self, topic="basics"):
        """Get AI tutor lesson"""
        print(f"🤖 Getting AI tutor lesson on: {topic}")
        
        # Mock AI tutor response
        lessons = {
            "basics": {
                "title": "Trading Basics",
                "content": "Welcome to trading! Let's start with the fundamentals...",
                "exercises": ["What is a market order?", "Explain bid vs ask"],
                "duration": "15 minutes"
            },
            "strategies": {
                "title": "Trading Strategies",
                "content": "Learn about different trading strategies...",
                "exercises": ["What is SMA?", "Explain RSI indicator"],
                "duration": "20 minutes"
            }
        }
        
        lesson = lessons.get(topic, lessons["basics"])
        print(f"📚 Lesson: {lesson['title']}")
        print(f"⏱️  Duration: {lesson['duration']}")
        print(f"📝 Content: {lesson['content'][:100]}...")
        
        return lesson
    
    def run_paper_trade(self, symbol="BTC-USD", amount=1000):
        """Run a paper trade simulation"""
        print(f"📊 Running paper trade simulation...")
        print(f"💰 Symbol: {symbol}")
        print(f"💵 Amount: ${amount}")
        
        # Simulate trade execution
        time.sleep(2)
        
        # Mock trade result
        trade_result = {
            "id": f"paper_trade_{int(time.time())}",
            "symbol": symbol,
            "amount": amount,
            "execution_price": 45000.0,
            "status": "executed",
            "timestamp": datetime.now().isoformat(),
            "profit_loss": 25.50
        }
        
        print(f"✅ Paper trade executed!")
        print(f"📈 Execution price: ${trade_result['execution_price']}")
        print(f"💰 P&L: ${trade_result['profit_loss']}")
        
        return trade_result
    
    def run_basic_backtest(self, symbol="BTC-USD"):
        """Run a basic backtest for learning"""
        print(f"🔬 Running basic backtest for learning...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        response = self.session.post(f"{self.api_url}/backtest", json={
            "symbol": symbol,
            "strategy": "SMA",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "initial_capital": 10000
        })
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Backtest completed!")
            print(f"📊 Total Return: {result['total_return']:.2%}")
            print(f"📈 Sharpe Ratio: {result['sharpe_ratio']:.2f}")
            print(f"📉 Max Drawdown: {result['max_drawdown']:.2%}")
            return result
        else:
            print(f"❌ Backtest failed: {response.text}")
            return None
    
    def get_progress_report(self):
        """Get learner progress report"""
        print("📊 Generating progress report...")
        
        progress = {
            "lessons_completed": 3,
            "paper_trades": 5,
            "backtests_run": 2,
            "current_streak": 7,
            "badges_earned": ["First Trade", "Backtest Master", "Consistent Learner"],
            "next_milestone": "Complete 10 paper trades to unlock Pro features"
        }
        
        print("🎯 Progress Report:")
        print(f"📚 Lessons completed: {progress['lessons_completed']}")
        print(f"📊 Paper trades: {progress['paper_trades']}")
        print(f"🔬 Backtests run: {progress['backtests_run']}")
        print(f"🔥 Current streak: {progress['current_streak']} days")
        print(f"🏆 Badges: {', '.join(progress['badges_earned'])}")
        print(f"🎯 Next milestone: {progress['next_milestone']}")
        
        return progress
    
    def run_full_demo(self):
        """Run complete learner demo workflow"""
        print("🚀 Starting Learner Demo Workflow")
        print("=" * 50)
        
        # 1. Sign up
        if not self.signup_learner("learner@demo.com", "demo123"):
            return
        
        # 2. Get AI tutor lesson
        lesson = self.get_ai_tutor_lesson("basics")
        time.sleep(1)
        
        # 3. Run paper trade
        trade = self.run_paper_trade("BTC-USD", 1000)
        time.sleep(1)
        
        # 4. Run backtest
        backtest = self.run_basic_backtest("BTC-USD")
        time.sleep(1)
        
        # 5. Get progress report
        progress = self.get_progress_report()
        
        print("\n" + "=" * 50)
        print("🎉 Learner Demo Completed!")
        print("📈 Ready to explore more features?")
        print("💡 Try upgrading to Pro for live trading!")

if __name__ == "__main__":
    demo = LearnerDemo()
    demo.run_full_demo()
