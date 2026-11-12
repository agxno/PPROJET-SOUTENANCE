/**
 * BOUTIQUE — Filtres côté client
 */
(function () {
    'use strict';

    const grid = document.getElementById('boutique-grid');
    if (!grid) return;

    const cards = Array.from(grid.querySelectorAll('.boutique-card'));
    const countEl = document.getElementById('boutique-count');
    const emptyEl = document.getElementById('boutique-empty');

    const state = {
        categories: [],
        prix: '',
        stock: false,
        promo: false,
        tri: 'featured',
    };

    const applyFilters = () => {
        let visible = 0;

        cards.forEach((card) => {
            const cat = card.dataset.categorie;
            const prix = parseFloat(card.dataset.prix);
            const stock = parseInt(card.dataset.stock, 10) > 0;
            const promo = card.dataset.promo === 'true';

            let ok = true;

            if (state.categories.length > 0 && !state.categories.includes(cat)) {
                ok = false;
            }

            if (ok && state.prix) {
                if (state.prix === '2000000+') {
                    if (prix < 2000000) ok = false;
                } else {
                    const [min, max] = state.prix.split('-').map(Number);
                    if (prix < min || prix > max) ok = false;
                }
            }

            if (ok && state.stock && !stock) ok = false;
            if (ok && state.promo && !promo) ok = false;

            card.hidden = !ok;
            if (ok) visible++;
        });

        if (countEl) countEl.textContent = visible;
        if (emptyEl) emptyEl.hidden = visible > 0;
    };

    const applySort = () => {
        const visibleCards = cards.filter((c) => !c.hidden);

        visibleCards.sort((a, b) => {
            const pa = parseFloat(a.dataset.prix);
            const pb = parseFloat(b.dataset.prix);

            if (state.tri === 'price-asc') return pa - pb;
            if (state.tri === 'price-desc') return pb - pa;
            if (state.tri === 'newest') {
                return (b.dataset.date || '').localeCompare(a.dataset.date || '');
            }
            return 0;
        });

        visibleCards.forEach((card) => grid.appendChild(card));
    };

    // ─── Event listeners ───
    document.querySelectorAll('[data-filter="categorie"]').forEach((input) => {
        input.addEventListener('change', () => {
            state.categories = Array.from(
                document.querySelectorAll('[data-filter="categorie"]:checked')
            ).map((i) => i.value);
            applyFilters();
        });
    });

    document.querySelectorAll('[data-filter="prix"]').forEach((input) => {
        input.addEventListener('change', () => {
            state.prix = input.value;
            applyFilters();
        });
    });

    document.querySelectorAll('[data-filter="stock"]').forEach((input) => {
        input.addEventListener('change', () => {
            state.stock = input.checked;
            applyFilters();
        });
    });

    document.querySelectorAll('[data-filter="promo"]').forEach((input) => {
        input.addEventListener('change', () => {
            state.promo = input.checked;
            applyFilters();
        });
    });

    const triSelect = document.querySelector('[data-filter="tri"]');
    if (triSelect) {
        triSelect.addEventListener('change', () => {
            state.tri = triSelect.value;
            applySort();
        });
    }

    document.querySelectorAll('[data-clear-filters]').forEach((btn) => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('[data-filter="categorie"]').forEach((i) => (i.checked = false));
            document.querySelectorAll('[data-filter="prix"]').forEach((i) => {
                i.checked = i.value === '';
            });
            document.querySelectorAll('[data-filter="stock"], [data-filter="promo"]').forEach((i) => (i.checked = false));
            if (triSelect) triSelect.value = 'featured';

            state.categories = [];
            state.prix = '';
            state.stock = false;
            state.promo = false;
            state.tri = 'featured';

            applyFilters();
            applySort();
        });
    });

    applyFilters();
})();

/* ==========================================
   NOUVEAUTÉS — Carrousel squeeze
========================================== */
(function () {
    const carousel = document.getElementById('squeeze-carousel');
    if (!carousel) return;

    const panels = Array.from(carousel.querySelectorAll('.squeeze-panel'));
    const prevBtn = carousel.querySelector('[data-squeeze-prev]');
    const nextBtn = carousel.querySelector('[data-squeeze-next]');
    if (!panels.length) return;

    let current = panels.findIndex((p) => p.classList.contains('is-open'));
    if (current < 0) current = 0;

    const updateButtons = () => {
        if (prevBtn) prevBtn.disabled = current <= 0;
        if (nextBtn) nextBtn.disabled = current >= panels.length - 1;
    };

    const open = (index) => {
        if (index < 0 || index >= panels.length) return;
        panels.forEach((p, i) => {
            p.classList.toggle('is-open', i === index);
            p.setAttribute('aria-selected', i === index ? 'true' : 'false');
        });
        current = index;
        updateButtons();
    };

    // Clic sur une lamelle : ouvrir
    panels.forEach((panel, i) => {
        panel.addEventListener('click', () => open(i));
    });

    // Flèches
    if (prevBtn) prevBtn.addEventListener('click', () => open(current - 1));
    if (nextBtn) nextBtn.addEventListener('click', () => open(current + 1));

    // Clavier
    carousel.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') {
            e.preventDefault();
            open(current - 1);
        } else if (e.key === 'ArrowRight') {
            e.preventDefault();
            open(current + 1);
        }
    });

    // Init
    open(current);
})();