from typing import Dict, Any
import pytest
from src.hivemind.issue import HivemindIssue


@pytest.fixture
def issue() -> HivemindIssue:
    return HivemindIssue()


@pytest.mark.unit
class TestHivemindIssue:
    def test_init(self, issue: HivemindIssue) -> None:
        """Test initialization of HivemindIssue"""
        assert issue.questions == []
        assert issue.name is None
        assert issue.description == ''
        assert issue.tags == []
        assert issue.answer_type == 'String'
        assert issue.constraints is None
        assert issue.restrictions is None
        assert issue.on_selection is None

    def test_add_question(self, issue: HivemindIssue) -> None:
        """Test adding questions"""
        question: str = "What is your favorite color?"
        issue.add_question(question)
        assert len(issue.questions) == 1
        assert issue.questions[0] == question

        # Test duplicate question
        issue.add_question(question)
        assert len(issue.questions) == 1

        # Test non-string question
        issue.add_question(123)  # type: ignore
        assert len(issue.questions) == 1

    def test_set_constraints_valid(self, issue: HivemindIssue) -> None:
        """Test setting valid constraints"""
        constraints: Dict[str, Any] = {
            'min_length': 5,
            'max_length': 10,
            'regex': r'^[a-z]+$',
            'choices': ['red', 'blue', 'green']
        }
        issue.set_constraints(constraints)
        assert issue.constraints == constraints

    def test_set_constraints_invalid_type(self, issue: HivemindIssue) -> None:
        """Test setting constraints with invalid type"""
        with pytest.raises(Exception) as exc_info:
            issue.set_constraints([])  # type: ignore
        assert 'constraints must be a dict' in str(exc_info.value)

    def test_set_constraints_invalid_key(self, issue: HivemindIssue) -> None:
        """Test setting constraints with invalid key"""
        with pytest.raises(Exception) as exc_info:
            issue.set_constraints({'invalid_key': 'value'})
        assert 'constraints contain an invalid key' in str(exc_info.value)

    def test_set_restrictions_valid(self, issue: HivemindIssue) -> None:
        """Test setting valid restrictions"""
        restrictions: Dict[str, int] = {
            'options_per_address': 3
        }
        issue.set_restrictions(restrictions)
        assert issue.restrictions == restrictions

    def test_set_restrictions_invalid_type(self, issue: HivemindIssue) -> None:
        """Test setting restrictions with invalid type"""
        with pytest.raises(Exception) as exc_info:
            issue.set_restrictions([])  # type: ignore
        assert 'Restrictions is not a dict' in str(exc_info.value)

    def test_set_restrictions_invalid_key(self, issue: HivemindIssue) -> None:
        """Test setting restrictions with invalid key"""
        with pytest.raises(Exception) as exc_info:
            issue.set_restrictions({'invalid_key': 'value'})
        assert 'Invalid key in restrictions' in str(exc_info.value)

    def test_set_restrictions_invalid_options_per_address(self, issue: HivemindIssue) -> None:
        """Test setting restrictions with invalid options_per_address"""
        with pytest.raises(Exception) as exc_info:
            issue.set_restrictions({'options_per_address': 0})
        assert 'options_per_address in restrictions must be a positive integer' in str(exc_info.value)

    def test_set_restrictions_none(self, issue: HivemindIssue) -> None:
        """Test setting restrictions to None"""
        # First set some restrictions
        restrictions = {'options_per_address': 3}
        issue.set_restrictions(restrictions)
        assert issue.restrictions == restrictions
        
        # Then set to None
        issue.set_restrictions(None)
        assert issue.restrictions is None

    def test_initialization(self):
        assert isinstance(HivemindIssue(), HivemindIssue)

    def test_saving_without_name_raises_exception(self):
        hivemind_issue = HivemindIssue()
        hivemind_issue.add_question('what?')
        with pytest.raises(Exception):
            hivemind_issue.save()

    @pytest.mark.parametrize("name", ['',
                                      ''.join(['a' for _ in range(51)]),
                                      42,
                                      None,
                                      {},
                                      [],
                                      42 + 0j,
                                      42.0])
    def test_saving_with_invalid_name_raises_exception(self, name):
        hivemind_issue = HivemindIssue()
        hivemind_issue.add_question('what?')
        hivemind_issue.name = name
        with pytest.raises(Exception):
            hivemind_issue.save()

    def test_setting_question(self):
        hivemind_issue = HivemindIssue()
        hivemind_issue.name = 'Test'
        question = 'What?'
        hivemind_issue.add_question(question)
        hivemind_issue.save()
        assert hivemind_issue.questions[0] == question

    def test_setting_description(self):
        hivemind_issue = HivemindIssue()
        hivemind_issue.name = 'Test'
        question = 'What?'
        hivemind_issue.add_question(question)
        description = 'this.'
        hivemind_issue.description = description
        hivemind_issue.save()
        assert hivemind_issue.description == description

    def test_setting_tags(self):
        hivemind_issue = HivemindIssue()
        hivemind_issue.name = 'Test'
        hivemind_issue.add_question('what?')
        tags = ['tag1', 'tag2', 'tag3']
        hivemind_issue.tags = tags
        hivemind_issue.save()
        assert hivemind_issue.tags == tags

    @pytest.mark.parametrize("answer_type", ['String', 'Bool', 'Integer', 'Float', 'Hivemind', 'File', 'Complex'])
    def test_setting_a_valid_answer_type(self, answer_type):
        hivemind_issue = HivemindIssue()
        hivemind_issue.name = 'Test'
        hivemind_issue.add_question('what?')
        hivemind_issue.answer_type = answer_type
        hivemind_issue.save()
        assert hivemind_issue.answer_type == answer_type

    def test_setting_an_invalid_answer_type(self):
        hivemind_issue = HivemindIssue()
        hivemind_issue.name = 'Test'
        hivemind_issue.add_question('what?')
        with pytest.raises(Exception):
            hivemind_issue.answer_type = 'invalid_type'
            hivemind_issue.save()

    def test_setting_complex_constraints(self):
        hivemind_issue = HivemindIssue()
        hivemind_issue.name = 'Test'
        hivemind_issue.add_question('what?')
        hivemind_issue.answer_type = 'Complex'
        hivemind_issue.set_constraints(constraints={'specs': {'a_string': 'String', 'a_float': 'Float'}})

        with pytest.raises(Exception):
            hivemind_issue.set_constraints(constraints={'specs': {'a_string': 'foo', 'a_float': 'Float'}})

        with pytest.raises(Exception):
            hivemind_issue.set_constraints(constraints={'specs': {'a_string': 'String', 'a_float': 42.0}})

        with pytest.raises(Exception):
            hivemind_issue.set_constraints(constraints={'specs': 'foo'})

    @pytest.mark.parametrize("constraint_type", ['min_length', 'max_length', 'min_value', 'max_value', 'decimals'])
    def test_setting_constraints_types(self, constraint_type):
        hivemind_issue = HivemindIssue()
        hivemind_issue.name = 'Test'
        hivemind_issue.add_question('what?')
        hivemind_issue.set_constraints({constraint_type: 2})
        assert hivemind_issue.constraints == {constraint_type: 2}

        with pytest.raises(Exception):
            hivemind_issue.set_constraints({constraint_type: '2'})

    def test_setting_regex_constraints(self):
        hivemind_issue = HivemindIssue()
        hivemind_issue.name = 'Test'
        hivemind_issue.add_question('what?')
        hivemind_issue.set_constraints({'regex': '^[a-z]+'})
        assert hivemind_issue.constraints == {'regex': '^[a-z]+'}

        with pytest.raises(Exception):
            hivemind_issue.set_constraints({'regex': 2})

    def test_setting_invalid_constraints(self):
        hivemind_issue = HivemindIssue()
        hivemind_issue.name = 'Test'
        hivemind_issue.add_question('what?')
        with pytest.raises(Exception):
            hivemind_issue.set_constraints({'foo': 'bar'})

    def test_saving_a_hivemind_question(self):
        hivemind_issue = HivemindIssue()
        hivemind_issue.name = 'The meaning of life'
        hivemind_issue.add_question(question='What is the Answer to the Ultimate Question of Life, the Universe, and Everything?')
        hivemind_issue.description = 'What is the meaning of life?'
        hivemind_issue.tags = ['life', 'universe', 'everything']
        hivemind_issue.answer_type = 'String'
        hivemind_issue.set_constraints({'min_length': 2})

        issue_hash = hivemind_issue.save()
        assert issue_hash is not None

    def test_set_restrictions(self):
        hivemind_issue = HivemindIssue()
        hivemind_issue.name = 'Test'
        hivemind_issue.add_question('what?')

        restrictions = {'addresses': ['14PJA8RkjT65aPWUT7ezw9MvWgCHitQ59m', '1LRsTRrxFevPgoGn8MowPJi3Rp6ZfQex15'],
                        'options_per_address': 1}

        hivemind_issue.set_restrictions(restrictions=restrictions)
        assert hivemind_issue.restrictions == restrictions

    def test_issue_properties(self):
        """Test the HivemindIssue properties"""
        hivemind_issue = HivemindIssue()
        hivemind_issue.name = "Test Issue"
        hivemind_issue.description = "Test Description"
        hivemind_issue.add_question("Main Question?")
        hivemind_issue.add_question("Follow-up Question?")
        hivemind_issue.tags = ["tag1", "tag2"]
        hivemind_issue.answer_type = "String"
        hivemind_issue.set_constraints({"min_length": 5, "max_length": 10})

        # Test properties directly instead of using info() method
        assert hivemind_issue.name == "Test Issue"
        assert hivemind_issue.description == "Test Description"
        assert hivemind_issue.questions[0] == "Main Question?"
        assert hivemind_issue.questions[1] == "Follow-up Question?"
        assert hivemind_issue.tags == ["tag1", "tag2"]
        assert hivemind_issue.answer_type == "String"
        assert hivemind_issue.constraints["min_length"] == 5
        assert hivemind_issue.constraints["max_length"] == 10

    def test_valid_description_length(self):
        """Test validation of description length"""
        hivemind_issue = HivemindIssue()
        hivemind_issue.name = "Test"
        hivemind_issue.add_question("Question?")
        hivemind_issue.description = "a" * 5001  # Too long
        with pytest.raises(Exception) as exc_info:
            hivemind_issue.valid()
        assert "Invalid description" in str(exc_info.value)

    def test_valid_tag_format(self):
        """Test validation of tag format"""
        hivemind_issue = HivemindIssue()
        hivemind_issue.name = "Test"
        hivemind_issue.add_question("Question?")

        # Test tag with space
        hivemind_issue.tags = ["invalid tag"]
        with pytest.raises(Exception) as exc_info:
            hivemind_issue.valid()
        assert "Invalid tags" in str(exc_info.value)

        # Test duplicate tags
        hivemind_issue.tags = ["tag1", "tag1"]
        with pytest.raises(Exception) as exc_info:
            hivemind_issue.valid()
        assert "Invalid tags" in str(exc_info.value)

    def test_valid_question_format(self):
        """Test validation of question format"""
        hivemind_issue = HivemindIssue()
        hivemind_issue.name = "Test"

        # Test empty question
        hivemind_issue.questions = [""]
        with pytest.raises(Exception) as exc_info:
            hivemind_issue.valid()
        assert "Invalid questions" in str(exc_info.value)

        # Test too long question
        hivemind_issue.questions = ["a" * 256]
        with pytest.raises(Exception) as exc_info:
            hivemind_issue.valid()
        assert "Invalid questions" in str(exc_info.value)

    def test_valid_on_selection(self):
        """Test validation of on_selection values"""
        hivemind_issue = HivemindIssue()
        hivemind_issue.name = "Test"
        hivemind_issue.add_question("Question?")

        # Test invalid on_selection value
        hivemind_issue.on_selection = "InvalidValue"
        with pytest.raises(Exception) as exc_info:
            hivemind_issue.valid()
        assert "Invalid on_selection" in str(exc_info.value)

    def test_set_constraints_boolean_values(self):
        """Test setting true_value and false_value constraints"""
        hivemind_issue = HivemindIssue()
        hivemind_issue.name = "Test"
        hivemind_issue.add_question("Question?")
        hivemind_issue.answer_type = "Bool"

        # Test valid boolean constraints
        constraints = {"true_value": "yes", "false_value": "no"}
        hivemind_issue.set_constraints(constraints)
        assert hivemind_issue.constraints == constraints

        # Test invalid boolean constraints
        with pytest.raises(Exception):
            hivemind_issue.set_constraints({"true_value": 1, "false_value": 0})

    def test_set_constraints_block_height(self):
        """Test setting block_height constraint"""
        hivemind_issue = HivemindIssue()
        hivemind_issue.name = "Test"
        hivemind_issue.add_question("Question?")

        # Test valid block_height
        constraints = {"block_height": 12345}
        hivemind_issue.set_constraints(constraints)
        assert hivemind_issue.constraints == constraints

        # Test invalid block_height
        with pytest.raises(Exception):
            hivemind_issue.set_constraints({"block_height": "12345"})

    def test_set_restrictions_addresses(self):
        """Test setting address restrictions"""
        hivemind_issue = HivemindIssue()
        hivemind_issue.name = "Test"
        hivemind_issue.add_question("Question?")

        # Test valid addresses list
        restrictions = {"addresses": ["addr1", "addr2"]}
        hivemind_issue.set_restrictions(restrictions)
        assert hivemind_issue.restrictions == restrictions

        # Test invalid address type
        with pytest.raises(Exception):
            hivemind_issue.set_restrictions({"addresses": [123, 456]})

        # Test invalid addresses container
        with pytest.raises(Exception):
            hivemind_issue.set_restrictions({"addresses": "addr1,addr2"})

    def test_set_constraints_specs_validation(self):
        """Test validation of specs in constraints"""
        hivemind_issue = HivemindIssue()
        hivemind_issue.name = "Test"
        hivemind_issue.add_question("Question?")

        # Test invalid specs type
        with pytest.raises(Exception) as exc_info:
            hivemind_issue.set_constraints({"specs": 123})
        assert 'constraint "specs" must be a dict' in str(exc_info.value)

    def test_valid_empty_questions(self):
        """Test validation of empty questions list"""
        hivemind_issue = HivemindIssue()
        hivemind_issue.name = "Test"
        hivemind_issue.questions = []  # Empty questions list

        with pytest.raises(Exception) as exc_info:
            hivemind_issue.valid()
        assert "There must be at least 1 question" in str(exc_info.value)

    def test_set_constraints_invalid_choices_type(self, issue: HivemindIssue) -> None:
        """Test setting constraints with invalid choices type"""
        with pytest.raises(Exception) as exc_info:
            issue.set_constraints({'choices': 'not a list'})
        assert 'Value of constraint choices must be a list' in str(exc_info.value)

    def test_get_identification_cid(self) -> None:
        """Test the get_identification_cid method"""
        # Create and save a hivemind issue
        hivemind_issue = HivemindIssue()
        hivemind_issue.name = "Test Issue"
        hivemind_issue.add_question("Test Question?")
        issue_cid = hivemind_issue.save()

        # Get identification CID for a participant
        participant_name = "Test Participant"
        identification_cid = hivemind_issue.get_identification_cid(participant_name)

        # Verify the identification CID is not None and is a string
        assert identification_cid is not None
        assert isinstance(identification_cid, str)

        # Load the identification data from IPFS to verify its contents
        from ipfs_dict_chain.IPFSDict import IPFSDict
        identification_data = IPFSDict(cid=identification_cid)

        # Verify the data contains the correct hivemind_id and name
        assert identification_data['hivemind_id'] == issue_cid.replace('/ipfs/', '')
        assert identification_data['name'] == participant_name

    def test_set_constraints_none(self, issue: HivemindIssue) -> None:
        """Test setting constraints to None"""
        # First set some constraints
        constraints = {'min_length': 5, 'max_length': 10}
        issue.set_constraints(constraints)
        assert issue.constraints == constraints
        
        # Then set to None
        issue.set_constraints(None)
        assert issue.constraints is None
