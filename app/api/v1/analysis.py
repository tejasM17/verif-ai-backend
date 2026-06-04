import asyncio
import logging
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from app.core.firebase import require_student, verify_firebase_token, get_firestore
from app.models.document import Document
from app.schemas.analysis import AnalysisStartRequest, AnalysisStartResponse
from app.services.streaming import stream_graph_events
from app.services.graph.graph_builder import get_app
from firebase_admin import auth
from beanie import PydanticObjectId

router = APIRouter()
logger = logging.getLogger(__name__)

async def run_graph_and_save(job_id: str, initial_state: dict):
    """
    Background task to run the graph and update job status.
    """
    db = get_firestore()
    try:
        app = get_app()
        # Run graph to completion
        await app.ainvoke(initial_state)
        
        await db.collection("jobs").document(job_id).update({
            "status": "completed",
            "completed_at": datetime.utcnow()
        })
    except Exception as e:
        logger.error(f"Background analysis failed for job {job_id}: {str(e)}")
        try:
            await db.collection("jobs").document(job_id).update({
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.utcnow()
            })
        except:
            pass

@router.post("/start", response_model=AnalysisStartResponse, status_code=202)
async def start_analysis(
    req: AnalysisStartRequest,
    user: dict = Depends(require_student)
):
    """
    Starts the verification analysis process.
    """
    if user["uid"] != req.student_uid:
        raise HTTPException(status_code=403, detail="Can only start analysis for your own account")

    # Validate documents using Beanie
    try:
        resume_doc = await Document.find_one(
            Document.id == PydanticObjectId(req.resume_document_id), 
            Document.firebase_uid == user["uid"]
        )
    except:
        raise HTTPException(status_code=400, detail="Invalid resume document ID")

    if not resume_doc:
        raise HTTPException(status_code=404, detail="Resume document not found")
        
    for doc_id in req.cert_doc_ids:
        try:
            cert_doc = await Document.find_one(
                Document.id == PydanticObjectId(doc_id), 
                Document.firebase_uid == user["uid"]
            )
        except:
            raise HTTPException(status_code=400, detail=f"Invalid certificate document ID: {doc_id}")
            
        if not cert_doc:
            raise HTTPException(status_code=404, detail=f"Certificate document {doc_id} not found")

    # Update status to analyzing
    doc_ids = [PydanticObjectId(req.resume_document_id)] + [PydanticObjectId(d) for d in req.cert_doc_ids]
    await Document.find({"_id": {"$in": doc_ids}}).update({"$set": {"status": "analyzing"}})

    # Create job in Firestore
    job_id = str(uuid.uuid4())
    db = get_firestore()
    await db.collection("jobs").document(job_id).set({
        "job_id": job_id,
        "student_uid": user["uid"],
        "status": "analyzing",
        "resume_id": req.resume_document_id,
        "cert_ids": req.cert_doc_ids,
        "github_url": req.github_url,
        "created_at": datetime.utcnow()
    })

    initial_state = {
        "student_uid": user["uid"],
        "resume_doc_id": req.resume_document_id,
        "cert_doc_ids": req.cert_doc_ids,
        "github_url": req.github_url,
        "completed_agents": [],
        "research_logs": [],
        "flags": []
    }

    asyncio.create_task(run_graph_and_save(job_id, initial_state))

    return {
        "job_id": job_id,
        "websocket_url": f"/api/v1/analysis/stream/{job_id}"
    }

@router.websocket("/stream/{job_id}")
async def stream_analysis(websocket: WebSocket, job_id: str, token: str = Query(...)):
    """
    WebSocket endpoint to stream analysis progress.
    """
    await websocket.accept()
    
    try:
        # Verify token
        user = auth.verify_id_token(token)
        
        db = get_firestore()
        job_doc = await db.collection("jobs").document(job_id).get()
        if not job_doc.exists:
            await websocket.send_json({"type": "error", "data": {"message": "Job not found"}})
            await websocket.close()
            return
            
        job_data = job_doc.to_dict()
        if job_data["student_uid"] != user["uid"] and user.get("role") != "recruiter":
            await websocket.send_json({"type": "error", "data": {"message": "Forbidden"}})
            await websocket.close()
            return

        initial_state = {
            "student_uid": job_data["student_uid"],
            "resume_doc_id": job_data["resume_id"],
            "cert_doc_ids": job_data["cert_ids"],
            "github_url": job_data["github_url"],
            "completed_agents": [],
            "research_logs": [],
            "flags": []
        }

        async for event in stream_graph_events(initial_state):
            await websocket.send_json(event)
            if event["type"] in ["analysis_complete", "error"]:
                break
        
        await websocket.close()

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {str(e)}")
        try:
            await websocket.send_json({"type": "error", "data": {"message": str(e)}})
            await websocket.close()
        except:
            pass

@router.get("/result/{student_uid}")
async def get_analysis_result(student_uid: str, user: dict = Depends(verify_firebase_token)):
    """
    Fetch latest verification result for a student.
    """
    if user["uid"] != student_uid and user.get("role") != "recruiter":
        raise HTTPException(status_code=403, detail="Forbidden")

    db = get_firestore()
    verif_query = db.collection("verifications").where("student_uid", "==", student_uid).order_by("created_at", direction="DESCENDING").limit(1)
    docs = await verif_query.get()
    
    if not docs:
        raise HTTPException(status_code=404, detail="No verification result found for this student")
    
    verif_data = docs[0].to_dict()
    
    # Also fetch individual agent results
    results_query = db.collection("ai_results").where("student_uid", "==", student_uid).order_by("created_at", direction="DESCENDING").limit(3)
    results_docs = await results_query.get()
    
    agent_results = [d.to_dict() for d in results_docs]
    
    return {
        "success": True,
        "data": {
            "verification": verif_data,
            "agent_results": agent_results
        }
    }
