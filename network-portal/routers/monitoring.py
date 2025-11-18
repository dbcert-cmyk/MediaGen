"""
Monitoring and metrics API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import httpx
import os

from database import get_db, MonitoringMetric, Device

router = APIRouter()

class MetricResponse(BaseModel):
    device_id: int
    metric_type: str
    metric_name: str
    value: str
    unit: str
    timestamp: datetime

    class Config:
        from_attributes = True

@router.get("/metrics/{device_id}", response_model=List[MetricResponse])
async def get_device_metrics(
    device_id: int,
    metric_type: Optional[str] = None,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get metrics for a specific device"""
    since = datetime.utcnow() - timedelta(hours=hours)

    query = db.query(MonitoringMetric).filter(
        MonitoringMetric.device_id == device_id,
        MonitoringMetric.timestamp >= since
    )

    if metric_type:
        query = query.filter(MonitoringMetric.metric_type == metric_type)

    metrics = query.order_by(MonitoringMetric.timestamp.desc()).all()
    return metrics

@router.get("/netdata/metrics")
async def get_netdata_metrics():
    """Get metrics from Netdata"""
    netdata_url = "http://netdata:19999/api/v1/info"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(netdata_url, timeout=5.0)
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Netdata unavailable: {str(e)}")

@router.get("/librenms/devices")
async def get_librenms_devices():
    """Get devices from LibreNMS"""
    librenms_url = os.getenv("LIBRENMS_URL", "http://librenms:8000")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{librenms_url}/api/v0/devices",
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": "LibreNMS API error", "devices": []}
    except Exception as e:
        return {"error": str(e), "devices": []}

@router.get("/netbox/devices")
async def get_netbox_devices():
    """Get devices from Netbox"""
    netbox_url = os.getenv("NETBOX_URL", "http://netbox:8080")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{netbox_url}/api/dcim/devices/",
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": "Netbox API error", "results": []}
    except Exception as e:
        return {"error": str(e), "results": []}

@router.get("/dashboard/summary")
async def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get summary statistics for dashboard"""
    total_devices = db.query(Device).count()
    online_devices = db.query(Device).filter(Device.status == "online").count()
    offline_devices = db.query(Device).filter(Device.status == "offline").count()

    # Group devices by type
    device_types = db.query(Device.device_type).distinct().all()
    devices_by_type = {}
    for (dtype,) in device_types:
        if dtype:
            count = db.query(Device).filter(Device.device_type == dtype).count()
            devices_by_type[dtype] = count

    return {
        "total_devices": total_devices,
        "online_devices": online_devices,
        "offline_devices": offline_devices,
        "devices_by_type": devices_by_type,
        "timestamp": datetime.utcnow()
    }
