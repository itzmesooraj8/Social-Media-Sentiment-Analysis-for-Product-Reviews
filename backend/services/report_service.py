import os
import json
import csv
import io
import asyncio
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
from services.ai_service import ai_service
from database import supabase

logger = logging.getLogger(__name__)

# --- SAFETY UPDATE: Graceful imports for ReportLab ---
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    _REPORTLAB_AVAILABLE = True
except ImportError:
    _REPORTLAB_AVAILABLE = False
    logger.warning("'reportlab' not installed. PDF generation disabled.")
# ----------------------------------------------------

class ReportService:
    def __init__(self):
        # Use absolute path for reliability on Render
        self.reports_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports"))
        os.makedirs(self.reports_dir, exist_ok=True)

    async def _upload_to_supabase(self, filepath: str, product_id: str, format_type: str):
        """
        Uploads the file to Supabase Storage and saves a record in the 'reports' database table.
        """
        if not supabase:
            logger.info("Supabase client not initialized. Skipping upload.")
            return

        filename = os.path.basename(filepath)
        storage_path = f"generated/{filename}"
        
        try:
            # 1. Upload to Storage Bucket (Expected bucket name: 'reports')
            # Note: The 'reports' bucket must exist and have public/authenticated access enabled.
            with open(filepath, 'rb') as f:
                async def _upload():
                    return supabase.storage.from_('reports').upload(storage_path, f, {"upsert": "true"})
                
                # Check if we should use thread for sync library or if it's async
                # supabase-py 2.0+ is usually sync unless using async client. 
                # database.py uses create_client which is sync.
                # However, the routers call these methods. I will use asyncio.to_thread for safety.
                await asyncio.to_thread(supabase.storage.from_('reports').upload, storage_path, f, {"upsert": "true"})

            # 2. Get File Stats
            file_size = os.path.getsize(filepath)

            # 3. Insert Record into 'reports' table
            report_data = {
                "product_id": product_id,
                "filename": filename,
                "storage_path": storage_path,
                "type": format_type,
                "size": file_size
            }
            await asyncio.to_thread(supabase.table("reports").insert(report_data).execute)
            logger.info(f"Successfully saved persistent report record: {filename}")

        except Exception as e:
            logger.error(f"Failed to upload report to Supabase Storage: {e}")
            logger.info("Local report file still available for immediate download.")

    async def generate_excel_report(self, product_id: str) -> str:
        """
        Generate an Excel report with multiple sheets: Summary, Reviews, Topics.
        """
        logger.info(f"Excel generation started for Product: {product_id}")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{product_id}_{timestamp}.xlsx"
        filepath = os.path.join(self.reports_dir, filename)

        # 1. Fetch Data
        try:
            logger.info("Fetching reviews for Excel...")
            task = asyncio.to_thread(lambda: supabase.table("reviews").select("*, sentiment_analysis(*)").eq("product_id", product_id).execute())
            resp = await task
            reviews = resp.data or []
            logger.info(f"Fetched {len(reviews)} reviews for Excel.")
            
            # Topics
            t_task = asyncio.to_thread(lambda: supabase.table("topic_analysis").select("*").order("size", desc=True).limit(20).execute())
            t_resp = await t_task
            topics = t_resp.data or []
        except Exception as e:
            print(f"Error fetching data for Excel: {e}")
            reviews = []
            topics = []

        # 2. Prepare DataFrames
        review_rows = []
        for r in reviews:
            sa = r.get("sentiment_analysis", {})
            if isinstance(sa, list) and sa: sa = sa[0]
            
            review_rows.append({
                "Date": r.get("created_at"),
                "Platform": r.get("platform"),
                "Author": r.get("username"),
                "Content": r.get("content"),
                "Sentiment": sa.get("label", "NEUTRAL") if sa else "NEUTRAL",
                "Score": sa.get("score", 0.5) if sa else 0.5,
                "Credibility": sa.get("credibility", 0) if sa else 0,
                "Likes": r.get("like_count", 0),
                "Replies": r.get("reply_count", 0)
            })
        df_reviews = pd.DataFrame(review_rows)
        df_topics = pd.DataFrame(topics)

        summary_data = {
            "Generated At": [datetime.now().isoformat()],
            "Total Reviews": [len(reviews)],
            "Average Sentiment": [df_reviews["Score"].mean() if not df_reviews.empty else 0],
            "Positive Reviews": [len(df_reviews[df_reviews["Sentiment"] == "POSITIVE"]) if not df_reviews.empty else 0],
            "Negative Reviews": [len(df_reviews[df_reviews["Sentiment"] == "NEGATIVE"]) if not df_reviews.empty else 0]
        }
        df_summary = pd.DataFrame(summary_data)

        # 3. Write to Excel (Blocking IO - run in thread)
        def _write():
            with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
                df_summary.to_excel(writer, sheet_name='Summary', index=False)
                df_reviews.to_excel(writer, sheet_name='Reviews', index=False)
                df_topics.to_excel(writer, sheet_name='Topics', index=False)
        
        await asyncio.to_thread(_write)

        # 4. Upload to Persistance
        await self._upload_to_supabase(filepath, product_id, "excel")
            
        return filepath

    async def generate_pdf_report(self, product_id: str) -> str:
        """
        Generate a 'Real Intelligence' PDF report for a product_id.
        Includes: Credibility Audit, Topic Landscape, Engagement Impact.
        """
        logger.info(f"PDF generation started for Product: {product_id}")
        if not _REPORTLAB_AVAILABLE:
            logger.error("ReportLab not available. PDF generation aborted.")
            raise ImportError("PDF generation requires reportlab")

        # 1. Fetch Reviews with Deep Analysis Data
        try:
            logger.info("Fetching reviews for PDF...")
            task = asyncio.to_thread(lambda: supabase.table("reviews").select("*, sentiment_analysis(*), like_count, reply_count").eq("product_id", product_id).execute())
            resp = await task
            rows = resp.data or []
            logger.info(f"Fetched {len(rows)} reviews for PDF.")
        except Exception as e:
            print(f"Failed to fetch reviews for report: {e}")
            rows = []

        # 2. Fetch Global Topics
        try:
            topic_task = asyncio.to_thread(lambda: supabase.table("topic_analysis").select("*").order("size", desc=True).limit(5).execute())
            topic_resp = await topic_task
            global_topics = topic_resp.data or []
        except Exception:
            global_topics = []

        # --- Calculations ---
        total = len(rows)
        if total == 0:
            return await self._generate_empty_report(product_id)

        scores = []
        verified_count = 0
        suspicious_count = 0
        pos_reviews = []
        neg_reviews = []

        for r in rows:
            sa = r.get("sentiment_analysis")
            if isinstance(sa, list) and sa: sa = sa[0]
            
            if sa:
                scores.append(float(sa.get("score", 0.5)))
                cred = float(sa.get("credibility", 0))
                if cred > 0.7: verified_count += 1
                elif cred < 0.4: suspicious_count += 1
                
                lbl = sa.get("label")
                if lbl == "POSITIVE": pos_reviews.append(r)
                elif lbl == "NEGATIVE": neg_reviews.append(r)

        avg_sent = sum(scores) / total if scores else 0
        pos_pct = (len(pos_reviews) / total * 100) if total else 0
        neg_pct = (len(neg_reviews) / total * 100) if total else 0
        
        avg_likes_pos = sum(r.get("like_count", 0) for r in pos_reviews) / len(pos_reviews) if pos_reviews else 0
        avg_likes_neg = sum(r.get("like_count", 0) for r in neg_reviews) / len(neg_reviews) if neg_reviews else 0

        # --- PDF Construction ---
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{product_id}_{timestamp}.pdf"
        filepath = os.path.join(self.reports_dir, filename)

        def _build_pdf():
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            story.append(Paragraph(f"Deep Analysis Report: {product_id}", styles['Title']))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
            story.append(Spacer(1, 20))

            story.append(Paragraph("1. Executive Summary", styles['Heading2']))
            summary_data = [
                ['Metric', 'Value'],
                ['Total Analyzed Reviews', str(total)],
                ['Average Sentiment Score', f"{avg_sent:.2f} / 1.0"],
                ['Positive Sentiment', f"{pos_pct:.1f}%"],
                ['Negative Sentiment', f"{neg_pct:.1f}%"],
                ['Credible Sources', f"{verified_count} verified"],
            ]
            t = Table(summary_data, colWidths=[200, 200])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(t)
            story.append(Spacer(1, 20))

            story.append(Paragraph("2. Credibility Audit", styles['Heading2']))
            story.append(Paragraph("We analyzed the trustworthiness of the review sources based on account age, karma, and bot patterns.", styles['Normal']))
            story.append(Spacer(1, 10))
            
            cred_data = [
                ['Category', 'Count', 'Implication'],
                ['Verified / High Trust', str(verified_count), 'Weight highly in decision making'],
                ['Suspicious / Low Trust', str(suspicious_count), 'Potential bot activity or spam'],
                ['Neutral / Average', str(total - verified_count - suspicious_count), 'Standard user feedback']
            ]
            t_cred = Table(cred_data, colWidths=[150, 100, 200])
            t_cred.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#8e44ad")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(t_cred)
            story.append(Spacer(1, 20))

            story.append(Paragraph("3. Topic Landscape (Emerging Themes)", styles['Heading2']))
            if global_topics:
                topic_data = [['Topic Keyword', 'Volume', 'Sentiment Context']]
                for topic in global_topics:
                    topic_data.append([
                        topic.get("topic_name", "N/A"),
                        str(topic.get("size", 0)),
                        "Mixed/General"
                    ])
                t_topic = Table(topic_data, colWidths=[150, 100, 200])
                t_topic.setStyle(TableStyle([
                     ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#27ae60")),
                     ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                     ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ]))
                story.append(t_topic)
            else:
                story.append(Paragraph("No significant topic clusters detected yet.", styles['Italic']))
            story.append(Spacer(1, 20))

            story.append(Paragraph("4. Engagement Impact", styles['Heading2']))
            story.append(Paragraph("How users are reacting to different sentiments:", styles['Normal']))
            story.append(Spacer(1, 10))
            
            eng_data = [
                ['Sentiment Type', 'Avg. Likes/Engagement', 'Interpretation'],
                ['Positive Reviews', f"{avg_likes_pos:.1f}", 'Validation / Agreement'],
                ['Negative Reviews', f"{avg_likes_neg:.1f}", 'Viral Complaints / Issues']
            ]
            t_eng = Table(eng_data, colWidths=[150, 150, 150])
            t_eng.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e67e22")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(t_eng)

            doc.build(story)
        
        await asyncio.to_thread(_build_pdf)

        # 4. Upload to Persistance
        await self._upload_to_supabase(filepath, product_id, "pdf")

        return filepath

    async def _generate_empty_report(self, product_id):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{product_id}_{timestamp}_empty.pdf"
        filepath = os.path.join(self.reports_dir, filename)
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        await asyncio.to_thread(doc.build, [Paragraph(f"No data available for {product_id}", getSampleStyleSheet()['Normal'])])
        
        await self._upload_to_supabase(filepath, product_id, "pdf")
        return filepath

    async def generate_report(self, data: Dict[str, Any], format: str = "csv", product_id: str = "generic") -> str:
        """
        Legacy/CSV generation support.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if format == "csv":
            filename = f"report_{product_id}_{timestamp}.csv"
            filepath = os.path.join(self.reports_dir, filename)
            
            reviews = data.get("recent_reviews", [])
            if not reviews:
                return filepath
            
            def _write_csv():
                keys = reviews[0].keys()
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(reviews)
            
            await asyncio.to_thread(_write_csv)
            await self._upload_to_supabase(filepath, product_id, "csv")
            return filepath
        
        raise ValueError(f"Unsupported format: {format}")

report_service = ReportService()
