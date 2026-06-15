"""
GPA / CGPA forecasting engine.

The model is deterministic and auditable: it uses teacher-entered Result rows,
orders them by terminal, validates the forecast with rolling historical
predictions, and exposes chart-ready data for the student dashboard.
"""
from __future__ import annotations

from collections import defaultdict
from statistics import mean

from core.grading_utils import grade_info_for_percentage
from core.models import Result

TERMINALS = ['1st', '2nd', '3rd', 'Final']
TERMINAL_LABELS = {
    '1st': '1st Terminal',
    '2nd': '2nd Terminal',
    '3rd': '3rd Terminal',
    'Final': 'Final Terminal',
}
CREDITS_PER_SUBJECT = 3
STRONG_THRESHOLD = 70
WEAK_THRESHOLD = 50
CRITICAL_CGPA = 3.0
MAX_GPA = 4.0
MIN_GPA = 0.0


def _clamp_gpa(value: float) -> float:
    return round(max(MIN_GPA, min(MAX_GPA, float(value))), 2)


def _safe_pct(result) -> float:
    return round((result.marks_obtained / result.total_marks * 100), 2) if result.total_marks else 0.0


def _gpa_point_from_pct(percentage: float) -> float:
    return float(grade_info_for_percentage(percentage)['subject_gpa'])


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


def _terminal_order(terminal: str) -> int:
    try:
        return TERMINALS.index(terminal)
    except ValueError:
        return len(TERMINALS)


def _linear_slope(values: list[float]) -> float:
    """Return GPA points gained/lost per period using least-squares slope."""
    if len(values) < 2:
        return 0.0
    xs = list(range(len(values)))
    x_bar = mean(xs)
    y_bar = mean(values)
    denom = sum((x - x_bar) ** 2 for x in xs)
    if denom == 0:
        return 0.0
    return sum((x - x_bar) * (y - y_bar) for x, y in zip(xs, values)) / denom


def _predict_next_gpa(values: list[float]) -> float:
    """
    Predict the next terminal GPA from prior terminal GPAs.

    The blend favors recent performance while still considering trend. This is
    intentionally simple because the dataset per student is small.
    """
    if not values:
        return 0.0
    if len(values) == 1:
        return _clamp_gpa(values[-1])

    recent_window = values[-3:]
    weighted_recent = sum((i + 1) * v for i, v in enumerate(recent_window)) / sum(range(1, len(recent_window) + 1))
    slope_projection = values[-1] + _linear_slope(values)
    return _clamp_gpa((weighted_recent * 0.65) + (slope_projection * 0.35))


def _load_student_results(student) -> list:
    return list(
        Result.objects.filter(student=student)
        .select_related('subject')
        .order_by('terminal', 'subject__name', 'id')
    )


def compute_semester_periods(student, results: list | None = None) -> list[dict]:
    """Aggregate teacher-entered subject marks by terminal period."""
    results = _load_student_results(student) if results is None else results
    by_terminal: dict[str, list] = defaultdict(list)
    for result in results:
        by_terminal[result.terminal].append(result)

    periods = []
    for terminal in sorted(by_terminal, key=_terminal_order):
        term_results = by_terminal[terminal]
        quality_points = 0.0
        credits = 0
        marks_obtained = 0.0
        total_marks = 0.0
        failed_subjects = 0

        subject_rows = []
        for result in term_results:
            pct = _safe_pct(result)
            gp = _gpa_point_from_pct(pct)
            cr = CREDITS_PER_SUBJECT
            quality_points += gp * cr
            credits += cr
            marks_obtained += result.marks_obtained
            total_marks += result.total_marks
            failed_subjects += 0 if pct >= 40 else 1
            subject_rows.append({
                'subject': result.subject.name,
                'subject_code': result.subject.code,
                'percentage': pct,
                'gpa_point': gp,
                'marks_obtained': result.marks_obtained,
                'total_marks': result.total_marks,
                'passed': pct >= 40,
            })

        gpa = round(quality_points / credits, 2) if credits else 0.0
        overall_pct = round((marks_obtained / total_marks * 100), 1) if total_marks else 0.0
        periods.append({
            'terminal': terminal,
            'label': TERMINAL_LABELS.get(terminal, terminal),
            'semester_label': f'Period {len(periods) + 1}',
            'gpa': gpa,
            'overall_pct': overall_pct,
            'credits': credits,
            'quality_points': round(quality_points, 2),
            'subject_count': len(term_results),
            'failed_subjects': failed_subjects,
            'subjects': subject_rows,
            'order': _terminal_order(terminal),
        })
    return periods


