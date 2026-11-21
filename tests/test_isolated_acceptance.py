import pytest
from run_isolated_acceptance import validate_database


@pytest.mark.parametrize('name',['iso27001','postgres','iso_acceptance_wrong','iso_acceptance_123456789abc;DROP DATABASE postgres'])
def test_main_or_arbitrary_database_is_never_a_cleanup_target(name):
    with pytest.raises(ValueError):validate_database(name,'iso27001')


def test_only_generated_name_distinct_from_source_is_allowed():
    validate_database('iso_acceptance_123456789abc','iso27001')
    with pytest.raises(ValueError):validate_database('iso_acceptance_123456789abc','iso_acceptance_123456789abc')
