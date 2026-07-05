export default function AboutModal({ models, onClose }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} aria-label="Close">
          &times;
        </button>

        <h2>What is this?</h2>
        <p>
          Humanity's first exam asks state-of-the-art models to respond to a six simple
          questions. By reading their responses, you can decide how much you like a model.
        </p>

        <ul className="model-list">
          {models.map((model) => (
            <li key={model.id}>
              <a href={`https://openrouter.ai/${model.id}`} target="_blank" rel="noopener noreferrer">
                {model.name}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
