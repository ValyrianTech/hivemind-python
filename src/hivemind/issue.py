#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import List, Optional, Dict, Union
from ipfs_dict_chain.IPFSDict import IPFSDict
from .validators import valid_address, valid_bech32_address


class HivemindIssue(IPFSDict):
    """A class representing a voting issue in the Hivemind protocol.

    This class handles the creation and management of voting issues, including
    questions, constraints, and restrictions on who can vote.

    :ivar questions: List of questions associated with this issue
    :type questions: List[str]
    :ivar name: Name of the issue
    :type name: Optional[str]
    :ivar description: Description of the issue
    :type description: str
    :ivar tags: List of tags associated with this issue
    :type tags: List[str]
    :ivar answer_type: Type of answer expected ('String', 'Integer', 'Float')
    :type answer_type: str
    :ivar constraints: Optional constraints on voting
    :type constraints: Optional[Dict[str, Union[str, int, float, list]]]
    :ivar restrictions: Optional restrictions on who can vote
    :type restrictions: Optional[Dict[str, Union[List[str], int]]]
    :ivar on_selection: Action to take when an option is selected
    :type on_selection: Optional[str]
    """

    def __init__(self, cid: Optional[str] = None) -> None:
        """Initialize a new HivemindIssue.

        :param cid: The IPFS multihash of the hivemind issue
        :type cid: Optional[str]
        """
        self.questions: List[str] = []
        self.name: Optional[str] = None
        self.description: str = ''
        self.tags: List[str] = []
        self.answer_type: str = 'String'
        self.constraints: Optional[Dict[str, Union[str, int, float, list]]] = None
        self.restrictions: Optional[Dict[str, Union[List[str], int]]] = None

        # What happens when an option is selected: valid values are None, Finalize, Exclude, Reset
        # None : nothing happens
        # Finalize : Hivemind is finalized, no new options or opinions can be added anymore
        # Exclude : The selected option is excluded from the results
        # Reset : All opinions are reset
        self.on_selection: Optional[str] = None

        super().__init__(cid=cid)

    def add_question(self, question: str) -> None:
        """Add a question to the hivemind issue.

        :param question: The question text to add
        :type question: str
        :raises ValueError: If question is invalid or already exists
        """
        if isinstance(question, str) and question not in self.questions:
            self.questions.append(question)

    def set_constraints(self, constraints: Dict[str, Union[str, int, float, list]]) -> None:
        """Set constraints for the hivemind issue.

        :param constraints: Dictionary of constraints
        :type constraints: Dict[str, Union[str, int, float, list]]
        :raises Exception: If constraints are invalid
        """
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

        for constraint_type in ['regex', 'true_value', 'false_value']:
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

    def set_restrictions(self, restrictions: Dict[str, Union[List[str], int]]) -> None:
        """Set voting restrictions for the hivemind issue.

        :param restrictions: Dictionary of restrictions
        :type restrictions: Dict[str, Union[List[str], int]]
        :raises Exception: If restrictions are invalid
        """
        if not isinstance(restrictions, dict):
            raise Exception('Restrictions is not a dict , got %s instead' % type(restrictions))

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

    def info(self) -> str:
        """Get information about the hivemind issue.

        :return: A string containing formatted information about the hivemind issue
        :rtype: str
        """
        info = 'Hivemind name: %s\n' % self.name
        info += 'Hivemind description: %s\n' % self.description

        for i, question in enumerate(self.questions):
            info += 'Hivemind question %s: %s\n' % (i+1, question)

        info += 'Hivemind tags: %s\n' % self.tags
        info += 'Answer type: %s\n' % self.answer_type

        for constraint_type, constraint_value in self.constraints.items():
            info += 'Constraint %s: %s\n' % (constraint_type, constraint_value)

        for i, additional_question in enumerate(self.questions[1:]):
            info += 'Additional question %s: %s\n' % (i + 1, additional_question)

        return info

    def save(self) -> str:
        """Save the hivemind issue to IPFS.

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

        :return: True if valid, raises exception otherwise
        :rtype: bool
        :raises Exception: If any validation fails
        """
        # Name must be a string, not empty and not longer than 50 characters
        if not (isinstance(self.name, str) and 0 < len(self.name) <= 50):
            raise Exception('Invalid name for Hivemind Issue: %s' % self.name)

        # Description must be a string, not longer than 255 characters
        if not (isinstance(self.description, str) and len(self.description) <= 255):
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