import unittest

from app.services.text_processing import chunk_document, clean_steam_content


class TextProcessingTests(unittest.TestCase):
    def test_clean_markup(self) -> None:
        value = clean_steam_content("[h2]Balance[/h2]<br><b>Buff</b> &amp; fix")
        self.assertNotIn("[h2]", value)
        self.assertNotIn("<b>", value)
        self.assertIn("Buff & fix", value)

    def test_chunks_have_stable_hash_and_index(self) -> None:
        content = "Balance Changes\n\n" + ("Character A attack increased. " * 20)
        first = chunk_document(title="Patch 1", content=content, max_chars=180)
        second = chunk_document(title="Patch 1", content=content, max_chars=180)
        self.assertGreater(len(first), 1)
        self.assertEqual([item.chunk_index for item in first], list(range(len(first))))
        self.assertEqual(
            [item.content_hash for item in first], [item.content_hash for item in second]
        )


if __name__ == "__main__":
    unittest.main()
