const display = document.querySelector('.display');
let cur = '0', first = null, op = null, reset = false;

const update = () => display.textContent = cur;

async function callBackend(endpoint, body) {
    try {
        const r = await fetch(`http://localhost/api/${endpoint}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body)
        });
        const d = await r.json();
        cur = String(d.result);
    } catch (e) {
        if(endpoint === 'calculate') {
            const m = {'+':body.a+body.b, '-':body.a-body.b, '*':body.a*body.b, '/':body.b===0?'Hiba':body.a/body.b};
            cur = String(m[body.operator]);
        } else cur = "Error";
    }
    update();
}

document.querySelector('.calculator-container').addEventListener('click', e => {
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
        callBackend('calculate', { a: first, b: parseFloat(cur), operator: op });
        op = null; reset = true;
    } else if (type === 'ai') {
        callBackend('ai', { text: cur });
        reset = true;
    } else if (type === 'clear') {
        cur = '0'; first = op = null; reset = false;
    }
    update();
});