from fastapi import FastAPI
from app.api.v1 import auth
from app.api.v1 import duty
from app.api.v1 import plan
from app.api.v1 import user
from app.api.v1 import faculty
from app.api.v1 import cafedra
from app.api.v1 import hesabat
from app.api.v1 import activity
from app.api.v1 import assessment
from fastapi.middleware.cors import CORSMiddleware

from fastapi.staticfiles import StaticFiles


app = FastAPI(
    title="AZTU Plan Hesabat API",
    version="1.0.0",
    description="Backend for AZTU Plan Hesabat system."
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(faculty.router, prefix="/api", tags=["Faculty"])
app.include_router(cafedra.router, prefix="/api", tags=["Cafedra"])
app.include_router(duty.router, prefix="/api", tags=["Duty"])
app.include_router(activity.router, prefix="/api", tags=["Activity"])
app.include_router(assessment.router, prefix="/api", tags=["Assessment"])
app.include_router(plan.router, prefix="/api", tags=["Plan"])
app.include_router(user.router, prefix="/api", tags=["User"])
app.include_router(hesabat.router, prefix="/api", tags=["Hesabat"])