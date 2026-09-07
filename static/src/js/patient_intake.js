/** @odoo-module **/

(function () {
    'use strict';

    function initSignaturePads(form) {
        const pads = form.querySelectorAll('.o_sig_pad');
        if (!pads.length) {
            return;
        }
        pads.forEach(function (pad) {
            const key = pad.dataset.sigPad;
            const canvas = pad.querySelector('canvas');
            const input = form.querySelector('input[data-sig-input="' + key + '"]');
            const clearBtn = form.querySelector('[data-sig-clear="' + key + '"]');
            if (!canvas || !input) {
                return;
            }
            const ctx = canvas.getContext('2d');
            let drawing = false;
            let hasInk = false;

            ctx.strokeStyle = '#1a2530';
            ctx.lineWidth = 2.5;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';

            function drawPlaceholder() {
                if (hasInk) {
                    return;
                }
                ctx.save();
                ctx.setLineDash([6, 4]);
                ctx.strokeStyle = '#c9c9c9';
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                ctx.moveTo(canvas.width * 0.08, canvas.height * 0.5);
                ctx.lineTo(canvas.width * 0.92, canvas.height * 0.5);
                ctx.stroke();
                ctx.restore();
                ctx.fillStyle = '#9aa0a6';
                ctx.font = '20px sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText('Sign here', canvas.width / 2, canvas.height / 2);
            }

            function getPos(ev) {
                const rect = canvas.getBoundingClientRect();
                const scaleX = canvas.width / rect.width;
                const scaleY = canvas.height / rect.height;
                return {
                    x: (ev.clientX - rect.left) * scaleX,
                    y: (ev.clientY - rect.top) * scaleY,
                };
            }

            canvas.addEventListener('pointerdown', function (ev) {
                ev.preventDefault();
                canvas.setPointerCapture(ev.pointerId);
                drawing = true;
                hasInk = true;
                const p = getPos(ev);
                ctx.setLineDash([]);
                ctx.beginPath();
                ctx.moveTo(p.x, p.y);
            });
            canvas.addEventListener('pointermove', function (ev) {
                if (!drawing) {
                    return;
                }
                ev.preventDefault();
                const p = getPos(ev);
                ctx.lineTo(p.x, p.y);
                ctx.stroke();
            });
            function endDrawing() {
                drawing = false;
            }
            canvas.addEventListener('pointerup', endDrawing);
            canvas.addEventListener('pointercancel', endDrawing);

            if (clearBtn) {
                clearBtn.addEventListener('click', function (ev) {
                    ev.preventDefault();
                    ctx.setLineDash([]);
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    hasInk = false;
                    input.value = '';
                    drawPlaceholder();
                });
            }

            form.addEventListener('submit', function () {
                input.value = hasInk ? canvas.toDataURL('image/png') : '';
            });

            drawPlaceholder();
        });
    }

    function initStepper(form) {
        const steps = Array.prototype.slice.call(form.querySelectorAll('.o_intake_step'));
        if (!steps.length) {
            return null;
        }
        const indicators = form.querySelectorAll('[data-step-ind]');
        const nextBtn = form.querySelector('[data-step-next]');
        const prevBtn = form.querySelector('[data-step-prev]');
        const submitBtn = form.querySelector('[data-step-submit]');
        let index = 0;
        steps.forEach(function (step, j) {
            if (step.classList.contains('active')) {
                index = j;
            }
        });

        function show(i) {
            index = Math.max(0, Math.min(i, steps.length - 1));
            steps.forEach(function (step, j) {
                step.classList.toggle('active', j === index);
                step.disabled = j !== index;
            });
            indicators.forEach(function (el) {
                const n = parseInt(el.dataset.stepInd, 10);
                el.classList.toggle('active', n === index + 1);
                el.classList.toggle('done', n < index + 1);
            });
            if (nextBtn) {
                nextBtn.classList.toggle('d-none', index === steps.length - 1);
            }
            if (prevBtn) {
                prevBtn.classList.toggle('d-none', index === 0);
            }
            if (submitBtn) {
                submitBtn.classList.toggle('d-none', index !== steps.length - 1);
            }
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', function (ev) {
                ev.preventDefault();
                if (!form.checkValidity()) {
                    form.reportValidity();
                    return;
                }
                show(index + 1);
            });
        }
        if (prevBtn) {
            prevBtn.addEventListener('click', function (ev) {
                ev.preventDefault();
                show(index - 1);
            });
        }

        form.addEventListener('keydown', function (ev) {
            if (ev.key === 'Enter' && ev.target.tagName === 'INPUT') {
                ev.preventDefault();
                if (index === steps.length - 1) {
                    form.requestSubmit();
                } else if (nextBtn) {
                    nextBtn.click();
                }
            }
        });

        form.addEventListener('submit', function (ev) {
            ev.preventDefault();
            const activeStep = steps[index];
            if (!activeStep.checkValidity()) {
                activeStep.reportValidity();
                return;
            }
            const missing = Array.prototype.slice
                .call(form.querySelectorAll('input[data-sig-required]'))
                .filter(function (i) {
                    return !i.value;
                });
            if (missing.length) {
                alert('Please draw your signature on both the Data Privacy Consent and the Waiver before submitting.');
                show(steps.length - 1);
                return;
            }
            steps.forEach(function (step) {
                step.disabled = false;
            });
            form.submit();
        });

        show(0);
    }

    function init() {
        const form = document.getElementById('odental_intake_form');
        if (!form) {
            return;
        }
        initSignaturePads(form);
        initStepper(form);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();