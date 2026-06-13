"""
TU / Soch College grading scale (see media/GPA.png).

Percentage bands map to letter Grade and subject GPA (4.0 scale).
Overall GPA = average of subject GPAs only when every subject is >= 40%.
"""

from __future__ import annotations

# (min_percentage_inclusive, letter_grade, subject_gpa)
SOCH_GRADE_BANDS: list[tuple[float, str, float]] = [
    (85, 'A+', 4.0),
    (80, 'A+', 3.7),
    (75, 'B+', 3.3),
    (70, 'B', 3.0),
    (65, 'B-', 2.7),
    (60, 'C+', 2.3),
    (55, 'C', 2.0),
    (50, 'C-', 1.7),
    (45, 'D', 1.3),
    (40, 'D', 1.0),
    (0, 'F', 0.0),
]

PASS_MARK_PERCENT = 40.0


def grade_info_for_percentage(percentage: float) -> dict:
    """Return letter grade, subject GPA, and pass flag for a percentage."""
    pct = float(percentage)
    for min_pct, grade, gpa in SOCH_GRADE_BANDS:
        if pct >= min_pct:
            return {
                'grade': grade,
                'subject_gpa': gpa,
                'passed': pct >= PASS_MARK_PERCENT,
            }
    return {'grade': 'F', 'subject_gpa': 0.0, 'passed': False}


def summarize_terminal_results(results) -> dict:
    """Build mark-sheet rows and overall summary from Result queryset/list."""
    items = []
    total_obt = 0.0
    total_pos = 0.0

    for r in results:
        pct = (r.marks_obtained / r.total_marks * 100) if r.total_marks > 0 else 0
        info = grade_info_for_percentage(pct)
        items.append({
            'result': r,
            'percentage': round(pct, 1),
            'grade': info['grade'],
            'subject_gpa': info['subject_gpa'],
        })
        total_obt += r.marks_obtained
        total_pos += r.total_marks

    all_passed = all(item['percentage'] >= PASS_MARK_PERCENT for item in items) if items else False
    overall_percentage = round((total_obt / total_pos * 100) if total_pos > 0 else 0, 2)

    if all_passed and items:
        gpa = round(sum(item['subject_gpa'] for item in items) / len(items), 2)
        overall_grade = grade_info_for_percentage(overall_percentage)['grade']
    else:
        gpa = None
        overall_grade = 'F'

    return {
        'student_results': items,
        'total_subjects': len(items),
        'total_marks_obtained': total_obt,
        'total_marks': total_pos,
        'overall_percentage': overall_percentage,
        'gpa': gpa,
        'all_passed': all_passed,
        'overall_grade': overall_grade,
    }
