/**
 * Spiral Animation — Canvas-based particle spiral
 * Adapted from 21st.dev/Kain0127/spiral-animation for vanilla JS
 */

(function () {
    const canvas = document.getElementById('spiralCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Config
    const NUM_STARS = 3000;
    const TRAIL_LENGTH = 60;
    const SPIRAL_TURNS = 6;
    const CAMERA_Z = -400;
    const CAMERA_TRAVEL = 3400;
    const VIEW_ZOOM = 100;
    const START_DOT_Y_OFFSET = 28;
    const CHANGE_EVENT_TIME = 0.32;
    const CYCLE_DURATION = 15000; // 15 seconds per cycle

    let time = 0;
    let size = 0;
    let dpr = 1;
    let stars = [];
    let animId = null;
    let lastTimestamp = 0;

    // Seeded random for consistent star placement
    function seededRandom(seed) {
        return function () {
            seed = (seed * 9301 + 49297) % 233280;
            return seed / 233280;
        };
    }

    // Math helpers
    function ease(p, g) {
        if (p < 0.5) return 0.5 * Math.pow(2 * p, g);
        return 1 - 0.5 * Math.pow(2 * (1 - p), g);
    }

    function easeOutElastic(x) {
        const c4 = (2 * Math.PI) / 4.5;
        if (x <= 0) return 0;
        if (x >= 1) return 1;
        return Math.pow(2, -8 * x) * Math.sin((x * 8 - 0.75) * c4) + 1;
    }

    function map(value, s1, e1, s2, e2) {
        return s2 + (e2 - s2) * ((value - s1) / (e1 - s1));
    }

    function constrain(v, min, max) {
        return Math.min(Math.max(v, min), max);
    }

    function lerp(a, b, t) {
        return a * (1 - t) + b * t;
    }

    // Spiral path: parametric equation
    function spiralPath(p) {
        p = constrain(1.2 * p, 0, 1);
        p = ease(p, 1.8);
        const theta = 2 * Math.PI * SPIRAL_TURNS * Math.sqrt(p);
        const r = 170 * Math.sqrt(p);
        return { x: r * Math.cos(theta), y: r * Math.sin(theta) + START_DOT_Y_OFFSET };
    }

    // 3D projection
    function showProjectedDot(px, py, pz, sizeFactor) {
        const t2 = constrain(map(time, CHANGE_EVENT_TIME, 1, 0, 1), 0, 1);
        const newCameraZ = CAMERA_Z + ease(Math.pow(t2, 1.2), 1.8) * CAMERA_TRAVEL;

        if (pz > newCameraZ) {
            const depth = pz - newCameraZ;
            const x = VIEW_ZOOM * px / depth;
            const y = VIEW_ZOOM * py / depth;
            const sw = 400 * sizeFactor / depth;

            ctx.beginPath();
            ctx.arc(x, y, Math.max(sw / 2, 0.3), 0, Math.PI * 2);
            ctx.fill();
        }
    }

    // Star class
    function createStar(rng) {
        const angle = rng() * Math.PI * 2;
        const distance = 30 * rng() + 15;
        const rotDir = rng() > 0.5 ? 1 : -1;
        const expRate = 1.2 + rng() * 0.8;
        const finalScale = 0.7 + rng() * 0.6;
        const dx = distance * Math.cos(angle);
        const dy = distance * Math.sin(angle);
        const spiralLoc = (1 - Math.pow(1 - rng(), 3.0)) / 1.3;
        let z = lerp(0.5 * CAMERA_Z, CAMERA_TRAVEL + CAMERA_Z, rng());
        z = lerp(z, CAMERA_TRAVEL / 2, 0.3 * spiralLoc);
        const swFactor = Math.pow(rng(), 2.0);

        return { angle, distance, rotDir, expRate, finalScale, dx, dy, spiralLoc, z, swFactor };
    }

    function renderStar(star, p) {
        const sp = spiralPath(star.spiralLoc);
        const q = p - star.spiralLoc;
        if (q <= 0) return;

        const dp = constrain(4 * q, 0, 1);
        let easing;
        const lin = dp;
        const elastic = easeOutElastic(dp);
        const pow2 = Math.pow(dp, 2);

        if (dp < 0.3) easing = lerp(lin, pow2, dp / 0.3);
        else if (dp < 0.7) easing = lerp(pow2, elastic, (dp - 0.3) / 0.4);
        else easing = elastic;

        let sx, sy;

        if (dp < 0.3) {
            sx = lerp(sp.x, sp.x + star.dx * 0.3, easing / 0.3);
            sy = lerp(sp.y, sp.y + star.dy * 0.3, easing / 0.3);
        } else if (dp < 0.7) {
            const mid = (dp - 0.3) / 0.4;
            const curve = Math.sin(mid * Math.PI) * star.rotDir * 1.5;
            const bx = sp.x + star.dx * 0.3;
            const by = sp.y + star.dy * 0.3;
            const tx = sp.x + star.dx * 0.7;
            const ty = sp.y + star.dy * 0.7;
            const px2 = -star.dy * 0.4 * curve;
            const py2 = star.dx * 0.4 * curve;
            sx = lerp(bx, tx, mid) + px2 * mid;
            sy = lerp(by, ty, mid) + py2 * mid;
        } else {
            const fp = (dp - 0.7) / 0.3;
            const bx = sp.x + star.dx * 0.7;
            const by = sp.y + star.dy * 0.7;
            const td = star.distance * star.expRate * 1.5;
            const spiralAngle = star.angle + 1.2 * star.rotDir * fp * Math.PI;
            const tx = sp.x + td * Math.cos(spiralAngle);
            const ty = sp.y + td * Math.sin(spiralAngle);
            sx = lerp(bx, tx, fp);
            sy = lerp(by, ty, fp);
        }

        const vx = (star.z - CAMERA_Z) * sx / VIEW_ZOOM;
        const vy = (star.z - CAMERA_Z) * sy / VIEW_ZOOM;

        let sizeMul = 1.0;
        if (dp < 0.6) sizeMul = 1.0 + dp * 0.2;
        else {
            const t = (dp - 0.6) / 0.4;
            sizeMul = 1.2 * (1 - t) + star.finalScale * t;
        }

        showProjectedDot(vx, vy, star.z, 8.5 * star.swFactor * sizeMul);
    }

    // Draw trail
    function drawTrail(t1) {
        for (let i = 0; i < TRAIL_LENGTH; i++) {
            const f = map(i, 0, TRAIL_LENGTH, 1.1, 0.1);
            const sw = (1.3 * (1 - t1) + 3.0 * Math.sin(Math.PI * t1)) * f;
            const pt = t1 - 0.00015 * i;
            const pos = spiralPath(pt);

            ctx.beginPath();
            ctx.arc(pos.x, pos.y, Math.max(sw / 2, 0.3), 0, Math.PI * 2);
            ctx.fill();
        }
    }

    // Main render
    function render() {
        ctx.fillStyle = 'rgba(3, 7, 18, 1)';
        ctx.fillRect(0, 0, size, size);

        ctx.save();
        ctx.translate(size / 2, size / 2);

        const t1 = constrain(map(time, 0, CHANGE_EVENT_TIME + 0.25, 0, 1), 0, 1);
        const t2 = constrain(map(time, CHANGE_EVENT_TIME, 1, 0, 1), 0, 1);

        ctx.rotate(-Math.PI * ease(t2, 2.7));

        // Trail
        ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
        drawTrail(t1);

        // Stars
        ctx.fillStyle = 'rgba(255, 255, 255, 0.85)';
        for (const star of stars) {
            renderStar(star, t1);
        }

        // Center dot
        if (time > CHANGE_EVENT_TIME) {
            ctx.fillStyle = 'white';
            const dy = CAMERA_Z * START_DOT_Y_OFFSET / VIEW_ZOOM;
            showProjectedDot(0, dy, CAMERA_TRAVEL, 2.5);
        }

        ctx.restore();
    }

    // Animation loop
    function animate(timestamp) {
        if (!lastTimestamp) lastTimestamp = timestamp;
        const delta = timestamp - lastTimestamp;
        lastTimestamp = timestamp;

        time += delta / CYCLE_DURATION;
        if (time > 1) time -= 1;

        render();
        animId = requestAnimationFrame(animate);
    }

    // Resize handler
    function resize() {
        const hero = canvas.parentElement;
        const w = hero.offsetWidth;
        const h = hero.offsetHeight;
        dpr = window.devicePixelRatio || 1;
        size = Math.max(w, h);

        canvas.width = w * dpr;
        canvas.height = h * dpr;
        canvas.style.width = w + 'px';
        canvas.style.height = h + 'px';

        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.scale(dpr, dpr);
        size = Math.max(w, h);
    }

    // Init
    function init() {
        const rng = seededRandom(1234);
        stars = [];
        for (let i = 0; i < NUM_STARS; i++) {
            stars.push(createStar(rng));
        }

        resize();
        window.addEventListener('resize', resize);
        animId = requestAnimationFrame(animate);
    }

    init();
})();
