import os
import json
import csv
import io
from datetime import datetime
from typing import Dict, Any, List
from services.ai_service import ai_service

# --- SAFETY UPDATE: Graceful imports for ReportLab ---
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    _REPORTLAB_AVAILABLE = True
except ImportError:
    _REPORTLAB_AVAILABLE = False
    print("⚠️ Warning: 'reportlab' not installed. PDF generation disabled.")
# ----------------------------------------------------

class ReportService:
    def __init__(self):
        self.reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate_recommendations(self, stats: dict) -> List[str]:
        """
        Generate business recommendations based on statistics.
        """
        recommendations = []
        
        # Rule 1: Low Positive Sentiment
        pos_percent = stats.get("positive_percent", 0)
        if pos_percent < 40:
            recommendations.append("CRITICAL: Immediate PR intervention required.")

        # Rule 2: Price Sensitivity
        # Check if 'price' is in negative topics
        negative_topics = stats.get("negative_topics", [])
        if any("price" in t.lower() or "expensive" in t.lower() or "cost" in t.lower() for t in negative_topics):
            recommendations.append("Action: Re-evaluate pricing strategy vs competitors.")
            
        # Rule 3: Logistics Issues
        if any("shipping" in t.lower() or "delivery" in t.lower() or "arrive" in t.lower() for t in negative_topics):
            recommendations.append("Action: Audit logistics partners.")

        # Additional Rules
        if not recommendations and pos_percent > 80:
             recommendations.append("Performance is excellent. Consider a loyalty campaign.")
             
        return recommendations

    def generate_report(self, data: Dict[str, Any], format: str = "json") -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sentiment_report_{timestamp}.{format}"
        filepath = os.path.join(self.reports_dir, filename)

        if format == "json":
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        
        elif format == "csv":
            self._generate_csv(data, filepath)
            
        elif format == "pdf":
            if not _REPORTLAB_AVAILABLE:
                raise ImportError("PDF generation requires 'reportlab'. Please install it: pip install reportlab")
            self._generate_pdf(data, filepath)
            
        else:
            raise ValueError(f"Unsupported format: {format}")
            
        return filepath

    def _generate_csv(self, data: Dict[str, Any], filepath: str):
        # Flatten simple stats for CSV
        stats = data.get('statistics', {})
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Total Reviews', stats.get('total_reviews', 0)])
            writer.writerow(['Average Rating', stats.get('average_rating', 0)])
            writer.writerow(['Sentiment Score', stats.get('sentiment_score', 0)])
            
            writer.writerow([])
            writer.writerow(['Recent Reviews'])
            writer.writerow(['Date', 'Source', 'Sentiment', 'Text'])
            
            for review in data.get('recent_reviews', []):
                writer.writerow([
                    review.get('created_at'),
                    review.get('source'),
                    review.get('sentiment_label'),
                    review.get('content', '')[:100] + '...'
                ])

    def _generate_pdf(self, data: Dict[str, Any], filepath: str):
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        story.append(Paragraph("Sentiment Analysis Report", styles['Title']))
        story.append(Spacer(1, 12))

        # Overview
        story.append(Paragraph("Overview", styles['Heading2']))
        stats = data.get('statistics', {})
        
        overview_data = [
            ['Metric', 'Value'],
            ['Total Reviews', str(stats.get('total_reviews', 0))],
            ['Average Rating', f"{stats.get('average_rating', 0):.2f}"],
            ['Sentiment Score', f"{stats.get('sentiment_score', 0):.2f}"]
        ]
        
        t = Table(overview_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(t)
        story.append(Spacer(1, 20))

        # Recent Reviews
        story.append(Paragraph("Recent Reviews", styles['Heading2']))
        for review in data.get('recent_reviews', [])[:5]:
            text = f"<b>{review.get('source', 'Unknown')}</b> ({review.get('sentiment_label', 'Neutral')}): {review.get('content', '')[:200]}..."
            story.append(Paragraph(text, styles['Normal']))
            story.append(Spacer(1, 10))

        doc.build(story)

    def generate_pdf_report(self, product_id: str) -> str:
        """Generate a PDF report for a product_id.

        The PDF contains: Total Reviews, Avg Sentiment Score, Top 5 positive and top 5 negative reviews,
        and AI Business Recommendations.
        """
        if not _REPORTLAB_AVAILABLE:
            raise ImportError("PDF generation requires reportlab")

        # Query Supabase for reviews
        try:
            from database import supabase
            resp = supabase.table("reviews").select("*, sentiment_analysis(*), sentiment_score, sentiment_label").eq("product_id", product_id).execute()
            rows = resp.data or []
        except Exception as e:
            print(f"Failed to fetch reviews for report: {e}")
            rows = []

        total = len(rows)
        avg_sent = 0.0
        pos_count = 0
        texts = []
        
        try:
            scores = []
            for r in rows:
                s = float(r.get("sentiment_score") or 0)
                scores.append(s)
                if r.get("sentiment_label") == "POSITIVE" or (r.get("sentiment_analysis") and r.get("sentiment_analysis")[0].get("label") == "POSITIVE"):
                    pos_count += 1
                
                content = r.get("content") or r.get("text") or ""
                if content:
                    texts.append(content)

            if scores:
                avg_sent = sum(scores) / len(scores)
        except Exception:
            avg_sent = 0.0

        pos_percent = (pos_count / total * 100) if total > 0 else 0

        # Extract topics to find negative themes
        topics = ai_service.extract_topics(texts, top_k=10)
        neg_topics = [t["topic"] for t in topics if t["sentiment"] == "negative"]

        # Generate Recommendations
        recs = self.generate_recommendations({
            "positive_percent": pos_percent,
            "negative_topics": neg_topics
        })

        # Sort top positive and negative by sentiment_score
        positives = sorted([r for r in rows if (r.get("sentiment_score") is not None)], key=lambda x: float(x.get("sentiment_score") or 0), reverse=True)[:5]
        negatives = sorted([r for r in rows if (r.get("sentiment_score") is not None)], key=lambda x: float(x.get("sentiment_score") or 0))[:5]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{product_id}_{timestamp}.pdf"
        filepath = os.path.join(self.reports_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(f"Sentiment Report - Product {product_id}", styles['Title']))
        story.append(Spacer(1, 12))

        # Overview Table
        story.append(Paragraph("Overview", styles['Heading2']))
        overview = [
            ['Metric', 'Value'],
            ['Total Reviews', str(total)],
            ['Average Sentiment', f"{avg_sent:.3f}"],
            ['Positive Reviews', f"{pos_percent:.1f}%"],
        ]
        t = Table(overview)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        story.append(t)
        story.append(Spacer(1, 20))

        # AI Recommendations Section
        if recs:
            story.append(Paragraph("AI Business Recommendations", styles['Heading2']))
            for rec in recs:
                # Style check for "CRITICAL"
                if "CRITICAL" in rec:
                    story.append(Paragraph(f"<b><font color='red'>{rec}</font></b>", styles['Normal']))
                else:
                    story.append(Paragraph(f"• {rec}", styles['Normal']))
                story.append(Spacer(1, 6))
            story.append(Spacer(1, 12))

        def add_review_list(title, items):
            story.append(Paragraph(title, styles['Heading3']))
            for r in items:
                text = r.get('content') or r.get('text') or ''
                label = r.get('sentiment_label') or ''
                score = r.get('sentiment_score')
                src = r.get('source_url') or r.get('url') or ''
                line = f"({label} - {score}) {text[:300]}"
                story.append(Paragraph(line, styles['Normal']))
                if src:
                    story.append(Paragraph(f"Source: {src}", styles['Italic']))
                story.append(Spacer(1, 6))

        add_review_list('Top Positive Reviews', positives)
        story.append(Spacer(1, 12))
        add_review_list('Top Negative Reviews', negatives)

        doc.build(story)
        return filepath

report_service = ReportService()
