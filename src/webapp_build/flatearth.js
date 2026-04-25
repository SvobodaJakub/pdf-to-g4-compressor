/**
 * Flat Earth Background Animation (en-FE / cs-FE / sk-FE locale)
 * CSS 3D flat earth discs with particle waterfalls drifting through a starfield
 */

var FE_LAND_PATHS = [FLATEARTH_PATHS_PLACEHOLDER];

var feAnimId = null;
var feWaterSystems = [];
var feDiscs = [];

function feProjectPoint(x, y, z) {
    var cosA = 0.5299, sinA = 0.848; // cos/sin(58°) precomputed
    var rx = x - 170, ry = y - 170;
    var ry2 = ry * cosA - z * sinA;
    var rz2 = ry * sinA + z * cosA;
    var scale = 600 / (600 - rz2);
    return { x: 170 + rx * scale, y: 170 + ry2 * scale };
}

function feComputeEdges() {
    var R = 170, N = 120;
    var front = [], back = [];
    var projCenter = feProjectPoint(170, 170, 14);
    for (var i = 0; i < N; i++) {
        var a = (i / N) * Math.PI * 2;
        var x = 170 + R * Math.cos(a), y = 170 + R * Math.sin(a);
        var bot = feProjectPoint(x, y, 0);
        var top = feProjectPoint(x, y, 28);
        if (bot.y > top.y) {
            if (bot.y > projCenter.y) front.push(bot);
            else back.push(bot);
        }
    }
    return { front: front, back: back, cx: projCenter.x, cy: projCenter.y };
}

var feWorldSVGCache = null;
function feCreateWorldSVG() {
    if (feWorldSVGCache) return feWorldSVGCache;
    var svg = '<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%;display:block;">';
    svg += '<defs><clipPath id="dc"><circle cx="50" cy="50" r="48"/></clipPath></defs>';
    svg += '<g clip-path="url(#dc)">';
    svg += '<circle cx="50" cy="50" r="49" fill="#1565a0"/>';
    svg += '<circle cx="50" cy="50" r="47" fill="#1a78b8"/>';
    svg += '<circle cx="50" cy="50" r="44" fill="#1e88c8"/>';
    for (var i = 0; i < FE_LAND_PATHS.length; i++) {
        svg += '<path d="' + FE_LAND_PATHS[i] + '" fill="#3a7228" stroke="#2d5a1e" stroke-width="0.15"/>';
    }
    svg += '<circle cx="50" cy="50" r="4.5" fill="#dce8f2" opacity="0.4"/>';
    svg += '<circle cx="50" cy="50" r="47" fill="none" stroke="rgba(220,235,250,0.15)" stroke-width="2"/>';
    svg += '</g>';
    svg += '<circle cx="50" cy="50" r="48" fill="none" stroke="rgba(200,220,240,0.2)" stroke-width="0.6"/>';
    svg += '</svg>';
    feWorldSVGCache = svg;
    return svg;
}

// Pre-compute slab ring styles
var feSlabStyles = [];
for (var si = 0; si < 5; si++) {
    var z = (si / 5) * 28;
    var t = si / 5;
    var r = Math.round(115 - 35 * t), g = Math.round(95 - 30 * t), b = Math.round(65 - 25 * t);
    feSlabStyles.push('transform:translateZ(' + z + 'px);background:rgb(' + r + ',' + g + ',' + b + ');border:1px solid rgb(' + (r-12) + ',' + (g-12) + ',' + (b-8) + ')');
}

function feCreateDisc(container, worldSVG) {
    var wrapper = document.createElement('div');
    wrapper.className = 'fe-world-wrapper';
    // Use will-change to promote to GPU layer
    wrapper.style.willChange = 'transform';

    var canvasBack = document.createElement('canvas');
    canvasBack.className = 'fe-water-back';
    canvasBack.width = 340; canvasBack.height = 500;
    wrapper.appendChild(canvasBack);

    var world = document.createElement('div');
    world.className = 'fe-world';
    var slab = document.createElement('div');
    slab.className = 'fe-slab';

    // 5 slab rings (was 10, then 6 — 5 is still convincing)
    for (var i = 0; i < 5; i++) {
        var ring = document.createElement('div');
        ring.className = 'fe-side';
        ring.style.cssText = feSlabStyles[i];
        slab.appendChild(ring);
    }

    var top = document.createElement('div');
    top.className = 'fe-top';
    top.style.transform = 'translateZ(28px)';
    top.innerHTML = worldSVG;
    slab.appendChild(top);

    var sunOrbit = document.createElement('div');
    sunOrbit.className = 'fe-sun-orbit';
    sunOrbit.style.animationDuration = (7 + Math.random() * 4) + 's';
    var sun = document.createElement('div');
    sun.className = 'fe-sun';
    sunOrbit.appendChild(sun);
    slab.appendChild(sunOrbit);

    world.appendChild(slab);
    wrapper.appendChild(world);

    var canvasFront = document.createElement('canvas');
    canvasFront.className = 'fe-water-front';
    canvasFront.width = 340; canvasFront.height = 500;
    wrapper.appendChild(canvasFront);

    container.appendChild(wrapper);
    return { wrapper: wrapper, canvasBack: canvasBack, canvasFront: canvasFront };
}

// Pre-computed color palette (avoid string creation per particle)
var fePalette = [];
for (var pi = 0; pi <= 20; pi++) {
    fePalette.push('hsl(200,75%,' + (50 + pi) + '%)');
}

