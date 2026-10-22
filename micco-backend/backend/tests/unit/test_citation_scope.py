from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.rag import validate_answer_citations


def source(source_id):
    return SimpleNamespace(index=source_id)


def image(image_id):
    return SimpleNamespace(ref_id=image_id)


def test_citation_ids_must_match_current_retrieval():
    assert validate_answer_citations("Theo tài liệu [ab12]", [source("ab12")]) == "Theo tài liệu [ab12]"
    with pytest.raises(HTTPException) as error:
        validate_answer_citations("Theo tài liệu [hbc1]", [source("hbcl")])
    assert error.value.status_code == 502


def test_image_ids_are_valid_and_years_are_not_citation_ids():
    assert validate_answer_citations("Ảnh [im31], năm [2024]", [], [image("im31")]) == "Ảnh [im31], năm [2024]"


def test_previous_turn_citation_is_rejected():
    with pytest.raises(HTTPException) as error:
        validate_answer_citations("[ab12]", [source("cd34")])
    assert error.value.status_code == 502


def test_citation_spacing_is_normalized_after_validation():
    assert validate_answer_citations("Theo [ rn2o] và [lm6y ]", [source("rn2o"), source("lm6y")]) == "Theo [rn2o] và [lm6y]"
    with pytest.raises(HTTPException) as error:
        validate_answer_citations("[ hbc1 ]", [source("hbcl")])
    assert error.value.status_code == 502
