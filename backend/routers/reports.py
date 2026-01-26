from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from typing import Optional
import os

from services.report_service import report_service
from database import supabase

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/export")
async def export_report(product_id: str = Query(...), format: str = Query("csv", regex="^(csv|pdf|excel)$")):
    """
    Export product analysis report in CSV, PDF or Excel format.
    """
    try:
        # Check if product exists
        p = supabase.table("products").select("name").eq("id", product_id).single().execute()
        if not p.data:
            raise HTTPException(status_code=404, detail="Product not found")

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
