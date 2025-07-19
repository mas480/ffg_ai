import pytest
from analyzer import (
    extract_scores,
    highlight_best_worst_phrases,
    classify_image_clip,
    encode_image_base64,
    print_photo_analysis_results
)
from unittest.mock import patch
from pathlib import Path

def test_extract_scores_valid_json():
    text = '{"score": 5}\nРекомендация: всё ок'
    result = extract_scores(text)
    assert result[0] == {"score": 5}
    assert "Рекомендация" in result[1]

def test_extract_scores_no_json():
    text = "Рекомендация: всё ок"
    result = extract_scores(text)
    assert result[0] == {}
    assert "всё ок" in result[1]

def test_highlight_best_worst_phrases():
    text = "**Отлично!** А вот __это__ можно улучшить."
    highlights = highlight_best_worst_phrases(text)
    assert highlights["best"] == ["Отлично!"]
    assert highlights["worst"] == ["это"]

def test_encode_image_base64(tmp_path):
    img_path = tmp_path / "test.png"
    img_path.write_bytes(b"fake image content")
    b64 = encode_image_base64(str(img_path), include_mime=False)
    assert isinstance(b64, str)

@patch("analyzer.explain_photo_via_gpt")
@patch("analyzer.classify_image_clip")
def test_print_photo_analysis_results(mock_classify, mock_explain):
    mock_results = [{
        "image_path": "/fake/image1.jpg",
        "photo_class": "Класс 1",
        "class_rank": 1,
        "confidence": 0.9,
        "feedback": "Совет",
        "recommended_position": 1
    }]
    text = print_photo_analysis_results(mock_results)
    assert "Фото:" in text
    assert "Фидбек" in text