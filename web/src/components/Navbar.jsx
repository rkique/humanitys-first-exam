export default function Navbar({ slugs, activeSlug, onSelect }) {
  return (
    <div className="navbar">
      {slugs.map((slug) => (
        <div
          key={slug}
          className={`tab${slug === activeSlug ? ' active' : ''}`}
          onClick={() => onSelect(slug)}
        >
          {slug}
        </div>
      ))}
    </div>
  );
}
