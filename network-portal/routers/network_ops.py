"""
Network operations API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import asyncio

from database import get_db, NetworkScan, Device
from mcp_servers.network_scanner import scan_network
from mcp_servers.ssh_manager import execute_ssh_command

router = APIRouter()

class ScanRequest(BaseModel):
    subnet: str
    scan_type: str = "discovery"  # discovery, port_scan

class ScanResponse(BaseModel):
    id: int
    scan_type: str
    subnet: str
    status: str
    started_at: datetime

    class Config:
        from_attributes = True

class SSHCommandRequest(BaseModel):
    device_id: int
    command: str
    username: str
    password: Optional[str] = None
    use_key: bool = False

@router.post("/scan", response_model=ScanResponse)
async def start_network_scan(
    scan_request: ScanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start a network scan"""
    # Create scan record
    scan = NetworkScan(
        scan_type=scan_request.scan_type,
        subnet=scan_request.subnet,
        status="running"
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # Run scan in background
    background_tasks.add_task(
        run_scan_task,
        scan.id,
        scan_request.subnet,
        scan_request.scan_type
    )

    return scan

async def run_scan_task(scan_id: int, subnet: str, scan_type: str):
    """Background task for network scanning"""
    from database import SessionLocal

    db = SessionLocal()
    try:
        # Perform scan
        results = await scan_network(subnet, scan_type)

        # Update scan record
        scan = db.query(NetworkScan).filter(NetworkScan.id == scan_id).first()
        if scan:
            scan.status = "completed"
            scan.results = results
            scan.completed_at = datetime.utcnow()

            # Auto-create devices from discovery
            if scan_type == "discovery" and results.get("hosts"):
                for host in results["hosts"]:
                    # Check if device already exists
                    existing = db.query(Device).filter(
                        Device.ip_address == host["ip"]
                    ).first()

                    if not existing:
                        device = Device(
                            name=f"Auto-discovered-{host['ip']}",
                            device_type="unknown",
                            ip_address=host["ip"],
                            mac_address=host.get("mac"),
                            vendor=host.get("vendor"),
                            status="online",
                            last_seen=datetime.utcnow(),
                            metadata={"discovered_by_scan": scan_id}
                        )
                        db.add(device)

            db.commit()
    except Exception as e:
        scan = db.query(NetworkScan).filter(NetworkScan.id == scan_id).first()
        if scan:
            scan.status = "failed"
            scan.results = {"error": str(e)}
            scan.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()

@router.get("/scans", response_model=List[ScanResponse])
async def list_scans(db: Session = Depends(get_db)):
    """List all network scans"""
    scans = db.query(NetworkScan).order_by(NetworkScan.started_at.desc()).limit(50).all()
    return scans

@router.get("/scans/{scan_id}")
async def get_scan_results(scan_id: int, db: Session = Depends(get_db)):
    """Get detailed scan results"""
    scan = db.query(NetworkScan).filter(NetworkScan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    return {
        "id": scan.id,
        "scan_type": scan.scan_type,
        "subnet": scan.subnet,
        "status": scan.status,
        "results": scan.results,
        "started_at": scan.started_at,
        "completed_at": scan.completed_at
    }

@router.post("/ssh/execute")
async def execute_ssh(command_request: SSHCommandRequest, db: Session = Depends(get_db)):
    """Execute SSH command on a device"""
    device = db.query(Device).filter(Device.id == command_request.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    try:
        result = await execute_ssh_command(
            host=device.ip_address,
            username=command_request.username,
            password=command_request.password,
            command=command_request.command,
            use_key=command_request.use_key
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
