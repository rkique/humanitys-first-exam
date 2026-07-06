import { useEffect, useState } from 'react';
import Navbar from './components/Navbar.jsx';
import ResponseGrid from './components/ResponseGrid.jsx';
import AboutModal from './components/AboutModal.jsx';

const BASE = import.meta.env.BASE_URL;

function slugFromPath(slugs) {
  let path = window.location.pathname;
  if (path.startsWith(BASE)) path = path.slice(BASE.length);
  path = path.replace(/^\/+|\/+$/g, '');
  return slugs.includes(path) ? path : null;
}

export default function App() {
  const [data, setData] = useState(null);
  const [activeSlug, setActiveSlug] = useState(null);
  const [aboutOpen, setAboutOpen] = useState(false);

  useEffect(() => {
    fetch('cache/models_latest.json', { cache: 'no-store' })
      .then((res) => res.json())
      .then((json) => {
        setData(json);
        const slugs = Object.keys(json.categories);
        setActiveSlug(slugFromPath(slugs) || slugs[0]);
      });
  }, []);

  useEffect(() => {
    if (!data) return;
    const slugs = Object.keys(data.categories);
    const onPopState = () => setActiveSlug(slugFromPath(slugs) || slugs[0]);
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, [data]);

  function selectSlug(slug) {
    setActiveSlug(slug);
    window.history.pushState(null, '', BASE + slug);
  }

  if (!data) {
    return <div className="wrap" />;
  }

  const slugs = Object.keys(data.categories);
  const category = data.categories[activeSlug];

  return (
    <div className="wrap">
      <h1 className="page-title">Humanity's First Exam</h1>

      <Navbar slugs={slugs} activeSlug={activeSlug} onSelect={selectSlug} />

      <div className="prompt-text">{category.prompt}</div>

      <ResponseGrid models={data.models} category={category} />

      <button className="help-button" onClick={() => setAboutOpen(true)} aria-label="About this page">
        ?
      </button>

      {aboutOpen && <AboutModal models={data.models} onClose={() => setAboutOpen(false)} />}
    </div>
  );
}
