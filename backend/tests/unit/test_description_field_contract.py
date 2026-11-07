""" v2 

/ Hình ảnh & Tư liệu/ Bố cục & Trọng tâm/ Ghi chú thuyết trình

"""

import json

import pytest

from models import Settings, db
from services import prompts
from services.prompts import (
    EXTRA_FIELD_INSTRUCTIONS,
    _format_extra_field_instructions,
    get_all_descriptions_stream_prompt,
    get_description_to_outline_prompt,
    get_description_to_outline_prompt_markdown,
    get_outline_generation_prompt,
    get_outline_generation_prompt_markdown,
    get_outline_parsing_prompt,
    get_outline_parsing_prompt_markdown,
    get_outline_refinement_prompt,
    get_page_description_prompt,
)
from services.task_manager import _append_extra_fields


class _Ctx:
    """ Test docstring """

    creation_type = 'idea'
    idea_prompt = ' AI '
    outline_text = ''
    description_text = 'AI \n'
    reference_files_content = None
    outline_requirements = None
    description_requirements = None


@pytest.fixture
def ctx():
    return _Ctx()


# Test verification logic

def test_default_fields_render_full_instructions():
    result = _format_extra_field_instructions(list(Settings.DEFAULT_EXTRA_FIELDS))

    for name in Settings.DEFAULT_EXTRA_FIELDS:
        assert EXTRA_FIELD_INSTRUCTIONS[name] in result


def test_field_instructions_state_exclusion_rules():
    """ Test docstring """
    materials = EXTRA_FIELD_INSTRUCTIONS['Hình ảnh & Tư liệu']
    assert '' in materials
    assert '' in materials

    layout = EXTRA_FIELD_INSTRUCTIONS['Bố cục & Trọng tâm']
    assert '' in layout
    assert '' in layout

    notes = EXTRA_FIELD_INSTRUCTIONS['Ghi chú thuyết trình']
    assert '' in notes


def test_field_instructions_carry_length_budget():
    """ Test docstring """
    assert ' 3 ' in EXTRA_FIELD_INSTRUCTIONS['Hình ảnh & Tư liệu']
    assert '' in EXTRA_FIELD_INSTRUCTIONS['Bố cục & Trọng tâm']


def test_custom_field_falls_back_to_generic_instruction():
    result = _format_extra_field_instructions([''])

    assert '[]' in result


def test_legacy_field_names_do_not_borrow_new_definitions():
    """ Test docstring """
    result = _format_extra_field_instructions(['Bố cục & Trọng tâm', 'Bố cục & Trọng tâm'])

    assert EXTRA_FIELD_INSTRUCTIONS['Bố cục & Trọng tâm'] not in result
    assert 'Bố cục & Trọng tâm[Bố cục & Trọng tâm' in result
    assert 'Bố cục & Trọng tâm[Bố cục & Trọng tâm' in result


def test_empty_field_list_renders_nothing():
    assert _format_extra_field_instructions([]) == ''
    assert _format_extra_field_instructions(None) == ''


# Test verification logic

def test_page_description_prompt_drops_standalone_material_section(ctx):
    prompt = get_page_description_prompt(
        ctx, outline=[], page_outline={'title': 'AI '}, page_index=2,
        extra_fields=list(Settings.DEFAULT_EXTRA_FIELDS),
    )

    assert ':' not in prompt
    assert '' not in prompt
    assert EXTRA_FIELD_INSTRUCTIONS['Hình ảnh & Tư liệu'] in prompt


def test_page_description_prompt_states_verbatim_and_title_rules(ctx):
    prompt = get_page_description_prompt(
        ctx, outline=[], page_outline={'title': 'AI '}, page_index=2,
        extra_fields=list(Settings.DEFAULT_EXTRA_FIELDS),
    )

    assert '' in prompt
    assert '' in prompt
    assert 'takeaway' in prompt


