"""
GPA / CGPA forecasting engine — uses Result marks + GradeScale grade points.
No AI; rule-based strength, risk, and recovery calculations.
"""
from __future__ import annotations

from core.models import GradeScale, Result

TERMINALS = ['1st', '2nd', '3rd', 'Final']
CREDITS_PER_SUBJECT = 3
STRONG_THRESHOLD = 70
WEAK_THRESHOLD = 50
CRITICAL_CGPA = 3.0


def _grade_scale():
    return GradeScale.objects.filter(is_active=True).first()


def _total_semesters(student) -> int:
    if student.level == 'bachelor':
        return 8
    if student.level == 'college':
        return 2
    return 4


def _current_semester_num(student) -> int:
    if student.semester:
        raw = str(student.semester).strip().lower().replace('semester', '').replace('sem', '')
        try:
            return max(1, int(raw.split()[0]))
        except (ValueError, IndexError):
            pass
    if student.level == 'college':
        return 1 if str(student.student_class).upper() in ('XI', '11') else 2
    try:
        return max(1, int(student.student_class))
    except (ValueError, TypeError):
        return 1


def _result_gpa_point(result, gs) -> float:
    if not gs:
        return 0.0
    return gs.get_grade_point(result.percentage)


def compute_semester_periods(student) -> list[dict]:
    """Aggregate GPA by terminal (each terminal = one academic period)."""
    gs = _grade_scale()
    results = list(
        Result.objects.filter(student=student).select_related('subject').order_by('terminal', 'subject__name')
    )
    periods = []
    terminal_order = {t: i for i, t in enumerate(TERMINALS)}

    for terminal in TERMINALS:
        term_results = [r for r in results if r.terminal == terminal]
        if not term_results:
            continue
        quality_points = 0.0
        credits = 0
        for r in term_results:
            cr = CREDITS_PER_SUBJECT
            gp = _result_gpa_point(r, gs)
            quality_points += gp * cr
            credits += cr
        gpa = round(quality_points / credits, 2) if credits else 0.0
        periods.append({
            'terminal': terminal,
            'label': f'{terminal} Terminal',
            'semester_label': f'Sem {len(periods) + 1}',
            'gpa': gpa,
            'credits': credits,
            'quality_points': round(quality_points, 2),
            'subject_count': len(term_results),
            'order': terminal_order.get(terminal, 99),
        })

    periods.sort(key=lambda p: p['order'])
    for i, p in enumerate(periods):
        p['semester_label'] = f'Sem {i + 1}'
    return periods


def compute_cgpa_timeline(periods: list[dict]) -> list[dict]:
    """Running CGPA after each completed period."""
    timeline = []
    cum_qp = 0.0
    cum_cr = 0
    for p in periods:
        cum_qp += p['quality_points']
        cum_cr += p['credits']
        cgpa = round(cum_qp / cum_cr, 2) if cum_cr else 0.0
        timeline.append({
            'label': p['semester_label'],
            'terminal': p['terminal'],
            'semester_gpa': p['gpa'],
            'cgpa': cgpa,
        })
    return timeline


def compute_subject_strengths(student) -> list[dict]:
    """Average % per subject → strong / average / weak."""
    results = Result.objects.filter(student=student).select_related('subject')
    by_subject: dict[str, list[float]] = {}
    for r in results:
        by_subject.setdefault(r.subject.name, []).append(r.percentage)

    strengths = []
    for name, pcts in sorted(by_subject.items()):
        avg = round(sum(pcts) / len(pcts), 1)
        if avg >= STRONG_THRESHOLD:
            level, label = 'strong', 'Strong'
        elif avg >= WEAK_THRESHOLD:
            level, label = 'average', 'Average'
        else:
            level, label = 'weak', 'Weak'
        strengths.append({
            'subject': name,
            'average_pct': avg,
            'level': level,
            'label': label,
            'samples': len(pcts),
        })
    strengths.sort(key=lambda x: x['average_pct'], reverse=True)
    return strengths


def detect_risk(cgpa: float, timeline: list[dict]) -> dict:
    if cgpa < CRITICAL_CGPA:
        return {
            'level': 'critical',
            'title': 'Critical Risk',
            'message': f'CGPA {cgpa:.2f} is below {CRITICAL_CGPA:.1f} — immediate academic support recommended.',
            'icon': 'fa-exclamation-triangle',
        }
    if len(timeline) >= 2:
        delta = timeline[-1]['cgpa'] - timeline[-2]['cgpa']
        if delta < -0.1:
            return {
                'level': 'high',
                'title': 'High Risk',
                'message': 'CGPA is on a declining trend — focus on weaker subjects this term.',
                'icon': 'fa-arrow-down',
            }
        if delta > 0.05:
            return {
                'level': 'low',
                'title': 'Low Risk',
                'message': 'CGPA is improving — keep up your current study habits.',
                'icon': 'fa-arrow-up',
            }
    return {
        'level': 'medium',
        'title': 'Moderate Risk',
        'message': 'Performance is stable — set a target CGPA and track each semester.',
        'icon': 'fa-minus',
    }


