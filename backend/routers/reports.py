from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import FileResponse
from typing import Optional
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from services.report_service import report_service
from database import supabase

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("")
async def list_reports():
    """List available generated reports."""
    try:
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
        if not os.path.exists(reports_dir):
            return {"success": True, "data": []}
            
        files = []
        for f in os.listdir(reports_dir):
            if f.endswith(".pdf") or f.endswith(".xlsx") or f.endswith(".csv"):
                path = os.path.join(reports_dir, f)
                stats = os.stat(path)
                files.append({
                    "name": f,
                    "created_at": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                    "size": stats.st_size,
                    "type": f.split(".")[-1]
                })
        
        # Sort by newest first
        files.sort(key=lambda x: x["created_at"], reverse=True)
        return {"success": True, "data": files}
    except Exception as e:
        print(f"List reports error: {e}")
        return {"success": False, "data": []}

@router.get("/{filename}")
async def get_report_file(filename: str):
    """Download a specific report file."""
    try:
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
        filepath = os.path.join(reports_dir, filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Report not found")
            
        return FileResponse(filepath, filename=filename)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.api_route("/export", methods=["GET", "POST"])
async def export_report(product_id: str = Query(None), format: str = Query("csv", regex="^(csv|pdf|excel)$"), p_id: str = Body(None), fmt: str = Body(None)):
    """
    Export product analysis report in CSV, PDF or Excel format.
    Supports both GET (Query) and POST (Body) for maximum compatibility.
    """
    # Resolve parameters from Query or Body
    final_product_id = product_id or p_id
    final_format = format or fmt or "csv"

    if not final_product_id:
        raise HTTPException(status_code=400, detail="Missing product_id")

    # Use resolved variables
    product_id = final_product_id
    format = final_format
    try:
        # Check if product exists
        # Check if product exists (Try ID first, then Name fallback)
        logger.info(f"Exporting report for product_id: {product_id}")
        
        # Use limit(1) instead of single() to avoid exception on 0 rows
        p_resp = supabase.table("products").select("id, name").eq("id", product_id).limit(1).execute()
        
        real_id = None
        if p_resp.data:
             real_id = p_resp.data[0]['id']
        else:
            # Fallback: Try finding by Name (case-insensitive)
            logger.info(f"Product ID lookup failed, trying name fallback for: {product_id}")
            p_resp = supabase.table("products").select("id, name").ilike("name", product_id).limit(1).execute()
            if p_resp.data:
                real_id = p_resp.data[0]['id']
                logger.info(f"Found product by name: {real_id}")
            else:
                logger.warning(f"Product not found: {product_id}")
                raise HTTPException(status_code=404, detail=f"Product not found: {product_id}")
        
        product_id = real_id # Ensure we use the UUID for subsequent queries

        if format == "pdf":
            filepath = report_service.generate_pdf_report(product_id)
            media_type = "application/pdf"
            filename = f"report_{product_id}.pdf"
        elif format == "excel":
            filepath = report_service.generate_excel_report(product_id)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"report_{product_id}.xlsx"
        else:
            # Prepare data for generic CSV export
            # We fetch reviews joined with sentiment
            resp = supabase.table("reviews").select("*, sentiment_analysis(*)").eq("product_id", product_id).limit(1000).execute()
            data = {
                "statistics": {
                    "total_reviews": len(resp.data or []),
                    "average_rating": 0, # Placeholder if no rating field
                    "sentiment_score": 0 # Placeholder, calc handled in report service if needed
                },
                "recent_reviews": []
            }
            # flatten for CSV
            for r in (resp.data or []):
                sent = r.get("sentiment_analysis", [{}])
                label = sent[0].get("label") if sent else "NEUTRAL"
                data["recent_reviews"].append({
                    "created_at": r.get("created_at"),
                    "source": r.get("platform"),
                    "sentiment_label": label,
                    "content": r.get("content")
                })
            
            filepath = report_service.generate_report(data, format="csv")
            media_type = "text/csv"
            filename = f"report_{product_id}.csv"
            
        return FileResponse(filepath, media_type=media_type, filename=filename)

    except ImportError as e:
         raise HTTPException(status_code=501, detail=f"Export feature missing dependency: {e}")
    except Exception as e:
        print(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report")
