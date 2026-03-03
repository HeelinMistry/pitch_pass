from fastapi import FastAPI
from app.api import login, register

app = FastAPI(title="Scalable WebAuthn API")

# Include the routers
app.include_router(login.router, prefix="/api")
app.include_router(register.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "API is online. Go to /docs for Swagger UI"}

# To run: uvicorn app.main:app --reload