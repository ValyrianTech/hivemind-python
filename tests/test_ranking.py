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
        assert ranking.get() == []

    def test_get_auto_ranking_without_options(self, ranking: Ranking) -> None:
        """Test getting auto ranking without providing options"""
        ranking.set_auto_high('preferred_option')
        with pytest.raises(Exception) as exc_info:
            ranking.get()
        assert 'Options are required for auto ranking' in str(exc_info.value)

    def test_to_dict_fixed(self, ranking: Ranking) -> None:
        """Test converting fixed ranking to dict"""
        choices: List[str] = ['option1', 'option2', 'option3']
        ranking.set_fixed(choices)
        ranking_dict: Dict[str, Any] = ranking.to_dict()
        assert ranking_dict['type'] == 'fixed'
        assert ranking_dict['fixed'] == choices

    def test_to_dict_auto_high(self, ranking: Ranking) -> None:
        """Test converting auto high ranking to dict"""
        choice: str = 'preferred_option'
        ranking.set_auto_high(choice)
        ranking_dict: Dict[str, Any] = ranking.to_dict()
        assert ranking_dict['type'] == 'auto_high'
        assert ranking_dict['auto'] == choice

    def test_to_dict_auto_low(self, ranking: Ranking) -> None:
        """Test converting auto low ranking to dict"""
        choice: str = 'preferred_option'
        ranking.set_auto_low(choice)
        ranking_dict: Dict[str, Any] = ranking.to_dict()
        assert ranking_dict['type'] == 'auto_low'
        assert ranking_dict['auto'] == choice
