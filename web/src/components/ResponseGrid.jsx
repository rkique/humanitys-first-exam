const MIN_FONT = 0.85;
const MAX_FONT = 1.3;
const MIN_LEN = 40;
const MAX_LEN = 300;
const CHARS_PER_LINE = 40;

function fontSizeFor(text) {
  const lines = text.split('\n').length;
  const effectiveLen = Math.max(text.length, lines * CHARS_PER_LINE);
  const t = Math.min(1, Math.max(0, (effectiveLen - MIN_LEN) / (MAX_LEN - MIN_LEN)));
  return (MAX_FONT - t * (MAX_FONT - MIN_FONT)).toFixed(2) + 'rem';
}

function modelNameOnly(name) {
  const idx = name.indexOf(': ');
  return idx === -1 ? name : name.slice(idx + 2);
}

export default function ResponseGrid({ models, category }) {
  return (
    <div className="grid">
      {models.map((model) => {
        const entry = category.responses[model.id] || {};
        const text = entry.error
          ? `(no response: ${entry.error})`
          : entry.content || '(empty response)';

        return (
          <div
            key={model.id}
            className="card"
            style={{ background: model.color, borderColor: model.color }}
          >
            <div className="card-title">{modelNameOnly(model.name)}</div>
            <div className="response-text" style={{ fontSize: fontSizeFor(text) }}>
              {text}
            </div>
          </div>
        );
      })}
    </div>
  );
}
