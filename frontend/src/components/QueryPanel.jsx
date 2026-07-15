import { useState } from "react";

export default function QueryPanel({
  suggestions,
  activeQuestion,
  answer,
  loading,
  onAsk,
}) {
  const [customQuestion, setCustomQuestion] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    const q = customQuestion.trim();
    if (q) {
      onAsk(q);
      setCustomQuestion("");
    }
  };

  return (
    <section className="panel query-panel">
      <h2 className="panel__title">Ask About This Agreement</h2>
      <p className="panel__desc">
        Compact professional query panel — ask specific questions about this agreement.
      </p>

      <form className="query-form" onSubmit={handleSubmit}>
        <input
          type="text"
          className="query-input"
          placeholder="Ask a question about this agreement…"
          value={customQuestion}
          onChange={(e) => setCustomQuestion(e.target.value)}
          disabled={loading}
        />
        <button type="submit" className="btn btn--primary btn--sm" disabled={loading}>
          Ask
        </button>
      </form>

      <div className="query-columns">
        <div className="query-suggestions">
          <p className="query-suggestions__label">Suggested Questions</p>
          <ul className="suggestion-list">
            {suggestions.map((q) => (
              <li key={q}>
                <button
                  type="button"
                  className={`suggestion-btn ${activeQuestion === q ? "suggestion-btn--active" : ""}`}
                  onClick={() => onAsk(q)}
                  disabled={loading}
                >
                  {q}
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className="query-answers">
          <p className="query-answers__label">Answer</p>
          {loading && (
            <div className="answer-bubble answer-bubble--loading">
              <span className="btn-spinner" />
              Finding answer…
            </div>
          )}
          {!loading && answer && (
            <>
              <div className="answer-bubble">{answer.answer}</div>
              {answer.sources?.length > 0 && (
                <div className="answer-sources">
                  Sources: {answer.sources.join(", ")}
                </div>
              )}
            </>
          )}
          {!loading && !answer && (
            <p className="empty-state">Select a question or type your own above.</p>
          )}
        </div>
      </div>
    </section>
  );
}
