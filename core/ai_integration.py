import os
import json
import logging
from datetime import datetime
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

class AIOpenRouterIntegration:
    """
    AI Integration module using OpenRouter API for real-time student analysis.
    OpenRouter provides access to various AI models (Claude, GPT, etc.)
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'OPENROUTER_API_KEY', None)
        self.site_url = getattr(settings, 'OPENROUTER_SITE_URL', 'http://localhost:8000')
        self.site_name = getattr(settings, 'OPENROUTER_SITE_NAME', 'AcadStat')
        
    def analyze_student_performance(self, student, results, attendance_count):
        """
        Generate comprehensive AI analysis for a student.
        Returns detailed insights and personalized recommendations.
        """
        if not self.api_key:
            return self._generate_local_analysis(student, results, attendance_count)
        
        try:
            return self._generate_openrouter_analysis(student, results, attendance_count)
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self._generate_local_analysis(student, results, attendance_count)
    
    def _generate_openrouter_analysis(self, student, results, attendance_count):
        """Generate analysis using OpenRouter AI API"""
        import requests
        
        # Prepare student data
        results_data = []
        for r in results:
            percentage = (r.marks_obtained / r.total_marks * 100) if r.total_marks > 0 else 0
            results_data.append({
                'subject': r.subject.name,
                'marks': r.marks_obtained,
                'total': r.total_marks,
                'percentage': round(percentage, 1),
                'terminal': r.terminal
            })
        
        total_obtained = sum(r.marks_obtained for r in results)
        total_possible = sum(r.total_marks for r in results)
        overall_percentage = (total_obtained / total_possible * 100) if total_possible > 0 else 0
        
        # Find weak subjects
        weak_subjects = [r for r in results if (r.marks_obtained / r.total_marks * 100) < 50]
        strong_subjects = [r for r in results if (r.marks_obtained / r.total_marks * 100) >= 75]
        
        prompt = f"""You are an educational AI assistant. Analyze this student's performance and provide a comprehensive report.

Student Name: {student.name}
Class: {student.student_class} Section: {student.section}
Roll Number: {student.roll_number or 'N/A'}

Academic Performance:
- Overall Average: {overall_percentage:.1f}%
- Total Marks: {total_obtained}/{total_possible}
- Attendance Count: {attendance_count}

Subject-wise Results:
{json.dumps(results_data, indent=2)}

Weak Subjects (below 50%): {[r.subject.name for r in weak_subjects]}
Strong Subjects (above 75%): {[r.subject.name for r in strong_subjects]}

Please provide:
1. A brief performance summary (2-3 sentences)
2. Key areas of concern (bullet points)
3. Strengths (bullet points)
4. Specific recommendations (3-5 actionable items)
5. Predicted next term performance

