from __future__ import annotations

from ekb_reliability.classification import ComponentClassifier


def test_component_classifier_is_available_from_bundle():
    clf = ComponentClassifier()
    assert clf.is_available is True
    result = clf.predict("RES 10K OHM 1% 0603")
    assert result["family"] != "unknown"
