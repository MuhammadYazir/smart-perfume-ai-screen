from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import base64
import json
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class PerfumePreferences(BaseModel):
    gender: str = "Any"
    time: str = "Any"
    season: str = "Any"
    occasion: str = "Any"
    scent: str = "Any"
    budget: str = "Any"

class PerfumeRecommendation(BaseModel):
    name: str
    match_percentage: int
    scent_notes: str
    description: str
    scent_family: str

class RecommendationResponse(BaseModel):
    recommendations: List[PerfumeRecommendation]

class ImageAnalysisRequest(BaseModel):
    image_base64: str
    preferences: Optional[PerfumePreferences] = None

class ImageAnalysisResponse(BaseModel):
    identified: bool
    name: str
    scent_notes: str
    description: str
    suitable_for: str
    matches_preferences: Optional[bool] = None
    match_explanation: Optional[str] = None

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Perfume Recommender API"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "perfume-recommender"}

@api_router.post("/recommend")
async def get_recommendations(preferences: PerfumePreferences):
    """Get AI-powered perfume recommendations based on user preferences"""
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured")
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"perfume-rec-{uuid.uuid4()}",
        system_message="""You are a world-renowned perfume expert and luxury fragrance consultant. 
Your recommendations are precise, sophisticated, and tailored to each customer's unique profile.
Always respond in valid JSON format."""
    ).with_model("openai", "gpt-4o")
    
    prompt = f"""Based on these preferences, recommend 2 perfect perfumes:

Customer Profile:
- Gender: {preferences.gender}
- Time of Use: {preferences.time}
- Season: {preferences.season}
- Occasion: {preferences.occasion}
- Preferred Scent: {preferences.scent}
- Budget: {preferences.budget}

Respond ONLY with valid JSON in this exact format:
{{
    "recommendations": [
        {{
            "name": "Perfume Name by Brand",
            "match_percentage": 95,
            "scent_notes": "Top: bergamot, pink pepper | Heart: rose, jasmine | Base: sandalwood, musk",
            "description": "A sophisticated description of the fragrance, its character, and why it perfectly matches the customer's preferences.",
            "scent_family": "floral"
        }},
        {{
            "name": "Second Perfume Name by Brand",
            "match_percentage": 88,
            "scent_notes": "Top: citrus, lavender | Heart: iris, violet | Base: vetiver, amber",
            "description": "A captivating description explaining the fragrance profile.",
            "scent_family": "woody"
        }}
    ]
}}"""
    
    try:
        response = await chat.send_message(UserMessage(text=prompt))
        # Parse JSON from response
        json_str = response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0]
        
        result = json.loads(json_str.strip())
        
        # Save to database
        doc = {
            "id": str(uuid.uuid4()),
            "preferences": preferences.model_dump(),
            "recommendations": result.get("recommendations", []),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await db.recommendations.insert_one(doc)
        
        return result
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/analyze-image")
async def analyze_perfume_image(request: ImageAnalysisRequest):
    """Analyze uploaded perfume image to identify the fragrance"""
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured")
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"perfume-analyze-{uuid.uuid4()}",
        system_message="""You are an expert perfume identifier. Analyze perfume bottle images to identify the fragrance.
Always respond in valid JSON format."""
    ).with_model("openai", "gpt-4o")
    
    pref_text = ""
    if request.preferences:
        pref_text = f"""
        
Also, the customer has these preferences:
- Gender: {request.preferences.gender}
- Time: {request.preferences.time}
- Season: {request.preferences.season}
- Occasion: {request.preferences.occasion}
- Preferred Scent: {request.preferences.scent}

Tell them if this perfume matches their preferences."""
    
    prompt = f"""Analyze this perfume bottle image. Identify:
1. The perfume name and brand
2. Its scent profile and notes
3. Typical occasions and seasons it suits{pref_text}

Respond ONLY with valid JSON:
{{
    "identified": true,
    "name": "Perfume Name by Brand",
    "scent_notes": "Top notes, heart notes, base notes",
    "description": "Description of the fragrance",
    "suitable_for": "Best suited occasions and times",
    "matches_preferences": true,
    "match_explanation": "Why it does/doesn't match the customer's preferences"
}}

If you cannot identify the perfume, set "identified": false and provide your best guess."""
    
    try:
        image_content = ImageContent(image_base64=request.image_base64)
        response = await chat.send_message(UserMessage(
            text=prompt,
            file_contents=[image_content]
        ))
        
        json_str = response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0]
        
        result = json.loads(json_str.strip())
        return result
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/history")
async def get_recommendation_history():
    """Get recent recommendation history"""
    history = await db.recommendations.find({}, {"_id": 0}).sort("timestamp", -1).limit(10).to_list(10)
    return {"history": history}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