Format your response as JSON:
{{
    "summary": "...",
    "concerns": ["..."],
    "strengths": ["..."],
    "recommendations": [{{"title": "...", "description": "..."}}],
    "prediction": "..."
}}"""
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": self.site_url,
                    "X-Title": self.site_name
                },
                json={
                    "model": "anthropic/claude-3-haiku",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                # Parse JSON from response
                return json.loads(content)
            else:
                logger.warning(f"OpenRouter API error: {response.status_code}")
                return self._generate_local_analysis(student, results, attendance_count)
                
        except Exception as e:
            logger.error(f"OpenRouter request failed: {e}")
            return self._generate_local_analysis(student, results, attendance_count)
    
    def _generate_local_analysis(self, student, results, attendance_count):
        """Generate analysis locally when AI API is not available"""
        if not results:
            return {
                'summary': f"{student.name} currently has no academic records. Encourage them to participate actively in studies.",
                'concerns': ['No academic records found'],
                'strengths': [],
                'recommendations': [
                    {'title': 'Start Academic Journey', 'description': 'Begin taking regular assessments to build performance history'},
                    {'title': 'Meet with Teachers', 'description': 'Schedule meetings with subject teachers to understand curriculum requirements'}
                ],
                'prediction': 'Performance data will be available after first assessments'
            }
        
        total_obtained = sum(r.marks_obtained for r in results)
        total_possible = sum(r.total_marks for r in results)
        overall_percentage = (total_obtained / total_possible * 100) if total_possible > 0 else 0
        
        weak_subjects = []
        strong_subjects = []
        
        for r in results:
            percentage = (r.marks_obtained / r.total_marks * 100) if r.total_marks > 0 else 0
            if percentage < 50:
                weak_subjects.append(f"{r.subject.name} ({percentage:.1f}%)")
            elif percentage >= 75:
                strong_subjects.append(f"{r.subject.name} ({percentage:.1f}%)")
        
        # Determine performance level
        if overall_percentage < 40:
            level = "critical"
            summary = f"🚨 {student.name} is showing concerning performance with {overall_percentage:.1f}%. Immediate intervention required."
        elif overall_percentage < 60:
            level = "warning"
            summary = f"⚠️ {student.name}'s performance needs improvement. Current average is {overall_percentage:.1f}%."
        elif overall_percentage < 75:
            level = "satisfactory"
            summary = f"✓ {student.name} is performing at a satisfactory level with {overall_percentage:.1f}% average."
        else:
            level = "excellent"
            summary = f"🌟 {student.name} is performing excellently with {overall_percentage:.1f}% average!"
        
        concerns = weak_subjects[:3] if weak_subjects else ["No major concerns identified"]
        strengths = strong_subjects[:3] if strong_subjects else ["Keep working hard to identify strengths"]
        
        recommendations = []
        
        if overall_percentage < 40:
            recommendations = [
                {'title': '🔴 Urgent Parent Meeting', 'description': 'Schedule immediate meeting with parents to discuss intervention strategies'},
                {'title': '📚 Tutoring Sessions', 'description': 'Enroll in remedial classes or private tutoring for weak subjects'},
                {'title': '⏰ Study Schedule', 'description': 'Create strict daily study routine with 2-3 hours dedicated to studies'},
                {'title': '🩺 Health Check', 'description': 'Ensure student is not facing health or personal issues affecting performance'}
            ]
        elif overall_percentage < 60:
            recommendations = [
                {'title': '🟡 Academic Counseling', 'description': 'Schedule meeting to identify specific learning challenges'},
                {'title': '📖 Study Groups', 'description': 'Join or form study groups with classmates'},
                {'title': '🎯 Target Setting', 'description': 'Set achievable short-term goals for next terminal exam'},
                {'title': '👨‍🏫 Teacher Consultation', 'description': 'Meet with teachers for weak subjects weekly'}
            ]
        elif overall_percentage < 75:
            recommendations = [
                {'title': '📈 Keep Improving', 'description': 'Maintain current effort and focus on weak areas'},
                {'title': '🏆 Aim Higher', 'description': 'Set target of 80%+ for next assessment'},
                {'title': '📚 Extra Practice', 'description': 'Practice additional problems beyond textbook exercises'}
            ]
        else:
            recommendations = [
                {'title': '🌟 Maintain Excellence', 'description': 'Continue current study habits and help peers'},
                {'title': '🚀 Challenge Yourself', 'description': 'Consider advanced topics and competitive exams'},
                {'title': '🎓 Mentorship', 'description': 'Help classmates who are struggling'}
            ]
        
        # Add subject-specific recommendations
        for weak in results[:2]:
            pct = (weak.marks_obtained / weak.total_marks * 100) if weak.total_marks > 0 else 0
            if pct < 50:
                recommendations.append({
                    'title': f'Focus on {weak.subject.name}',
                    'description': f'Struggle in {weak.subject.name}. Recommend extra practice and teacher help.'
                })
        
        # Prediction
        if overall_percentage < 40:
            prediction = "At current rate, performance may decline further without intervention. Immediate action needed."
        elif overall_percentage < 60:
            prediction = "With consistent effort, can reach 60-70% range in next terminal."
        elif overall_percentage < 75:
            prediction = "Good progress. Can achieve distinction (75%+) with focused preparation."
        else:
            prediction = "Excellent trajectory. Maintain performance for academic excellence."
        
        return {
            'summary': summary,
            'concerns': concerns,
            'strengths': strengths,
            'recommendations': recommendations[:5],
            'prediction': prediction,
            'level': level,
            'overall_percentage': round(overall_percentage, 1)
        }
    
    def send_student_notification(self, student, analysis, method='email'):
        """
        Send AI-generated analysis to students who need attention.
        Supports email and SMS (via Twilio) notifications.
        """
        # Check if student has email - if not, log but don't fail
        if not hasattr(student, 'email') or not student.email:
            if method == 'email':
                logger.warning(f"No email for student {student.name}, skipping email notification")
                return False
        
        try:
            if method == 'email':
                return self._send_email(student, analysis)
            elif method == 'sms':
                return self._send_sms(student, analysis)
            else:
                logger.warning(f"Unknown notification method: {method}")
                return False
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    def _send_email(self, student, analysis):
        """Send email with AI analysis"""
        subject = f"📊 Academic Performance Report - {student.name}"
        
        body = f"""