function FEWater(canvasBack, canvasFront, edges) {
    this.ctxBack = canvasBack.getContext('2d');
    this.ctxFront = canvasFront.getContext('2d');
    this.backP = [];
    this.frontP = [];
    this.edges = edges;
}

FEWater.prototype.spawn = function(edgePoints, particles) {
    if (!edgePoints.length) return;
    var ep = edgePoints[Math.floor(Math.random() * edgePoints.length)];
    var dx = ep.x - this.edges.cx, dy = ep.y - this.edges.cy;
    var len = Math.sqrt(dx*dx + dy*dy) || 1;
    particles.push({
        x: ep.x + (Math.random()-0.5)*1.5, y: ep.y + (Math.random()-0.5)*1.5,
        vx: (dx/len)*0.35 + (Math.random()-0.5)*0.1,
        vy: 0.5 + Math.random()*0.5,
        life: 1.0, size: 0.5 + Math.random()*0.8
    });
};

FEWater.prototype.update = function() {
    var i, p, ps;
    for (i = 0; i < 10; i++) this.spawn(this.edges.front, this.frontP);
    for (i = 0; i < 4; i++) this.spawn(this.edges.back, this.backP);
    var lists = [this.frontP, this.backP];
    for (var li = 0; li < 2; li++) {
        ps = lists[li];
        for (i = ps.length - 1; i >= 0; i--) {
            p = ps[i];
            p.x += p.vx; p.y += p.vy; p.vy += 0.03; p.life -= 0.008;
            if (p.life <= 0 || p.y > 500) ps.splice(i, 1);
        }
    }
};

FEWater.prototype.drawLayer = function(ctx, particles) {
    ctx.clearRect(0, 0, 340, 500);
    for (var i = 0; i < particles.length; i++) {
        var p = particles[i];
        ctx.globalAlpha = Math.min(p.life * 0.6, 0.5);
        ctx.fillStyle = fePalette[Math.min(Math.round(p.life * 20), 20)];
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, 6.283);
        ctx.fill();
    }
    ctx.globalAlpha = 1;
};

FEWater.prototype.draw = function() {
    this.drawLayer(this.ctxBack, this.backP);
    this.drawLayer(this.ctxFront, this.frontP);
};

FEWater.prototype.clear = function() {
    if (this.frontP.length > 0 || this.backP.length > 0) {
        this.frontP.length = 0;
        this.backP.length = 0;
        this.ctxFront.clearRect(0, 0, 340, 500);
        this.ctxBack.clearRect(0, 0, 340, 500);
    }
};

function feInit() {
    var bg = document.getElementById('feBg');
    if (!bg) return;

    feStop();
    bg.innerHTML = '';
    feDiscs = [];
    feWaterSystems = [];

    var edges = feComputeEdges();
    var worldSVG = feCreateWorldSVG();

    // 2x3 hex grid: sparser, ~4 visible on screen, 6 total (was 9)
    var cellW = 900, cellH = 750;
    var cols = 2, rows = 3;
    var tileW = Math.max(cols * cellW + cellW / 2, window.innerWidth + cellW + 400);
    var tileH = Math.max(rows * cellH, window.innerHeight + cellH + 500);

    var gridOffX = Math.random() * tileW;
    var gridOffY = Math.random() * tileH;

    var screenW = window.innerWidth + 400;
    var screenH = window.innerHeight + 500;

    for (var r = 0; r < rows; r++) {
        for (var c = 0; c < cols; c++) {
            var result = feCreateDisc(bg, worldSVG);
            result.wrapper.style.opacity = 0.65 + Math.random() * 0.25;
            var initX = (c * cellW + (r % 2) * (cellW / 2) + gridOffX) % tileW;
            var initY = (r * cellH + gridOffY) % tileH;
            feDiscs.push({
                el: result.wrapper, x: initX, y: initY,
                tileW: tileW, tileH: tileH, offX: cellW, offY: cellH,
                ws: feWaterSystems.length, vis: false
            });
            feWaterSystems.push(new FEWater(result.canvasBack, result.canvasFront, edges));
        }
    }

    var lastTime = performance.now();
    var vx = 22, vy = 15;

    function animate(now) {
        var dt = (now - lastTime) / 1000;
        if (dt > 0.1) dt = 0.1;
        lastTime = now;

        for (var i = 0; i < feDiscs.length; i++) {
            var d = feDiscs[i];
            d.x += vx * dt;
            d.y += vy * dt;
            if (d.x > d.tileW) d.x -= d.tileW;
            if (d.y > d.tileH) d.y -= d.tileH;
            var sx = d.x - d.offX;
            var sy = d.y - d.offY;
            d.el.style.transform = 'translate(' + sx + 'px,' + sy + 'px)';
            d.vis = (sx > -400 && sx < screenW && sy > -500 && sy < screenH);
        }

        for (var j = 0; j < feDiscs.length; j++) {
            var ws = feWaterSystems[feDiscs[j].ws];
            if (feDiscs[j].vis) {
                ws.update();
                ws.draw();
            } else {
                ws.clear();
            }
        }

        feAnimId = requestAnimationFrame(animate);
    }
    feAnimId = requestAnimationFrame(animate);
}

function feStop() {
    if (feAnimId) {
        cancelAnimationFrame(feAnimId);
        feAnimId = null;
    }
    feWaterSystems = [];
    feDiscs = [];
    var bg = document.getElementById('feBg');
    if (bg) bg.innerHTML = '';
}
