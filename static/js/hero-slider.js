/**
 * HERO SLIDER — Glass effect (Three.js + GSAP)
 * Version complète avec 6 slides.
 */
(function () {
    'use strict';

    const heroEl = document.querySelector('.hero-slider');
    if (!heroEl) return;

    const canvas = heroEl.querySelector('.webgl-canvas');

    // Vérifier WebGL + Three.js + GSAP
    const supportsWebGL = (() => {
        try {
            const c = document.createElement('canvas');
            return !!(window.WebGLRenderingContext && (c.getContext('webgl') || c.getContext('experimental-webgl')));
        } catch (e) {
            return false;
        }
    })();

    if (!supportsWebGL || typeof THREE === 'undefined' || typeof gsap === 'undefined') {
        heroEl.classList.add('no-webgl');
        console.warn('[hero-slider] Fallback actif — WebGL:', supportsWebGL, '| THREE:', typeof THREE, '| GSAP:', typeof gsap);
        return;
    }

    // ─── Slides ───
    const SLIDES = [
        {
            title: "L'éclat",
            subtitle: "Qui vous ressemble",
            description: "Des bijoux choisis avec soin pour leur finition et leur élégance.",
            media: "/static/img/fallback1.jpeg"
        },
        {
            title: "L'élégance",
            subtitle: "Traverse le temps",
            description: "Des pièces d'exception façonnées pour traverser les générations.",
            media: "/static/img/fallback2.jpeg"
        },
        {
            title: "La précision",
            subtitle: "De nos artisans",
            description: "Chaque création Maison Lumière est travaillée à la main par nos artisans joailliers.",
            media: "/static/img/fallback3.jpeg"
        },
        {
            title: "L'émotion",
            subtitle: "À chaque instant",
            description: "Un bijou, un souvenir, une histoire à écrire ensemble.",
            media: "/static/img/fallback4.jpeg"
        },
        {
            title: "La passion",
            subtitle: "Du travail bien fait",
            description: "Chaque pierre est sélectionnée avec exigence et traçabilité.",
            media: "/static/img/fallback5.jpeg"
        },
        {
            title: "L'exception",
            subtitle: "À l'état pur",
            description: "Des éditions limitées, façonnées pour célébrer un moment unique.",
            media: "/static/img/fallback6.jpeg"
        },
    ];

    const CONFIG = {
        transitionDuration: 2.0,
        autoSlideSpeed: 5000,
    };

    // ─── State ───
    let currentSlideIndex = 0;
    let isTransitioning = false;
    let shaderMaterial, renderer, scene, camera;
    let slideTextures = [];
    let texturesLoaded = false;
    let autoSlideTimer = null;
    let progressAnimation = null;

    // ─── Shaders ───
    const vertexShader = `
        varying vec2 vUv;
        void main() {
            vUv = uv;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
    `;

    const fragmentShader = `
        uniform sampler2D uTexture1;
        uniform sampler2D uTexture2;
        uniform float uProgress;
        uniform vec2 uResolution;
        uniform vec2 uTexture1Size;
        uniform vec2 uTexture2Size;
        varying vec2 vUv;

        vec2 getCoverUV(vec2 uv, vec2 textureSize) {
            vec2 s = uResolution / textureSize;
            float scale = max(s.x, s.y);
            vec2 scaledSize = textureSize * scale;
            vec2 offset = (uResolution - scaledSize) * 0.5;
            return (uv * uResolution - offset) / scaledSize;
        }

        vec4 glassEffect(vec2 uv, float progress) {
            float time = progress * 5.0;
            vec2 uv1 = getCoverUV(uv, uTexture1Size);
            vec2 uv2 = getCoverUV(uv, uTexture2Size);

            float maxR = length(uResolution) * 0.85;
            float br = progress * maxR;
            vec2 p = uv * uResolution;
            vec2 c = uResolution * 0.5;
            float d = length(p - c);
            float nd = d / max(br, 0.001);
            float param = smoothstep(br + 3.0, br - 3.0, d);

            vec4 img;
            if (param > 0.0) {
                float ro = 0.08 * pow(smoothstep(0.3, 1.0, nd), 1.5);
                vec2 dir = (d > 0.0) ? (p - c) / d : vec2(0.0);
                vec2 distUV = uv2 - dir * ro;
                distUV += vec2(sin(time + nd * 10.0), cos(time * 0.8 + nd * 8.0)) * 0.015 * nd * param;

                float ca = 0.02 * pow(smoothstep(0.3, 1.0, nd), 1.2);
                img = vec4(
                    texture2D(uTexture2, distUV + dir * ca * 1.2).r,
                    texture2D(uTexture2, distUV + dir * ca * 0.2).g,
                    texture2D(uTexture2, distUV - dir * ca * 0.8).b,
                    1.0
                );

                float rim = smoothstep(0.95, 1.0, nd) * (1.0 - smoothstep(1.0, 1.01, nd));
                img.rgb += rim * 0.08;
            } else {
                img = texture2D(uTexture2, uv2);
            }

            vec4 oldImg = texture2D(uTexture1, uv1);

            if (progress > 0.95) {
                img = mix(img, texture2D(uTexture2, uv2), (progress - 0.95) / 0.05);
            }

            return mix(oldImg, img, param);
        }

        void main() {
            gl_FragColor = glassEffect(vUv, uProgress);
        }
    `;

    // ─── Helpers ───
    const splitText = (text) => {
        return text.split('').map(char =>
            `<span style="display: inline-block; opacity: 0;">${char === ' ' ? '&nbsp;' : char}</span>`
        ).join('');
    };

    const updateContent = (idx) => {
        const titleEl = document.getElementById('mainTitle');
        const descEl = document.getElementById('mainDesc');
        if (!titleEl || !descEl) return;

        gsap.to(titleEl.children, { y: -20, opacity: 0, duration: 0.5, stagger: 0.02, ease: "power2.in" });
        gsap.to(descEl, { y: -10, opacity: 0, duration: 0.4, ease: "power2.in" });

        setTimeout(() => {
            titleEl.innerHTML = splitText(SLIDES[idx].title);
            descEl.textContent = SLIDES[idx].description;
            gsap.set(titleEl.children, { opacity: 0 });
            gsap.set(descEl, { y: 20, opacity: 0 });

            const children = titleEl.children;
            gsap.set(children, { y: 20 });
            gsap.to(children, { y: 0, opacity: 1, duration: 0.8, stagger: 0.03, ease: "power3.out" });
            gsap.to(descEl, { y: 0, opacity: 1, duration: 0.8, delay: 0.2, ease: "power3.out" });
        }, 500);
    };

    const updateNavigationState = (idx) => {
        document.querySelectorAll(".slide-nav-item").forEach((el, i) => {
            el.classList.toggle("active", i === idx);
        });
    };

    const updateSlideProgress = (idx, prog) => {
        const el = document.querySelectorAll(".slide-nav-item")[idx]?.querySelector(".slide-progress-fill");
        if (el) {
            el.style.width = `${prog}%`;
            el.style.opacity = '1';
        }
    };

    const fadeSlideProgress = (idx) => {
        const el = document.querySelectorAll(".slide-nav-item")[idx]?.querySelector(".slide-progress-fill");
        if (el) {
            el.style.opacity = '0';
            setTimeout(() => el.style.width = "0%", 300);
        }
    };

    const quickResetProgress = (idx) => {
        const el = document.querySelectorAll(".slide-nav-item")[idx]?.querySelector(".slide-progress-fill");
        if (el) {
            el.style.transition = "width 0.2s ease-out";
            el.style.width = "0%";
            setTimeout(() => el.style.transition = "width 0.1s ease, opacity 0.3s ease", 200);
        }
    };

    const updateCounter = (idx) => {
        const sn = document.getElementById("slideNumber");
        if (sn) sn.textContent = String(idx + 1).padStart(2, "0");
        const st = document.getElementById("slideTotal");
        if (st) st.textContent = String(SLIDES.length).padStart(2, "0");
    };

    const createSlidesNavigation = () => {
        const nav = document.getElementById("slidesNav");
        if (!nav) return;
        nav.innerHTML = "";
        SLIDES.forEach((slide, i) => {
            const item = document.createElement("div");
            item.className = `slide-nav-item${i === 0 ? " active" : ""}`;
            item.dataset.slideIndex = String(i);
            item.innerHTML = `
                <div class="slide-progress-line"><div class="slide-progress-fill"></div></div>
                <div class="slide-nav-title">${slide.subtitle}</div>
            `;
            item.addEventListener("click", (e) => {
                e.stopPropagation();
                if (!isTransitioning && i !== currentSlideIndex) {
                    stopAutoSlideTimer();
                    quickResetProgress(currentSlideIndex);
                    navigateToSlide(i);
                }
            });
            nav.appendChild(item);
        });
    };

    // ─── Navigation ───
    const navigateToSlide = (targetIndex) => {
        if (isTransitioning || targetIndex === currentSlideIndex) return;
        stopAutoSlideTimer();
        quickResetProgress(currentSlideIndex);

        const currentTexture = slideTextures[currentSlideIndex];
        const targetTexture = slideTextures[targetIndex];
        if (!currentTexture || !targetTexture) return;

        isTransitioning = true;
        shaderMaterial.uniforms.uTexture1.value = currentTexture;
        shaderMaterial.uniforms.uTexture2.value = targetTexture;
        shaderMaterial.uniforms.uTexture1Size.value = currentTexture.userData.size;
        shaderMaterial.uniforms.uTexture2Size.value = targetTexture.userData.size;

        updateContent(targetIndex);

        currentSlideIndex = targetIndex;
        updateCounter(currentSlideIndex);
        updateNavigationState(currentSlideIndex);

        gsap.fromTo(shaderMaterial.uniforms.uProgress,
            { value: 0 },
            {
                value: 1,
                duration: CONFIG.transitionDuration,
                ease: "power2.inOut",
                onComplete: () => {
                    shaderMaterial.uniforms.uProgress.value = 0;
                    shaderMaterial.uniforms.uTexture1.value = targetTexture;
                    shaderMaterial.uniforms.uTexture1Size.value = targetTexture.userData.size;
                    isTransitioning = false;
                    safeStartTimer(100);
                }
            }
        );
    };

    const handleSlideChange = () => {
        if (isTransitioning || !texturesLoaded) return;
        navigateToSlide((currentSlideIndex + 1) % SLIDES.length);
    };

    // ─── Timer ───
    const startAutoSlideTimer = () => {
        if (!texturesLoaded) return;
        stopAutoSlideTimer();
        let progress = 0;
        const increment = (100 / CONFIG.autoSlideSpeed) * 50;
        progressAnimation = setInterval(() => {
            progress += increment;
            updateSlideProgress(currentSlideIndex, progress);
            if (progress >= 100) {
                clearInterval(progressAnimation);
                progressAnimation = null;
                fadeSlideProgress(currentSlideIndex);
                if (!isTransitioning) handleSlideChange();
            }
        }, 50);
    };

    const stopAutoSlideTimer = () => {
        if (progressAnimation) clearInterval(progressAnimation);
        if (autoSlideTimer) clearTimeout(autoSlideTimer);
        progressAnimation = null;
        autoSlideTimer = null;
    };

    const safeStartTimer = (delay = 0) => {
        stopAutoSlideTimer();
        if (texturesLoaded) {
            if (delay > 0) autoSlideTimer = setTimeout(startAutoSlideTimer, delay);
            else startAutoSlideTimer();
        }
    };

    // ─── Textures ───
    const loadImageTexture = (src) => new Promise((resolve, reject) => {
        const loader = new THREE.TextureLoader();
        loader.crossOrigin = 'anonymous';
        loader.load(src, (texture) => {
            texture.minFilter = THREE.LinearFilter;
            texture.magFilter = THREE.LinearFilter;
            texture.userData = {
                size: new THREE.Vector2(texture.image.width, texture.image.height)
            };
            resolve(texture);
        }, undefined, reject);
    });

    // ─── Init ───
    const initRenderer = async () => {
        if (!canvas) return;
        scene = new THREE.Scene();
        camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

        renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: false });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

        shaderMaterial = new THREE.ShaderMaterial({
            uniforms: {
                uTexture1: { value: null },
                uTexture2: { value: null },
                uProgress: { value: 0 },
                uResolution: { value: new THREE.Vector2(window.innerWidth, window.innerHeight) },
                uTexture1Size: { value: new THREE.Vector2(1, 1) },
                uTexture2Size: { value: new THREE.Vector2(1, 1) },
            },
            vertexShader,
            fragmentShader,
        });

        scene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), shaderMaterial));

        for (const slide of SLIDES) {
            try {
                slideTextures.push(await loadImageTexture(slide.media));
            } catch (err) {
                console.warn('[hero-slider] Image non chargée:', slide.media, err);
            }
        }

        if (slideTextures.length < 2) {
            heroEl.classList.add('no-webgl');
            console.warn('[hero-slider] Pas assez d\'images chargées, fallback actif');
            return;
        }

        shaderMaterial.uniforms.uTexture1.value = slideTextures[0];
        shaderMaterial.uniforms.uTexture2.value = slideTextures[1];
        shaderMaterial.uniforms.uTexture1Size.value = slideTextures[0].userData.size;
        shaderMaterial.uniforms.uTexture2Size.value = slideTextures[1].userData.size;

        texturesLoaded = true;

        const render = () => {
            requestAnimationFrame(render);
            renderer.render(scene, camera);
        };
        render();

        safeStartTimer(500);
    };

    const initTextContent = () => {
        const tEl = document.getElementById('mainTitle');
        const dEl = document.getElementById('mainDesc');
        if (!tEl || !dEl) return;
        tEl.innerHTML = splitText(SLIDES[0].title);
        dEl.textContent = SLIDES[0].description;
        gsap.fromTo(tEl.children, { y: 20, opacity: 0 }, { y: 0, opacity: 1, duration: 1, stagger: 0.03, ease: "power3.out", delay: 0.5 });
        gsap.fromTo(dEl, { y: 20, opacity: 0 }, { y: 0, opacity: 1, duration: 1, ease: "power3.out", delay: 0.8 });
    };

    // ─── Boot ───
    createSlidesNavigation();
    updateCounter(0);
    initTextContent();
    initRenderer();

    // ─── Listeners ───
    document.addEventListener("visibilitychange", () => {
        document.hidden ? stopAutoSlideTimer() : (!isTransitioning && safeStartTimer());
    });

    window.addEventListener("resize", () => {
        if (renderer && shaderMaterial) {
            renderer.setSize(window.innerWidth, window.innerHeight);
            shaderMaterial.uniforms.uResolution.value.set(window.innerWidth, window.innerHeight);
        }
    });

    console.info('[hero-slider] Initialisé ✅');

})();