def required_gpa_for_target(
    target_cgpa: float,
    completed_qp: float,
    completed_credits: int,
    remaining_credits: int,
) -> float | None:
    if remaining_credits <= 0:
        return None
    total_credits = completed_credits + remaining_credits
    needed_qp = target_cgpa * total_credits - completed_qp
    return round(needed_qp / remaining_credits, 2)


def recovery_plan(
    expected_cgpa: float,
    actual_cgpa: float,
    remaining_semesters: int,
    completed_qp: float,
    completed_credits: int,
    credits_per_semester: float,
) -> dict | None:
    if remaining_semesters <= 0 or actual_cgpa >= expected_cgpa:
        return None
    remaining_credits = remaining_semesters * credits_per_semester
    required = required_gpa_for_target(
        expected_cgpa, completed_qp, completed_credits, remaining_credits
    )
    if required is None:
        return None
    gap = round(expected_cgpa - actual_cgpa, 2)
    extra_even = round(gap / remaining_semesters, 2) if remaining_semesters else 0
    return {
        'expected_cgpa': expected_cgpa,
        'actual_cgpa': actual_cgpa,
        'gap': gap,
        'required_gpa': required,
        'extra_per_semester': extra_even,
        'remaining_semesters': remaining_semesters,
        'message': (
            f'You need {required:.2f} average GPA in the next '
            f'{remaining_semesters} semester{"s" if remaining_semesters != 1 else ""} '
            f'to reach {expected_cgpa:.2f} CGPA.'
        ),
        'recovery_message': (
            f'Expected ~{expected_cgpa:.2f} but at {actual_cgpa:.2f}. '
            f'Recover ~{extra_even:.2f} GPA points per remaining semester on average.'
        ),
    }


def build_gpa_forecast(student, target_cgpa: float = 3.5) -> dict:
    periods = compute_semester_periods(student)
    timeline = compute_cgpa_timeline(periods)
    strengths = compute_subject_strengths(student)

    completed_qp = sum(p['quality_points'] for p in periods)
    completed_credits = sum(p['credits'] for p in periods)
    current_cgpa = round(completed_qp / completed_credits, 2) if completed_credits else 0.0

    total_semesters = _total_semesters(student)
    current_sem = _current_semester_num(student)
    remaining_semesters = max(total_semesters - current_sem + 1, 0)

    credits_per_semester = (
        completed_credits / len(periods) if periods else CREDITS_PER_SUBJECT * 5
    )
    remaining_credits = remaining_semesters * credits_per_semester

    required_gpa = required_gpa_for_target(
        target_cgpa, completed_qp, completed_credits, remaining_credits
    )

    risk = detect_risk(current_cgpa, timeline)

    expected_cgpa = target_cgpa
    recovery = recovery_plan(
        expected_cgpa=expected_cgpa,
        actual_cgpa=current_cgpa,
        remaining_semesters=remaining_semesters,
        completed_qp=completed_qp,
        completed_credits=completed_credits,
        credits_per_semester=credits_per_semester,
    )

    if required_gpa is not None and remaining_semesters:
        required_message = (
            f'You need {required_gpa:.2f} average in the next '
            f'{remaining_semesters} semester{"s" if remaining_semesters != 1 else ""} '
            f'to hit {target_cgpa:.2f} CGPA.'
        )
    elif remaining_semesters == 0:
        required_message = 'No remaining semesters — CGPA is final for this program stage.'
    else:
        required_message = 'Add more marks to calculate required GPA.'

    semester_gpa_chart = {
        'labels': [p['semester_label'] for p in periods],
        'datasets': [{
            'label': 'Semester GPA',
            'data': [p['gpa'] for p in periods],
            'borderColor': '#667eea',
            'backgroundColor': '#667eea',
            'pointBackgroundColor': '#667eea',
            'tension': 0.35,
            'fill': False,
        }],
    }

    cgpa_growth_chart = {
        'labels': [t['label'] for t in timeline],
        'datasets': [{
            'label': 'CGPA',
            'data': [t['cgpa'] for t in timeline],
            'borderColor': '#10b981',
            'backgroundColor': '#10b981',
            'pointBackgroundColor': '#10b981',
            'tension': 0.35,
            'fill': False,
        }],
    }

    return {
        'periods': periods,
        'timeline': timeline,
        'strengths': strengths,
        'current_cgpa': current_cgpa,
        'target_cgpa': target_cgpa,
        'total_semesters': total_semesters,
        'current_semester': current_sem,
        'remaining_semesters': remaining_semesters,
        'completed_credits': completed_credits,
        'completed_quality_points': round(completed_qp, 2),
        'remaining_credits': round(remaining_credits, 1),
        'credits_per_semester': round(credits_per_semester, 1),
        'required_gpa': required_gpa,
        'required_message': required_message,
        'recovery': recovery,
        'risk': risk,
        'has_data': bool(periods),
        'semester_gpa_chart': semester_gpa_chart,
        'cgpa_growth_chart': cgpa_growth_chart,
    }