def compute_cgpa_timeline(periods: list[dict]) -> list[dict]:
    """Running CGPA after each completed terminal period."""
    timeline = []
    cum_qp = 0.0
    cum_cr = 0
    for period in periods:
        cum_qp += period['quality_points']
        cum_cr += period['credits']
        timeline.append({
            'label': period['semester_label'],
            'terminal': period['terminal'],
            'terminal_label': period['label'],
            'semester_gpa': period['gpa'],
            'cgpa': round(cum_qp / cum_cr, 2) if cum_cr else 0.0,
            'credits': cum_cr,
        })
    return timeline


def compute_subject_strengths(student, results: list | None = None) -> list[dict]:
    """Average %, latest %, trend, and classification per subject."""
    results = _load_student_results(student) if results is None else results
    by_subject: dict[int, dict] = {}
    for result in results:
        entry = by_subject.setdefault(result.subject_id, {
            'subject': result.subject.name,
            'subject_code': result.subject.code,
            'points': [],
        })
        entry['points'].append({
            'terminal': result.terminal,
            'order': _terminal_order(result.terminal),
            'percentage': _safe_pct(result),
            'gpa_point': _gpa_point_from_pct(_safe_pct(result)),
        })

    strengths = []
    for entry in by_subject.values():
        points = sorted(entry['points'], key=lambda p: p['order'])
        percentages = [p['percentage'] for p in points]
        avg = round(mean(percentages), 1)
        latest = percentages[-1]
        slope = round(_linear_slope(percentages), 2)
        if avg >= STRONG_THRESHOLD:
            level, label = 'strong', 'Strong'
        elif avg >= WEAK_THRESHOLD:
            level, label = 'average', 'Average'
        else:
            level, label = 'weak', 'Weak'
        if slope <= -5:
            trend = 'declining'
        elif slope >= 5:
            trend = 'improving'
        else:
            trend = 'stable'
        strengths.append({
            'subject': entry['subject'],
            'subject_code': entry['subject_code'],
            'average_pct': avg,
            'latest_pct': round(latest, 1),
            'trend_delta': slope,
            'trend': trend,
            'level': level,
            'label': label,
            'samples': len(points),
            'points': points,
        })
    strengths.sort(key=lambda item: (item['level'] == 'weak', item['average_pct']), reverse=True)
    return strengths


def forecast_future_periods(periods: list[dict], remaining_periods: int, completed_qp: float, completed_credits: int) -> list[dict]:
    """Project future GPA and CGPA from observed terminal GPA trend."""
    observed = [p['gpa'] for p in periods]
    if not observed or remaining_periods <= 0:
        return []

    credits_per_period = round(completed_credits / len(periods), 1) if periods else CREDITS_PER_SUBJECT * 5
    future = []
    running_qp = completed_qp
    running_credits = completed_credits
    series = observed[:]
    for index in range(remaining_periods):
        predicted_gpa = _predict_next_gpa(series)
        running_qp += predicted_gpa * credits_per_period
        running_credits += credits_per_period
        future.append({
            'label': f'Forecast {index + 1}',
            'predicted_gpa': predicted_gpa,
            'predicted_cgpa': round(running_qp / running_credits, 2) if running_credits else predicted_gpa,
            'credits': credits_per_period,
        })
        series.append(predicted_gpa)
    return future


