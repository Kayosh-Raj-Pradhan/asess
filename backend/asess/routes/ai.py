from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import json
import base64
import re

from asess.core.database import SessionLocal
from asess.services.ml_service import eye_disease_model
from asess.models.scan import ScanResult
from asess.models.patient import Patient
from asess.schemas.scan import ScanRead, ScanUpdate

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ──────────────── Predict & Save ────────────────

@router.post("/predict")
async def predict_eye_disease(
    file: UploadFile = File(...),
    patient_name: str = Form("Unknown"),
    patient_id: str = Form(None),
    notes: str = Form(None),
    screened_by: str = Form(None),
    db: Session = Depends(get_db)
):
    if eye_disease_model is None:
        raise HTTPException(status_code=503, detail="AI model is currently unavailable")

    # Validate patient_id format: 3 letters + 3 numbers (e.g. ABC123)
    if patient_id:
        if not re.match(r'^[A-Za-z]{3}[0-9]{3}$', patient_id):
            raise HTTPException(
                status_code=400,
                detail="Patient ID must be 3 letters followed by 3 numbers (e.g. ABC123)"
            )
        # Check for duplicate patient_id with different name
        existing = db.query(Patient).filter(Patient.patient_id == patient_id.upper()).first()
        if existing and existing.patient_name.lower() != patient_name.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Patient ID {patient_id.upper()} is already assigned to '{existing.patient_name}'"
            )
        patient_id = patient_id.upper()  # Normalize to uppercase

    try:
        image_bytes = await file.read()
        result = eye_disease_model.predict(image_bytes)

        # Encode image to base64 for storage
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        # Save to database
        scan = ScanResult(
            patient_name=patient_name,
            patient_id=patient_id or f"UNK{int(datetime.utcnow().timestamp()) % 1000:03d}",
            prediction=result["prediction"],
            confidence=result["confidence"],
            all_probabilities=json.dumps(result["all_probabilities"]),
            notes=notes,
            screened_by=screened_by or "System",
            status="Pending Review",
            image_data=image_b64,
            scan_date=datetime.utcnow()
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)

        # Auto-create patient profile if not exists
        pid = scan.patient_id
        existing_patient = db.query(Patient).filter(Patient.patient_id == pid).first()
        if not existing_patient:
            new_patient = Patient(
                patient_id=pid,
                patient_name=patient_name,
                created_by=screened_by or "System"
            )
            db.add(new_patient)
            db.commit()

        return JSONResponse({
            "status": "success",
            "scan_id": scan.id,
            "prediction": result["prediction"],
            "confidence": result["confidence"],
            "all_probabilities": result["all_probabilities"]
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

# ──────────────── Get All Scans (History) ────────────────

@router.get("/scans")
def get_all_scans(db: Session = Depends(get_db)):
    scans = db.query(ScanResult).order_by(ScanResult.scan_date.desc()).all()
    results = []
    for s in scans:
        results.append({
            "id": s.id,
            "patient_name": s.patient_name,
            "patient_id": s.patient_id,
            "prediction": s.prediction,
            "confidence": s.confidence,
            "notes": s.notes,
            "screened_by": s.screened_by,
            "status": s.status,
            "scan_date": s.scan_date.isoformat() if s.scan_date else None,
        })
    return results

# ──────────────── Get Single Scan (Report) ────────────────

@router.get("/scans/{scan_id}")
def get_scan_by_id(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(ScanResult).filter(ScanResult.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    return {
        "id": scan.id,
        "patient_name": scan.patient_name,
        "patient_id": scan.patient_id,
        "prediction": scan.prediction,
        "confidence": scan.confidence,
        "all_probabilities": json.loads(scan.all_probabilities) if scan.all_probabilities else {},
        "notes": scan.notes,
        "screened_by": scan.screened_by,
        "status": scan.status,
        "image_data": scan.image_data,
        "scan_date": scan.scan_date.isoformat() if scan.scan_date else None,
    }

# ──────────────── Update Scan (status/notes) ────────────────

@router.put("/scans/{scan_id}")
def update_scan(scan_id: int, update: ScanUpdate, db: Session = Depends(get_db)):
    scan = db.query(ScanResult).filter(ScanResult.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if update.status is not None:
        scan.status = update.status
    if update.notes is not None:
        scan.notes = update.notes

    db.commit()
    db.refresh(scan)
    return {"detail": "Scan updated successfully"}

# ──────────────── Delete Scan ────────────────

@router.delete("/scans/{scan_id}")
def delete_scan(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(ScanResult).filter(ScanResult.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    db.delete(scan)
    db.commit()
    return {"detail": "Scan deleted successfully"}

# ──────────────── Analytics ────────────────

@router.get("/analytics")
def get_analytics(db: Session = Depends(get_db)):
    total_scans = db.query(func.count(ScanResult.id)).scalar() or 0

    abnormal_count = db.query(func.count(ScanResult.id)).filter(
        ScanResult.prediction != "Normal"
    ).scalar() or 0
    abnormal_pct = round((abnormal_count / total_scans * 100), 1) if total_scans > 0 else 0

    normal_count = total_scans - abnormal_count
    normal_pct = round((normal_count / total_scans * 100), 1) if total_scans > 0 else 0

    verified_count = db.query(func.count(ScanResult.id)).filter(
        ScanResult.status == "Verified"
    ).scalar() or 0
    pending_count = total_scans - verified_count

    avg_conf = db.query(func.avg(ScanResult.confidence)).scalar()
    avg_confidence = round(float(avg_conf), 1) if avg_conf else 0

    conditions = db.query(
        ScanResult.prediction, func.count(ScanResult.id)
    ).group_by(ScanResult.prediction).all()
    condition_dist = {row[0]: row[1] for row in conditions}

    screeners = db.query(
        ScanResult.screened_by, func.count(ScanResult.id)
    ).group_by(ScanResult.screened_by).order_by(
        func.count(ScanResult.id).desc()
    ).limit(5).all()
    top_screeners = {row[0]: row[1] for row in screeners if row[0]}

    daily_scans = {}
    for i in range(6, -1, -1):
        day = datetime.utcnow().date() - timedelta(days=i)
        count = db.query(func.count(ScanResult.id)).filter(
            func.date(ScanResult.scan_date) == day
        ).scalar() or 0
        daily_scans[day.strftime("%a")] = count

    return {
        "total_scans": total_scans,
        "abnormal_percentage": abnormal_pct,
        "normal_percentage": normal_pct,
        "verified_count": verified_count,
        "pending_count": pending_count,
        "avg_confidence": avg_confidence,
        "condition_distribution": condition_dist,
        "top_screeners": top_screeners,
        "daily_scans": daily_scans,
    }