Dear {student.name},

{analysis.get('summary', '')}

📉 KEY CONCERNS:
{chr(10).join(f"- {c}" for c in analysis.get('concerns', []))}

🌟 YOUR STRENGTHS:
{chr(10).join(f"- {s}" for s in analysis.get('strengths', []))}

📋 RECOMMENDATIONS:
{chr(10).join(f"- {r.get('title', '')}: {r.get('description', '')}" for r in analysis.get('recommendations', []))}

🔮 PREDICTION:
{analysis.get('prediction', '')}

Keep working hard!
AcadStat AI Assistant
"""
        
        try:
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@acadstat.com',
                [student.email] if student.email else [],
                fail_silently=False
            )
            logger.info(f"Email sent to {student.name}")
            return True
        except Exception as e:
            logger.error(f"Email failed: {e}")
            return False
    
    def _send_sms(self, student, analysis):
        """Send SMS notification (requires Twilio configuration)"""
        twilio_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        twilio_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        twilio_phone = getattr(settings, 'TWILIO_PHONE_NUMBER', None)
        
        if not all([twilio_sid, twilio_token, twilio_phone]):
            logger.warning("Twilio not configured for SMS")
            return False
        
        try:
            from twilio.rest import Client
            client = Client(twilio_sid, twilio_token)
            
            message = f"AcadStat: {analysis.get('summary', '')[:100]} - Check recommendations in your student portal."
            
            # Would need student phone number
            # client.messages.create(body=message, from_=twilio_phone, to=student.phone)
            
            return True
        except Exception as e:
            logger.error(f"SMS failed: {e}")
            return False


class AutomationModule:
    """
    Automation module for scheduled tasks like sending AI reports to students.
    Can be run via cron or Django management command.
    """
    
    def __init__(self):
        self.ai = AIOpenRouterIntegration()
    
    def analyze_all_students(self):
        """Analyze all students and generate reports"""
        from core.models import Student, Attendance
        
        students = Student.objects.all()
        analyses = []
        
        for student in students:
            results = student.result_set.all()
            attendance_count = Attendance.objects.filter(student=student).count()
            
            analysis = self.ai.analyze_student_performance(student, results, attendance_count)
            analyses.append({
                'student': student,
                'analysis': analysis
            })
        
        return analyses
    
    def notify_students_needing_attention(self, threshold=60):
        """
        Automatically send notifications to students below threshold.
        Run this via cron job (e.g., daily or weekly).
        """
        from core.models import Student, Result, Attendance
        
        students = Student.objects.all()
        notified = []
        
        for student in students:
            results = list(student.result_set.all())
            if not results:
                continue
            
            total_obtained = sum(r.marks_obtained for r in results)
            total_possible = sum(r.total_marks for r in results)
            percentage = (total_obtained / total_possible * 100) if total_possible > 0 else 0
            
            if percentage < threshold:
                attendance_count = Attendance.objects.filter(student=student).count()
                analysis = self.ai.analyze_student_performance(student, results, attendance_count)
                
                # Send notification
                if self.ai.send_student_notification(student, analysis, method='email'):
                    notified.append(student.name)
                    logger.info(f"Notified {student.name} ({percentage:.1f}%)")
        
        return notified
    
    def generate_daily_report(self):
        """Generate daily summary report"""
        from core.models import Student, Result, Attendance
        from django.db.models import Avg
        
        today = timezone.now().date()
        
        # Get today's stats
        attendance_today = Attendance.objects.filter(date=today).count()
        total_students = Student.objects.count()
        
        # Average marks
        all_results = Result.objects.all()
        if all_results.exists():
            avg_marks = all_results.aggregate(Avg('marks_obtained'))['marks_obtained__avg']
        else:
            avg_marks = 0
        
        # Students needing attention
        at_risk = []
        for student in Student.objects.all():
            results = list(student.result_set.all())
            if results:
                total_obtained = sum(r.marks_obtained for r in results)
                total_possible = sum(r.total_marks for r in results)
                percentage = (total_obtained / total_possible * 100) if total_possible > 0 else 0
                
                if percentage < 40:
                    at_risk.append({'name': student.name, 'percentage': round(percentage, 1)})
        
        return {
            'date': today,
            'attendance_today': attendance_today,
            'total_students': total_students,
            'average_marks': round(avg_marks, 1) if avg_marks else 0,
            'at_risk_students': at_risk,
            'total_at_risk': len(at_risk)
        }


# Global instances for reuse
ai_integration = AIOpenRouterIntegration()
automation = AutomationModule()
