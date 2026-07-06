export default function AboutModal({ models, onClose }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} aria-label="Close">
          &times;
        </button>

        <h2>What is this?</h2>
        <p>
          Named after <a href="https://agi.safe.ai/">Humanity's Last Exam </a>, Humanity's First Exam asks nine state-of-the-art models to respond to a six simple
          questions.  <br/>
          By reading their responses, you can decide how much you like a model. <br />
          Updates every Sunday; contact <a href="mailto:eriq.xia@gmail.com">eriq.xia@gmail.com</a> with suggestions.
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
