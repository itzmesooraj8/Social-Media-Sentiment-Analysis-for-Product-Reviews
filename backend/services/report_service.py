import os
from typing import List, Dict, Any
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from database import supabase
import pandas as pd
import io

class ReportService:
    def __init__(self):
        pass

    async def generate_report(self, report_type: str, file_format: str = "pdf") -> Dict[str, Any]:
        """
        Generate a report of the given type and format.
        Returns: { "filename": str, "content": bytes, "content_type": str }
        """
        # Fetch Real Data
        data = await self._fetch_data(report_type)
        
        filename = f"{report_type}_report_{datetime.now().strftime('%Y%m%d')}"
        
        if file_format.lower() == "excel":
            content = self._create_excel(data)
            return {
                "filename": f"{filename}.xlsx",
                "content": content,
                "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
        else:
            content = self._create_pdf(data, report_type)
            return {
                "filename": f"{filename}.pdf",
                "content": content,
                "content_type": "application/pdf"
            }

    async def _fetch_data(self, report_type: str):
        """Fetch data from Supabase"""
        if report_type == "sentiment":
            # Get reviews + sentiment
            res = supabase.table("reviews").select("*, sentiment_analysis(*)").order("created_at", desc=True).limit(200).execute()
            return res.data
        elif report_type == "credibility":
            # Filter for credibility issues
            res = supabase.table("sentiment_analysis").select("*, reviews(*)").lt("credibility", 60).order("created_at", desc=True).execute()
            return res.data
        return []

    def _create_excel(self, data: List[Dict]) -> bytes:
        if not data:
            df = pd.DataFrame({"Message": ["No Data Available"]})
        else:
            # Flatten data
            flat_data = []
            for item in data:
                flat = item.copy()
                if "sentiment_analysis" in item and isinstance(item["sentiment_analysis"], list) and item["sentiment_analysis"]:
                     sa = item["sentiment_analysis"][0]
                     flat["sentiment"] = sa.get("label")
                     flat["score"] = sa.get("score")
                     flat["credibility"] = sa.get("credibility")
                     del flat["sentiment_analysis"]
                elif "reviews" in item: # Credibility report structure
                     rev = item.get("reviews")
                     if rev:
                         flat["text"] = rev.get("text")
                         flat["platform"] = rev.get("platform")
                     del flat["reviews"]
                flat_data.append(flat)
            
            df = pd.DataFrame(flat_data)
            
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Report')
        return output.getvalue()

    def _create_pdf(self, data: List[Dict], title: str) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        elements.append(Paragraph(f"Sentiment Beacon - {title.title()} Report", styles['Title']))
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 12))

        if not data:
             elements.append(Paragraph("No data found for this period.", styles['Normal']))
        else:
            # Summary Stats
            total = len(data)
            elements.append(Paragraph(f"Total Rows Analyzed: {total}", styles['Heading2']))
            elements.append(Spacer(1, 12))

            # Table
            table_data = [["ID", "Platform", "Sentiment/Score", "Text Snippet"]]
            for item in data[:50]: # Limit PDF rows
                text = item.get("text", "")[:50] + "..."
                if "reviews" in item:
                    text = item["reviews"].get("text", "")[:50] + "..."
                
                sentiment = "N/A"
                if "sentiment_analysis" in item and item["sentiment_analysis"]:
                     s = item["sentiment_analysis"][0]
                     sentiment = f"{s.get('label')} ({s.get('score'):.2f})"
                elif "label" in item:
                     sentiment = f"{item.get('label')} ({item.get('score'):.2f})"
                
                row = [
                    str(item.get("id", ""))[:8],
                    item.get("platform", "Unknown"),
                    sentiment,
                    text
                ]
                table_data.append(row)

            t = Table(table_data, colWidths=[60, 60, 100, 300])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(t)

        doc.build(elements)
        return buffer.getvalue()

report_service = ReportService()
