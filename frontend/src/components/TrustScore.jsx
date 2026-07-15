function scoreColor(score) {
  if (score < 55) return "#ef4444";
  if (score < 75) return "#f59e0b";
  return "#22c55e";
}

export default function TrustScore({ score, riskLevel, explanation }) {
  const color = scoreColor(score);
  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (score / 100) * circumference;

  return (
    <section className="panel result-card trust-score-card">
      <h2 className="panel__title">Trust Score</h2>
      <div className="trust-score">
        <div className="trust-gauge">
          <svg viewBox="0 0 120 120" className="trust-gauge__svg">
            <circle
              cx="60"
              cy="60"
              r="54"
              fill="none"
              stroke="#e5e7eb"
              strokeWidth="10"
            />
            <circle
              cx="60"
              cy="60"
              r="54"
              fill="none"
              stroke={color}
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              transform="rotate(-90 60 60)"
              className="trust-gauge__arc"
            />
          </svg>
          <div className="trust-gauge__label">
            <span className="trust-gauge__title">Trust Score</span>
            <span className="trust-gauge__value" style={{ color }}>
              {score}/100
            </span>
            <span className="trust-gauge__level">{riskLevel} Risk</span>
          </div>
        </div>
        {explanation && (
          <p className="trust-score__explanation">{explanation}</p>
        )}
      </div>
    </section>
  );
}
