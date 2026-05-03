const display = document.querySelector('.display');
let cur = '0', first = null, op = null, reset = false;

const update = () => display.textContent = cur;


async function callBackend(a, b, operator) {
    try {
        const r = await fetch('http://localhost/api/calculate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ a, b, operator })
        });
        const d = await r.json();
        cur = String(d.result);
    } catch (e) {
        const m = {'+':a+b, '-':a-b, '*':a*b, '/':b===0?'Hiba':a/b};
        cur = String(m[operator]);
    }
    update();
}

document.querySelector('.buttons').addEventListener('click', e => {
    const btn = e.target;
    if (!btn.matches('button')) return;
    const { type } = btn.dataset, val = btn.value;

    if (type === 'number') {
        cur = (cur === '0' || reset) ? val : cur + val;
        reset = false;
    } else if (type === 'operator') {
        first = parseFloat(cur);
        op = val;
        reset = true;
    } else if (type === 'equals' && op) {
        callBackend(first, parseFloat(cur), op);
        op = null; reset = true;
    } else if (type === 'clear') {
        cur = '0'; first = op = null; reset = false;
    }
    update();
});