def test_stream_description_prompt_matches_contract(ctx):
    prompt = get_all_descriptions_stream_prompt(
        ctx, outline=[], flat_pages=[{'title': 'AI ', 'points': ['']}],
        extra_fields=list(Settings.DEFAULT_EXTRA_FIELDS),
    )

    assert '' not in prompt
    assert '' in prompt
    assert '' in prompt
    # Test verification logic
    for marker in ('<!-- BEGIN -->', '<!-- PAGE_END -->', '<!-- END -->'):
        assert marker in prompt


# Test verification logic

@pytest.mark.parametrize('build', [
    lambda c: get_outline_generation_prompt(c),
    lambda c: get_outline_generation_prompt_markdown(c),
    lambda c: get_outline_refinement_prompt([], '', c),
])
def test_generation_and_refinement_prompts_carry_takeaway_rule(ctx, build):
    prompt = build(ctx)

    assert 'takeaway' in prompt.lower()
    assert 'never a topic phrase' in prompt or 'topic phrase' in prompt


def test_takeaway_rule_exempts_functional_pages(ctx):
    prompt = get_outline_generation_prompt(ctx)

    assert 'functional pages' in prompt
    assert 'do not force assertions' in prompt


def test_takeaway_rule_requires_coherent_storyline(ctx):
    prompt = get_outline_generation_prompt(ctx)

    assert 'storyline' in prompt


@pytest.mark.parametrize('build', [
    lambda c: get_outline_generation_prompt(c),
    lambda c: get_outline_generation_prompt_markdown(c),
    lambda c: get_outline_refinement_prompt([], '', c),
])
def test_cover_and_toc_are_exempt_from_part_grouping(ctx, build):
    """ Test docstring """
    prompt = build(ctx)

    assert 'table of contents' in prompt or '' in prompt
    assert 'never to a part' in prompt or '' in prompt


def test_outline_json_format_example_keeps_cover_outside_part():
    """ Test docstring """
    assert '"part": "Part 1: Introduction"' in prompts._OUTLINE_JSON_FORMAT
    # Test verification logic
    welcome_pos = prompts._OUTLINE_JSON_FORMAT.index('"Welcome"')
    part1_pos = prompts._OUTLINE_JSON_FORMAT.index('"part": "Part 1: Introduction"')
    assert welcome_pos < part1_pos


@pytest.mark.parametrize('build', [
    lambda c: get_description_to_outline_prompt(c),
    lambda c: get_description_to_outline_prompt_markdown(c),
])
def test_description_derived_outlines_exempt_cover_from_part(ctx, build):
    prompt = build(ctx)
    assert 'never to a part' in prompt


@pytest.mark.parametrize('build', [
    lambda c: get_outline_parsing_prompt(c),
    lambda c: get_outline_parsing_prompt_markdown(c),
])
def test_outline_parsing_prompts_do_not_inject_part_exemption(ctx, build):
    """ Test docstring """
    prompt = build(ctx)
    assert 'never to a part' not in prompt


@pytest.mark.parametrize('build', [
    lambda c: get_description_to_outline_prompt(c),
    lambda c: get_description_to_outline_prompt_markdown(c),
])
def test_description_derived_outlines_use_conditional_takeaway(ctx, build):
    """ Test docstring """
    prompt = build(ctx)

    assert 'takeaway assertion' in prompt
    assert "implied by the user's text" in prompt


@pytest.mark.parametrize('build', [
    lambda c: get_outline_parsing_prompt(c),
    lambda c: get_outline_parsing_prompt_markdown(c),
])
def test_outline_parsing_prompts_stay_faithful(ctx, build):
    """ Test docstring """
    prompt = build(ctx)

    assert 'takeaway' not in prompt.lower()


# Test verification logic

def test_default_fields_are_orthogonal_trio():
    assert Settings.DEFAULT_EXTRA_FIELDS == ['Hình ảnh & Tư liệu', 'Bố cục & Trọng tâm', 'Ghi chú thuyết trình']
    assert Settings.DEFAULT_IMAGE_PROMPT_FIELDS == ['Hình ảnh & Tư liệu', 'Bố cục & Trọng tâm']
    assert 'Ghi chú thuyết trình' not in Settings.DEFAULT_IMAGE_PROMPT_FIELDS


