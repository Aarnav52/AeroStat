from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes, flights, index

app = FastAPI(title="Airfare Price Index API")

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development only, as requested
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "healthy"}

app.include_router(routes.router, prefix="/routes", tags=["Routes"])
app.include_router(flights.router, prefix="/flights", tags=["Flights"])
app.include_router(index.router, prefix="/index", tags=["Index"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
