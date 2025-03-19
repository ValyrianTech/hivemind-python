from typing import List, Dict, Any
import pytest
from hivemind import Ranking


@pytest.fixture
def ranking() -> Ranking:
    return Ranking()


@pytest.mark.unit
class TestRanking:
    def test_init(self, ranking: Ranking) -> None:
        """Test initialization of Ranking"""
        assert ranking.fixed is None
        assert ranking.auto is None
        assert ranking.type is None

    def test_set_fixed(self, ranking: Ranking) -> None:
        """Test setting fixed ranking"""
        choices: List[str] = ['option1', 'option2', 'option3']
        ranking.set_fixed(choices)
        assert ranking.fixed == choices
        assert ranking.type == 'fixed'

    def test_set_auto_high(self, ranking: Ranking) -> None:
        """Test setting auto high ranking"""
        choice: str = 'preferred_option'
        ranking.set_auto_high(choice)
        assert ranking.auto == choice
        assert ranking.type == 'auto_high'

    def test_set_auto_low(self, ranking: Ranking) -> None:
        """Test setting auto low ranking"""
        choice: str = 'preferred_option'
        ranking.set_auto_low(choice)
        assert ranking.auto == choice
        assert ranking.type == 'auto_low'

    def test_get_fixed_ranking(self, ranking: Ranking) -> None:
        """Test getting fixed ranking"""
        choices: List[str] = ['option1', 'option2', 'option3']
        ranking.set_fixed(choices)
        assert ranking.get() == choices

    def test_get_empty_ranking(self, ranking: Ranking) -> None:
        """Test getting ranking when none is set"""
        with pytest.raises(Exception) as exc_info:
            ranking.get()
        assert 'No ranking was set' in str(exc_info.value)

    def test_get_auto_ranking_without_options(self, ranking: Ranking) -> None:
        """Test getting auto ranking without providing options"""
        ranking.set_auto_high('preferred_option')
        with pytest.raises(Exception) as exc_info:
            ranking.get()
        assert 'No options given for auto ranking' in str(exc_info.value)

    def test_to_dict_fixed(self, ranking: Ranking) -> None:
        """Test converting fixed ranking to dict"""
        choices: List[str] = ['option1', 'option2', 'option3']
        ranking.set_fixed(choices)
        ranking_dict: Dict[str, Any] = ranking.to_dict()
        assert ranking_dict == {'fixed': choices}

    def test_to_dict_auto_high(self, ranking: Ranking) -> None:
        """Test converting auto high ranking to dict"""
        choice: str = 'preferred_option'
        ranking.set_auto_high(choice)
        ranking_dict: Dict[str, Any] = ranking.to_dict()
        assert ranking_dict == {'auto_high': choice}

    def test_to_dict_auto_low(self, ranking: Ranking) -> None:
        """Test converting auto low ranking to dict"""
        choice: str = 'preferred_option'
        ranking.set_auto_low(choice)
        ranking_dict: Dict[str, Any] = ranking.to_dict()
        assert ranking_dict == {'auto_low': choice}

    def test_set_fixed_invalid_items(self, ranking: Ranking) -> None:
        """Test setting fixed ranking with invalid items"""
        choices = ['option1', 2, 'option3']  # 2 is not a string
        with pytest.raises(Exception) as exc_info:
            ranking.set_fixed(choices)
        assert 'Invalid ranked choice' in str(exc_info.value)

    def test_set_auto_high_invalid_choice(self, ranking: Ranking) -> None:
        """Test setting auto high ranking with invalid choice"""
        choice = 123  # Not a string
        with pytest.raises(Exception) as exc_info:
            ranking.set_auto_high(choice)
        assert 'Invalid choice for auto ranking' in str(exc_info.value)

    def test_set_auto_low_invalid_choice(self, ranking: Ranking) -> None:
        """Test setting auto low ranking with invalid choice"""
        choice = 123  # Not a string
        with pytest.raises(Exception) as exc_info:
            ranking.set_auto_low(choice)
        assert 'Invalid choice for auto ranking' in str(exc_info.value)

    def test_get_auto_ranking_invalid_options(self, ranking: Ranking) -> None:
        """Test getting auto ranking with invalid options"""
        ranking.set_auto_high('preferred_option')
        invalid_options = ['not_an_option_object']
        with pytest.raises(Exception) as exc_info:
            ranking.get(invalid_options)
        assert 'Invalid list of options given for auto ranking' in str(exc_info.value)

    def test_get_auto_high_ranking(self, ranking: Ranking) -> None:
        """Test getting auto high ranking with valid options"""
        from hivemind import HivemindOption

        # Create test options with different values
        options = []
        for val in [10, 20, 30, 40]:
            opt = HivemindOption()
            opt.value = val
            opt.save()  # Save to IPFS to get CID
            options.append(opt)

        # Set preferred value in the middle
        preferred = HivemindOption()
        preferred.value = 25
        preferred.save()  # Save to IPFS to get CID
        ranking.set_auto_high(preferred.cid())

        # Get ranked options
        ranked_cids = ranking.get(options)

        # Verify the order - should be ordered by distance to 25, with higher values preferred when equally distant
        # Expected order: 30 (diff=5), 20 (diff=5), 40 (diff=15), 10 (diff=15)
        expected_values = [30, 20, 40, 10]
        actual_values = [next(opt.value for opt in options if opt.cid() == cid) for cid in ranked_cids]
        assert actual_values == expected_values

    def test_get_auto_low_ranking(self, ranking: Ranking) -> None:
        """Test getting auto low ranking with valid options"""
        from hivemind import HivemindOption

        # Create test options with different values
        options = []
        for val in [10, 20, 30, 40]:
            opt = HivemindOption()
            opt.value = val
            opt.save()  # Save to IPFS to get CID
            options.append(opt)

        # Set preferred value in the middle
        preferred = HivemindOption()
        preferred.value = 25
        preferred.save()  # Save to IPFS to get CID
        ranking.set_auto_low(preferred.cid())

        # Get ranked options
        ranked_cids = ranking.get(options)

        # Verify the order - should be ordered by distance to 25, with lower values preferred
        # Expected order: 20 (diff=5), 30 (diff=5), 10 (diff=15), 40 (diff=15)
        expected_values = [20, 30, 10, 40]
        actual_values = [next(opt.value for opt in options if opt.cid() == cid) for cid in ranked_cids]
        assert actual_values == expected_values

    def test_auto_ranking_calculation_exception(self, ranking: Ranking) -> None:
        """Test exception handling during auto ranking calculation"""
        from hivemind import HivemindOption
        import unittest.mock as mock

        # Create a valid preferred option
        preferred = HivemindOption()
        preferred.value = 25
        preferred.save()
        ranking.set_auto_high(preferred.cid())

        # Create test options with invalid values that will cause an exception during calculation
        options = []
        opt = HivemindOption()
        opt.value = "not_a_number"  # This will cause a TypeError during comparison
        opt.save()
        options.append(opt)

        # Add a valid option as well
        valid_opt = HivemindOption()
        valid_opt.value = 30
        valid_opt.save()
        options.append(valid_opt)

        # The get method should raise an exception
        with pytest.raises(Exception) as exc_info:
            ranking.get(options)

        # Verify the exception message contains the original error
        assert "Error during auto ranking calculation" in str(exc_info.value)