def test_legacy_equiv_covers_all_retired_names():
    assert Settings.LEGACY_FIELD_EQUIV == {
        'Hình ảnh & Tư liệu': 'Hình ảnh & Tư liệu',
        'Bố cục & Trọng tâm': 'Bố cục & Trọng tâm',
        'Bố cục & Trọng tâm': 'Bố cục & Trọng tâm',
        'Gợi ý bố cục': 'Bố cục & Trọng tâm',
    }


# Test verification logic

@pytest.mark.parametrize('build', [
    lambda c: get_outline_generation_prompt(c),
    lambda c: get_outline_generation_prompt_markdown(c),
])
def test_takeaway_rule_bans_topic_announcing_sentences(ctx, build):
    """ Test docstring """
    prompt = build(ctx)
    # Test verification logic
    assert 'reveals when to switch' in prompt


def test_takeaway_rule_requires_evidence_not_restatement(ctx):
    """ Test docstring """
    prompt = get_outline_generation_prompt(ctx)
    assert 'EVIDENCE' in prompt
    assert 'not a reworded restatement' in prompt


def test_outline_markdown_prompt_bans_deck_level_title(ctx):
    """ Test docstring """
    prompt = get_outline_generation_prompt_markdown(ctx)
    assert 'deck-level document title' in prompt


# Test verification logic

def test_parse_outline_ignores_deck_title_before_cover():
    """ deck  H1  part
     # Part """
    from services.ai_service import AIService

    md = (
        "# Bao cao chien luoc\n"
        "## Bao cao chien luoc\n"
        "- Phu de va thong tin\n"
        "# Phan 1: Phan tich kinh te\n"
        "## Chi phi hien tai tang nhanh\n"
        "- Rui ro mat kiem soat\n"
    )
    pages = AIService.parse_markdown_outline(md)

    assert len(pages) == 2
    # Test verification logic
    assert 'part' not in pages[0]
    assert pages[0]['title'] == 'AI '
    # Test verification logic
    assert pages[1].get('part') == 'Phan 1: Phan tich kinh te'


def test_parse_outline_keeps_opening_chapter_without_cover():
    """Khong co trang bia rieng, mo dau truc tiep bang chuong thi H1 dau tien la part that."""
    from services.ai_service import AIService

    md = (
        "# Chuong 1\n"
        "## Trang 1\n"
        "- Y 1\n"
        "## Trang 2\n"
        "- Y 2\n"
    )
    pages = AIService.parse_markdown_outline(md)

    assert len(pages) == 2
    assert pages[0].get('part') == 'Chuong 1'
    assert pages[1].get('part') == 'Chuong 1'
@pytest.mark.parametrize('legacy_name', ['Hình ảnh & Tư liệu', 'Bố cục & Trọng tâm', 'Bố cục & Trọng tâm', 'Gợi ý bố cục'])
def test_legacy_fields_still_reach_image_prompt(legacy_name):
    """ Test docstring """
    result = _append_extra_fields(
        '',
        {'extra_fields': {legacy_name: ''}},
        set(Settings.DEFAULT_IMAGE_PROMPT_FIELDS),
    )

    assert f'{legacy_name}' in result


def test_legacy_speaker_notes_still_excluded():
    result = _append_extra_fields(
        '',
        {'extra_fields': {'Ghi chú thuyết trình': ''}},
        set(Settings.DEFAULT_IMAGE_PROMPT_FIELDS),
    )

    assert result == ''


def test_new_fields_reach_image_prompt():
    result = _append_extra_fields(
        '',
        {'extra_fields': {'Hình ảnh & Tư liệu': '', 'Bố cục & Trọng tâm': ''}},
        set(Settings.DEFAULT_IMAGE_PROMPT_FIELDS),
    )

    assert 'Hình ảnh & Tư liệu' in result
    assert 'Bố cục & Trọng tâm' in result


