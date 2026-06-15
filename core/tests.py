from django.test import TestCase

from core.gpa_forecasting import build_gpa_forecast
from core.models import Result, Student, Subject


class GPAForecastingTests(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            name='Forecast Student',
            roll_number='FS-1',
            level='bachelor',
            student_class='1',
            section='A',
            semester='1',
        )
        self.math = Subject.objects.create(name='Mathematics', code='MATH101')
        self.science = Subject.objects.create(name='Science', code='SCI101')
        marks = {
            '1st': (72, 68),
            '2nd': (76, 70),
            '3rd': (82, 74),
            'Final': (84, 78),
        }
        for terminal, (math_mark, science_mark) in marks.items():
            Result.objects.create(
                student=self.student,
                subject=self.math,
                terminal=terminal,
                marks_obtained=math_mark,
                total_marks=100,
            )
            Result.objects.create(
                student=self.student,
                subject=self.science,
                terminal=terminal,
                marks_obtained=science_mark,
                total_marks=100,
            )

    def test_forecast_uses_temporal_teacher_marks(self):
        forecast = build_gpa_forecast(self.student, target_cgpa=3.5)

        self.assertEqual(len(forecast['periods']), 4)
        self.assertEqual([p['terminal'] for p in forecast['periods']], ['1st', '2nd', '3rd', 'Final'])
        self.assertGreater(forecast['current_cgpa'], 0)
        self.assertGreaterEqual(forecast['projected_cgpa'], forecast['current_cgpa'])
        self.assertEqual(forecast['validation']['sample_size'], 3)
        self.assertIn(forecast['validation']['quality'], {'strong', 'moderate', 'volatile'})

    def test_required_gpa_reports_unattainable_targets(self):
        forecast = build_gpa_forecast(self.student, target_cgpa=4.0)

        self.assertIsNotNone(forecast['raw_required_gpa'])
        if forecast['raw_required_gpa'] > 4:
            self.assertIn('above the 4.0 maximum', forecast['required_message'])

    def test_chart_payloads_are_chartjs_ready(self):
        forecast = build_gpa_forecast(self.student, target_cgpa=3.5)

        for key in ['semester_gpa_chart', 'cgpa_growth_chart', 'subject_strength_chart', 'validation_chart']:
            self.assertIn('labels', forecast[key])
            self.assertIn('datasets', forecast[key])
            self.assertTrue(forecast[key]['datasets'])
