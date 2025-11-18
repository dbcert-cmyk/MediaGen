"""
Device management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from database import get_db, Device

router = APIRouter()

class DeviceCreate(BaseModel):
    name: str
    device_type: str
    ip_address: str
    mac_address: str = None
    vendor: str = None
    model: str = None
    location: str = None

class DeviceResponse(BaseModel):
    id: int
    name: str
    device_type: str
    ip_address: str
    mac_address: str = None
    vendor: str = None
    model: str = None
    location: str = None
    status: str
    last_seen: datetime = None
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[DeviceResponse])
async def list_devices(db: Session = Depends(get_db)):
    """List all devices"""
    devices = db.query(Device).all()
    return devices

@router.post("/", response_model=DeviceResponse)
async def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    """Add a new device"""
    db_device = Device(**device.dict())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device

@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: int, db: Session = Depends(get_db)):
    """Get device by ID"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

@router.delete("/{device_id}")
async def delete_device(device_id: int, db: Session = Depends(get_db)):
    """Delete a device"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    db.delete(device)
    db.commit()
    return {"message": "Device deleted successfully"}

@router.post("/{device_id}/ping")
async def ping_device(device_id: int, db: Session = Depends(get_db)):
    """Ping a device to check connectivity"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Use ping command
    import subprocess
    try:
        result = subprocess.run(
            ["ping", "-c", "3", device.ip_address],
            capture_output=True,
            text=True,
            timeout=5
        )
        is_online = result.returncode == 0

        # Update device status
        device.status = "online" if is_online else "offline"
        device.last_seen = datetime.utcnow() if is_online else device.last_seen
        db.commit()

        return {
            "device_id": device_id,
            "status": device.status,
            "output": result.stdout
        }
    except subprocess.TimeoutExpired:
        device.status = "offline"
        db.commit()
        return {
            "device_id": device_id,
            "status": "offline",
            "output": "Ping timeout"
        }
