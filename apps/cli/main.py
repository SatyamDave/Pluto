#!/usr/bin/env python3
"""
AI Market Terminal CLI
Command-line interface for trading and backtesting
"""

import click
import requests
import json
import os
from datetime import datetime, timedelta
from typing import Optional
import sys

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
AUTH_TOKEN_FILE = os.path.expanduser("~/.ai-market-terminal/token")

class APIClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.token = self._load_token()
    
    def _load_token(self) -> Optional[str]:
        """Load authentication token from file"""
        try:
            os.makedirs(os.path.dirname(AUTH_TOKEN_FILE), exist_ok=True)
            if os.path.exists(AUTH_TOKEN_FILE):
                with open(AUTH_TOKEN_FILE, 'r') as f:
                    return f.read().strip()
        except Exception:
            pass
        return None
    
    def _save_token(self, token: str):
        """Save authentication token to file"""
        try:
            os.makedirs(os.path.dirname(AUTH_TOKEN_FILE), exist_ok=True)
            with open(AUTH_TOKEN_FILE, 'w') as f:
                f.write(token)
        except Exception as e:
            click.echo(f"Warning: Could not save token: {e}")
    
    def _get_headers(self):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def login(self, email: str, password: str) -> bool:
        """Login and save token"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={"email": email, "password": password},
                headers=self._get_headers()
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self._save_token(self.token)
                return True
            else:
                click.echo(f"Login failed: {response.text}")
                return False
        except Exception as e:
            click.echo(f"Login error: {e}")
            return False
    
    def signup(self, email: str, password: str) -> bool:
        """Sign up new user"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/signup",
                json={"email": email, "password": password},
                headers=self._get_headers()
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self._save_token(self.token)
                return True
            else:
                click.echo(f"Signup failed: {response.text}")
                return False
        except Exception as e:
            click.echo(f"Signup error: {e}")
            return False
    
    def get_profile(self):
        """Get user profile"""
        try:
            response = requests.get(
                f"{self.base_url}/user/profile",
                headers=self._get_headers()
            )
            if response.status_code == 200:
                return response.json()
            else:
                click.echo(f"Failed to get profile: {response.text}")
                return None
        except Exception as e:
            click.echo(f"Profile error: {e}")
            return None
    
    def create_backtest(self, symbol: str, strategy: str, start_date: str, end_date: str, initial_capital: float = 10000):
        """Create a new backtest"""
        try:
            response = requests.post(
                f"{self.base_url}/backtest",
                json={
                    "symbol": symbol,
                    "strategy": strategy,
                    "start_date": start_date,
                    "end_date": end_date,
                    "initial_capital": initial_capital
                },
                headers=self._get_headers()
            )
            if response.status_code == 200:
                return response.json()
            else:
                click.echo(f"Backtest creation failed: {response.text}")
                return None
        except Exception as e:
            click.echo(f"Backtest error: {e}")
            return None
    
    def get_backtest(self, backtest_id: str):
        """Get backtest results"""
        try:
            response = requests.get(
                f"{self.base_url}/backtest/{backtest_id}",
                headers=self._get_headers()
            )
            if response.status_code == 200:
                return response.json()
            else:
                click.echo(f"Failed to get backtest: {response.text}")
                return None
        except Exception as e:
            click.echo(f"Backtest error: {e}")
            return None
    
    def list_backtests(self):
        """List all backtests"""
        try:
            response = requests.get(
                f"{self.base_url}/backtests",
                headers=self._get_headers()
            )
            if response.status_code == 200:
                return response.json()
            else:
                click.echo(f"Failed to list backtests: {response.text}")
                return None
        except Exception as e:
            click.echo(f"List backtests error: {e}")
            return None

# CLI Commands
@click.group()
@click.version_option(version="0.9.0-beta")
def cli():
    """AI Market Terminal CLI - Command-line trading and backtesting"""
    pass

@cli.command()
@click.option('--email', prompt='Email', help='Your email address')
@click.option('--password', prompt='Password', hide_input=True, help='Your password')
def login(email, password):
    """Login to AI Market Terminal"""
    client = APIClient()
    if client.login(email, password):
        click.echo("✅ Login successful!")
        profile = client.get_profile()
        if profile:
            click.echo(f"Welcome, {profile['email']} (Tier: {profile['tier']})")
    else:
        click.echo("❌ Login failed")
        sys.exit(1)

