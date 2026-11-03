(function () {
    'use strict';

    var hero = document.querySelector('[data-hero]');
    if (!hero) { return; }

    var scene = hero.querySelector('[data-scene]');
    var bague = hero.querySelector('[data-bague]');
    var eclatEl = hero.querySelector('[data-eclat]');
    var canvas = hero.querySelector('[data-poussiere]');
    if (!scene || !bague || !canvas) { return; }

    var ctx = canvas.getContext('2d');
    var reduit = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var tactile = window.matchMedia('(hover: none)').matches;

    var largeur = 0;
    var hauteur = 0;
    var dpr = 1;
    var particules = [];
    var etincelles = [];
    var pointeur = { x: -9999, y: -9999, actif: false, dernierX: 0, dernierY: 0 };
    var cible = { rx: 0, ry: 0, tx: 0, ty: 0, lx: 50, ly: 36, eclat: 0 };
    var actuel = { rx: 0, ry: 0, tx: 0, ty: 0, lx: 50, ly: 36, eclat: 0 };
    var visible = true;
    var cadre = null;

    function borner(valeur, min, max) { return Math.max(min, Math.min(max, valeur)); }

    /* ---------- Poussière dorée ---------- */
    function creerParticules() {
        var nombre = Math.round(borner((largeur * hauteur) / 9500, 40, tactile ? 70 : 150));
        particules = [];
        for (var i = 0; i < nombre; i++) {
            particules.push({
                hx: Math.random() * largeur,
                hy: Math.random() * hauteur,
                vx: (Math.random() - 0.5) * 0.12,
                vy: -0.04 - Math.random() * 0.14,
                r: 0.5 + Math.random() * 1.7,
                a: 0.25 + Math.random() * 0.6,
                p: Math.random() * 6.283,
                ox: 0, oy: 0, ovx: 0, ovy: 0
            });
        }
    }

    function redimensionner() {
        var rect = hero.getBoundingClientRect();
        largeur = Math.max(1, Math.round(rect.width));
        hauteur = Math.max(1, Math.round(rect.height));
        dpr = Math.min(window.devicePixelRatio || 1, 2);
        canvas.width = Math.round(largeur * dpr);
        canvas.height = Math.round(hauteur * dpr);
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        creerParticules();
    }

    function etoile(x, y, taille, alpha) {
        ctx.globalAlpha = alpha;
        ctx.strokeStyle = '#fff4d6';
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(x - taille, y);
        ctx.lineTo(x + taille, y);
        ctx.moveTo(x, y - taille);
        ctx.lineTo(x, y + taille);
        ctx.stroke();
        ctx.fillStyle = '#fff';
        ctx.beginPath();
        ctx.arc(x, y, taille * 0.2, 0, 6.283);
        ctx.fill();
    }

    function dessiner(t, animer) {
        ctx.clearRect(0, 0, largeur, hauteur);
        var rayon = tactile ? 110 : 140;

        for (var i = 0; i < particules.length; i++) {
            var p = particules[i];
            if (animer) {
                p.hx += p.vx;
                p.hy += p.vy;
                if (p.hy < -10) { p.hy = hauteur + 10; p.hx = Math.random() * largeur; }
                if (p.hx < -10) { p.hx = largeur + 10; }
                if (p.hx > largeur + 10) { p.hx = -10; }

                // La poussière s'écarte du curseur, puis revient doucement
                if (pointeur.actif) {
                    var dx = p.hx + p.ox - pointeur.x;
                    var dy = p.hy + p.oy - pointeur.y;
                    var d = Math.sqrt(dx * dx + dy * dy) || 1;
                    if (d < rayon) {
                        var force = Math.pow(1 - d / rayon, 2) * 2.2;
                        p.ovx += (dx / d) * force;
                        p.ovy += (dy / d) * force;
                    }
                }
                p.ovx += -p.ox * 0.018;
                p.ovy += -p.oy * 0.018;
                p.ovx *= 0.9;
                p.ovy *= 0.9;
                p.ox += p.ovx;
                p.oy += p.ovy;
            }
            var alpha = p.a * (0.55 + 0.45 * Math.sin(t * 0.0021 + p.p));
            ctx.globalAlpha = alpha;
            ctx.fillStyle = 'rgb(246, 214, 160)';
            ctx.beginPath();
            ctx.arc(p.hx + p.ox, p.hy + p.oy, p.r, 0, 6.283);
            ctx.fill();
        }

        for (var j = etincelles.length - 1; j >= 0; j--) {
            var e = etincelles[j];
            e.vie -= 0.022;
            if (e.vie <= 0) { etincelles.splice(j, 1); continue; }
            e.x += e.vx;
            e.y += e.vy;
            etoile(e.x, e.y, e.taille * (0.5 + e.vie * 0.5), e.vie);
        }
        ctx.globalAlpha = 1;
    }

    /* ---------- Pointeur : souris au survol, doigt au glissement ---------- */
    function surPointeur(e) {
        var rect = hero.getBoundingClientRect();
        var zone = scene.getBoundingClientRect();
        var cx = zone.left + zone.width / 2;
        var cy = zone.top + zone.height / 2;
        var nx = borner((e.clientX - cx) / (rect.width * 0.5), -1, 1);
        var ny = borner((e.clientY - cy) / (rect.height * 0.5), -1, 1);

        pointeur.x = e.clientX - rect.left;
        pointeur.y = e.clientY - rect.top;
        pointeur.actif = true;

        cible.ry = nx * 17;
        cible.rx = -ny * 12;
        cible.tx = nx * 16;
        cible.ty = ny * 11;
        cible.lx = borner(((e.clientX - zone.left) / zone.width) * 100, -10, 110);
        cible.ly = borner(((e.clientY - zone.top) / zone.height) * 100, -10, 110);

        if (eclatEl) {
            var pt = eclatEl.getBoundingClientRect();
            var ex = pt.left + pt.width / 2 - e.clientX;
            var ey = pt.top + pt.height / 2 - e.clientY;
            cible.eclat = borner(1 - Math.sqrt(ex * ex + ey * ey) / 300, 0, 1);
        }

        // Étincelles quand le curseur passe vite sur la bague
        var vitesse = Math.abs(e.clientX - pointeur.dernierX) + Math.abs(e.clientY - pointeur.dernierY);
        pointeur.dernierX = e.clientX;
        pointeur.dernierY = e.clientY;
        var surBague = Math.abs(e.clientX - cx) < zone.width * 0.45 && Math.abs(e.clientY - cy) < zone.height * 0.5;
        if (surBague && vitesse > 9 && etincelles.length < 40) {
            for (var i = 0; i < 2; i++) {
                etincelles.push({
                    x: pointeur.x + (Math.random() - 0.5) * 36,
                    y: pointeur.y + (Math.random() - 0.5) * 36,
                    vx: (Math.random() - 0.5) * 0.9,
                    vy: -0.2 - Math.random() * 0.7,
                    taille: 4 + Math.random() * 7,
                    vie: 1
                });
            }
        }
    }

    function finPointeur() {
        pointeur.actif = false;
        pointeur.x = -9999;
        pointeur.y = -9999;
        cible.eclat = 0;
    }

    /* ---------- Boucle d'animation ---------- */
    function boucle(t) {
        if (!visible) { cadre = null; return; }

        if (!pointeur.actif) {
            // Au repos, la bague se balance doucement et le diamant respire
            cible.ry = Math.sin(t / 2600) * 7;
            cible.rx = Math.cos(t / 3100) * 4;
            cible.tx = 0;
            cible.ty = 0;
            cible.lx = 50 + Math.sin(t / 2600) * 32;
            cible.ly = 36 + Math.cos(t / 3100) * 10;
            cible.eclat = 0.3 + 0.35 * Math.sin(t / 900);
        }

        var k = 0.085;
        for (var cle in actuel) {
            if (Object.prototype.hasOwnProperty.call(actuel, cle)) {
                actuel[cle] += (cible[cle] - actuel[cle]) * k;
            }
        }
        var flotte = Math.sin(t / 1500) * 6;

        bague.style.setProperty('--rx', actuel.rx.toFixed(2) + 'deg');
        bague.style.setProperty('--ry', actuel.ry.toFixed(2) + 'deg');
        bague.style.setProperty('--tx', actuel.tx.toFixed(2) + 'px');
        bague.style.setProperty('--ty', (actuel.ty + flotte).toFixed(2) + 'px');
        bague.style.setProperty('--lx', actuel.lx.toFixed(1) + '%');
        bague.style.setProperty('--ly', actuel.ly.toFixed(1) + '%');
        bague.style.setProperty('--eclat', borner(actuel.eclat, 0, 1).toFixed(3));

        dessiner(t, true);
        cadre = window.requestAnimationFrame(boucle);
    }

    function demarrer() {
        if (reduit || cadre !== null || !visible || document.hidden) { return; }
        cadre = window.requestAnimationFrame(boucle);
    }

    function arreter() {
        if (cadre !== null) {
            window.cancelAnimationFrame(cadre);
            cadre = null;
        }
    }

    /* ---------- Mise en route ---------- */
    redimensionner();

    if (reduit) {
        // Mouvement réduit : une image fixe, sans animation ni suivi du curseur
        bague.style.setProperty('--eclat', '0.6');
        dessiner(0, false);
    } else {
        hero.addEventListener('pointermove', surPointeur, { passive: true });
        hero.addEventListener('pointerdown', surPointeur, { passive: true });
        hero.addEventListener('pointerleave', finPointeur, { passive: true });
        hero.addEventListener('pointerup', finPointeur, { passive: true });
        hero.addEventListener('pointercancel', finPointeur, { passive: true });
        demarrer();
    }

    var attente = null;
    window.addEventListener('resize', function () {
        window.clearTimeout(attente);
        attente = window.setTimeout(function () {
            redimensionner();
            if (reduit) { dessiner(0, false); }
        }, 150);
    });

    // On économise la batterie quand le hero n'est pas à l'écran ou l'onglet caché
    if ('IntersectionObserver' in window) {
        new IntersectionObserver(function (entrees) {
            visible = entrees[0].isIntersecting;
            if (visible) { demarrer(); } else { arreter(); }
        }, { threshold: 0.05 }).observe(hero);
    }
    document.addEventListener('visibilitychange', function () {
        if (document.hidden) { arreter(); } else { demarrer(); }
    });
})();