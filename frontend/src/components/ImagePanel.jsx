export default function ImagePanel({ data }) {
  const imgSrc = data.image || 'kotel.jpg';
  const fallback = 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Jerusalem_Symbol.svg/600px-Jerusalem_Symbol.svg.png';

  return (
    <div className="area-image">
      <img
        src={imgSrc}
        alt="Shul Image"
        className="shul-image"
        onError={(e) => { e.target.src = fallback; }}
      />
    </div>
  );
}
