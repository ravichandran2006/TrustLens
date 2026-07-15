export default function Recommendations({ recommendations }) {
  return (
    <section className="panel result-card">
      <h2 className="panel__title">Key Recommendations</h2>
      <p className="panel__desc">Key recommendations for this agreement:</p>
      {recommendations?.length > 0 ? (
        <ul className="recommendations-list">
          {recommendations.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="empty-state">No specific recommendations.</p>
      )}
    </section>
  );
}
