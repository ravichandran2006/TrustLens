import { useState, useCallback } from "react";
import {
  analyzeAgreement,
  askQuestion,
  extractPageText,
  isExtensionContext,
} from "./api/client";
import Header from "./components/Header";
import InputSection from "./components/InputSection";
import ExecutiveSummary from "./components/ExecutiveSummary";
import RiskAnalysis from "./components/RiskAnalysis";
import TrustScore from "./components/TrustScore";
import Recommendations from "./components/Recommendations";
import QueryPanel from "./components/QueryPanel";
import "./styles/App.css";

const DEFAULT_SUGGESTIONS = [
  "Is my data shared with third parties?",
  "Can I cancel my subscription anytime?",
  "Are refunds available?",
  "What happens if I miss a payment?",
];

const SAMPLE_TEXT = `SUBSCRIPTION AGREEMENT

This Subscription Agreement ("Agreement") is entered into between the Subscriber and the Service Provider.

1. AUTO RENEWAL: Your subscription will automatically renew at the end of each billing period unless you cancel at least 30 days before the renewal date. You authorize us to charge your payment method on file.

2. DATA SHARING: We may share your personal information, usage data, and analytics with third-party vendors, partners, and advertisers for marketing and service improvement purposes.

3. REFUND POLICY: All payments are final. No refunds will be issued under any circumstances, including partial billing periods or unused services.

4. LATE PAYMENT: Failure to pay on time may result in immediate suspension of service and a late fee of 5% of the outstanding balance per month.

5. MODIFICATIONS: We reserve the right to modify these terms at any time without prior notice. Continued use constitutes acceptance of modified terms.`;

export default function App() {
  const [content, setContent] = useState(SAMPLE_TEXT);
  const [analysis, setAnalysis] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState(null);
  const [activeQuestion, setActiveQuestion] = useState(null);
  const [answer, setAnswer] = useState(null);
  const [questionLoading, setQuestionLoading] = useState(false);

  const handleAnalyze = useCallback(async () => {
    if (!content.trim()) {
      setError("Please enter agreement text to analyze.");
      return;
    }

    setStatus("loading");
    setError(null);
    setAnalysis(null);
    setActiveQuestion(null);
    setAnswer(null);

    try {
      const result = await analyzeAgreement(content.trim());
      setAnalysis(result);
      setStatus("complete");
    } catch (err) {
      setError(err.message || "Analysis failed. Is the backend running?");
      setStatus("idle");
    }
  }, [content]);

  const handleExtractPage = useCallback(async () => {
    if (!isExtensionContext()) return;

    setError(null);
    try {
      const text = await extractPageText();
      if (text) {
        setContent(text);
        setAnalysis(null);
        setStatus("idle");
      }
    } catch (err) {
      setError(err.message);
    }
  }, []);

  const handleAskQuestion = useCallback(
    async (question) => {
      if (!analysis?.agreement_id) {
        setError("Analyze an agreement first before asking questions.");
        return;
      }

      setActiveQuestion(question);
      setQuestionLoading(true);
      setAnswer(null);
      setError(null);

      try {
        const result = await askQuestion(analysis.agreement_id, question);
        setAnswer(result);
      } catch (err) {
        setError(err.message || "Failed to get an answer.");
      } finally {
        setQuestionLoading(false);
      }
    },
    [analysis]
  );

  const suggestions =
    analysis?.risks?.length > 0
      ? [
          ...analysis.risks.slice(0, 2).map((r) => `Tell me more about: ${r.title}`),
          ...DEFAULT_SUGGESTIONS,
        ].slice(0, 4)
      : DEFAULT_SUGGESTIONS;

  return (
    <div className="app-shell">
      <div className="app-hero">
        <div className="logo-mark" aria-hidden="true">
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
            <path d="M16 18v4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </div>
        <h1 className="app-hero-title">TrustLens</h1>
        <p className="app-hero-subtitle">
          AI Agreement &amp; Policy Risk Intelligence Agent
        </p>
      </div>

      <div className="app-card">
        <Header status={status} />

        {error && (
          <div className="error-banner" role="alert">
            {error}
          </div>
        )}

        <InputSection
          content={content}
          onChange={setContent}
          onAnalyze={handleAnalyze}
          onExtractPage={handleExtractPage}
          loading={status === "loading"}
          showExtract={isExtensionContext()}
        />

        {analysis && (
          <>
            <div className="results-grid">
              <ExecutiveSummary summary={analysis.summary} />
              <RiskAnalysis risks={analysis.risks} />
            </div>

            <div className="results-grid">
              <TrustScore
                score={analysis.consumer_safety_score}
                riskLevel={analysis.risk_level}
                explanation={analysis.score_explanation}
              />
              <Recommendations recommendations={analysis.recommendations} />
            </div>

            <QueryPanel
              suggestions={suggestions}
              activeQuestion={activeQuestion}
              answer={answer}
              loading={questionLoading}
              onAsk={handleAskQuestion}
            />
          </>
        )}
      </div>
    </div>
  );
}
