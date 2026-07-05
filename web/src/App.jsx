import { useEffect, useState } from 'react';
import Navbar from './components/Navbar.jsx';
import ResponseGrid from './components/ResponseGrid.jsx';
import AboutModal from './components/AboutModal.jsx';

export default function App() {
  const [data, setData] = useState(null);
  const [activeSlug, setActiveSlug] = useState(null);
  const [aboutOpen, setAboutOpen] = useState(false);

  useEffect(() => {
    fetch('cache/models_latest.json', { cache: 'no-store' })
      .then((res) => res.json())
      .then((json) => {
        setData(json);
        setActiveSlug(Object.keys(json.categories)[0]);
      });
  }, []);

  if (!data) {
    return <div className="wrap" />;
  }

  const slugs = Object.keys(data.categories);
  const category = data.categories[activeSlug];

  return (
    <div className="wrap">
      <h1 className="page-title">Humanity's First Exam</h1>

      <Navbar slugs={slugs} activeSlug={activeSlug} onSelect={setActiveSlug} />

      <div className="prompt-text">{category.prompt}</div>

      <ResponseGrid models={data.models} category={category} />

      <button className="help-button" onClick={() => setAboutOpen(true)} aria-label="About this page">
        ?
      </button>

      {aboutOpen && <AboutModal models={data.models} onClose={() => setAboutOpen(false)} />}
    </div>
  );
}
