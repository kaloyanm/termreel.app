from fastapi import APIRouter

from app.flavours import load_flavours
from app.schemas import FlavourRead

router = APIRouter(prefix="/api/flavours", tags=["flavours"])


@router.get("", response_model=list[FlavourRead])
def list_flavours():
    return [FlavourRead(**f) for f in load_flavours()]
