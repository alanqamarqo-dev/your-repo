import pathlib


def test_pipeline_doc_exists():
    p = pathlib.Path(r"d:/AGL/Integration_Layer/PIPELINE.md")
    assert p.exists(), "PIPELINE.md should exist in Integration_Layer"
    text = p.read_text(encoding='utf8')
    assert 'واجهة' in text or 'API' in text, "PIPELINE.md should contain Arabic summary"


def test_pipeline_contains_json_example():
    p = pathlib.Path(r"d:/AGL/Integration_Layer/PIPELINE.md")
    text = p.read_text(encoding='utf8')
    assert '"ok": true' in text or '"confidence":' in text, "PIPELINE.md should include example JSON schema"
