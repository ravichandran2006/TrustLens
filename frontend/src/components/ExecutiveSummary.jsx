export default function ExecutiveSummary({ summary }) {
  return (
    <section className="panel result-card">
      <h2 className="panel__title">Executive Summary</h2>
      <p className="panel__desc">
        A plain-language overview of the key terms and findings in this agreement.
      </p>
      {summary?.length > 0 ? (
        <ul className="summary-list">
          {summary.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="empty-state">No summary available.</p>
      )}
    </section>
  );
}
