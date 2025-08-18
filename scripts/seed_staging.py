#!/usr/bin/env python3
"""
Seed Data Script for AI Market Terminal Staging
Creates demo users and sample data for beta testing
"""

import requests
import json
import secrets
import string
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

class StagingSeeder:
    def __init__(self, api_url: str = "https://api.staging.aimarketterminal.com"):
        self.api_url = api_url
        self.session = requests.Session()
        self.admin_token = None
        
    def generate_password(self, length: int = 12) -> str:
        """Generate a secure random password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def login_admin(self) -> bool:
        """Login as admin user"""
        try:
            response = self.session.post(f"{self.api_url}/auth/login", json={
                "email": "admin@aimarketterminal.com",
                "password": "admin123"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                print("✅ Admin login successful")
                return True
            else:
                print(f"❌ Admin login failed: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Admin login error: {e}")
            return False
    
    def create_demo_user(self, email: str, tier: str, name: str = None) -> Dict[str, Any]:
        """Create a demo user with specified tier"""
        try:
            password = self.generate_password()
            
            # Create user
            user_data = {
                "email": email,
                "password": password,
                "tier": tier,
                "name": name or email.split('@')[0].title()
            }
            
            response = self.session.post(f"{self.api_url}/admin/users", json=user_data)
            
            if response.status_code == 200:
                user = response.json()
                print(f"✅ Created {tier} user: {email}")
                
                return {
                    "email": email,
                    "password": password,
                    "tier": tier,
                    "name": name,
                    "user_id": user.get("id")
                }
            else:
                print(f"❌ Failed to create user {email}: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error creating user {email}: {e}")
            return None
    
    def create_demo_backtest(self, user_id: str, symbol: str, strategy: str) -> Dict[str, Any]:
        """Create a demo backtest for a user"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            backtest_data = {
                "user_id": user_id,
                "symbol": symbol,
                "strategy": strategy,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "initial_capital": 10000,
                "total_return": 0.15 + (secrets.randbelow(20) - 10) / 100,  # Random return between 5-25%
                "sharpe_ratio": 1.0 + secrets.randbelow(20) / 10,  # Random Sharpe between 1.0-3.0
                "max_drawdown": -0.05 - secrets.randbelow(10) / 100,  # Random drawdown between -5% to -15%
                "status": "completed",
                "parameters": {
                    "short_window": 20,
                    "long_window": 50,
                    "position_size": 0.1
                },
                "results": {
                    "total_trades": secrets.randbelow(50) + 10,
                    "win_rate": 0.5 + secrets.randbelow(30) / 100,
                    "avg_holding_period": secrets.randbelow(10) + 1
                }
            }
            
            response = self.session.post(f"{self.api_url}/admin/backtests", json=backtest_data)
            
            if response.status_code == 200:
                backtest = response.json()
                print(f"✅ Created backtest for {symbol} with {strategy}")
                return backtest
            else:
                print(f"❌ Failed to create backtest: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error creating backtest: {e}")
            return None
    
    def create_demo_trades(self, user_id: str, backtest_id: str, symbol: str) -> List[Dict[str, Any]]:
        """Create demo trades for a backtest"""
        try:
            trades = []
            base_price = 150.0 if symbol == "AAPL" else 45000.0 if symbol == "BTC-USD" else 3000.0
            
            for i in range(10):
                # Random trade data
                side = "buy" if i % 2 == 0 else "sell"
                quantity = secrets.randbelow(100) + 1
                price = base_price + (secrets.randbelow(100) - 50)
                timestamp = datetime.now() - timedelta(days=secrets.randbelow(365))
                
                trade_data = {
                    "user_id": user_id,
                    "backtest_id": backtest_id,
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "price": price,
                    "timestamp": timestamp.isoformat(),
                    "trade_type": "paper",
                    "status": "executed"
                }
                
                response = self.session.post(f"{self.api_url}/admin/trades", json=trade_data)
                
                if response.status_code == 200:
                    trades.append(response.json())
                else:
                    print(f"❌ Failed to create trade: {response.text}")
            
            print(f"✅ Created {len(trades)} demo trades")
            return trades
        except Exception as e:
            print(f"❌ Error creating trades: {e}")
            return []
    
    def create_sample_strategies(self) -> List[Dict[str, Any]]:
        """Create sample strategies for the marketplace"""
        try:
            strategies = [
                {
                    "name": "Simple Moving Average Crossover",
                    "description": "Buy when short SMA crosses above long SMA, sell when it crosses below",
                    "category": "trend_following",
                    "difficulty": "beginner",
                    "parameters": {
                        "short_window": {"type": "int", "default": 20, "min": 5, "max": 50},
                        "long_window": {"type": "int", "default": 50, "min": 20, "max": 200},
                        "position_size": {"type": "float", "default": 0.1, "min": 0.01, "max": 1.0}
                    },
                    "code": "def sma_crossover(data, short_window=20, long_window=50, position_size=0.1):\n    # Strategy implementation\n    pass",
                    "tags": ["SMA", "crossover", "trend"]
                },
                {
                    "name": "RSI Mean Reversion",
                    "description": "Buy when RSI is oversold, sell when overbought",
                    "category": "mean_reversion",
                    "difficulty": "intermediate",
                    "parameters": {
                        "rsi_period": {"type": "int", "default": 14, "min": 5, "max": 30},
                        "oversold": {"type": "int", "default": 30, "min": 10, "max": 40},
                        "overbought": {"type": "int", "default": 70, "min": 60, "max": 90}
                    },
                    "code": "def rsi_mean_reversion(data, rsi_period=14, oversold=30, overbought=70):\n    # Strategy implementation\n    pass",
                    "tags": ["RSI", "mean_reversion", "oscillator"]
                },
                {
                    "name": "Momentum Breakout",
                    "description": "Buy on price breakouts with high volume confirmation",
                    "category": "momentum",
                    "difficulty": "advanced",
                    "parameters": {
                        "lookback_period": {"type": "int", "default": 20, "min": 5, "max": 50},
                        "volume_multiplier": {"type": "float", "default": 1.5, "min": 1.0, "max": 3.0},
                        "stop_loss": {"type": "float", "default": 0.05, "min": 0.01, "max": 0.20}
                    },
                    "code": "def momentum_breakout(data, lookback_period=20, volume_multiplier=1.5, stop_loss=0.05):\n    # Strategy implementation\n    pass",
                    "tags": ["momentum", "breakout", "volume"]
                }
            ]
            
            created_strategies = []
            for strategy in strategies:
                response = self.session.post(f"{self.api_url}/admin/strategies", json=strategy)
                
                if response.status_code == 200:
                    created_strategies.append(response.json())
                    print(f"✅ Created strategy: {strategy['name']}")
                else:
                    print(f"❌ Failed to create strategy {strategy['name']}: {response.text}")
            
            return created_strategies
        except Exception as e:
            print(f"❌ Error creating strategies: {e}")
            return []
    
    def generate_invite_links(self, users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate single-use invite links for demo users"""
        try:
            invite_links = []
            
            for user in users:
                if user and user.get("user_id"):
                    invite_data = {
                        "user_id": user["user_id"],
                        "email": user["email"],
                        "tier": user["tier"],
                        "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
                        "single_use": True
                    }
                    
                    response = self.session.post(f"{self.api_url}/admin/invites", json=invite_data)
                    
                    if response.status_code == 200:
                        invite = response.json()
                        invite_links.append({
                            "email": user["email"],
                            "tier": user["tier"],
                            "invite_url": f"{self.api_url.replace('/api', '')}/invite/{invite['code']}",
                            "expires_at": invite["expires_at"]
                        })
                        print(f"✅ Generated invite link for {user['email']}")
                    else:
                        print(f"❌ Failed to generate invite for {user['email']}: {response.text}")
            
            return invite_links
        except Exception as e:
            print(f"❌ Error generating invite links: {e}")
            return []
    
    def run_seeding(self) -> Dict[str, Any]:
        """Run the complete seeding process"""
        print("🌱 Starting AI Market Terminal Staging Seeding")
        print("=" * 50)
        
        # Login as admin
        if not self.login_admin():
            return {"success": False, "error": "Admin login failed"}
        
        # Create demo users
        demo_users = [
            {"email": "learner@test.aimarketterminal.com", "tier": "learner", "name": "Demo Learner"},
            {"email": "pro@test.aimarketterminal.com", "tier": "pro", "name": "Demo Pro"},
            {"email": "quant@test.aimarketterminal.com", "tier": "quant", "name": "Demo Quant"},
            {"email": "enterprise-admin@test.aimarketterminal.com", "tier": "enterprise", "name": "Demo Enterprise Admin"}
        ]
        
        created_users = []
        for user_data in demo_users:
            user = self.create_demo_user(user_data["email"], user_data["tier"], user_data["name"])
            if user:
                created_users.append(user)
        
        # Create demo backtests
        backtests = []
        for user in created_users:
            if user.get("user_id"):
                # Create AAPL backtest
                aapl_backtest = self.create_demo_backtest(user["user_id"], "AAPL", "SMA")
                if aapl_backtest:
                    backtests.append(aapl_backtest)
                    self.create_demo_trades(user["user_id"], aapl_backtest["id"], "AAPL")
                
                # Create BTC backtest for Pro+ users
                if user["tier"] in ["pro", "quant", "enterprise"]:
                    btc_backtest = self.create_demo_backtest(user["user_id"], "BTC-USD", "RSI")
                    if btc_backtest:
                        backtests.append(btc_backtest)
                        self.create_demo_trades(user["user_id"], btc_backtest["id"], "BTC-USD")
        
        # Create sample strategies
        strategies = self.create_sample_strategies()
        
        # Generate invite links
        invite_links = self.generate_invite_links(created_users)
        
        # Generate credentials table
        credentials_table = self.generate_credentials_table(created_users)
        
        # Save results
        results = {
            "success": True,
            "users_created": len(created_users),
            "backtests_created": len(backtests),
            "strategies_created": len(strategies),
            "invite_links": len(invite_links),
            "credentials_table": credentials_table,
            "invite_links": invite_links
        }
        
        print("\n" + "=" * 50)
        print("🎉 Seeding completed successfully!")
        print(f"✅ Created {len(created_users)} demo users")
        print(f"✅ Created {len(backtests)} demo backtests")
        print(f"✅ Created {len(strategies)} sample strategies")
        print(f"✅ Generated {len(invite_links)} invite links")
        
        return results
    
    def generate_credentials_table(self, users: List[Dict[str, Any]]) -> str:
        """Generate a markdown table with user credentials"""
        table = "| Email | Password | Tier | Name |\n"
        table += "|-------|----------|------|------|\n"
        
        for user in users:
            if user:
                table += f"| {user['email']} | {user['password']} | {user['tier']} | {user['name']} |\n"
        
        return table
    
    def save_results(self, results: Dict[str, Any]):
        """Save seeding results to files"""
        try:
            # Save credentials to console (for 1Password)
            print("\n🔐 DEMO USER CREDENTIALS")
            print("=" * 30)
            print("IMPORTANT: Store these credentials securely in 1Password!")
            print("Never commit these to version control.")
            print("\n" + results["credentials_table"])
            
            # Save invite links
            with open("docs/BETA_TESTERS.md", "w") as f:
                f.write("# Beta Tester Accounts\n\n")
                f.write("## Demo Users\n\n")
                f.write("The following demo accounts have been created for beta testing:\n\n")
                f.write(results["credentials_table"])
                f.write("\n## Invite Links\n\n")
                f.write("Single-use invite links for beta testers:\n\n")
                for invite in results["invite_links"]:
                    f.write(f"- **{invite['email']}** ({invite['tier']}): {invite['invite_url']}\n")
                    f.write(f"  - Expires: {invite['expires_at']}\n\n")
                f.write("\n## Security Notice\n\n")
                f.write("⚠️ **IMPORTANT**: These credentials are for staging/testing only.\n")
                f.write("Do not use these accounts in production.\n")
                f.write("Store the actual passwords securely in 1Password.\n")
            
            print(f"\n📄 Results saved to docs/BETA_TESTERS.md")
            
        except Exception as e:
            print(f"❌ Error saving results: {e}")

def main():
    seeder = StagingSeeder()
    results = seeder.run_seeding()
    
    if results["success"]:
        seeder.save_results(results)
        print("\n🎯 Next Steps:")
        print("1. Store credentials in 1Password")
        print("2. Share invite links with beta testers")
        print("3. Monitor usage in Grafana dashboard")
        print("4. Collect feedback via GitHub Issues")
    else:
        print(f"\n❌ Seeding failed: {results.get('error', 'Unknown error')}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
