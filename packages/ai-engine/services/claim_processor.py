"""
Claim Processor Service

Handles AI-powered extraction, processing, and management of identity claims
from various data sources.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import structlog

from openai import AsyncOpenAI
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from ..core.database import get_prisma_client, Claim, ClaimType, ClaimCategory
from ..core.config import settings

logger = structlog.get_logger()

class SkillClaim(BaseModel):
    """Structured skill claim"""
    skill: str = Field(description="The skill name")
    proficiency_level: str = Field(description="Beginner, Intermediate, Advanced, Expert")
    years_experience: Optional[float] = Field(description="Years of experience")
    proof_sources: List[str] = Field(description="List of proof sources")
    confidence_score: float = Field(description="AI confidence score 0-1")

class ExperienceClaim(BaseModel):
    """Structured experience claim"""
    title: str = Field(description="Job title or role")
    company: str = Field(description="Company or organization")
    start_date: str = Field(description="Start date")
    end_date: Optional[str] = Field(description="End date if applicable")
    description: str = Field(description="Role description")
    achievements: List[str] = Field(description="Key achievements")
    skills_used: List[str] = Field(description="Skills used in this role")
    proof_sources: List[str] = Field(description="List of proof sources")

class ProjectClaim(BaseModel):
    """Structured project claim"""
    name: str = Field(description="Project name")
    description: str = Field(description="Project description")
    technologies: List[str] = Field(description="Technologies used")
    role: str = Field(description="Role in the project")
    impact: str = Field(description="Impact or results")
    proof_sources: List[str] = Field(description="List of proof sources")

class ClaimProcessor:
    """AI-powered claim processor"""
    
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.llm = OpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model_name=settings.AI_MODEL,
            temperature=0.1
        )
        self.initialized = False
        
    async def initialize(self):
        """Initialize the claim processor"""
        if self.initialized:
            return
            
        logger.info("Initializing Claim Processor")
        
        # Test OpenAI connection
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            logger.info("OpenAI connection successful")
        except Exception as e:
            logger.error("Failed to connect to OpenAI", error=str(e))
            raise
        
        self.initialized = True
        logger.info("Claim Processor initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up Claim Processor")
        # Close any open connections if needed
    
    async def extract_skills_from_github(self, github_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract skills from GitHub data"""
        try:
            # Analyze repositories and commits
            repos = github_data.get("repositories", [])
            commits = github_data.get("commits", [])
            
            skills_analysis = []
            
            for repo in repos:
                # Analyze repository for technologies
                languages = repo.get("languages", {})
                description = repo.get("description", "")
                topics = repo.get("topics", [])
                
                # Use AI to extract skills from repo data
                repo_skills = await self._analyze_repo_skills(
                    languages, description, topics, repo.get("name", "")
                )
                skills_analysis.extend(repo_skills)
            
            # Aggregate and deduplicate skills
            aggregated_skills = self._aggregate_skills(skills_analysis)
            
            # Convert to claim format
            claims = []
            for skill_data in aggregated_skills:
                claim = {
                    "type": ClaimType.SKILL,
                    "category": ClaimCategory.WORK,
                    "title": skill_data["skill"],
                    "description": f"Proficiency in {skill_data['skill']} demonstrated through GitHub contributions",
                    "content": {
                        "skill": skill_data["skill"],
                        "proficiency_level": skill_data["proficiency_level"],
                        "years_experience": skill_data.get("years_experience"),
                        "proof_sources": skill_data["proof_sources"],
                        "confidence_score": skill_data["confidence_score"]
                    },
                    "confidence": skill_data["confidence_score"],
                    "proofSources": skill_data["proof_sources"]
                }
                claims.append(claim)
            
            return claims
            
        except Exception as e:
            logger.error("Error extracting skills from GitHub", error=str(e))
            return []
    
    async def extract_experience_from_linkedin(self, linkedin_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract work experience from LinkedIn data"""
        try:
            positions = linkedin_data.get("positions", [])
            
            claims = []
            for position in positions:
                # Use AI to enhance and verify experience data
                enhanced_exp = await self._enhance_experience_data(position)
                
                claim = {
                    "type": ClaimType.EXPERIENCE,
                    "category": ClaimCategory.WORK,
                    "title": enhanced_exp["title"],
                    "description": enhanced_exp["description"],
                    "content": {
                        "title": enhanced_exp["title"],
                        "company": enhanced_exp["company"],
                        "start_date": enhanced_exp["start_date"],
                        "end_date": enhanced_exp.get("end_date"),
                        "description": enhanced_exp["description"],
                        "achievements": enhanced_exp["achievements"],
                        "skills_used": enhanced_exp["skills_used"],
                        "proof_sources": enhanced_exp["proof_sources"]
                    },
                    "confidence": enhanced_exp["confidence_score"],
                    "proofSources": enhanced_exp["proof_sources"]
                }
                claims.append(claim)
            
            return claims
            
        except Exception as e:
            logger.error("Error extracting experience from LinkedIn", error=str(e))
            return []
    
    async def extract_projects_from_data(self, data: Dict[str, Any], source_type: str) -> List[Dict[str, Any]]:
        """Extract project claims from various data sources"""
        try:
            projects = []
            
            if source_type == "github":
                repos = data.get("repositories", [])
                for repo in repos:
                    if repo.get("fork", False):  # Skip forked repositories
                        continue
                        
                    project = await self._analyze_github_project(repo)
                    if project:
                        projects.append(project)
            
            # Convert to claim format
            claims = []
            for project_data in projects:
                claim = {
                    "type": ClaimType.PROJECT,
                    "category": ClaimCategory.WORK,
                    "title": project_data["name"],
                    "description": project_data["description"],
                    "content": {
                        "name": project_data["name"],
                        "description": project_data["description"],
                        "technologies": project_data["technologies"],
                        "role": project_data["role"],
                        "impact": project_data["impact"],
                        "proof_sources": project_data["proof_sources"]
                    },
                    "confidence": project_data["confidence_score"],
                    "proofSources": project_data["proof_sources"]
                }
                claims.append(claim)
            
            return claims
            
        except Exception as e:
            logger.error("Error extracting projects", error=str(e))
            return []
    
    async def store_claims(self, user_id: str, claims: List[Dict[str, Any]], source_type: str):
        """Store claims in the database"""
        try:
            db = await get_prisma_client()
            
            stored_claims = []
            for claim_data in claims:
                # Create the claim
                claim = await db.claim.create(
                    data={
                        "userId": user_id,
                        "type": claim_data["type"],
                        "category": claim_data["category"],
                        "title": claim_data["title"],
                        "description": claim_data.get("description"),
                        "content": claim_data["content"],
                        "confidence": claim_data["confidence"],
                        "proofSources": claim_data.get("proofSources", []),
                        "isPublic": True,
                        "isArchived": False
                    }
                )
                stored_claims.append(claim)
            
            logger.info(f"Stored {len(stored_claims)} claims for user {user_id}")
            return stored_claims
            
        except Exception as e:
            logger.error("Error storing claims", error=str(e), user_id=user_id)
            raise
    
    async def generate_card(self, user_id: str, card_type: str, claim_ids: List[str], 
                          template: str = "default", settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate an identity card from selected claims"""
        try:
            db = await get_prisma_client()
            
            # Fetch claims
            claims = await db.claim.find_many(
                where={
                    "id": {"in": claim_ids},
                    "userId": user_id
                }
            )
            
            if not claims:
                raise ValueError("No claims found")
            
            # Generate card data
            card_data = await self._generate_card_content(claims, card_type, template)
            
            # Create card in database
            card = await db.identitycard.create(
                data={
                    "userId": user_id,
                    "type": card_type.upper(),
                    "title": card_data["title"],
                    "subtitle": card_data.get("subtitle"),
                    "template": template,
                    "layout": settings.get("layout") if settings else None,
                    "settings": settings,
                    "isPublic": True,
                    "shareSlug": self._generate_share_slug(user_id, card_type)
                }
            )
            
            # Link claims to card
            await db.identitycard.update(
                where={"id": card.id},
                data={
                    "claims": {
                        "connect": [{"id": claim_id} for claim_id in claim_ids]
                    }
                }
            )
            
            # Generate QR code
            qr_code_url = await self._generate_qr_code(card.shareSlug)
            
            return {
                "id": card.id,
                "share_url": f"/card/{card.shareSlug}",
                "qr_code_url": qr_code_url,
                "preview": card_data
            }
            
        except Exception as e:
            logger.error("Error generating card", error=str(e), user_id=user_id)
            raise
    
    async def extract_skills(self, text: str) -> List[str]:
        """Extract skills from text using AI"""
        try:
            prompt = PromptTemplate(
                input_variables=["text"],
                template="""
                Extract technical skills and programming languages from the following text.
                Return only the skill names as a JSON array.
                
                Text: {text}
                
                Skills:"""
            )
            
            chain = LLMChain(llm=self.llm, prompt=prompt)
            result = await chain.arun(text=text)
            
            # Parse JSON result
            try:
                skills = json.loads(result)
                return skills if isinstance(skills, list) else []
            except json.JSONDecodeError:
                # Fallback: extract skills manually
                return self._extract_skills_fallback(result)
                
        except Exception as e:
            logger.error("Error extracting skills from text", error=str(e))
            return []
    
    async def analyze_credibility(self, claim_data: Dict[str, Any]) -> float:
        """Analyze credibility of a claim using AI"""
        try:
            prompt = PromptTemplate(
                input_variables=["claim_data"],
                template="""
                Analyze the credibility of the following claim based on its proof sources and content.
                Return a confidence score between 0 and 1.
                
                Claim: {claim_data}
                
                Confidence Score:"""
            )
            
            chain = LLMChain(llm=self.llm, prompt=prompt)
            result = await chain.arun(claim_data=json.dumps(claim_data))
            
            # Parse confidence score
            try:
                confidence = float(result.strip())
                return max(0.0, min(1.0, confidence))
            except ValueError:
                return 0.5  # Default confidence
                
        except Exception as e:
            logger.error("Error analyzing credibility", error=str(e))
            return 0.5
    
    async def get_processing_stats(self) -> Dict[str, Any]:
        """Get AI processing statistics"""
        try:
            db = await get_prisma_client()
            
            # Get counts
            total_claims = await db.claim.count()
            total_cards = await db.identitycard.count()
            total_verifications = await db.verification.count()
            
            # Get recent activity
            recent_claims = await db.claim.count(
                where={
                    "createdAt": {
                        "gte": datetime.utcnow() - timedelta(days=7)
                    }
                }
            )
            
            return {
                "total_claims": total_claims,
                "total_cards": total_cards,
                "total_verifications": total_verifications,
                "recent_claims": recent_claims,
                "processing_success_rate": 0.95  # TODO: Calculate actual rate
            }
            
        except Exception as e:
            logger.error("Error getting processing stats", error=str(e))
            return {}
    
    # Private helper methods
    
    async def _analyze_repo_skills(self, languages: Dict[str, int], description: str, 
                                 topics: List[str], repo_name: str) -> List[Dict[str, Any]]:
        """Analyze repository to extract skills"""
        try:
            # Combine all text data
            text_data = f"Repository: {repo_name}\nDescription: {description}\nTopics: {', '.join(topics)}\nLanguages: {json.dumps(languages)}"
            
            prompt = f"""
            Analyze this GitHub repository data and extract technical skills with confidence levels.
            Return JSON array of skills with format:
            [{{"skill": "Python", "proficiency_level": "Advanced", "confidence_score": 0.9, "proof_sources": ["github_repo"]}}]
            
            Repository data:
            {text_data}
            """
            
            response = await self.openai_client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.1
            )
            
            result = response.choices[0].message.content
            skills = json.loads(result)
            
            return skills if isinstance(skills, list) else []
            
        except Exception as e:
            logger.error("Error analyzing repo skills", error=str(e))
            return []
    
    def _aggregate_skills(self, skills_analysis: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate and deduplicate skills"""
        skill_map = {}
        
        for skill_data in skills_analysis:
            skill_name = skill_data["skill"].lower()
            
            if skill_name not in skill_map:
                skill_map[skill_name] = skill_data
            else:
                # Merge with existing skill data
                existing = skill_map[skill_name]
                existing["confidence_score"] = max(existing["confidence_score"], skill_data["confidence_score"])
                existing["proof_sources"].extend(skill_data["proof_sources"])
        
        return list(skill_map.values())
    
    async def _enhance_experience_data(self, position: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance LinkedIn experience data using AI"""
        try:
            prompt = f"""
            Enhance this LinkedIn position data with more detailed information.
            Return enhanced data in JSON format.
            
            Position: {json.dumps(position)}
            """
            
            response = await self.openai_client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.1
            )
            
            result = response.choices[0].message.content
            enhanced = json.loads(result)
            
            return enhanced
            
        except Exception as e:
            logger.error("Error enhancing experience data", error=str(e))
            return position
    
    async def _analyze_github_project(self, repo: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze GitHub repository as a project"""
        try:
            if repo.get("fork", False):
                return None
            
            prompt = f"""
            Analyze this GitHub repository as a project and extract project information.
            Return project data in JSON format or null if not a significant project.
            
            Repository: {json.dumps(repo)}
            """
            
            response = await self.openai_client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.1
            )
            
            result = response.choices[0].message.content
            
            if result.lower() == "null":
                return None
            
            project_data = json.loads(result)
            return project_data
            
        except Exception as e:
            logger.error("Error analyzing GitHub project", error=str(e))
            return None
    
    async def _generate_card_content(self, claims: List[Claim], card_type: str, template: str) -> Dict[str, Any]:
        """Generate card content from claims"""
        try:
            # Group claims by type
            skills = [c for c in claims if c.type == ClaimType.SKILL]
            experiences = [c for c in claims if c.type == ClaimType.EXPERIENCE]
            projects = [c for c in claims if c.type == ClaimType.PROJECT]
            
            # Generate card title and subtitle
            title = f"{card_type.title()} Identity Card"
            subtitle = f"{len(claims)} verified claims"
            
            return {
                "title": title,
                "subtitle": subtitle,
                "skills": [c.content for c in skills],
                "experiences": [c.content for c in experiences],
                "projects": [c.content for c in projects],
                "template": template
            }
            
        except Exception as e:
            logger.error("Error generating card content", error=str(e))
            return {"title": "Identity Card", "subtitle": "Generated card"}
    
    def _generate_share_slug(self, user_id: str, card_type: str) -> str:
        """Generate a unique share slug for the card"""
        import hashlib
        import time
        
        # Create a unique slug based on user_id, card_type, and timestamp
        base = f"{user_id}-{card_type}-{int(time.time())}"
        hash_object = hashlib.md5(base.encode())
        return f"{card_type.lower()}-{hash_object.hexdigest()[:8]}"
    
    async def _generate_qr_code(self, share_slug: str) -> Optional[str]:
        """Generate QR code for card sharing"""
        try:
            import qrcode
            from io import BytesIO
            import base64
            
            # Create QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(f"https://identity.me/card/{share_slug}")
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            logger.error("Error generating QR code", error=str(e))
            return None
    
    def _extract_skills_fallback(self, text: str) -> List[str]:
        """Fallback method to extract skills from text"""
        # Simple keyword-based extraction
        skill_keywords = [
            "python", "javascript", "java", "c++", "c#", "go", "rust", "php", "ruby",
            "react", "vue", "angular", "node.js", "django", "flask", "spring",
            "docker", "kubernetes", "aws", "azure", "gcp", "sql", "mongodb",
            "redis", "elasticsearch", "machine learning", "ai", "data science"
        ]
        
        found_skills = []
        text_lower = text.lower()
        
        for skill in skill_keywords:
            if skill in text_lower:
                found_skills.append(skill.title())
        
        return found_skills
