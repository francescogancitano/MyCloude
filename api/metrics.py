from fastapi import APIRouter, Depends, HTTPException, status
from lib.database import DatabaseManager, get_db
import json
from api.auth import get_current_user
from schemas import UserInDB

router = APIRouter()

@router.get("/metrics", tags=["Metrics"])
def get_system_metrics(
    current_user: UserInDB = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """provides the latest system metrics from the database via a stored procedure."""
    metrics_json_string = db.getSystemStatusInJson()

    if metrics_json_string:
        metrics_data = json.loads(metrics_json_string)
        return metrics_data

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no metrics found")