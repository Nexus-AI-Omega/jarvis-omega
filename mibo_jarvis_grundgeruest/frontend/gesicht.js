// Jarvis' Fenster: zeigt das Gesicht als LED-Raster und den letzten Wortwechsel.
// Das Bild rechnet der Server (gesicht.py); hier wird es nur gezeichnet.

const leinwand = document.getElementById('gesicht');
const stift = leinwand.getContext('2d');
const duZeile = document.getElementById('du');
const jarvisZeile = document.getElementById('jarvis');

async function zeichnen() {
    try {
        const r = await fetch('/api/gesicht', { cache: 'no-store' });
        const px = new Uint8Array(await r.arrayBuffer());
        const n = Math.round(Math.sqrt(px.length / 3));
        const zelle = leinwand.width / n;
        const led = zelle * 0.4;               // runde LEDs mit Abstand dazwischen
        stift.fillStyle = '#03060d';
        stift.fillRect(0, 0, leinwand.width, leinwand.height);
        for (let y = 0; y < n; y++) {
            for (let x = 0; x < n; x++) {
                const i = (y * n + x) * 3;
                const an = Math.max(px[i], px[i + 1], px[i + 2]) > 30;   // fast schwarze Randpixel zaehlen als aus
                // ausgeschaltete LEDs ganz schwach, damit man das Raster ahnt
                stift.fillStyle = an ? `rgb(${px[i]},${px[i + 1]},${px[i + 2]})` : '#0a1424';
                stift.beginPath();
                stift.arc((x + 0.5) * zelle, (y + 0.5) * zelle, led, 0, 2 * Math.PI);
                stift.fill();
            }
        }
        setTimeout(zeichnen, 60);
    } catch (e) {
        setTimeout(zeichnen, 2000);            // Jarvis startet gerade neu
    }
}

function verbinden() {
    const ws = new WebSocket(`ws://${location.host}/ws`);
    ws.onmessage = (e) => {
        const m = JSON.parse(e.data);
        if (m.art === 'du') {
            duZeile.textContent = `„${m.text}“`;
            jarvisZeile.textContent = '…';
        } else {
            jarvisZeile.textContent = m.text;
        }
    };
    ws.onclose = () => setTimeout(verbinden, 2000);
}

leinwand.addEventListener('click', () => fetch('/api/zuhoeren', { method: 'POST' }));

zeichnen();
verbinden();
