from fastapi import APIRouter
from . import wallet

api_router = APIRouter()
api_router.include_router(wallet.router, prefix="/leaves-wallets", tags=["wallets"])
