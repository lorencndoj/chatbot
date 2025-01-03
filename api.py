from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from chatbot import WebScraper, SearchResult
import asyncio

app = FastAPI(
    title="Search API",
    description="Advanced search API with comprehensive analysis",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize scraper lazily
scraper = None

async def get_scraper():
    global scraper
    if scraper is None:
        scraper = WebScraper()
    return scraper

class SearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10

class SearchResponse(BaseModel):
    title: str
    url: str
    summary: str
    key_points: List[str]
    statistics: List[str]
    expert_opinions: List[str]
    pros_cons: dict
    source_credibility: str
    related_topics: List[str]
    ranking_score: float

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Search API",
        "version": "1.0.0",
        "endpoints": [
            {"path": "/search", "method": "POST", "description": "Perform a search with analysis"}
        ]
    }

@app.post("/search", response_model=List[SearchResponse])
async def search(request: SearchRequest):
    try:
        # Get scraper instance
        search_scraper = await get_scraper()
        
        # Perform search
        results = await search_scraper.search_and_scrape(request.query, request.max_results)
        
        # Convert to response model
        response = []
        for result in results:
            response.append(SearchResponse(
                title=result.title,
                url=result.url,
                summary=result.summary,
                key_points=result.key_points,
                statistics=result.statistics,
                expert_opinions=result.expert_opinions,
                pros_cons=result.pros_cons,
                source_credibility=result.source_credibility,
                related_topics=result.related_topics,
                ranking_score=result.ranking_score
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    if scraper:
        await scraper.close()

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
