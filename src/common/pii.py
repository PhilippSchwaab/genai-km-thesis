import re

from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_analyzer.nlp_engine import SpacyNlpEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

_analyzer: AnalyzerEngine | None = None
_anonymizer: AnonymizerEngine | None = None

_ENTITY_TYPES = [
    "PERSON",
    "LOCATION",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "URL",
]

_LABEL_PREFIX = {
    "PERSON": "Person",
    "LOCATION": "Location",
    "EMAIL_ADDRESS": "Email",
    "PHONE_NUMBER": "Phone",
    "URL": "URL",
}

_PARAGRAPH_SEP = re.compile(r"\n\s*\n")


def _get_analyzer() -> AnalyzerEngine:
    global _analyzer
    if _analyzer is None:
        nlp = SpacyNlpEngine(models=[{"lang_code": "en", "model_name": "en_core_web_lg"}])
        _analyzer = AnalyzerEngine(nlp_engine=nlp)
    return _analyzer


def _get_anonymizer() -> AnonymizerEngine:
    global _anonymizer
    if _anonymizer is None:
        _anonymizer = AnonymizerEngine()
    return _anonymizer


def _analyze_by_paragraph(text: str, language: str) -> list[RecognizerResult]:
    """Analyze each paragraph independently to prevent cross-paragraph NER merges."""
    analyzer = _get_analyzer()
    all_results: list[RecognizerResult] = []

    for m in _PARAGRAPH_SEP.finditer(text):
        pass  # just to check if there are paragraphs

    parts = _PARAGRAPH_SEP.split(text)
    if len(parts) <= 1:
        return analyzer.analyze(text=text, entities=_ENTITY_TYPES, language=language)

    offset = 0
    for part in parts:
        start = text.index(part, offset)
        results = analyzer.analyze(text=part, entities=_ENTITY_TYPES, language=language)
        for r in results:
            r.start += start
            r.end += start
        all_results.extend(results)
        offset = start + len(part)

    return all_results


def redact(text: str, language: str = "en") -> tuple[str, dict[str, str]]:
    """Replace PII spans with type-prefixed placeholders.

    Returns (anonymized_text, mapping) where mapping maps each original
    PII string to its placeholder, e.g. {"Alice": "[Person 1]"}.
    """
    results = _analyze_by_paragraph(text, language)

    # Build stable mapping: same surface form → same placeholder (left-to-right)
    mapping: dict[str, str] = {}
    counters: dict[str, int] = {}
    for r in sorted(results, key=lambda res: res.start):
        surface = text[r.start : r.end]
        if surface not in mapping:
            prefix = _LABEL_PREFIX.get(r.entity_type, r.entity_type)
            counters[prefix] = counters.get(prefix, 0) + 1
            mapping[surface] = f"[{prefix} {counters[prefix]}]"

    # Let Presidio handle overlap resolution and replacement
    operators = {"DEFAULT": OperatorConfig("custom", {"lambda": lambda s: mapping.get(s, s)})}
    result = _get_anonymizer().anonymize(
        text=text, analyzer_results=results, operators=operators
    )

    return result.text, mapping
