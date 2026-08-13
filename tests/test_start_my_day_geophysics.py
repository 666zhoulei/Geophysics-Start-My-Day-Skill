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
        return b"%PDF-1.4 test"


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
    def test_download_records_local_wikilink(self, _urlopen):
        papers = [{
            "arxiv_id": "2601.01234",
            "title": "A seismic paper",
            "pdf_url": "https://arxiv.org/pdf/2601.01234",
        }]
        with tempfile.TemporaryDirectory() as temp_dir:
            search_arxiv.download_top_papers(papers, temp_dir)
            self.assertTrue((Path(temp_dir) / "2601.01234.pdf").exists())
            self.assertEqual(papers[0]["local_pdf_wikilink"], "[[2601.01234.pdf|PDF]]")

    def test_download_fails_when_any_pdf_url_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(RuntimeError):
                search_arxiv.download_top_papers([{"title": "No open PDF"}], temp_dir)

    def test_semantic_scholar_open_access_pdf_is_supported(self):
        paper = {"openAccessPdf": {"url": "https://example.org/paper.pdf"}}
        self.assertEqual(search_arxiv.paper_pdf_url(paper), "https://example.org/paper.pdf")


if __name__ == "__main__":
    unittest.main()
