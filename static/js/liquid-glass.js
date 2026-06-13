/**
 * AcadStat — SVG displacement liquid glass for navbars (iOS 26–style)
 */
(function () {
    'use strict';

    const NAV_CONFIG = {
        glassThickness: 52,
        bezelWidth: 36,
        ior: 1.45,
        scaleRatio: 0.88,
        blur: 0.85,
        specularOpacity: 0.52,
        specularSat: 0,
        tintColor: '255,255,255',
        tintOpacity: 0.07,
        innerShadow: 'rgba(255,255,255,0.18)',
        innerShadowBlur: 14,
        innerShadowSpread: -8,
        balancedSpecular: true,
    };

    const targets = new Map();
    let defs = null;

    function clamp(n, min, max) {
        return Math.min(max, Math.max(min, n));
    }

    function navConfig() {
        const dark = document.documentElement.getAttribute('data-theme') === 'dark';
        return {
            ...NAV_CONFIG,
            tintColor: dark ? '24,28,38' : '255,255,255',
            tintOpacity: dark ? 0.14 : 0.09,
            innerShadow: dark ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.22)',
        };
    }

    function surfaceFn(x) {
        return Math.pow(1 - Math.pow(1 - x, 4), 0.25);
    }

    function calcRefractionProfile(glassThickness, bezelWidth, ior, samples) {
        samples = samples || 128;
        const eta = 1 / ior;
        function refract(nx, ny) {
            const dot = ny;
            const k = 1 - eta * eta * (1 - dot * dot);
            if (k < 0) return null;
            const sq = Math.sqrt(k);
            return [-(eta * dot + sq) * nx, eta - (eta * dot + sq) * ny];
        }
        const p = new Float64Array(samples);
        for (let i = 0; i < samples; i++) {
            const x = i / samples;
            const y = surfaceFn(x);
            const dx = x < 1 ? 0.0001 : -0.0001;
            const y2 = surfaceFn(x + dx);
            const deriv = (y2 - y) / dx;
            const mag = Math.sqrt(deriv * deriv + 1);
            const ref = refract(-deriv / mag, -1 / mag);
            p[i] = ref ? ref[0] * ((y * bezelWidth + glassThickness) / ref[1]) : 0;
        }
        return p;
    }

    function generateDisplacementMap(w, h, radius, bezelWidth, profile, maxDisp) {
        const c = document.createElement('canvas');
        c.width = w;
        c.height = h;
        const ctx = c.getContext('2d');
        const img = ctx.createImageData(w, h);
        const d = img.data;
        for (let i = 0; i < d.length; i += 4) {
            d[i] = 128;
            d[i + 1] = 128;
            d[i + 2] = 0;
            d[i + 3] = 255;
        }
        const r = radius;
        const rSq = r * r;
        const r1Sq = (r + 1) ** 2;
        const rBSq = Math.max(r - bezelWidth, 0) ** 2;
        const wB = w - r * 2;
        const hB = h - r * 2;
        const S = profile.length;
        for (let y1 = 0; y1 < h; y1++) {
            for (let x1 = 0; x1 < w; x1++) {
                const x = x1 < r ? x1 - r : x1 >= w - r ? x1 - r - wB : 0;
                const y = y1 < r ? y1 - r : y1 >= h - r ? y1 - r - hB : 0;
                const dSq = x * x + y * y;
                if (dSq > r1Sq || dSq < rBSq) continue;
                const dist = Math.sqrt(dSq);
                const fromSide = r - dist;
                const op = dSq < rSq ? 1 : 1 - (dist - Math.sqrt(rSq)) / (Math.sqrt(r1Sq) - Math.sqrt(rSq));
                if (op <= 0 || dist === 0) continue;
                const cos = x / dist;
                const sin = y / dist;
                const bi = Math.min(((fromSide / bezelWidth) * S) | 0, S - 1);
                const disp = profile[bi] || 0;
                const dX = (-cos * disp) / maxDisp;
                const dY = (-sin * disp) / maxDisp;
                const idx = (y1 * w + x1) * 4;
                d[idx] = (128 + dX * 127 * op + 0.5) | 0;
                d[idx + 1] = (128 + dY * 127 * op + 0.5) | 0;
            }
        }
        ctx.putImageData(img, 0, 0);
        return c.toDataURL();
    }

    function generateSpecularMap(w, h, radius, bezelWidth, balanced) {
        const angle = Math.PI / 3;
        const c = document.createElement('canvas');
        c.width = w;
        c.height = h;
        const ctx = c.getContext('2d');
        const img = ctx.createImageData(w, h);
        const d = img.data;
        d.fill(0);
        const r = radius;
        const rSq = r * r;
        const r1Sq = (r + 1) ** 2;
        const rBSq = Math.max(r - bezelWidth, 0) ** 2;
        const wB = w - r * 2;
        const hB = h - r * 2;
        const sv = [Math.cos(angle), Math.sin(angle)];
        for (let y1 = 0; y1 < h; y1++) {
            for (let x1 = 0; x1 < w; x1++) {
                const x = x1 < r ? x1 - r : x1 >= w - r ? x1 - r - wB : 0;
                const y = y1 < r ? y1 - r : y1 >= h - r ? y1 - r - hB : 0;
                const dSq = x * x + y * y;
                if (dSq > r1Sq || dSq < rBSq) continue;
                const dist = Math.sqrt(dSq);
                const fromSide = r - dist;
                const op = dSq < rSq ? 1 : 1 - (dist - Math.sqrt(rSq)) / (Math.sqrt(r1Sq) - Math.sqrt(rSq));
                if (op <= 0 || dist === 0) continue;
                const cos = x / dist;
                const sin = -y / dist;
                const dot = balanced ? 1 : Math.abs(cos * sv[0] + sin * sv[1]);
                const edge = Math.sqrt(Math.max(0, 1 - (1 - fromSide) ** 2));
                const coeff = dot * edge;
                const col = (255 * coeff) | 0;
                const alpha = (col * coeff * op) | 0;
                const idx = (y1 * w + x1) * 4;
                d[idx] = col;
                d[idx + 1] = col;
                d[idx + 2] = col;
                d[idx + 3] = alpha;
            }
        }
        ctx.putImageData(img, 0, 0);
        return c.toDataURL();
    }

    function svgEl(tag, attrs) {
        const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
        Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
        return el;
    }

    function ensureDefs() {
        if (defs && document.documentElement.contains(defs)) return;
        const old = document.getElementById('acadstat-lg-defs');
        if (old) old.remove();
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '0');
        svg.setAttribute('height', '0');
        svg.style.cssText = 'position:fixed;top:0;left:0;width:0;height:0;pointer-events:none;z-index:-1;';
        defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        defs.id = 'acadstat-lg-defs';
        svg.appendChild(defs);
        document.documentElement.appendChild(svg);
    }

    function buildFilter(id, w, h, radius, cfg) {
        const bezel = Math.min(cfg.bezelWidth, radius - 1, Math.min(w, h) / 2 - 1);
        const profile = calcRefractionProfile(cfg.glassThickness, bezel, cfg.ior, 128);
        const maxDisp = Math.max(...Array.from(profile).map(Math.abs)) || 1;
        const dispUrl = generateDisplacementMap(w, h, radius, bezel, profile, maxDisp);
        const specUrl = generateSpecularMap(w, h, radius, bezel * 2.5, !!cfg.balancedSpecular);
        const scale = maxDisp * cfg.scaleRatio;
        const pad = cfg.balancedSpecular ? 0.36 : 0;
        const fx = Math.round(-w * pad);
        const fy = Math.round(-h * pad);
        const fw = Math.round(w * (1 + pad * 2));
        const fh = Math.round(h * (1 + pad * 2));

        const filter = svgEl('filter', {
            id,
            x: String(fx),
            y: String(fy),
            width: String(fw),
            height: String(fh),
            filterUnits: 'userSpaceOnUse',
            primitiveUnits: 'userSpaceOnUse',
            'color-interpolation-filters': 'sRGB',
        });
        const blur = svgEl('feGaussianBlur', { in: 'SourceGraphic', stdDeviation: cfg.blur, result: 'blurred' });
        const dispImg = svgEl('feImage', { href: dispUrl, x: 0, y: 0, width: w, height: h, result: 'disp_map' });
        const dispMap = svgEl('feDisplacementMap', {
            in: 'blurred',
            in2: 'disp_map',
            scale,
            xChannelSelector: 'R',
            yChannelSelector: 'G',
            result: 'displaced',
        });
        const sat = svgEl('feColorMatrix', { in: 'displaced', type: 'saturate', values: cfg.specularSat, result: 'displaced_sat' });
        const spec = svgEl('feImage', { href: specUrl, x: 0, y: 0, width: w, height: h, result: 'spec_layer' });
        const comp = svgEl('feComposite', { in: 'displaced_sat', in2: 'spec_layer', operator: 'in', result: 'spec_masked' });
        const tr = svgEl('feComponentTransfer', { in: 'spec_layer', result: 'spec_faded' });
        tr.appendChild(svgEl('feFuncA', { type: 'linear', slope: cfg.specularOpacity }));
        const b1 = svgEl('feBlend', { in: 'spec_masked', in2: 'displaced', mode: 'normal', result: 'with_sat' });
        const b2 = svgEl('feBlend', { in: 'spec_faded', in2: 'with_sat', mode: 'normal' });
        filter.append(blur, dispImg, dispMap, sat, spec, comp, tr, b1, b2);
        return filter;
    }

    function elevateChildren(el, refr, tint) {
        Array.from(el.children).forEach((child) => {
            if (child === refr || child === tint || child.classList.contains('lg-nav-glow')) return;
            if (getComputedStyle(child).position === 'static') child.style.position = 'relative';
            if (!child.style.zIndex) child.style.zIndex = '1';
        });
    }

    function applyGlass(el) {
        if (targets.has(el)) return;
        if (getComputedStyle(el).position === 'static') el.style.position = 'relative';

        const refr = document.createElement('div');
        refr.className = 'lg-layer lg-refract';
        refr.setAttribute('aria-hidden', 'true');
        const tint = document.createElement('div');
        tint.className = 'lg-layer lg-tint';
        tint.setAttribute('aria-hidden', 'true');

        const glow = el.querySelector('.lg-nav-glow');
        const anchor = glow ? glow.nextSibling : el.firstChild;
        el.insertBefore(refr, anchor);
        el.insertBefore(tint, refr.nextSibling);

        let filterNode = null;
        let timer = null;

        function rebuild() {
            ensureDefs();
            const rect = el.getBoundingClientRect();
            const w = Math.round(el.offsetWidth || rect.width);
            const h = Math.round(el.offsetHeight || rect.height);
            if (w < 4 || h < 4) return;

            const parentNav = el.closest('[data-lg-radius]');
            const dataR = parseFloat(
                el.getAttribute('data-lg-radius')
                || (parentNav ? parentNav.getAttribute('data-lg-radius') : '')
                || ''
            );
            const cssR = parseFloat(getComputedStyle(el).borderTopLeftRadius || '0');
            const r = Math.max(0, Math.min(
                Number.isFinite(dataR) ? dataR : cssR || 0,
                w / 2,
                h / 2
            ));

            if (filterNode) filterNode.remove();
            const cfg = navConfig();
            const id = 'acad-lg-' + Math.random().toString(36).slice(2, 10);
            filterNode = buildFilter(id, w, h, Math.max(r, 2), cfg);
            defs.appendChild(filterNode);

            const radiusPx = r + 'px';
            refr.style.borderRadius = radiusPx;
            tint.style.borderRadius = radiusPx;
            refr.style.backdropFilter = 'url(#' + id + ')';
            refr.style.webkitBackdropFilter = 'url(#' + id + ')';
            tint.style.backgroundColor = 'rgba(' + cfg.tintColor + ',' + cfg.tintOpacity + ')';
            tint.style.boxShadow = 'inset 0 0 ' + cfg.innerShadowBlur + 'px ' + cfg.innerShadowSpread + 'px ' + cfg.innerShadow;
            elevateChildren(el, refr, tint);
        }

        function schedule() {
            clearTimeout(timer);
            timer = setTimeout(rebuild, 16);
        }

        const ro = new ResizeObserver(schedule);
        ro.observe(el);

        targets.set(el, {
            rebuild,
            destroy() {
                clearTimeout(timer);
                ro.disconnect();
                if (filterNode) filterNode.remove();
                refr.remove();
                tint.remove();
            },
        });
        rebuild();
    }

    function removeGlass(el) {
        const inst = targets.get(el);
        if (!inst) return;
        inst.destroy();
        targets.delete(el);
    }

    function rebuildAll() {
        targets.forEach((inst) => inst.rebuild());
    }

    function isLandingNav(nav) {
        return nav.classList.contains('landing-nav');
    }

    function ensureNavInner(nav) {
        let inner = nav.querySelector(':scope > .lg-nav-inner');
        if (inner) return inner;

        inner = document.createElement('div');
        inner.className = 'lg-nav-inner';
        const glow = document.createElement('div');
        glow.className = 'lg-nav-glow';
        glow.setAttribute('aria-hidden', 'true');
        while (nav.firstChild) {
            inner.appendChild(nav.firstChild);
        }
        inner.insertBefore(glow, inner.firstChild);
        nav.appendChild(inner);
        return inner;
    }

    function unwrapNavInner(nav) {
        const inner = nav.querySelector(':scope > .lg-nav-inner');
        if (!inner) return;

        [...inner.children].forEach((child) => {
            if (child.classList.contains('lg-nav-glow') || child.classList.contains('lg-layer')) return;
            nav.insertBefore(child, inner);
        });
        inner.remove();
    }

    function glassHost(nav) {
        if (isLandingNav(nav) && !nav.classList.contains('scrolled')) {
            return nav;
        }
        return ensureNavInner(nav);
    }

    function navCandidates() {
        return document.querySelectorAll('.liquid-glass-nav, .landing-nav.scrolled, .app-page .navbar.app-nav-style');
    }

    function syncLandingNav(nav) {
        const past = (window.scrollY || 0) > 50;

        if (past && !nav.classList.contains('scrolled')) {
            nav.classList.add('scrolled', 'is-scrolled');
            applyGlass(ensureNavInner(nav));
            return;
        }

        if (!past && nav.classList.contains('scrolled')) {
            const host = nav.querySelector(':scope > .lg-nav-inner');
            if (host) removeGlass(host);
            nav.classList.remove('scrolled', 'is-scrolled');
            unwrapNavInner(nav);
        }
    }

    function syncNavGlass() {
        document.querySelectorAll('.landing-nav').forEach(syncLandingNav);
        document.querySelectorAll('.liquid-glass-nav, .app-page .navbar.app-nav-style').forEach((nav) => {
            if (!nav.classList.contains('landing-nav')) applyGlass(glassHost(nav));
        });
    }

    function bindNavGlow() {
        document.querySelectorAll('.lg-nav-inner').forEach((inner) => {
            const host = inner.closest('.liquid-glass-nav, .landing-nav');
            if (!host) return;
            inner.addEventListener('pointermove', (e) => {
                const r = inner.getBoundingClientRect();
                inner.style.setProperty('--gx', (e.clientX - r.left) + 'px');
                inner.style.setProperty('--gy', (e.clientY - r.top) + 'px');
                inner.style.setProperty('--ga', '0.22');
            });
            inner.addEventListener('pointerleave', () => {
                inner.style.setProperty('--ga', '0');
            });
        });
    }

    function init() {
        ensureDefs();
        syncNavGlass();
        bindNavGlow();

        window.addEventListener('scroll', () => {
            document.querySelectorAll('.landing-nav').forEach(syncLandingNav);
            navCandidates().forEach((nav) => {
                if (!nav.classList.contains('landing-nav')) {
                    nav.classList.toggle('is-scrolled', (window.scrollY || 0) > 12);
                }
            });
        }, { passive: true });

        window.addEventListener('resize', rebuildAll);
        window.addEventListener('acadstat:theme', () => {
            setTimeout(rebuildAll, 40);
        });
    }

    document.addEventListener('DOMContentLoaded', init);

    window.AcadStatLiquidGlass = { rebuildAll, syncNavGlass };
})();
