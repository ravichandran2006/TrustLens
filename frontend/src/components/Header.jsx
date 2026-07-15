function StatusBadge({ status }) {
  if (status === "loading") {
    return (
      <span className="status-badge status-badge--loading">
        <span className="status-dot status-dot--pulse" />
        Analyzing…
      </span>
    );
  }

  if (status === "complete") {
    return (
      <span className="status-badge status-badge--complete">
        <span className="status-dot status-dot--green" />
        Analysis Complete
      </span>
    );
  }

  return (
    <span className="status-badge status-badge--idle">
      <span className="status-dot status-dot--gray" />
      Ready
    </span>
  );
}

export default function Header({ status }) {
  return (
    <header className="dashboard-header">
      <div className="dashboard-header__brand">
        <div className="logo-mark logo-mark--sm" aria-hidden="true">
          <svg viewBox="0 0 32 32" fill="none">
            <path
              d="M16 2L4 8v8c0 7.2 5.1 13.9 12 15 6.9-1.1 12-7.8 12-15V8L16 2z"
              fill="currentColor"
              opacity="0.15"
            />
            <path
              d="M16 4L6 9v7c0 6.1 4.3 11.8 10 12.8 5.7-1 10-6.7 10-12.8V9L16 4z"
              stroke="currentColor"
              strokeWidth="1.5"
              fill="none"
            />
            <circle cx="16" cy="14" r="4" stroke="currentColor" strokeWidth="1.5" fill="none" />
          </svg>
        </div>
        <span className="dashboard-header__name">TrustLens</span>
      </div>
      <StatusBadge status={status} />
    </header>
  );
}
