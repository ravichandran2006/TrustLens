function severityClass(severity) {
  const level = severity?.toLowerCase();
  if (level === "high") return "risk-item--high";
  if (level === "medium") return "risk-item--medium";
  return "risk-item--low";
}

function WarningIcon() {
  return (
    <svg className="risk-icon" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <path
        fillRule="evenodd"
        d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
        clipRule="evenodd"
      />
    </svg>
  );
}

export default function RiskAnalysis({ risks }) {
  return (
    <section className="panel result-card">
      <h2 className="panel__title">Risk Analysis</h2>
      {risks?.length > 0 ? (
        <ul className="risk-list">
          {risks.map((risk, i) => (
            <li key={i} className={`risk-item ${severityClass(risk.severity)}`}>
              <WarningIcon />
              <div className="risk-item__body">
                <span className="risk-item__title">{risk.title}</span>
                <span className="risk-item__level">
                  Risk Level: {risk.severity}
                </span>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="empty-state">No significant risks detected.</p>
      )}
    </section>
  );
}
