import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).parents[1] / "skills" / "start-my-day" / "scripts" / "search_arxiv.py"
SPEC = importlib.util.spec_from_file_location("search_arxiv", SCRIPT)
search_arxiv = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(search_arxiv)


class FakeResponse:
    headers = {"Content-Type": "application/octet-stream"}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return b"%PDF-1.4\ncomplete test PDF\n%%EOF\n"


class StartMyDayGeophysicsTests(unittest.TestCase):
    def test_categories_come_from_config_without_duplicates(self):
        config = {
            "research_domains": {
                "a": {"arxiv_categories": ["physics.geo-ph", "eess.SP"]},
                "b": {"arxiv_categories": ["eess.SP", "cs.LG"]},
            }
        }
        self.assertEqual(
            search_arxiv.categories_from_config(config),
            ["physics.geo-ph", "eess.SP", "cs.LG"],
        )

    def test_preferred_venue_increases_relevance(self):
        paper = {
            "title": "Seismic deblending with sparse inversion",
            "summary": "A method for simultaneous source seismic data.",
            "categories": ["physics.geo-ph"],
            "venue": "GEOPHYSICS",
            "published_date": None,
        }
        config = {
            "research_domains": {
                "deblending": {
                    "keywords": ["seismic deblending"],
                    "arxiv_categories": ["physics.geo-ph"],
                    "priority": 10,
                }
            },
            "preferred_venues": ["GEOPHYSICS"],
        }
        scored = search_arxiv.filter_and_score_papers([paper], config)
        self.assertEqual(scored[0]["scores"]["relevance"], 2.3)
        self.assertIn("GEOPHYSICS", scored[0]["matched_keywords"])

    def test_broad_category_without_geophysics_keyword_is_rejected(self):
        paper = {
            "title": "Hyperspectral fish freshness classification",
            "summary": "A computer vision method for food quality.",
            "categories": ["eess.IV", "cs.LG"],
            "published_date": None,
        }
        config = {
            "research_domains": {
                "seismic": {
                    "keywords": ["seismic", "full waveform inversion"],
                    "arxiv_categories": ["physics.geo-ph", "eess.IV", "cs.LG"],
                    "priority": 10,
                }
            }
        }
        self.assertEqual(search_arxiv.filter_and_score_papers([paper], config), [])

    def test_geophysics_category_remains_strong_domain_evidence(self):
        paper = {
            "title": "A new subsurface imaging approach",
            "summary": "We recover geological structure from field observations.",
            "categories": ["physics.geo-ph"],
            "published_date": None,
        }
        config = {
            "research_domains": {
                "geophysics": {
                    "keywords": ["seismic"],
                    "arxiv_categories": ["physics.geo-ph"],
                    "priority": 10,
                }
            }
        }
        self.assertEqual(len(search_arxiv.filter_and_score_papers([paper], config)), 1)

    @patch.object(search_arxiv.urllib.request, "urlopen", return_value=FakeResponse())
    def test_download_records_local_wikilink_atomically(self, urlopen):
        candidates = [{
            "arxiv_id": "2601.01234",
            "title": "A seismic paper",
            "pdf_url": "https://arxiv.org/pdf/2601.01234",
        }]
        with tempfile.TemporaryDirectory() as temp_dir:
            papers, failures = search_arxiv.select_top_papers(candidates, 1, temp_dir)
            self.assertTrue((Path(temp_dir) / "2601.01234.pdf").exists())
            self.assertEqual(papers[0]["local_pdf_wikilink"], "[[2601.01234.pdf|PDF]]")
            self.assertEqual(papers[0]["download_status"], "downloaded")
            self.assertEqual(failures, [])
            self.assertEqual(urlopen.call_count, 1)
            self.assertEqual(list(Path(temp_dir).glob("*.part")), [])

    @patch.object(search_arxiv.urllib.request, "urlopen", return_value=FakeResponse())
    def test_existing_arxiv_version_is_reused_without_download(self, urlopen):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            existing = root / "original-local-name.pdf"
            existing.write_bytes(b"%PDF-1.4\nexisting PDF\n%%EOF\n")
            (root / "paper.md").write_text(
                "---\narxiv_id: 2608.05763\ntitle: Original title\n---\n"
                "[[original-local-name.pdf|PDF]]\n",
                encoding="utf-8",
            )
            candidates = [{
                "id": "https://arxiv.org/abs/2608.05763v9",
                "title": "Renamed version of the paper",
                "pdf_url": "https://arxiv.org/pdf/2608.05763v9",
            }]

            papers, failures = search_arxiv.select_top_papers(candidates, 1, temp_dir)

            self.assertEqual(papers[0]["local_pdf_filename"], existing.name)
            self.assertEqual(papers[0]["download_status"], "reused")
            self.assertEqual(failures, [])
            urlopen.assert_not_called()

    @patch.object(search_arxiv.urllib.request, "urlopen", return_value=FakeResponse())
    def test_missing_or_invalid_candidate_is_backfilled(self, urlopen):
        candidates = [
            {"title": "No open PDF"},
            {
                "title": "A valid replacement",
                "pdf_url": "https://example.org/replacement.pdf",
            },
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            papers, failures = search_arxiv.select_top_papers(candidates, 1, temp_dir)

            self.assertEqual([paper["title"] for paper in papers], ["A valid replacement"])
            self.assertEqual(len(failures), 1)
            self.assertIn("No open PDF", failures[0])
            self.assertEqual(urlopen.call_count, 1)

    def test_incomplete_existing_pdf_is_not_reused(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            broken = Path(temp_dir) / "A_seismic_paper.pdf"
            broken.write_bytes(b"%PDF-1.4\npartial")
            index = search_arxiv.build_existing_pdf_index(temp_dir)
            self.assertIsNone(
                search_arxiv.find_existing_pdf({"title": "A seismic paper"}, index)
            )

    def test_arxiv_versions_have_same_canonical_id(self):
        self.assertEqual(search_arxiv.canonical_arxiv_id("2608.05763v1"), "2608.05763")
        self.assertEqual(search_arxiv.canonical_arxiv_id("2608.05763v9"), "2608.05763")

    def test_semantic_scholar_open_access_pdf_is_supported(self):
        paper = {"openAccessPdf": {"url": "https://example.org/paper.pdf"}}
        self.assertEqual(search_arxiv.paper_pdf_url(paper), "https://example.org/paper.pdf")


if __name__ == "__main__":
    unittest.main()
