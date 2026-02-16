from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import FileResponse
from typing import Optional
import os
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from services.report_service import report_service
from database import supabase

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("")
async def list_reports():
    """List available reports from Supabase persistence."""
    try:
        # Fetch from database instead of local filesystem
        resp = await asyncio.to_thread(lambda: supabase.table("reports").select("*").order("created_at", desc=True).limit(50).execute())
        
        reports_data = []
        for r in (resp.data or []):
            reports_data.append({
                "name": r.get("filename"),
                "filename": r.get("filename"), # For backward compatibility with frontend
                "created_at": r.get("created_at"),
                "size": r.get("size", 0),
                "type": r.get("type"),
                "storage_path": r.get("storage_path")
            })
            
        return {"success": True, "data": reports_data}
    except Exception as e:
        logger.error(f"List reports error: {e}")
        return {"success": False, "data": []}

@router.get("/{filename}")
async def get_report_file(filename: str):
    """Download a report, prioritizing local file then Supabase Storage."""
    try:
        reports_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports"))
        filepath = os.path.join(reports_dir, filename)
        
        # 1. Try local cache first (for immediate downloads)
        if os.path.exists(filepath):
             return FileResponse(filepath, filename=filename)
             
        # 2. Fallback to Supabase Storage if local file is purged (Render reset)
        logger.info(f"Local file {filename} not found, attempting Supabase Storage download.")
        
        # We need the storage path
        resp = await asyncio.to_thread(lambda: supabase.table("reports").select("storage_path").eq("filename", filename).limit(1).execute())
        if not resp.data:
            raise HTTPException(status_code=404, detail="Report record not found")
            
        storage_path = resp.data[0]['storage_path']
        
        # Option A: Proxy the download (more secure/private)
        try:
             # This depends on supabase-py storage implementation
             # For simplicity, we can get a public URL or sign it
             file_data = await asyncio.to_thread(supabase.storage.from_('reports').download, storage_path)
             
             # Save to local cache for future hits
             with open(filepath, 'wb') as f:
                 f.write(file_data)
                 
             return FileResponse(filepath, filename=filename)
        except Exception as se:
            logger.error(f"Supabase Storage download failed: {se}")
            raise HTTPException(status_code=404, detail="Report not found in storage")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get report file error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.api_route("/export", methods=["GET", "POST"])
async def export_report(product_id: str = Query(None), format: str = Query("csv", pattern="^(csv|pdf|excel)$"), p_id: str = Body(None), fmt: str = Body(None)):
    """
    Export product analysis report with persistent storage.
    """
    final_product_id = product_id or p_id
    final_format = format or fmt or "csv"

    if not final_product_id:
        logger.error("Export failed: Missing product_id")
        raise HTTPException(status_code=400, detail="Missing product_id")

    product_id = final_product_id
    format = final_format
    
    try:
        logger.info(f"Exporting report for product_id: {product_id} in {format} format")
        
        # 1. Validate Product
        try:
            p_resp = await asyncio.to_thread(lambda: supabase.table("products").select("id, name").eq("id", product_id).limit(1).execute())
        except Exception as db_err:
            logger.error(f"Database error during product lookup: {db_err}")
            raise HTTPException(status_code=500, detail="Database connection error")
        
        real_id = None
        if p_resp.data:
             real_id = p_resp.data[0]['id']
        else:
            # Fallback for name lookup
            p_resp = await asyncio.to_thread(lambda: supabase.table("products").select("id, name").ilike("name", product_id).limit(1).execute())
            if p_resp.data:
                real_id = p_resp.data[0]['id']
            else:
                raise HTTPException(status_code=404, detail=f"Product not found: {product_id}")
        
        product_id = real_id

        # 2. Generate and Persistence handled inside service
        if format == "pdf":
            filepath = await report_service.generate_pdf_report(product_id)
            media_type = "application/pdf"
        elif format == "excel":
            filepath = await report_service.generate_excel_report(product_id)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            # Fetch data for CSV
            resp = await asyncio.to_thread(lambda: supabase.table("reviews").select("*, sentiment_analysis(*)").eq("product_id", product_id).limit(1000).execute())
            data = {
                "recent_reviews": []
            }
            for r in (resp.data or []):
                sent = r.get("sentiment_analysis", [{}])
                label = sent[0].get("label") if sent else "NEUTRAL"
                data["recent_reviews"].append({
                    "created_at": r.get("created_at"),
                    "source": r.get("platform"),
                    "sentiment_label": label,
                    "content": r.get("content")
                })
            
            filepath = await report_service.generate_report(data, format="csv", product_id=product_id)
            media_type = "text/csv"
            
        filename = os.path.basename(filepath)
        return FileResponse(filepath, media_type=media_type, filename=filename)

    except ImportError as e:
         raise HTTPException(status_code=501, detail=f"Export feature missing dependency: {e}")
    except Exception as e:
        logger.exception(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report")
