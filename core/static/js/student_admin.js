'use strict';

(function() {
    var LEVEL_CONFIG = {
        school: {
            classLabel: 'Student class:',
            classHint: 'Select class 1–10',
            classOptions: [
                ['', '---------'],
                ['1', '1'], ['2', '2'], ['3', '3'], ['4', '4'], ['5', '5'],
                ['6', '6'], ['7', '7'], ['8', '8'], ['9', '9'], ['10', '10']
            ]
        },
        college: {
            classLabel: 'Student class:',
            classHint: 'Select XI or XII',
            classOptions: [
                ['', '---------'],
                ['XI', 'XI'],
                ['XII', 'XII']
            ]
        },
        bachelor: {
            semesterLabel: 'Student Semester:',
            semesterHint: 'Select semester 1st–8th',
            semesterOptions: [
                ['', '---------'],
                ['1', '1st Semester'],
                ['2', '2nd Semester'],
                ['3', '3rd Semester'],
                ['4', '4th Semester'],
                ['5', '5th Semester'],
                ['6', '6th Semester'],
                ['7', '7th Semester'],
                ['8', '8th Semester']
            ]
        }
    };

    function init($) {
        function $row(fieldName) {
            return $('.form-row.field-' + fieldName + ', .fieldBox.field-' + fieldName);
        }

        function $label(fieldName) {
            return $('label[for="id_' + fieldName + '"]');
        }

        function $field(fieldName) {
            return $('#id_' + fieldName);
        }

        function ensureSelect($el) {
            if ($el.length && !$el.is('select')) {
                var $select = $('<select>', {
                    name: $el.attr('name'),
                    id: $el.attr('id'),
                    'class': 'student-level-select'
                });
                $el.replaceWith($select);
                return $select;
            }
            return $el;
        }

        function setSelectOptions($el, options, valueToKeep) {
            $el = ensureSelect($el);
            if (!$el.length) {
                return;
            }

            var keep = '';
            if (valueToKeep) {
                for (var i = 0; i < options.length; i++) {
                    if (options[i][0] === valueToKeep) {
                        keep = valueToKeep;
                        break;
                    }
                }
            }

            $el.empty();
            options.forEach(function(pair) {
                $el.append($('<option>', { value: pair[0], text: pair[1] }));
            });
            $el.val(keep);
            $el.addClass('is-updating');
            setTimeout(function() { $el.removeClass('is-updating'); }, 400);
        }

        function ensureHint($rowEl, fieldName, text) {
            var id = 'hint-' + fieldName;
            var $hint = $('#' + id);
            if (!$hint.length) {
                $hint = $('<span>', { id: id, 'class': 'student-level-hint' });
                $rowEl.find('div').last().append($hint);
            }
            $hint.text(text || '');
            return $hint;
        }

        function wrapRows() {
            ['student_class', 'semester'].forEach(function(name) {
                var $r = $row(name).first();
                if ($r.length && !$r.parent().hasClass('student-level-field-wrap')) {
                    $r.wrap('<div class="student-level-field-wrap"></div>');
                }
            });
        }

        function setRowVisible(fieldName, visible) {
            var $wrap = $row(fieldName).first().closest('.student-level-field-wrap');
            if (!$wrap.length) {
                return;
            }

            var $input = $field(fieldName);
            if (visible) {
                $wrap.removeClass('is-collapsed').addClass('is-expanded');
                $row(fieldName).first().show();
                $input.prop('disabled', false);
            } else {
                $wrap.removeClass('is-expanded').addClass('is-collapsed');
                $row(fieldName).first().hide();
                $input.prop('disabled', true).val('');
            }
        }

        function applyLevel(level, resetValues) {
            var cfg = LEVEL_CONFIG[level] || LEVEL_CONFIG.school;
            wrapRows();

            if (level === 'bachelor') {
                setRowVisible('student_class', false);
                setRowVisible('semester', true);

                $label('semester').text(cfg.semesterLabel);
                var semVal = resetValues ? '' : $field('semester').val();
                setSelectOptions($field('semester'), cfg.semesterOptions, resetValues ? '' : semVal);
                ensureHint($row('semester').first(), 'semester', cfg.semesterHint).addClass('is-visible');
                ensureHint($row('student_class').first(), 'student_class', '').removeClass('is-visible');
            } else {
                setRowVisible('semester', false);
                setRowVisible('student_class', true);

                $label('student_class').text(cfg.classLabel);
                var classVal = resetValues ? '' : $field('student_class').val();
                setSelectOptions($field('student_class'), cfg.classOptions, resetValues ? '' : classVal);
                ensureHint($row('student_class').first(), 'student_class', cfg.classHint).addClass('is-visible');
                ensureHint($row('semester').first(), 'semester', '').removeClass('is-visible');
            }
        }

        var $level = $('#id_level');
        if (!$level.length) {
            return;
        }

        wrapRows();
        applyLevel($level.val() || 'school', false);

        $level.on('change', function() {
            applyLevel($(this).val(), true);
        });

        $('form').on('submit', function() {
            $('#id_student_class, #id_semester').prop('disabled', false);
        });
    }

    function boot() {
        var $ = window.django && window.django.jQuery;
        if (!$) {
            return false;
        }
        $(function() { init($); });
        return true;
    }

    function waitForDjangoJQuery() {
        if (boot()) {
            return;
        }
        window.setTimeout(waitForDjangoJQuery, 30);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', waitForDjangoJQuery);
    } else {
        waitForDjangoJQuery();
    }
})();
