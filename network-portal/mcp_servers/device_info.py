"""
MCP Server for Device Information
"""
import logging
from typing import Dict, Optional
from database import SessionLocal, Device, MonitoringMetric
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

async def get_device_info(device_id: int) -> Dict:
    """
    Get comprehensive information about a device

    Args:
        device_id: Database ID of the device

    Returns:
        Dict with device information
    """
    db = SessionLocal()
    try:
        device = db.query(Device).filter(Device.id == device_id).first()

        if not device:
            return {"error": f"Device {device_id} not found"}

        # Get recent metrics
        metrics = db.query(MonitoringMetric).filter(
            MonitoringMetric.device_id == device_id,
            MonitoringMetric.timestamp >= datetime.utcnow() - timedelta(hours=1)
        ).all()

        metric_summary = {}
        for metric in metrics:
            if metric.metric_type not in metric_summary:
                metric_summary[metric.metric_type] = []
            metric_summary[metric.metric_type].append({
                "name": metric.metric_name,
                "value": metric.value,
                "unit": metric.unit,
                "timestamp": metric.timestamp.isoformat()
            })

        return {
            "device": {
                "id": device.id,
                "name": device.name,
                "type": device.device_type,
                "ip_address": device.ip_address,
                "mac_address": device.mac_address,
                "vendor": device.vendor,
                "model": device.model,
                "location": device.location,
                "status": device.status,
                "last_seen": device.last_seen.isoformat() if device.last_seen else None,
                "metadata": device.metadata
            },
            "metrics": metric_summary,
            "metrics_count": len(metrics)
        }

    except Exception as e:
        logger.error(f"Error getting device info: {e}")
        return {"error": str(e)}
    finally:
        db.close()

async def get_all_devices() -> Dict:
    """
    Get list of all devices
    """
    db = SessionLocal()
    try:
        devices = db.query(Device).all()

        device_list = []
        for device in devices:
            device_list.append({
                "id": device.id,
                "name": device.name,
                "type": device.device_type,
                "ip_address": device.ip_address,
                "status": device.status,
                "last_seen": device.last_seen.isoformat() if device.last_seen else None
            })

        return {
            "total_devices": len(device_list),
            "devices": device_list
        }

    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        return {"error": str(e)}
    finally:
        db.close()

async def update_device_status(device_id: int, status: str) -> Dict:
    """
    Update device status
    """
    db = SessionLocal()
    try:
        device = db.query(Device).filter(Device.id == device_id).first()

        if not device:
            return {"error": f"Device {device_id} not found"}

        device.status = status
        if status == "online":
            device.last_seen = datetime.utcnow()

        db.commit()

        return {
            "device_id": device_id,
            "status": status,
            "updated": True
        }

    except Exception as e:
        logger.error(f"Error updating device status: {e}")
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

async def add_device_metric(
    device_id: int,
    metric_type: str,
    metric_name: str,
    value: str,
    unit: str = ""
) -> Dict:
    """
    Add a monitoring metric for a device
    """
    db = SessionLocal()
    try:
        metric = MonitoringMetric(
            device_id=device_id,
            metric_type=metric_type,
            metric_name=metric_name,
            value=value,
            unit=unit,
            timestamp=datetime.utcnow()
        )

        db.add(metric)
        db.commit()

        return {
            "device_id": device_id,
            "metric_added": True,
            "metric_type": metric_type
        }

    except Exception as e:
        logger.error(f"Error adding metric: {e}")
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()
