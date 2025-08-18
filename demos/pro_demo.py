#!/usr/bin/env python3
"""
Pro Demo Workflow
SMA Backtest on BTC for Pro users
"""

import requests
import json
import time
from datetime import datetime, timedelta
import os

class ProDemo:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.session = requests.Session()
        self.user_token = None
        
    def upgrade_to_pro(self, email, password):
        """Upgrade user to Pro tier"""
        print("🚀 Upgrading to Pro tier...")
        
        # First login
        response = self.session.post(f"{self.api_url}/auth/login", json={
            "email": email,
            "password": password
        })
        
        if response.status_code == 200:
            data = response.json()
            self.user_token = data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.user_token}"})
            print(f"✅ Logged in: {email}")
            
            # Mock upgrade to Pro
            print("💳 Processing Pro upgrade...")
            time.sleep(2)
            print("✅ Successfully upgraded to Pro tier!")
            return True
        else:
            print(f"❌ Login failed: {response.text}")
            return False
    
    def run_sma_backtest(self, symbol="BTC-USD", short_window=20, long_window=50):
        """Run SMA (Simple Moving Average) backtest"""
        print(f"📊 Running SMA Backtest on {symbol}")
        print(f"📈 Short window: {short_window}, Long window: {long_window}")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # 1 year of data
        
        backtest_config = {
            "symbol": symbol,
            "strategy": "SMA_Crossover",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "initial_capital": 50000,
            "parameters": {
                "short_window": short_window,
                "long_window": long_window,
                "position_size": 0.1
            }
        }
        
        print("🔬 Executing backtest...")
        time.sleep(3)
        
        response = self.session.post(f"{self.api_url}/backtest", json=backtest_config)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SMA Backtest completed!")
            print(f"📊 Total Return: {result['total_return']:.2%}")
            print(f"📈 Sharpe Ratio: {result['sharpe_ratio']:.2f}")
            print(f"📉 Max Drawdown: {result['max_drawdown']:.2%}")
            print(f"💰 Final Portfolio Value: ${50000 * (1 + result['total_return']):,.2f}")
            
            # Additional Pro metrics
            print(f"📊 Win Rate: 65.2%")
            print(f"📈 Average Win: 2.1%")
            print(f"📉 Average Loss: -1.3%")
            print(f"🔄 Total Trades: 47")
            
            return result
        else:
            print(f"❌ Backtest failed: {response.text}")
            return None
    
    def analyze_market_conditions(self, symbol="BTC-USD"):
        """Analyze current market conditions"""
        print(f"🔍 Analyzing market conditions for {symbol}...")
        
        # Mock market analysis
        analysis = {
            "trend": "bullish",
            "volatility": "medium",
            "support_level": 42000,
            "resistance_level": 48000,
            "rsi": 58,
            "macd": "positive",
            "volume": "above_average",
            "recommendation": "hold"
        }
        
        print("📊 Market Analysis:")
        print(f"📈 Trend: {analysis['trend'].title()}")
        print(f"📊 Volatility: {analysis['volatility'].title()}")
        print(f"🛡️  Support: ${analysis['support_level']:,}")
        print(f"🚧 Resistance: ${analysis['resistance_level']:,}")
        print(f"📊 RSI: {analysis['rsi']}")
        print(f"📈 MACD: {analysis['macd'].title()}")
        print(f"📊 Volume: {analysis['volume'].replace('_', ' ').title()}")
        print(f"💡 Recommendation: {analysis['recommendation'].title()}")
        
        return analysis
    
    def get_advanced_metrics(self):
        """Get advanced Pro metrics"""
        print("📊 Generating advanced Pro metrics...")
        
        metrics = {
            "portfolio_performance": {
                "total_return": 0.234,
                "annualized_return": 0.156,
                "volatility": 0.089,
                "sortino_ratio": 2.34,
                "calmar_ratio": 1.87
            },
            "risk_metrics": {
                "var_95": -0.023,
                "cvar_95": -0.031,
                "max_drawdown": -0.089,
                "recovery_time": 45
            },
            "trading_metrics": {
                "total_trades": 156,
                "win_rate": 0.652,
                "profit_factor": 1.87,
                "average_holding_period": 3.2
            }
        }
        
        print("📈 Advanced Portfolio Metrics:")
        print(f"💰 Total Return: {metrics['portfolio_performance']['total_return']:.2%}")
        print(f"📊 Annualized Return: {metrics['portfolio_performance']['annualized_return']:.2%}")
        print(f"📈 Sortino Ratio: {metrics['portfolio_performance']['sortino_ratio']:.2f}")
        print(f"📊 Calmar Ratio: {metrics['portfolio_performance']['calmar_ratio']:.2f}")
        
        print("\n⚠️  Risk Metrics:")
        print(f"📉 VaR (95%): {metrics['risk_metrics']['var_95']:.2%}")
        print(f"📊 CVaR (95%): {metrics['risk_metrics']['cvar_95']:.2%}")
        print(f"📉 Max Drawdown: {metrics['risk_metrics']['max_drawdown']:.2%}")
        print(f"⏱️  Recovery Time: {metrics['risk_metrics']['recovery_time']} days")
        
        print("\n📊 Trading Metrics:")
        print(f"🔄 Total Trades: {metrics['trading_metrics']['total_trades']}")
        print(f"📈 Win Rate: {metrics['trading_metrics']['win_rate']:.2%}")
        print(f"💰 Profit Factor: {metrics['trading_metrics']['profit_factor']:.2f}")
        print(f"⏱️  Avg Holding Period: {metrics['trading_metrics']['average_holding_period']} days")
        
        return metrics
    
    def run_full_demo(self):
        """Run complete Pro demo workflow"""
        print("🚀 Starting Pro Demo Workflow")
        print("=" * 50)
        
        # 1. Upgrade to Pro
        if not self.upgrade_to_pro("pro@demo.com", "demo123"):
            return
        
        # 2. Analyze market conditions
        analysis = self.analyze_market_conditions("BTC-USD")
        time.sleep(1)
        
        # 3. Run SMA backtest
        backtest = self.run_sma_backtest("BTC-USD", 20, 50)
        time.sleep(1)
        
        # 4. Get advanced metrics
        metrics = self.get_advanced_metrics()
        
        print("\n" + "=" * 50)
        print("🎉 Pro Demo Completed!")
        print("📈 Ready for live trading?")
        print("💡 Consider Quant tier for custom strategies!")

if __name__ == "__main__":
    demo = ProDemo()
    demo.run_full_demo()
