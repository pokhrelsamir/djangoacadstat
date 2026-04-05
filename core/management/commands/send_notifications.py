from django.core.management.base import BaseCommand
from core.ai_integration import automation


class Command(BaseCommand):
    help = 'Send automated AI notifications to students needing attention'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--threshold',
            type=float,
            default=60,
            help='Percentage threshold to send notifications (default: 60)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show who would be notified without sending'
        )
    
    def handle(self, *args, **options):
        threshold = options['threshold']
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.WARNING(f'Analyzing students below {threshold}%...'))
        
        from core.models import Student, Result, Attendance
        
        students = Student.objects.all()
        to_notify = []
        
        for student in students:
            results = list(student.result_set.all())
            if not results:
                continue
            
            total_obtained = sum(r.marks_obtained for r in results)
            total_possible = sum(r.total_marks for r in results)
            percentage = (total_obtained / total_possible * 100) if total_possible > 0 else 0
            
            if percentage < threshold:
                attendance_count = Attendance.objects.filter(student=student).count()
                to_notify.append({
                    'student': student,
                    'percentage': percentage,
                    'attendance': attendance_count
                })
        
        self.stdout.write(self.style.SUCCESS(f'Found {len(to_notify)} students needing attention'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n--- DRY RUN: No notifications sent ---\n'))
            for item in to_notify:
                self.stdout.write(f"  - {item['student'].name}: {item['percentage']:.1f}%")
            return
        
        notified = automation.notify_students_needing_attention(threshold=threshold)
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Notifications sent to {len(notified)} students:'))
        for name in notified:
            self.stdout.write(f'  ✓ {name}')