@cli.command()
@click.option('--email', prompt='Email', help='Your email address')
@click.option('--password', prompt='Password', hide_input=True, help='Your password')
def signup(email, password):
    """Sign up for AI Market Terminal"""
    client = APIClient()
    if client.signup(email, password):
        click.echo("✅ Signup successful!")
        profile = client.get_profile()
        if profile:
            click.echo(f"Welcome, {profile['email']} (Tier: {profile['tier']})")
    else:
        click.echo("❌ Signup failed")
        sys.exit(1)

@cli.command()
def profile():
    """Show your profile information"""
    client = APIClient()
    profile = client.get_profile()
    if profile:
        click.echo("📊 Profile Information:")
        click.echo(f"  Email: {profile['email']}")
        click.echo(f"  Tier: {profile['tier']}")
        click.echo(f"  Status: {profile['subscription_status']}")
    else:
        click.echo("❌ Not logged in or failed to get profile")
        sys.exit(1)

@cli.command()
@click.option('--symbol', prompt='Symbol', help='Trading symbol (e.g., BTC-USD)')
@click.option('--strategy', prompt='Strategy', help='Strategy name (e.g., SMA, RSI)')
@click.option('--start-date', prompt='Start Date', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', prompt='End Date', help='End date (YYYY-MM-DD)')
@click.option('--capital', default=10000, help='Initial capital')
def backtest(symbol, strategy, start_date, end_date, capital):
    """Run a backtest"""
    client = APIClient()
    
    with click.progressbar(length=100, label='Running backtest...') as bar:
        bar.update(20)
        
        result = client.create_backtest(symbol, strategy, start_date, end_date, capital)
        bar.update(80)
        
        if result:
            click.echo("\n📈 Backtest Results:")
            click.echo(f"  ID: {result['id']}")
            click.echo(f"  Symbol: {result['symbol']}")
            click.echo(f"  Strategy: {result['strategy']}")
            click.echo(f"  Total Return: {result['total_return']:.2%}")
            click.echo(f"  Sharpe Ratio: {result['sharpe_ratio']:.2f}")
            click.echo(f"  Max Drawdown: {result['max_drawdown']:.2%}")
            click.echo(f"  Status: {result['status']}")
        else:
            click.echo("❌ Backtest failed")
            sys.exit(1)

@cli.command()
@click.option('--id', prompt='Backtest ID', help='Backtest ID to retrieve')
def get_backtest(id):
    """Get backtest results by ID"""
    client = APIClient()
    result = client.get_backtest(id)
    
    if result:
        click.echo("📈 Backtest Results:")
        click.echo(f"  ID: {result['id']}")
        click.echo(f"  Symbol: {result['symbol']}")
        click.echo(f"  Strategy: {result['strategy']}")
        click.echo(f"  Total Return: {result['total_return']:.2%}")
        click.echo(f"  Sharpe Ratio: {result['sharpe_ratio']:.2f}")
        click.echo(f"  Max Drawdown: {result['max_drawdown']:.2%}")
        click.echo(f"  Status: {result['status']}")
    else:
        click.echo("❌ Backtest not found")
        sys.exit(1)

@cli.command()
def list_backtests():
    """List all your backtests"""
    client = APIClient()
    backtests = client.list_backtests()
    
    if backtests:
        if not backtests:
            click.echo("No backtests found")
            return
        
        click.echo("📊 Your Backtests:")
        for bt in backtests:
            click.echo(f"  {bt['id']}: {bt['symbol']} - {bt['strategy']} ({bt['total_return']:.2%} return)")
    else:
        click.echo("❌ Failed to list backtests")
        sys.exit(1)

@cli.command()
def logout():
    """Logout and clear stored token"""
    try:
        if os.path.exists(AUTH_TOKEN_FILE):
            os.remove(AUTH_TOKEN_FILE)
            click.echo("✅ Logged out successfully")
        else:
            click.echo("ℹ️  No stored token found")
    except Exception as e:
        click.echo(f"❌ Logout error: {e}")
        sys.exit(1)

@cli.command()
def status():
    """Check API status"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            click.echo(f"✅ API Status: {data['status']}")
            click.echo(f"  Timestamp: {data['timestamp']}")
        else:
            click.echo("❌ API is not responding")
            sys.exit(1)
    except Exception as e:
        click.echo(f"❌ API connection error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    cli()