def test_unknown_custom_field_still_filtered():
    result = _append_extra_fields(
        '',
        {'extra_fields': {'': ''}},
        set(Settings.DEFAULT_IMAGE_PROMPT_FIELDS),
    )

    assert result == ''


def test_settings_default_getters_return_new_fields(client):
    with client.application.app_context():
        settings = Settings.get_settings()
        settings.description_extra_fields = None
        settings.image_prompt_extra_fields = None
        db.session.commit()

        assert settings.get_description_extra_fields() == ['Hình ảnh & Tư liệu', 'Bố cục & Trọng tâm', 'Ghi chú thuyết trình']
        assert settings.get_image_prompt_extra_fields() == ['Hình ảnh & Tư liệu', 'Bố cục & Trọng tâm']


def test_parseable_names_extend_instruction_names_with_legacy(client):
    """ Test docstring """
    from services.ai_service import AIService

    with client.application.app_context():
        settings = Settings.get_settings()
        settings.description_extra_fields = None
        db.session.commit()

        instructed = AIService._get_extra_field_names()
        parseable = AIService._get_parseable_field_names()

    assert instructed == list(Settings.DEFAULT_EXTRA_FIELDS)
    # Test verification logic
    for legacy in Settings.LEGACY_FIELD_EQUIV:
        assert legacy not in instructed
        assert legacy in parseable
    for name in instructed:
        assert name in parseable


# Test verification logic

def test_refinement_prompt_includes_existing_extra_fields(ctx):
    prompt = prompts.get_descriptions_refinement_prompt(
        current_descriptions=[{
            'index': 0,
            'title': 'AI ',
            'description_content': {
                'text': '- ',
                'extra_fields': {'Bố cục & Trọng tâm': ''},
            },
        }],
        user_requirement='',
        project_context=ctx,
    )

    assert 'Bố cục & Trọng tâm' in prompt
    assert '' in prompt


def test_refine_descriptions_splits_extra_fields_back_out(client, monkeypatch):
    """ Test docstring """
    from services.ai_service import AIService

    service = AIService.__new__(AIService)
    monkeypatch.setattr(
        AIService, 'generate_json',
        lambda self, prompt, **kwargs: [
            'AI \n\n- \nHình ảnh & Tư liệu\nBố cục & Trọng tâm',
        ],
    )
    monkeypatch.setattr(
        AIService, '_get_extra_field_names',
        staticmethod(lambda: list(Settings.DEFAULT_EXTRA_FIELDS)),
    )

    with client.application.app_context():
        result = service.refine_descriptions([], '', _Ctx())

    assert len(result) == 1
    assert result[0]['extra_fields'] == {'Hình ảnh & Tư liệu': '', 'Bố cục & Trọng tâm': ''}
    assert 'Hình ảnh & Tư liệu' not in result[0]['text']
    assert '' in result[0]['text']


def test_refine_descriptions_splits_legacy_field_names(client, monkeypatch):
    from services.ai_service import AIService

    service = AIService.__new__(AIService)
    monkeypatch.setattr(
        AIService, 'generate_json',
        lambda self, prompt, **kwargs: ['\n- \nBố cục & Trọng tâm'],
    )
    monkeypatch.setattr(
        AIService, '_get_extra_field_names',
        staticmethod(lambda: list(Settings.DEFAULT_EXTRA_FIELDS)),
    )

    with client.application.app_context():
        result = service.refine_descriptions([], '', _Ctx())

    assert result[0]['extra_fields'] == {'Bố cục & Trọng tâm': ''}


def test_refine_descriptions_without_fields_returns_text_only(client, monkeypatch):
    from services.ai_service import AIService

    service = AIService.__new__(AIService)
    monkeypatch.setattr(
        AIService, 'generate_json',
        lambda self, prompt, **kwargs: ['\n- '],
    )
    monkeypatch.setattr(
        AIService, '_get_extra_field_names',
        staticmethod(lambda: list(Settings.DEFAULT_EXTRA_FIELDS)),
    )

    with client.application.app_context():
        result = service.refine_descriptions([], '', _Ctx())

    assert 'extra_fields' not in result[0]
    assert '' in result[0]['text']