def temporal_validation(periods: list[dict]) -> dict:
    """Backtest one-step-ahead GPA prediction against known terminal marks."""
    if len(periods) < 3:
        return {
            'sample_size': max(len(periods) - 1, 0),
            'mae': None,
            'max_error': None,
            'reliability_score': None,
            'quality': 'insufficient',
            'message': 'At least 3 completed terminals are needed to validate forecast accuracy.',
            'points': [],
        }

    actuals = [p['gpa'] for p in periods]
    points = []
    errors = []
    for idx in range(1, len(actuals)):
        predicted = _predict_next_gpa(actuals[:idx])
        actual = actuals[idx]
        error = round(abs(predicted - actual), 2)
        errors.append(error)
        points.append({
            'label': periods[idx]['semester_label'],
            'terminal': periods[idx]['terminal'],
            'predicted': predicted,
            'actual': actual,
            'error': error,
        })

    mae = round(mean(errors), 2)
    max_error = round(max(errors), 2)
    reliability_score = round(max(0, min(100, 100 - (mae / MAX_GPA * 100))), 0)
    if mae <= 0.25:
        quality = 'strong'
        message = 'Historical backtest error is low; the forecast is relatively reliable.'
    elif mae <= 0.55:
        quality = 'moderate'
        message = 'Historical backtest error is moderate; use the forecast as a planning guide.'
    else:
        quality = 'volatile'
        message = 'Performance has been volatile; forecast confidence is limited.'

    return {
        'sample_size': len(points),
        'mae': mae,
        'max_error': max_error,
        'reliability_score': int(reliability_score),
        'quality': quality,
        'message': message,
        'points': points,
    }


def detect_risk(cgpa: float, timeline: list[dict], validation: dict) -> dict:
    if not timeline:
        return {
            'level': 'medium',
            'title': 'Awaiting Marks',
            'message': 'Add teacher-entered marks to unlock GPA forecasting.',
            'icon': 'fa-circle-info',
        }
    if cgpa < CRITICAL_CGPA:
        return {
            'level': 'critical',
            'title': 'Critical Risk',
            'message': f'CGPA {cgpa:.2f} is below {CRITICAL_CGPA:.1f}; immediate academic support is recommended.',
            'icon': 'fa-exclamation-triangle',
        }
    if validation.get('quality') == 'volatile':
        return {
            'level': 'high',
            'title': 'Volatile Trend',
            'message': 'Recent terminal marks fluctuate heavily; focus on consistency across subjects.',
            'icon': 'fa-wave-square',
        }
    if len(timeline) >= 2:
        delta = timeline[-1]['cgpa'] - timeline[-2]['cgpa']
        if delta < -0.1:
            return {
                'level': 'high',
                'title': 'Declining CGPA',
                'message': 'CGPA is trending down; prioritize weak and declining subjects this term.',
                'icon': 'fa-arrow-down',
            }
        if delta > 0.05:
            return {
                'level': 'low',
                'title': 'Improving CGPA',
                'message': 'CGPA is improving; keep the current study plan and protect strong subjects.',
                'icon': 'fa-arrow-up',
            }
    return {
        'level': 'medium',
        'title': 'Stable Performance',
        'message': 'Performance is stable; use the target calculator to plan the next terminal.',
        'icon': 'fa-minus',
    }


