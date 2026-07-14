from __future__ import annotations

import unittest

from app.application.use_cases.generate_summary import GenerateSummaryUseCase


class _RecordingSummaryClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def generate_summary(self, content: str, stage: str = "final", max_sentences: int = 6) -> list[str]:
        self.calls.append((stage, content))
        if stage == "map":
            return [f"Chunk summary for {content.split('.', 1)[0].strip()}."]
        return [
            "The document explains the overall rules for using the service.",
            "It describes how the service can change over time.",
            "It covers payments, renewals, refunds, and data use.",
            "It explains content rights, account control, and security limits.",
            "It warns that accounts can be suspended or ended.",
            "It limits liability and sends disputes to arbitration.",
        ]


class SummaryTests(unittest.TestCase):
    def test_summary_uses_hierarchical_map_reduce_pipeline(self) -> None:
        client = _RecordingSummaryClient()
        use_case = GenerateSummaryUseCase(llm_client=client, chunk_char_limit=120)

        content = (
            "Section one explains the introduction and the main purpose of the document. "
            "Section one also sets a few basic rules for using the service. "
            "Section two describes payment, renewal, and refund terms. "
            "Section two also explains data handling and content rights. "
            "Section three covers account limits, security, and service changes. "
            "Section three explains how disputes are handled and how liability is limited."
        )

        result = use_case.execute(content)

        map_calls = [call for call in client.calls if call[0] == "map"]
        reduce_calls = [call for call in client.calls if call[0] == "reduce"]

        self.assertGreaterEqual(len(map_calls), 2)
        self.assertEqual(len(reduce_calls), 1)
        self.assertEqual(len(result.bullets), 6)
        self.assertTrue(all(bullet.endswith((".", "!", "?")) for bullet in result.bullets))
        self.assertTrue(all("..." not in bullet for bullet in result.bullets))
        self.assertTrue(any("overall rules" in bullet for bullet in result.bullets))
        self.assertTrue(any("payments" in bullet.lower() for bullet in result.bullets))
        self.assertTrue(any("data" in bullet.lower() for bullet in result.bullets))
        self.assertTrue(any("arbitration" in bullet.lower() for bullet in result.bullets))

    def test_summary_fallback_uses_complete_sentences_without_truncation(self) -> None:
        use_case = GenerateSummaryUseCase()

        content = (
            "The opening section introduces the document and explains the basic relationship. "
            "The next section describes fees and billing. "
            "Another section covers data use and service changes. "
            "A later section explains account limits and content rights. "
            "The closing section explains dispute handling and liability."
        )

        result = use_case.execute(content)

        self.assertTrue(result.bullets)
        self.assertLessEqual(len(result.bullets), 6)
        self.assertTrue(all(bullet.endswith((".", "!", "?")) for bullet in result.bullets))
        self.assertTrue(all("..." not in bullet for bullet in result.bullets))


if __name__ == "__main__":
    unittest.main()