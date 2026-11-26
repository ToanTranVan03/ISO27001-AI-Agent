from compliance_ai.benchmark import score_predictions
from compliance_ai.rules import Status


def test_metrics_keep_abstentions_and_exclusions() -> None:
    measured = score_predictions(
        [
            (Status.NON_COMPLIANT, Status.NON_COMPLIANT),
            (Status.NON_COMPLIANT, Status.UNKNOWN),
            (Status.COMPLIANT, Status.COMPLIANT),
            (Status.COMPLIANT, Status.PARTIAL),
            (Status.UNKNOWN, Status.UNKNOWN),
            (Status.NA, Status.NON_COMPLIANT),
        ]
    )
    assert measured["precision"] == measured["recall"] == measured["f1"] == 0.5
    assert measured["fpr"] == 0.5
    assert measured["coverage"] == 0.6
    assert score_predictions([])["precision"] is None