def required_gpa_for_target(
    target_cgpa: float,
    completed_qp: float,
    completed_credits: int | float,
    remaining_credits: int | float,
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
    feasible = MIN_GPA <= required <= MAX_GPA
    required_display = _clamp_gpa(required)
    return {
        'expected_cgpa': expected_cgpa,
        'actual_cgpa': actual_cgpa,
        'gap': gap,
        'required_gpa': required_display,
        'raw_required_gpa': round(required, 2),
        'feasible': feasible,
        'extra_per_semester': round(gap / remaining_semesters, 2) if remaining_semesters else 0,
        'remaining_semesters': remaining_semesters,
        'message': (
            f'You need {required_display:.2f} average GPA in the next '
            f'{remaining_semesters} period{"s" if remaining_semesters != 1 else ""} '
            f'to reach {expected_cgpa:.2f} CGPA.'
        ) if feasible else (
            f'The target requires {required:.2f} average GPA, above the 4.0 maximum. '
            f'Choose a staged target or add more high-scoring periods first.'
        ),
        'recovery_message': (
            f'Current gap is {gap:.2f} CGPA points. Prioritize subjects with weak averages or declining trends.'
        ),
    }


def _chart_dataset(label: str, data: list, color: str, **extra) -> dict:
    ds = {
        'label': label,
        'data': data,
        'borderColor': color,
        'backgroundColor': color,
        'pointBackgroundColor': color,
        'tension': 0.35,
        'fill': False,
    }
    ds.update(extra)
    return ds


def build_chart_payloads(periods: list[dict], timeline: list[dict], future: list[dict], strengths: list[dict], validation: dict) -> dict:
    observed_labels = [p['semester_label'] for p in periods]
    future_labels = [f['label'] for f in future]
    combined_labels = observed_labels + future_labels
    observed_gpa = [p['gpa'] for p in periods]
    observed_cgpa = [t['cgpa'] for t in timeline]

    forecast_gpa = [None for _ in periods] + [f['predicted_gpa'] for f in future]
    forecast_cgpa = [None for _ in periods] + [f['predicted_cgpa'] for f in future]
    if periods and future:
        forecast_gpa[len(periods) - 1] = periods[-1]['gpa']
        forecast_cgpa[len(periods) - 1] = timeline[-1]['cgpa']

    return {
        'semester_gpa_chart': {
            'labels': combined_labels,
            'datasets': [
                _chart_dataset('Observed GPA', observed_gpa + [None for _ in future], '#2563eb'),
                _chart_dataset('Forecast GPA', forecast_gpa, '#f59e0b', borderDash=[6, 4]),
            ],
        },
        'cgpa_growth_chart': {
            'labels': combined_labels,
            'datasets': [
                _chart_dataset('Observed CGPA', observed_cgpa + [None for _ in future], '#10b981'),
                _chart_dataset('Forecast CGPA', forecast_cgpa, '#8b5cf6', borderDash=[6, 4]),
            ],
        },
        'subject_strength_chart': {
            'labels': [s['subject'] for s in strengths],
            'datasets': [{
                'label': 'Average %',
                'data': [s['average_pct'] for s in strengths],
                'backgroundColor': [
                    '#10b981' if s['level'] == 'strong' else '#f59e0b' if s['level'] == 'average' else '#ef4444'
                    for s in strengths
                ],
                'borderRadius': 6,
            }],
        },
        'validation_chart': {
            'labels': [p['label'] for p in validation.get('points', [])],
            'datasets': [
                _chart_dataset('Predicted GPA', [p['predicted'] for p in validation.get('points', [])], '#f59e0b'),
                _chart_dataset('Actual GPA', [p['actual'] for p in validation.get('points', [])], '#2563eb'),
            ],
        },
    }


def build_recommendations(strengths: list[dict], validation: dict, required_gpa: float | None) -> list[str]:
    recommendations = []
    weak = [s for s in strengths if s['level'] == 'weak']
    declining = [s for s in strengths if s['trend'] == 'declining']

    if weak:
        recommendations.append(f"Focus first on {', '.join(s['subject'] for s in weak[:3])}; these subjects pull GPA down fastest.")
    if declining:
        recommendations.append(f"Review recent preparation in {', '.join(s['subject'] for s in declining[:3])}; the temporal trend is declining.")
    if required_gpa is not None and required_gpa > 3.7:
        recommendations.append('Target requires near A-level performance; consider a staged target and weekly subject checkpoints.')
    if validation.get('quality') == 'volatile':
        recommendations.append('Prediction reliability is limited by volatile marks; improve consistency before trusting long-range forecasts.')
    if not recommendations:
        recommendations.append('Maintain current study rhythm and use the next terminal as a checkpoint against the forecast line.')
    return recommendations


def build_gpa_forecast(student, target_cgpa: float = 3.5) -> dict:
    results = _load_student_results(student)
    periods = compute_semester_periods(student, results)
    timeline = compute_cgpa_timeline(periods)
    strengths = compute_subject_strengths(student, results)

    completed_qp = sum(p['quality_points'] for p in periods)
    completed_credits = sum(p['credits'] for p in periods)
    current_cgpa = round(completed_qp / completed_credits, 2) if completed_credits else 0.0

    total_semesters = _total_semesters(student)
    current_sem = min(max(_current_semester_num(student), len(periods) or 1), total_semesters)
    remaining_semesters = max(total_semesters - len(periods), 0)
    credits_per_semester = round(completed_credits / len(periods), 1) if periods else CREDITS_PER_SUBJECT * 5
    remaining_credits = remaining_semesters * credits_per_semester

    required_raw = required_gpa_for_target(
        target_cgpa, completed_qp, completed_credits, remaining_credits
    )
    required_gpa = _clamp_gpa(required_raw) if required_raw is not None else None
    validation = temporal_validation(periods)
    future = forecast_future_periods(periods, remaining_semesters, completed_qp, completed_credits)
    projected_cgpa = future[-1]['predicted_cgpa'] if future else current_cgpa
    risk = detect_risk(current_cgpa, timeline, validation)
    recovery = recovery_plan(
        expected_cgpa=target_cgpa,
        actual_cgpa=current_cgpa,
        remaining_semesters=remaining_semesters,
        completed_qp=completed_qp,
        completed_credits=completed_credits,
        credits_per_semester=credits_per_semester,
    )

    if required_raw is not None and remaining_semesters:
        if required_raw > MAX_GPA:
            required_message = (
                f'Target {target_cgpa:.2f} requires {required_raw:.2f} average GPA, '
                'which is above the 4.0 maximum.'
            )
        elif required_raw < MIN_GPA:
            required_message = f'Current performance already protects the {target_cgpa:.2f} target.'
        else:
            required_message = (
                f'You need {required_raw:.2f} average in the next '
                f'{remaining_semesters} period{"s" if remaining_semesters != 1 else ""} '
                f'to hit {target_cgpa:.2f} CGPA.'
            )
    elif remaining_semesters == 0:
        required_message = 'No remaining periods in this program stage; CGPA is final for the available marks.'
    else:
        required_message = 'Add more teacher-entered marks to calculate required GPA.'

    charts = build_chart_payloads(periods, timeline, future, strengths, validation)
    recommendations = build_recommendations(strengths, validation, required_raw)

    return {
        'periods': periods,
        'timeline': timeline,
        'future_periods': future,
        'strengths': strengths,
        'validation': validation,
        'recommendations': recommendations,
        'current_cgpa': current_cgpa,
        'projected_cgpa': projected_cgpa,
        'target_cgpa': target_cgpa,
        'total_semesters': total_semesters,
        'current_semester': current_sem,
        'remaining_semesters': remaining_semesters,
        'completed_credits': completed_credits,
        'completed_quality_points': round(completed_qp, 2),
        'remaining_credits': round(remaining_credits, 1),
        'credits_per_semester': credits_per_semester,
        'required_gpa': required_gpa,
        'raw_required_gpa': round(required_raw, 2) if required_raw is not None else None,
        'required_message': required_message,
        'recovery': recovery,
        'risk': risk,
        'has_data': bool(periods),
        **charts,
    }
