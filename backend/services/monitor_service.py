from typing import Dict, Any, List
from database import supabase, create_alert_log

class MonitorService:
    async def check_triggers(self, review: Dict[str, Any]):
        """
        Real-time Alert Logic.
        Trigger 1 (Crisis): Sentiment < 0.2 AND Credibility > 0.8
        Trigger 2 (Viral Negative): Sentiment NEGATIVE AND Like Count > 50
        """
        try:
            analysis = review.get("analysis", {})
            metadata = review.get("metadata", {})
            
            score = float(analysis.get("score", 0.5))
            credibility = float(analysis.get("credibility", 0))
            label = analysis.get("label", "NEUTRAL")
            
            like_count = int(metadata.get("like_count", 0))
            
            # Trigger 1: Crisis (High Credibility, Low Sentiment)
            if score < 0.2 and credibility > 0.8:
                await self._create_alert(
                    title="CRITICAL: Trusted Negative Review",
                    message=f"Verified user (Cred: {credibility:.2f}) posted severe negative feedback.",
                    severity="critical",
                    platform=review.get("platform", "unknown"),
                    details=review
                )
                
            # Trigger 2: Viral Risk (Negative + High Engagement)
            if label == "NEGATIVE" and like_count > 50:
                 await self._create_alert(
                    title="VIRAL RISK: Negative Sentiment Spiking",
                    message=f"Negative review gaining traction ({like_count} likes).",
                    severity="high",
                    platform=review.get("platform", "unknown"),
                    details=review
                )
                
        except Exception as e:
            print(f"Monitor check_triggers error: {e}")

    async def _create_alert(self, title: str, message: str, severity: str, platform: str, details: Dict[str, Any]):
        try:
            alert = {
                "type": "automated_trigger",
                "title": title,
                "message": message,
                "severity": severity,
                "platform": platform,
                "is_read": False,
                "is_resolved": False,
                "details": details
            }
            await create_alert_log(alert)
        except Exception as e:
            print(f"Failed to insert alert: {e}")

monitor_service = MonitorService()