#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import List, Dict
from ipfs_dict_chain.IPFSDict import IPFSDict


class HivemindIssue(IPFSDict):
    """A class representing a voting issue in the Hivemind protocol.

    This class handles the creation and management of voting issues, including
    questions, constraints, and restrictions on who can vote.

    :ivar questions: List of questions associated with this issue
    :vartype questions: List[str]
    :ivar name: Name of the issue
    :vartype name: str | None
    :ivar description: Description of the issue
    :vartype description: str
    :ivar tags: List of tags associated with this issue
    :vartype tags: List[str]
    :ivar answer_type: Type of answer expected ('String', 'Integer', 'Float', 'Bool', 'Hivemind', 'File', 'Complex', 'Address')
    :vartype answer_type: str
    :ivar constraints: Constraints on voting
    :vartype constraints: Dict[str, str | int | float | list] | None
    :ivar restrictions: Restrictions on who can vote
    :vartype restrictions: Dict[str, List[str] | int] | None
    :ivar on_selection: Action to take when an option is selected
    :vartype on_selection: str | None
    :ivar author: Bitcoin address of the author who can finalize the hivemind
    :vartype author: str | None
    """

    def __init__(self, cid: str | None = None) -> None:
        """Initialize a new HivemindIssue.

        :param cid: The IPFS multihash of the hivemind issue
        :type cid: str | None
        :return: None
        """
        self.questions: List[str] = []
        self.name: str | None = None
        self.description: str = ''
        self.tags: List[str] = []
        self.answer_type: str = 'String'
        self.constraints: Dict[str, str | int | float | list] | None = None
        self.restrictions: Dict[str, List[str] | int] | None = None

        # What happens when an option is selected: valid values are None, Finalize, Exclude, Reset
        # None : nothing happens
        # Finalize : Hivemind is finalized, no new options or opinions can be added anymore
        # Exclude : The selected option is excluded from the results
        # Reset : All opinions are reset
        self.on_selection: str | None = None
        
        # Bitcoin address of the author who can finalize the hivemind
        self.author: str | None = None

        super().__init__(cid=cid)

    def add_question(self, question: str) -> None:
        """Add a question to the hivemind issue.

        :param question: The question text to add
        :type question: str
        :return: None
        :raises ValueError: If question is invalid or already exists
        """
        if isinstance(question, str) and question not in self.questions:
            self.questions.append(question)

    def set_constraints(self, constraints: Dict[str, str | int | float | list] | None) -> None:
        """Set constraints for the hivemind issue.

        Constraints can include various limitations on the answers, such as:
        - min_length/max_length: For string answers
        - min_value/max_value: For numeric answers
        - decimals: For float answers
        - regex: For string pattern validation
        - true_value/false_value: For boolean answers
        - specs: For complex answer types
        - choices: For predefined answer options
        - block_height: For blockchain-related constraints
        - filetype: For file answer types

        :param constraints: Dictionary of constraints
        :type constraints: Dict[str, str | int | float | list] | None
        :return: None
        :raises Exception: If constraints are invalid
        """
        if constraints is None:
            self.constraints = None
            return
            
        if not isinstance(constraints, dict):
            raise Exception('constraints must be a dict, got %s' % type(constraints))

        if 'specs' in constraints:
            specs = constraints['specs']
            if not isinstance(constraints['specs'], dict):
                raise Exception('constraint "specs" must be a dict, got %s' % type(specs))

            for key in specs:
                if specs[key] not in ['String', 'Integer', 'Float', 'Bool']:
                    raise Exception('Spec type must be String, Integer, Float, or Bool, got %s' % specs[key])

        for constraint_type in ['min_length', 'max_length', 'min_value', 'max_value', 'decimals']:
            if constraint_type in constraints and not isinstance(constraints[constraint_type], (int, float)):
                raise Exception('Value of constraint %s must be a number' % constraint_type)

        for constraint_type in ['regex', 'true_value', 'false_value', 'filetype']:
            if constraint_type in constraints and not isinstance(constraints[constraint_type], str):
                raise Exception('Value of constraint %s must be a string' % constraint_type)

        for constraint_type in ['choices']:
            if constraint_type in constraints and not isinstance(constraints[constraint_type], list):
                raise Exception('Value of constraint %s must be a list' % constraint_type)

        for constraint_type in ['block_height']:
            if constraint_type in constraints and not isinstance(constraints[constraint_type], int):
                raise Exception('Value of constraint %s must be a integer' % constraint_type)

        # Updated list of valid constraint keys
        valid_constraints = [
            'min_length', 'max_length', 'min_value', 'max_value', 'decimals', 
            'regex', 'true_value', 'false_value', 'specs', 'choices', 'block_height',
            'filetype'
        ]
            
        if all([key in valid_constraints for key in constraints.keys()]):
            self.constraints = constraints
        else:
            raise Exception('constraints contain an invalid key: %s' % constraints)

    def set_restrictions(self, restrictions: Dict[str, List[str] | int] | None) -> None:
        """Set voting restrictions for the hivemind issue.

        Restrictions can include:
        - addresses: List of Bitcoin addresses allowed to vote
        - options_per_address: Maximum number of options each address can submit

        :param restrictions: Dictionary of restrictions
        :type restrictions: Dict[str, List[str] | int] | None
        :return: None
        :raises Exception: If restrictions are invalid
        """
        if restrictions is None:
            self.restrictions = None
            return
            
        if not isinstance(restrictions, dict):
            raise Exception('Restrictions is not a dict or None, got %s instead' % type(restrictions))

        for key in restrictions.keys():
            if key not in ['addresses', 'options_per_address']:
                raise Exception('Invalid key in restrictions: %s' % key)

        if 'addresses' in restrictions:
            if not isinstance(restrictions['addresses'], list):
                raise Exception('addresses in restrictions must be a list, got %s instead' % type(restrictions['addresses']))

            for address in restrictions['addresses']:
                if not isinstance(address, str):
                    raise Exception('Address %s in restrictions is not a string!' % address)

        if 'options_per_address' in restrictions:
            if not isinstance(restrictions['options_per_address'], int) or restrictions['options_per_address'] < 1:
                raise Exception('options_per_address in restrictions must be a positive integer')

        self.restrictions = restrictions

    def save(self) -> str:
        """Save the hivemind issue to IPFS.

        Validates the issue before saving to ensure it meets all requirements.

        :return: The IPFS hash of the saved issue
        :rtype: str
        :raises Exception: If the issue is invalid
        """
        try:
            self.valid()
        except Exception as ex:
            raise Exception('Error: %s' % ex)
        else:
            return super(HivemindIssue, self).save()

    def valid(self) -> bool:
        """Check if the hivemind issue is valid.

        Validates all properties of the issue including:
        - name: Must be a non-empty string ≤ 50 characters
        - description: Must be a string ≤ 5000 characters
        - tags: Must be a list of unique strings without spaces, each ≤ 20 characters
        - questions: Must be a non-empty list of unique strings, each ≤ 255 characters
        - answer_type: Must be one of the allowed types
        - on_selection: Must be one of the allowed values

        :return: True if valid, raises exception otherwise
        :rtype: bool
        :raises Exception: If any validation fails
        """
        # Name must be a string, not empty and not longer than 50 characters
        if not isinstance(self.name, str) or not (0 < len(self.name) <= 50):
            raise Exception('Invalid name for Hivemind Issue: %s' % self.name)

        # Description must be a string, not longer than 5000 characters
        if not (isinstance(self.description, str) and len(self.description) <= 5000):
            raise Exception('Invalid description for Hivemind Issue: %s' % self.description)

        # Tags must be a list of strings, each tag can not contain spaces and can not be empty or longer than 20 characters
        if not (isinstance(self.tags, list) and all([isinstance(tag, str) and ' ' not in tag and 0 < len(tag) <= 20 and self.tags.count(tag) == 1 for tag in self.tags])):
            raise Exception('Invalid tags for Hivemind Issue: %s' % self.tags)

        # Questions must be a list of strings, each question can not be empty or longer than 255 characters and must be unique
        if not (isinstance(self.questions, list) and all([isinstance(question, str) and 0 < len(question) <= 255 and self.questions.count(question) == 1 for question in self.questions])):
            raise Exception('Invalid questions for Hivemind Issue: %s' % self.questions)

        if len(self.questions) == 0:
            raise Exception('There must be at least 1 question in the Hivemind Issue.')

        # Answer_type must in allowed values
        if self.answer_type not in ['String', 'Bool', 'Integer', 'Float', 'Hivemind', 'File', 'Complex', 'Address']:
            raise Exception('Invalid answer_type for Hivemind Issue: %s' % self.answer_type)

        # On_selection must be in allowed values
        if self.on_selection not in [None, 'Finalize', 'Exclude', 'Reset']:
            raise Exception('Invalid on_selection for Hivemind Issue: %s' % self.on_selection)

        return True

    def get_identification_cid(self, name: str) -> str:
        """Get the identification CID so that a participant can self-identify for this issue.

        Creates an IPFS dictionary containing the hivemind ID and participant name,
        then saves it to IPFS and returns the resulting CID.

        :param name: The name of the participant
        :type name: str
        :return: The identification CID
        :rtype: str
        """
        data = IPFSDict()
        data['hivemind_id'] = self.cid().replace('/ipfs/', '')
        data['name'] = name
        cid = data.save()

        return cid
