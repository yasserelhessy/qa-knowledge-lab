const form = document.querySelector('#ask-form');
const question = document.querySelector('#question');
const submit = document.querySelector('#submit');
const result = document.querySelector('#result');
const error = document.querySelector('#error');
fetch('/api/health').then(r => { if (!r.ok) throw Error(); return r.json(); })
  .then(data => { document.querySelector('#mode').textContent = data.mode === 'demo' ? '● Offline demo' : '● Live model'; })
  .catch(() => { document.querySelector('#mode').textContent = 'Service unavailable'; });
document.querySelectorAll('[data-question]').forEach(button => {
  button.addEventListener('click', () => { question.value = button.dataset.question; question.focus(); });
});
form.addEventListener('submit', async event => {
  event.preventDefault();
  error.hidden = true; result.hidden = true; submit.disabled = true;
  submit.textContent = 'Checking evidence…';
  try {
    const response = await fetch('/api/ask', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({question: question.value.trim()}),
      signal: AbortSignal.timeout(30000)
    });
    if (!response.ok) throw new Error(response.status === 422 ? 'Enter a question with 3–500 characters.' : 'The answer service is unavailable. Please retry.');
    const data = await response.json();
    document.querySelector('#answer').textContent = data.answer;
    document.querySelector('#status').textContent = data.status === 'answered' ? 'Source attached' : 'Not in the playbook';
    const sources = document.querySelector('#sources');
    sources.replaceChildren();
    for (const source of data.sources) {
      const details = document.createElement('details');
      const summary = document.createElement('summary');
      const excerpt = document.createElement('p');
      summary.textContent = `Evidence · ${source.title}`;
      excerpt.textContent = source.excerpt;
      details.append(summary, excerpt); sources.append(details);
    }
    result.hidden = false;
  } catch (problem) {
    error.textContent = problem.name === 'TimeoutError' ? 'Request timed out. Please retry.' : problem.message;
    error.hidden = false;
  } finally {
    submit.disabled = false; submit.textContent = 'Find an answer →';
  }
});
