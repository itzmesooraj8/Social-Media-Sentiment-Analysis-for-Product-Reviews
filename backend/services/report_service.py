import os
import json
import csv
from datetime import datetime
from typing import Dict, Any, List
from services.ai_service import ai_service
from database import supabase

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
    print("⚠️ Warning: 'reportlab' not installed. PDF generation disabled.")
# ----------------------------------------------------

class ReportService:
    def __init__(self):
        self.reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate_pdf_report(self, product_id: str) -> str:
        """
        Generate a 'Real Intelligence' PDF report for a product_id.
        Includes: Credibility Audit, Topic Landscape, Engagement Impact.
        """
        if not _REPORTLAB_AVAILABLE:
            raise ImportError("PDF generation requires reportlab")

        # 1. Fetch Reviews with Deep Analysis Data
        try:
            resp = supabase.table("reviews").select("*, sentiment_analysis(*), like_count, reply_count").eq("product_id", product_id).execute()
            rows = resp.data or []
        except Exception as e:
            print(f"Failed to fetch reviews for report: {e}")
            rows = []

        # 2. Fetch Global Topics (as proxy for emerging topics if product-specific not available)
        try:
            topic_resp = supabase.table("topic_analysis").select("*").order("size", desc=True).limit(5).execute()
            global_topics = topic_resp.data or []
        except Exception:
            global_topics = []

        # --- Calculations ---
        total = len(rows)
        if total == 0:
            return self._generate_empty_report(product_id)

        # Sentiment Stats
        scores = [float(r.get("sentiment_analysis", {}).get("score", 0.5) if r.get("sentiment_analysis") else 0.5) for r in rows]
        avg_sent = sum(scores) / total if scores else 0
        
        # Credibility Audit
        # Threshold: > 0.7 is Verified, < 0.4 is Suspicious
        verified_count = sum(1 for r in rows if float(r.get("sentiment_analysis", {}).get("credibility", 0) if r.get("sentiment_analysis") else 0) > 0.7)
        suspicious_count = sum(1 for r in rows if float(r.get("sentiment_analysis", {}).get("credibility", 0) if r.get("sentiment_analysis") else 0) < 0.4)
        
        # Engagement Impact
        # Avg Likes for Positive vs Negative
        pos_reviews = [r for r in rows if r.get("sentiment_analysis", {}).get("label") == "POSITIVE"]
        neg_reviews = [r for r in rows if r.get("sentiment_analysis", {}).get("label") == "NEGATIVE"]
        
        avg_likes_pos = sum(r.get("like_count", 0) for r in pos_reviews) / len(pos_reviews) if pos_reviews else 0
        avg_likes_neg = sum(r.get("like_count", 0) for r in neg_reviews) / len(neg_reviews) if neg_reviews else 0


        # --- PDF Construction ---
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{product_id}_{timestamp}.pdf"
        filepath = os.path.join(self.reports_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        story.append(Paragraph(f"Deep Analysis Report: {product_id}", styles['Title']))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 20))

        # 1. Executive Summary
        story.append(Paragraph("1. Executive Summary", styles['Heading2']))
        summary_data = [
            ['Metric', 'Value'],
            ['Total Analyzed Reviews', str(total)],
            ['Average Sentiment Score', f"{avg_sent:.2f} / 1.0"],
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

        # 2. Credibility Audit
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

        # 3. Topic Landscape
        story.append(Paragraph("3. Topic Landscape (Emerging Themes)", styles['Heading2']))
        if global_topics:
            topic_data = [['Topic Keyword', 'Volume', 'Sentiment Context']]
            for topic in global_topics:
                topic_data.append([
                    topic.get("topic_name", "N/A"),
                    str(topic.get("size", 0)),
                    "Mixed/General" # Placeholder as table doesn't have per-topic sentiment context easily accessible without complex join
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

        # 4. Engagement Impact
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
        return filepath

    def _generate_empty_report(self, product_id):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{product_id}_{timestamp}_empty.pdf"
        filepath = os.path.join(self.reports_dir, filename)
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        doc.build([Paragraph(f"No data available for {product_id}", getSampleStyleSheet()['Normal'])])
        return filepath

report_service = ReportService()