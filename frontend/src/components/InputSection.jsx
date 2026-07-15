export default function InputSection({
  content,
  onChange,
  onAnalyze,
  onExtractPage,
  loading,
  showExtract,
}) {
  return (
    <section className="panel input-section">
      <h2 className="panel__title">Input Section</h2>
      <textarea
        className="input-textarea"
        value={content}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Paste your agreement, terms of service, or privacy policy here…"
        rows={8}
        disabled={loading}
      />
      <div className="input-actions">
        {showExtract && (
          <button
            type="button"
            className="btn btn--secondary"
            onClick={onExtractPage}
            disabled={loading}
          >
            Extract from Page
          </button>
        )}
        <button
          type="button"
          className="btn btn--primary"
          onClick={onAnalyze}
          disabled={loading}
        >
          {loading ? (
            <>
              <span className="btn-spinner" aria-hidden="true" />
              Analyzing…
            </>
          ) : (
            <>
              <svg className="btn-icon" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616 1.738 5.574a1 1 0 01-.285 1.05A3.989 3.989 0 0115 15a3.989 3.989 0 01-2.122-.665 1 1 0 01-.285-1.05l1.715-5.493L9 6.477V16h2a1 1 0 110 2H9a1 1 0 01-1-1v-7H5a1 1 0 110-2h2V3a1 1 0 011-1z" />
              </svg>
              Analyze
            </>
          )}
        </button>
      </div>
    </section>
  );
}
