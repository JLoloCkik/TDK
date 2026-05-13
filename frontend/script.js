const display = document.querySelector('.display');
const input = document.getElementById('ai-input');

let cur = '0', prev = null, op = null, reset = false;

const update = () => display.textContent = cur;

const api = async (url, body) => {
    // Kiolvassuk, melyik backendet választottad a rádión
    const port = document.querySelector('input[name="backend"]:checked').value;

    try {
        const r = await fetch(`http://127.0.0.1:${port}/api/${url}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body)
        });
        const data = await r.json();

        if (url === "calculate"){
            cur = String(data.result);
            update();
        }
    } catch (e) {
        cur = "Szerver hiba";
        update();
        console.error("Hiba a backend elérésekor:", e);
    }
};


// ---- LOGIC ----
const number = v => {
    if (reset) { cur = v; reset = false; }
    else cur = cur === '0' ? v : cur + v;
};

const decimal = () => {
    if (!cur.includes('.')) cur += '.';
};

const operator = v => {
    if (op && !reset) compute();
    prev = +cur;
    op = v;
    reset = true;
};

const compute = () => {
    if (!op || prev === null) return;
    api('calculate', { a: prev, b: +cur, operator: op });
    op = null;
    reset = true;
};

const clear = () => {
    cur = '0';
    prev = op = null;
    reset = false;
};


// ---- BUTTONS ----
document.querySelector('.buttons').onclick = e => {
    if (!e.target.matches('button')) return;

    const { type, value } = e.target.dataset;

    if (type === 'number') number(value);
    if (type === 'decimal') decimal();
    if (type === 'operator') operator(value);
    if (type === 'equals') compute();
    if (type === 'clear') clear();

    update();
};

// ---- AI ----
const sendAI = () => {
    const text = input.value;
    if (!text) return;
    api('ai', {
        text: input.value,
        current_number: cur
    });
    input.value = '';
    reset = true;
};

document.getElementById('ai-send').onclick = sendAI;
input.addEventListener('keydown', e => e.key === 'Enter' && sendAI());

update();