def test_refine_descriptions_flattens_dict_items(client, monkeypatch):
    """ Test docstring """
    from services.ai_service import AIService

    service = AIService.__new__(AIService)
    monkeypatch.setattr(
        AIService, 'generate_json',
        lambda self, prompt, **kwargs: [
            {'': '- ', 'Bố cục & Trọng tâm': ''},
        ],
    )
    monkeypatch.setattr(
        AIService, '_get_extra_field_names',
        staticmethod(lambda: list(Settings.DEFAULT_EXTRA_FIELDS)),
    )

    with client.application.app_context():
        result = service.refine_descriptions([], '', _Ctx())

    assert result[0]['extra_fields'] == {'Bố cục & Trọng tâm': ''}
    assert '' in result[0]['text']
    assert '{' not in result[0]['text']


def test_parse_extra_fields_matches_field_at_text_start():
    """ Test docstring """
    from services.ai_service import AIService

    text, fields = AIService._parse_extra_fields(
        'Hình ảnh & Tư liệu\nBố cục & Trọng tâm',
        ['Hình ảnh & Tư liệu', 'Bố cục & Trọng tâm'],
    )

    assert fields == {'Hình ảnh & Tư liệu': '', 'Bố cục & Trọng tâm': ''}
    assert text == ''


def test_refine_descriptions_flattens_dict_with_field_first(client, monkeypatch):
    """ Test docstring """
    from services.ai_service import AIService

    service = AIService.__new__(AIService)
    monkeypatch.setattr(
        AIService, 'generate_json',
        lambda self, prompt, **kwargs: [
            {'Hình ảnh & Tư liệu': '', 'Bố cục & Trọng tâm': ''},
        ],
    )
    monkeypatch.setattr(
        AIService, '_get_extra_field_names',
        staticmethod(lambda: list(Settings.DEFAULT_EXTRA_FIELDS)),
    )

    with client.application.app_context():
        result = service.refine_descriptions([], '', _Ctx())

    assert result[0]['extra_fields'] == {'Hình ảnh & Tư liệu': '', 'Bố cục & Trọng tâm': ''}
    assert result[0]['text'] == ''


def test_refine_descriptions_flattens_list_values(client, monkeypatch):
    """ Test docstring """
    from services.ai_service import AIService

    service = AIService.__new__(AIService)
    monkeypatch.setattr(
        AIService, 'generate_json',
        lambda self, prompt, **kwargs: [
            {'': ['- ', '- '], 'Bố cục & Trọng tâm': ''},
        ],
    )
    monkeypatch.setattr(
        AIService, '_get_extra_field_names',
        staticmethod(lambda: list(Settings.DEFAULT_EXTRA_FIELDS)),
    )

    with client.application.app_context():
        result = service.refine_descriptions([], '', _Ctx())

    assert result[0]['extra_fields'] == {'Bố cục & Trọng tâm': ''}
    assert '' in result[0]['text'] and '' in result[0]['text']
    assert '[' not in result[0]['text']


def test_refinement_prompt_tolerates_null_text(ctx):
    """ Test docstring """
    prompt = prompts.get_descriptions_refinement_prompt(
        current_descriptions=[{
            'index': 0,
            'title': '',
            'description_content': {'text': None, 'extra_fields': {'Bố cục & Trọng tâm': ''}},
        }],
        user_requirement='',
        project_context=ctx,
    )

    assert 'Bố cục & Trọng tâm' in prompt


def test_refine_descriptions_rejects_non_list(client, monkeypatch):
    from services.ai_service import AIService

    service = AIService.__new__(AIService)
    monkeypatch.setattr(AIService, 'generate_json', lambda self, prompt, **kwargs: {'oops': 1})

    with client.application.app_context():
        with pytest.raises(ValueError):
            service.refine_descriptions([], '', _Ctx())