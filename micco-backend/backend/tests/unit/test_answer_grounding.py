"""Offline regressions using source text captured in chat-kb-20261022.

The LLM boundary deliberately selects misleading *verbatim* quotes and returns
an unsupported relation. The real guard must stop it despite valid citations.
No network, DB, or authorization mocks are involved.
"""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services.answer_guard import guard_answer, NO_EVIDENCE

LIVE = json.loads((Path(__file__).parents[1] / 'fixtures/answer_grounding_live.json').read_text())


class ScriptedProvider:
    def __init__(self, evidence, answer):
        self.evidence = evidence
        self.answer = answer
        self.inputs = []

    async def acomplete(self, messages, **kwargs):
        self.inputs.append(json.loads(messages[0].content))
        if len(self.inputs) == 1:
            return json.dumps({'evidence': self.evidence}, ensure_ascii=False)
        return json.dumps({'decision': 'replace', 'answer': self.answer,
                           'evidence': self.evidence}, ensure_ascii=False)


async def run_guard(question, sources, answer, quotes=None):
    evidence = quotes if quotes is not None else [
        {'source_id': s['index'], 'quote': s['content']} for s in sources]
    provider = ScriptedProvider(evidence, answer)
    result = await guard_answer(question, 'UNTRUSTED DRAFT',
                               [SimpleNamespace(**s) for s in sources], provider=provider)
    return result, provider


@pytest.mark.parametrize('case', ['hr-council', 'director-hr-council'])
@pytest.mark.parametrize('chunk', [0, 1])
async def test_administrative_lists_do_not_support_membership(case, chunk):
    data = LIVE[case]
    # Both the distribution list and implementation clause were actually retrieved.
    source = data['sources'][chunk]
    answer = f"Hội đồng An toàn lao động gồm các Phó Tổng giám đốc [{source['index']}]."
    result, _ = await run_guard(data['question'], [source], answer)
    assert result.answer == NO_EVIDENCE


async def test_unrelated_membership_does_not_support_requested_subject():
    data = LIVE['director-board-council']
    source = {**data['sources'][0],
              'content': 'Ban kiểm kê tài sản gồm các thành viên: Nguyễn Văn Nam, Lê Thị Mai.',
              'heading_path': ['Thành phần Ban kiểm kê tài sản'], 'source_file': 'Kiểm kê.docx'}
    result, _ = await run_guard(data['question'], [source],
                               'Hội đồng An toàn lao động gồm Nguyễn Văn Nam, Lê Thị Mai [1p76].')
    assert result.answer == NO_EVIDENCE


async def test_distribution_in_formation_document_is_not_membership():
    source = {**LIVE['director-board-council']['sources'][0],
              'heading_path': ['Hội đồng An toàn lao động', 'Nơi nhận'],
              'content': '- Nguyễn Văn Nam;\n- Lê Thị Mai.'}
    result, _ = await run_guard(LIVE['hr-council']['question'], [source],
                               'Hội đồng An toàn lao động gồm Nguyễn Văn Nam, Lê Thị Mai [1p76].')
    assert result.answer == NO_EVIDENCE


@pytest.mark.parametrize('case', ['director-board-council', 'hr-emicco-lock', 'hr-training',
                                'tech-record-retention', 'legal-contract-template'])
async def test_live_supported_answers_remain_available(case):
    data = LIVE[case]
    quotes = ([{'source_id': '1p76', 'quote': data['sources'][0]['content']}]
              if case == 'director-board-council' else None)
    result, _ = await run_guard(data['question'], data['sources'], data['answer'], quotes)
    assert result.answer == data['answer']
    assert result.reviewed


@pytest.mark.parametrize(('chunk', 'question', 'answer'), [
    (0, 'Quyết định quản lý vật tư được gửi e-copy cho những ai?',
     'Quyết định được gửi cho Đảng ủy, HĐTV và TGĐ [rwtq].'),
    (1, 'Ai chịu trách nhiệm thi hành Quyết định quản lý vật tư?',
     'Các Phó Tổng giám đốc, Kế toán trưởng, Trưởng các phòng chịu trách nhiệm thi hành [na02].'),
])
async def test_administrative_lists_still_answer_their_actual_relation(chunk, question, answer):
    result, _ = await run_guard(question, [LIVE['hr-council']['sources'][chunk]], answer)
    assert result.answer == answer


async def test_heading_context_identifies_membership_in_bare_name_list():
    source = {'index': 'abcd', 'content': 'Nguyễn Văn Nam; Lê Thị Mai.',
              'source_file': 'Quyết định thành lập Tổ kiểm kê.docx',
              'heading_path': ['Tổ kiểm kê', 'Thành viên']}
    result, provider = await run_guard('Tổ kiểm kê bao gồm những ai?', [source],
                                      'Tổ kiểm kê gồm Nguyễn Văn Nam; Lê Thị Mai [abcd].')
    assert result.answer != NO_EVIDENCE
    # Context must survive selection to prevent reinterpretation of bare lists.
    for payload in provider.inputs:
        assert payload['sources'][0]['heading_path'] == source['heading_path']
        assert payload['sources'][0]['source_file'] == source['source_file']


async def test_empty_sources_abstain():
    result, _ = await run_guard(LIVE['hr-public-empty']['question'], [], 'invented')
    assert result.answer == NO_EVIDENCE


async def test_name_only_quote_cannot_hide_distribution_context():
    source = {**LIVE['director-board-council']['sources'][0],
              'heading_path': ['Hội đồng An toàn lao động', 'Thành viên'],
              'content': 'Nơi nhận:\n- Nguyễn Văn Nam (e-copy);\n- Lê Thị Mai (e-copy).'}
    result, _ = await run_guard(LIVE['hr-council']['question'], [source],
                               'Nguyễn Văn Nam [1p76].',
                               [{'source_id': '1p76', 'quote': 'Nguyễn Văn Nam'}])
    assert result.answer == NO_EVIDENCE


async def test_membership_quote_survives_administrative_tail_in_same_chunk():
    source = {**LIVE['director-board-council']['sources'][0]}
    quote = source['content']
    source['content'] += '\nNơi nhận:\n- Phòng Nhân sự (e-copy).'
    result, _ = await run_guard(LIVE['hr-council']['question'], [source],
                               LIVE['director-board-council']['answer'],
                               [{'source_id': '1p76', 'quote': quote}])
    assert result.answer == LIVE['director-board-council']['answer']
