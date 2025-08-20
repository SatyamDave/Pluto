"""
GitHub Processor Service

Handles GitHub API integration and data extraction for identity claims.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import structlog

import httpx
from github import Github
from github.Repository import Repository
from github.Commit import Commit

from ..core.config import settings
from ..core.database import get_prisma_client

logger = structlog.get_logger()

class GitHubProcessor:
    """GitHub data processor"""
    
    def __init__(self):
        self.github_client: Optional[Github] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize GitHub processor"""
        if self.initialized:
            return
            
        logger.info("Initializing GitHub Processor")
        
        # Initialize GitHub client
        if settings.GITHUB_ACCESS_TOKEN:
            self.github_client = Github(settings.GITHUB_ACCESS_TOKEN)
            logger.info("GitHub client initialized with access token")
        
        # Initialize HTTP client
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "AI-Identity-Platform/1.0.0"
            }
        )
        
        self.initialized = True
        logger.info("GitHub Processor initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up GitHub Processor")
        
        if self.http_client:
            await self.http_client.aclose()
    
    async def process_user_data(self, user_id: str, github_data: Dict[str, Any], 
                              metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Process GitHub user data and extract claims"""
        try:
            logger.info("Processing GitHub data for user", user_id=user_id)
            
            claims = []
            
            # Extract username from data or metadata
            username = github_data.get("username") or metadata.get("github_username")
            if not username:
                raise ValueError("GitHub username not provided")
            
            # Fetch user data
            user_data = await self._fetch_user_data(username)
            
            # Extract different types of claims
            skill_claims = await self._extract_skill_claims(user_data)
            project_claims = await self._extract_project_claims(user_data)
            contribution_claims = await self._extract_contribution_claims(user_data)
            
            claims.extend(skill_claims)
            claims.extend(project_claims)
            claims.extend(contribution_claims)
            
            # Store raw data
            await self._store_raw_data(user_id, "github", user_data, metadata)
            
            logger.info(f"Extracted {len(claims)} claims from GitHub data", user_id=user_id)
            return claims
            
        except Exception as e:
            logger.error("Error processing GitHub data", error=str(e), user_id=user_id)
            raise
    
    async def _fetch_user_data(self, username: str) -> Dict[str, Any]:
        """Fetch comprehensive user data from GitHub"""
        try:
            if not self.github_client:
                raise ValueError("GitHub client not initialized")
            
            user_data = {
                "username": username,
                "profile": {},
                "repositories": [],
                "commits": [],
                "contributions": {},
                "skills": {}
            }
            
            # Fetch user profile
            user = self.github_client.get_user(username)
            user_data["profile"] = {
                "login": user.login,
                "name": user.name,
                "bio": user.bio,
                "location": user.location,
                "company": user.company,
                "blog": user.blog,
                "public_repos": user.public_repos,
                "public_gists": user.public_gists,
                "followers": user.followers,
                "following": user.following,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            }
            
            # Fetch repositories
            repos = await self._fetch_user_repositories(user)
            user_data["repositories"] = repos
            
            # Fetch recent commits
            commits = await self._fetch_user_commits(user)
            user_data["commits"] = commits
            
            # Analyze contributions
            contributions = await self._analyze_contributions(user, repos, commits)
            user_data["contributions"] = contributions
            
            # Extract skills from repositories
            skills = await self._extract_skills_from_repos(repos)
            user_data["skills"] = skills
            
            return user_data
            
        except Exception as e:
            logger.error("Error fetching GitHub user data", error=str(e), username=username)
            raise
    
    async def _fetch_user_repositories(self, user) -> List[Dict[str, Any]]:
        """Fetch user repositories with detailed information"""
        try:
            repos = []
            
            # Get public repositories
            for repo in user.get_repos():
                repo_data = {
                    "id": repo.id,
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "url": repo.html_url,
                    "clone_url": repo.clone_url,
                    "language": repo.language,
                    "fork": repo.fork,
                    "size": repo.size,
                    "stargazers_count": repo.stargazers_count,
                    "watchers_count": repo.watchers_count,
                    "forks_count": repo.forks_count,
                    "open_issues_count": repo.open_issues_count,
                    "default_branch": repo.default_branch,
                    "created_at": repo.created_at.isoformat() if repo.created_at else None,
                    "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                    "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                    "topics": list(repo.get_topics()) if hasattr(repo, 'get_topics') else [],
                    "languages": {},
                    "contributors": [],
                    "commits": []
                }
                
                # Get languages
                try:
                    languages = repo.get_languages()
                    repo_data["languages"] = languages
                except Exception as e:
                    logger.warning("Could not fetch languages for repo", repo=repo.name, error=str(e))
                
                # Get contributors (limited to avoid rate limits)
                try:
                    contributors = list(repo.get_contributors()[:10])
                    repo_data["contributors"] = [
                        {
                            "login": c.login,
                            "contributions": c.contributions
                        }
                        for c in contributors
                    ]
                except Exception as e:
                    logger.warning("Could not fetch contributors for repo", repo=repo.name, error=str(e))
                
                # Get recent commits
                try:
                    commits = list(repo.get_commits()[:20])
                    repo_data["commits"] = [
                        {
                            "sha": c.sha,
                            "message": c.commit.message,
                            "author": c.commit.author.name if c.commit.author else None,
                            "date": c.commit.author.date.isoformat() if c.commit.author and c.commit.author.date else None
                        }
                        for c in commits
                    ]
                except Exception as e:
                    logger.warning("Could not fetch commits for repo", repo=repo.name, error=str(e))
                
                repos.append(repo_data)
                
                # Limit to avoid rate limits
                if len(repos) >= 50:
                    break
            
            return repos
            
        except Exception as e:
            logger.error("Error fetching user repositories", error=str(e))
            return []
    
    async def _fetch_user_commits(self, user) -> List[Dict[str, Any]]:
        """Fetch user commits across repositories"""
        try:
            commits = []
            
            # Get commits from user's repositories
            for repo in user.get_repos():
                try:
                    repo_commits = list(repo.get_commits(author=user.login)[:10])
                    for commit in repo_commits:
                        commit_data = {
                            "sha": commit.sha,
                            "repo": repo.name,
                            "message": commit.commit.message,
                            "author": commit.commit.author.name if commit.commit.author else None,
                            "date": commit.commit.author.date.isoformat() if commit.commit.author and commit.commit.author.date else None,
                            "url": commit.html_url
                        }
                        commits.append(commit_data)
                except Exception as e:
                    logger.warning("Could not fetch commits for repo", repo=repo.name, error=str(e))
                
                # Limit to avoid rate limits
                if len(commits) >= 100:
                    break
            
            return commits
            
        except Exception as e:
            logger.error("Error fetching user commits", error=str(e))
            return []
    
    async def _analyze_contributions(self, user, repos: List[Dict[str, Any]], 
                                   commits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze user contributions and activity"""
        try:
            analysis = {
                "total_repos": len(repos),
                "total_commits": len(commits),
                "languages_used": {},
                "contribution_timeline": {},
                "repo_types": {
                    "original": 0,
                    "forked": 0
                },
                "activity_score": 0
            }
            
            # Analyze languages
            for repo in repos:
                for lang, bytes_count in repo.get("languages", {}).items():
                    if lang in analysis["languages_used"]:
                        analysis["languages_used"][lang] += bytes_count
                    else:
                        analysis["languages_used"][lang] = bytes_count
                
                # Count repo types
                if repo.get("fork"):
                    analysis["repo_types"]["forked"] += 1
                else:
                    analysis["repo_types"]["original"] += 1
            
            # Analyze contribution timeline
            for commit in commits:
                date = commit.get("date", "")
                if date:
                    date_key = date[:7]  # YYYY-MM
                    if date_key in analysis["contribution_timeline"]:
                        analysis["contribution_timeline"][date_key] += 1
                    else:
                        analysis["contribution_timeline"][date_key] = 1
            
            # Calculate activity score
            total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)
            total_forks = sum(repo.get("forks_count", 0) for repo in repos)
            analysis["activity_score"] = (
                len(repos) * 10 +
                len(commits) * 5 +
                total_stars * 2 +
                total_forks * 3
            )
            
            return analysis
            
        except Exception as e:
            logger.error("Error analyzing contributions", error=str(e))
            return {}
    
    async def _extract_skills_from_repos(self, repos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract skills from repository data"""
        try:
            skills = {}
            
            for repo in repos:
                # Primary language
                primary_lang = repo.get("language")
                if primary_lang:
                    if primary_lang in skills:
                        skills[primary_lang]["count"] += 1
                        skills[primary_lang]["bytes"] += repo.get("languages", {}).get(primary_lang, 0)
                    else:
                        skills[primary_lang] = {
                            "count": 1,
                            "bytes": repo.get("languages", {}).get(primary_lang, 0),
                            "repos": [repo["name"]]
                        }
                
                # All languages
                for lang, bytes_count in repo.get("languages", {}).items():
                    if lang in skills:
                        skills[lang]["bytes"] += bytes_count
                        if repo["name"] not in skills[lang]["repos"]:
                            skills[lang]["repos"].append(repo["name"])
                    else:
                        skills[lang] = {
                            "count": 1,
                            "bytes": bytes_count,
                            "repos": [repo["name"]]
                        }
            
            return skills
            
        except Exception as e:
            logger.error("Error extracting skills from repos", error=str(e))
            return {}
    
    async def _extract_skill_claims(self, user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract skill claims from GitHub data"""
        try:
            claims = []
            skills = user_data.get("skills", {})
            
            for skill_name, skill_data in skills.items():
                # Calculate proficiency based on usage
                total_bytes = skill_data.get("bytes", 0)
                repo_count = skill_data.get("count", 0)
                
                # Determine proficiency level
                if total_bytes > 1000000 or repo_count > 5:
                    proficiency = "Expert"
                elif total_bytes > 100000 or repo_count > 2:
                    proficiency = "Advanced"
                elif total_bytes > 10000 or repo_count > 1:
                    proficiency = "Intermediate"
                else:
                    proficiency = "Beginner"
                
                # Calculate confidence score
                confidence = min(0.95, (total_bytes / 1000000) * 0.5 + (repo_count / 10) * 0.5)
                
                claim = {
                    "type": "SKILL",
                    "category": "WORK",
                    "title": f"{skill_name} Developer",
                    "description": f"Proficiency in {skill_name} demonstrated through {repo_count} repositories",
                    "content": {
                        "skill": skill_name,
                        "proficiency_level": proficiency,
                        "years_experience": None,  # Could be calculated from commit dates
                        "proof_sources": skill_data.get("repos", []),
                        "confidence_score": confidence,
                        "total_bytes": total_bytes,
                        "repo_count": repo_count
                    },
                    "confidence": confidence,
                    "proofSources": [f"github_repo:{repo}" for repo in skill_data.get("repos", [])]
                }
                
                claims.append(claim)
            
            return claims
            
        except Exception as e:
            logger.error("Error extracting skill claims", error=str(e))
            return []
    
    async def _extract_project_claims(self, user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract project claims from GitHub data"""
        try:
            claims = []
            repos = user_data.get("repositories", [])
            
            for repo in repos:
                # Skip forked repositories
                if repo.get("fork", False):
                    continue
                
                # Only include significant projects
                if (repo.get("stargazers_count", 0) > 0 or 
                    repo.get("forks_count", 0) > 0 or
                    repo.get("size", 0) > 1000):
                    
                    languages = list(repo.get("languages", {}).keys())
                    
                    claim = {
                        "type": "PROJECT",
                        "category": "WORK",
                        "title": repo["name"],
                        "description": repo.get("description", f"GitHub project: {repo['name']}"),
                        "content": {
                            "name": repo["name"],
                            "description": repo.get("description", ""),
                            "technologies": languages,
                            "role": "Developer",
                            "impact": f"Created project with {repo.get('stargazers_count', 0)} stars and {repo.get('forks_count', 0)} forks",
                            "proof_sources": [repo["url"]],
                            "confidence_score": 0.9
                        },
                        "confidence": 0.9,
                        "proofSources": [repo["url"]]
                    }
                    
                    claims.append(claim)
            
            return claims
            
        except Exception as e:
            logger.error("Error extracting project claims", error=str(e))
            return []
    
    async def _extract_contribution_claims(self, user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract contribution claims from GitHub data"""
        try:
            claims = []
            contributions = user_data.get("contributions", {})
            
            if contributions.get("total_repos", 0) > 0:
                claim = {
                    "type": "ACHIEVEMENT",
                    "category": "WORK",
                    "title": "Open Source Contributor",
                    "description": f"Active GitHub contributor with {contributions['total_repos']} repositories",
                    "content": {
                        "achievement": "Open Source Contributor",
                        "description": f"Maintains {contributions['total_repos']} repositories with {contributions['total_commits']} commits",
                        "metrics": {
                            "repositories": contributions["total_repos"],
                            "commits": contributions["total_commits"],
                            "languages": len(contributions.get("languages_used", {})),
                            "activity_score": contributions.get("activity_score", 0)
                        },
                        "proof_sources": [f"github_profile:{user_data['username']}"],
                        "confidence_score": 0.95
                    },
                    "confidence": 0.95,
                    "proofSources": [f"github_profile:{user_data['username']}"]
                }
                
                claims.append(claim)
            
            return claims
            
        except Exception as e:
            logger.error("Error extracting contribution claims", error=str(e))
            return []
    
    async def _store_raw_data(self, user_id: str, source_type: str, data: Dict[str, Any], 
                            metadata: Optional[Dict[str, Any]] = None):
        """Store raw GitHub data in database"""
        try:
            db = await get_prisma_client()
            
            # Store raw data
            await db.rawdata.create(
                data={
                    "dataSourceId": f"{user_id}_{source_type}",  # This should be the actual DataSource ID
                    "type": f"{source_type}_user_data",
                    "data": data,
                    "metadata": metadata or {},
                    "isProcessed": True,
                    "processedAt": datetime.utcnow()
                }
            )
            
            logger.info("Stored raw GitHub data", user_id=user_id)
            
        except Exception as e:
            logger.error("Error storing raw GitHub data", error=str(e), user_id=user_id)
            # Don't raise - this is not critical for the main flow
