from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from typing import Optional
import os

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


@router.get("/export")
async def export_report(product_id: str = Query(...), format: str = Query("csv", regex="^(csv|pdf|excel)$")):
    """
    Export product analysis report in CSV, PDF or Excel format.
    """
    try:
        # Check if product exists
        # Check if product exists (Try ID first, then Name fallback)
        p = supabase.table("products").select("name").eq("id", product_id).single().execute()
        
        if not p.data:
            # Fallback: Try finding by Name (case-insensitive)
            # This handles cases where frontend might send the Name as ID
            p = supabase.table("products").select("id, name").ilike("name", product_id).limit(1).execute()
            
            if p.data:
                # Found by name, correct the product_id to the real ID if needed, 
                # though report generation usually uses the ID passed to query reviews.
                # If reviews use the UUID, we need the UUID.
                real_id = p.data[0]['id']
                # If the passed product_id was a Name, we should probably use the Found UUID for review lookup
                product_id = real_id
            else:
                raise HTTPException(status_code=404, detail=f"Product not found: {product_id}")

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
