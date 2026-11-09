/**
 * ANIMATIONS — GSAP + ScrollTrigger + Lenis
 * Version finale complète pour Maison Lumière.
 */
(function () {
    'use strict';

    if (typeof gsap === 'undefined') {
        console.warn('[animations] GSAP non chargé');
        return;
    }

    gsap.registerPlugin(ScrollTrigger);

    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reducedMotion) {
        console.info('[animations] reduced-motion activé');
        return;
    }

    // Lenis smooth scroll
    if (typeof Lenis !== 'undefined') {
        const lenis = new Lenis({
            lerp: 0.085,
            wheelMultiplier: 0.95,
            touchMultiplier: 1.4,
        });
        lenis.on('scroll', ScrollTrigger.update);
        gsap.ticker.add((time) => lenis.raf(time * 1000));
        gsap.ticker.lagSmoothing(0);
    }

    const q = (sel) => document.querySelector(sel);
    const qa = (sel) => document.querySelectorAll(sel);

    // ═══════════════════════════════════════════
    // 1. HERO
    // ═══════════════════════════════════════════
    const hero = q('.hero');
    if (hero) {
        const heroPanel = hero.querySelector('.hero-panel');
        const heroText = hero.querySelector('.hero-texte');
        const heroPhoto = hero.querySelector('.hero-photo');
        const tl = gsap.timeline({ delay: 0.2 });
        if (heroPanel) tl.fromTo(heroPanel, { scale: 0.94, opacity: 0 }, { scale: 1, opacity: 1, duration: 1, ease: 'power3.out' });
        if (heroText) tl.fromTo(heroText.children, { y: 30, opacity: 0 }, { y: 0, opacity: 1, duration: 0.9, stagger: 0.08, ease: 'power3.out' }, '-=0.7');
        if (heroPhoto) tl.fromTo(heroPhoto, { scale: 0.9, opacity: 0 }, { scale: 1, opacity: 1, duration: 1, ease: 'power3.out' }, '-=0.9');
    }

    // ═══════════════════════════════════════════
    // 2. PIECES — défilement horizontal
    // ═══════════════════════════════════════════
    const pieces = q('.pieces');
    if (pieces) {
        const stage = pieces.querySelector('.pieces-stage');
        const track = pieces.querySelector('.pieces-track');
        const items = track ? [...track.querySelectorAll('.pieces-item')] : [];
        if (stage && track && items.length >= 2) {
            pieces.classList.add('is-animated');
            const getRunLength = () => {
                const first = items[0];
                const last = items[items.length - 1];
                return last.offsetLeft - first.offsetLeft;
            };
            const setSectionHeight = () => {
                const runLength = getRunLength();
                pieces.style.setProperty('--pieces-run', `${runLength}px`);
                return runLength;
            };
            let runLength = setSectionHeight();
            const setTrackX = gsap.quickSetter(track, 'x', 'px');
            const setItemY = items.map((item) => gsap.quickSetter(item, 'y', 'px'));
            const setItemR = items.map((item) => gsap.quickSetter(item, 'rotation', 'deg'));
            const setImgX = items.map((item) => {
                const img = item.querySelector('.pieces-frame img');
                return img ? gsap.quickSetter(img, 'xPercent') : null;
            });
            const updateCurve = () => {
                const half = window.innerWidth / 2;
                const lift = window.innerHeight * (window.innerWidth < 641 ? 0.05 : 0.11);
                items.forEach((item, index) => {
                    const box = item.getBoundingClientRect();
                    const centerX = box.left + box.width / 2;
                    const raw = Math.max(-1.6, Math.min(1.6, (centerX - half) / half));
                    const c = Math.sign(raw) * Math.max(0, Math.abs(raw) - 0.12) / 0.88;
                    setItemY[index](lift * c * c);
                    setItemR[index](c * 8);
                    if (setImgX[index]) setImgX[index](-c * 7);
                });
            };
            ScrollTrigger.create({
                trigger: pieces,
                start: 'top top',
                end: () => `+=${runLength}`,
                scrub: 0.5,
                invalidateOnRefresh: true,
                onUpdate: (self) => {
                    setTrackX(-runLength * self.progress);
                    updateCurve();
                },
                onRefresh: () => {
                    runLength = setSectionHeight();
                    updateCurve();
                },
            });
            window.addEventListener('resize', () => {
                runLength = setSectionHeight();
                ScrollTrigger.refresh();
            });
            updateCurve();
        }
    }

    //     // ═══════════════════════════════════════════
    // 3. NOUVEAUTÉS — bleu nuit
    // ═══════════════════════════════════════════
    const nouveautesSection = q('.nouveautes');
    if (nouveautesSection) {
        // Titre qui glisse en sens opposés
        const titleSpans = nouveautesSection.querySelectorAll('.section-title > span');
        if (titleSpans.length >= 2) {
            gsap.fromTo(titleSpans[0],
                { x: -60, opacity: 0 },
                {
                    x: 0, opacity: 1, duration: 1, ease: 'power3.out',
                    scrollTrigger: { trigger: nouveautesSection, start: 'top 75%', once: true },
                }
            );
            gsap.fromTo(titleSpans[1],
                { x: 60, opacity: 0 },
                {
                    x: 0, opacity: 1, duration: 1, ease: 'power3.out',
                    scrollTrigger: { trigger: nouveautesSection, start: 'top 75%', once: true },
                }
            );
        }

        // Cartes produits en cascade
        const cards = nouveautesSection.querySelectorAll('.grille-produits > *');
        if (cards.length) {
            gsap.set(cards, { opacity: 0, y: 50 });
            ScrollTrigger.batch(cards, {
                start: 'top 90%',
                once: true,
                onEnter: (batch) => gsap.to(batch, {
                    opacity: 1, y: 0, duration: 0.8,
                    ease: 'power3.out', stagger: 0.1, overwrite: true,
                }),
            });
        }
    }

    // ═══════════════════════════════════════════
    // 4. GOLD — titres + orbes
    // ═══════════════════════════════════════════
    const goldTitle = q('.gold .section-title');
    if (goldTitle) {
        const spans = goldTitle.querySelectorAll(':scope > span');
        if (spans.length >= 2) {
            gsap.fromTo(spans[0], { x: -80, opacity: 0 }, {
                x: 0, opacity: 1, duration: 1, ease: 'power3.out',
                scrollTrigger: { trigger: goldTitle, start: 'top 85%', once: true },
            });
            gsap.fromTo(spans[1], { x: 80, opacity: 0 }, {
                x: 0, opacity: 1, duration: 1, ease: 'power3.out',
                scrollTrigger: { trigger: goldTitle, start: 'top 85%', once: true },
            });
        }
    }
    const goldRows = qa('.gold-row');
    if (goldRows.length) {
        gsap.set(goldRows, { opacity: 0, x: 60 });
        ScrollTrigger.batch(goldRows, {
            start: 'top 85%', once: true,
            onEnter: (batch) => gsap.to(batch, {
                opacity: 1, x: 0, duration: 0.9,
                ease: 'power3.out', stagger: 0.12, overwrite: true,
            }),
        });
        goldRows.forEach((row) => {
            const orb = row.querySelector('.gold-orb');
            if (orb) {
                gsap.fromTo(orb, { scale: 0.6, opacity: 0.4 }, {
                    scale: 1, opacity: 1, duration: 1, ease: 'elastic.out(1, 0.5)',
                    scrollTrigger: { trigger: row, start: 'top 85%', once: true },
                });
            }
        });
    }

    // ═══════════════════════════════════════════
    // 5. TÉMOIGNAGES — cartes + étoiles
    // ═══════════════════════════════════════════
    const temoignages = qa('.temoignages .temoignage');
    if (temoignages.length) {
        gsap.set(temoignages, { opacity: 0, y: 50 });
        ScrollTrigger.batch(temoignages, {
            start: 'top 88%', once: true,
            onEnter: (batch) => gsap.to(batch, {
                opacity: 1, y: 0, duration: 0.9,
                ease: 'power3.out', stagger: 0.12, overwrite: true,
            }),
        });
        temoignages.forEach((temoignage) => {
            const etoiles = temoignage.querySelector('.etoiles');
            if (etoiles) {
                gsap.fromTo(etoiles, { scale: 0, rotation: -180, opacity: 0 }, {
                    scale: 1, rotation: 0, opacity: 1,
                    duration: 0.8, ease: 'back.out(1.7)',
                    scrollTrigger: { trigger: temoignage, start: 'top 88%', once: true },
                });
            }
        });
    }

    // ═══════════════════════════════════════════
    // 6. STORIES (histoire accueil)
    // ═══════════════════════════════════════════
    const storyCards = qa('.stories .story-card');
    if (storyCards.length) {
        gsap.set(storyCards, { opacity: 0, y: 50 });
        storyCards.forEach((card) => {
            gsap.to(card, {
                opacity: 1, y: 0, duration: 1, ease: 'power3.out',
                scrollTrigger: { trigger: card, start: 'top 85%', once: true },
            });
        });
    }

    // ═══════════════════════════════════════════
    // 7. FAQ — questions en cascade
    // ═══════════════════════════════════════════
    const faqContainer = q('.faq');
    if (faqContainer) {
        const faqItems = faqContainer.querySelectorAll('details');
        if (faqItems.length) {
            gsap.set(faqItems, { opacity: 0, y: 30 });
            ScrollTrigger.batch(faqItems, {
                start: 'top 88%', once: true,
                onEnter: (batch) => gsap.to(batch, {
                    opacity: 1, y: 0, duration: 0.7,
                    ease: 'power2.out', stagger: 0.06, overwrite: true,
                }),
            });
        }
    }

    // ═══════════════════════════════════════════
    // 8. CARE — pilules
    // ═══════════════════════════════════════════
    const carePills = qa('.care-pill, .pilule, .care .pill');
    if (carePills.length) {
        carePills.forEach((pill, index) => {
            gsap.set(pill, {
                opacity: 0,
                x: ((index * 37) % 7 - 3) / 3 * 60,
                y: ((index * 53) % 5 - 2) / 2 * 40 + 40,
                rotation: ((index * 37) % 7 - 3) / 3 * 15,
            });
            gsap.to(pill, {
                opacity: 1, x: 0, y: 0, rotation: 0,
                duration: 0.9, ease: 'power3.out',
                delay: index * 0.05,
                scrollTrigger: { trigger: pill, start: 'top 85%', once: true },
            });
        });
    }

    // ═══════════════════════════════════════════
    // 9. CONTACT
    // ═══════════════════════════════════════════
    const contactInfo = q('.contact-info');
    const contactForm = q('.contact-form');
    if (contactInfo) {
        gsap.fromTo(contactInfo, { x: -60, opacity: 0 }, {
            x: 0, opacity: 1, duration: 1, ease: 'power3.out',
            scrollTrigger: { trigger: contactInfo, start: 'top 85%', once: true },
        });
    }
    if (contactForm) {
        gsap.fromTo(contactForm, { x: 60, opacity: 0 }, {
            x: 0, opacity: 1, duration: 1, ease: 'power3.out',
            scrollTrigger: { trigger: contactForm, start: 'top 85%', once: true },
        });
    }

    // ═══════════════════════════════════════════
    // 10. FOOTER
    // ═══════════════════════════════════════════
    const footer = q('.pied');
    const footerLogo = q('.pied .logo');
    if (footer && footerLogo) {
        gsap.fromTo(footerLogo,
            { opacity: 0, scale: 0.9, letterSpacing: '0.4em' },
            {
                opacity: 1, scale: 1, letterSpacing: '0.02em',
                duration: 1.4, ease: 'power3.out',
                scrollTrigger: { trigger: footer, start: 'top 90%', once: true },
            }
        );
    }
    const footerCols = qa('.pied-grille > div');
    if (footerCols.length) {
        gsap.set(footerCols, { opacity: 0, y: 30 });
        ScrollTrigger.batch(footerCols, {
            start: 'top 92%', once: true,
            onEnter: (batch) => gsap.to(batch, {
                opacity: 1, y: 0, duration: 0.8,
                ease: 'power2.out', stagger: 0.1, overwrite: true,
            }),
        });
    }

    // ═══════════════════════════════════════════
    // 11. SECTION TITLES génériques
    // ═══════════════════════════════════════════
    const sectionTitles = qa('.section-title:not(.pieces-head .section-title):not(.gold .section-title)');
    sectionTitles.forEach((title) => {
        gsap.fromTo(title, { opacity: 0, y: 30 }, {
            opacity: 1, y: 0, duration: 0.8, ease: 'power2.out',
            scrollTrigger: { trigger: title, start: 'top 88%', once: true },
        });
    });

    // ═══════════════════════════════════════════
    // 12. PAGES "page_texte" (FAQ, CGV, mentions, à propos...)
    // ═══════════════════════════════════════════
    const fil = q('.fil');
    if (fil) {
        gsap.fromTo(fil,
            { opacity: 0, y: -10 },
            { opacity: 1, y: 0, duration: 0.6, ease: 'power2.out', delay: 0.1 }
        );
    }

    const titrePage = q('.titre-page');
    if (titrePage) {
        gsap.fromTo(titrePage,
            { opacity: 0, y: 30 },
            { opacity: 1, y: 0, duration: 0.8, ease: 'power3.out', delay: 0.2 }
        );
    }

    const pageTexte = q('.page-texte');
    if (pageTexte && !faqContainer) {
        const children = pageTexte.querySelectorAll(':scope > *');
        if (children.length) {
            gsap.fromTo(children,
                { opacity: 0, y: 20 },
                {
                    opacity: 1, y: 0, duration: 0.6, ease: 'power2.out',
                    stagger: 0.05,
                    scrollTrigger: {
                        trigger: pageTexte,
                        start: 'top 80%',
                        once: true,
                    },
                }
            );
        }
    }

    // ═══════════════════════════════════════════
    // REFRESH
    // ═══════════════════════════════════════════
    window.addEventListener('load', () => {
        ScrollTrigger.refresh();
    });

    console.info('[animations] GSAP + ScrollTrigger + Lenis initialisés ✅');

})();