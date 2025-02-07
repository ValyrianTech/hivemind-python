#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ipfs_dict_chain.IPFSDict import IPFSDict
from .validators import valid_address, valid_bech32_address


class HivemindIssue(IPFSDict):
    def __init__(self, cid=None):
        """
        Constructor of Hivemind issue class

        :param cid: The ipfs multihash of the hivemind issue
        """
        super().__init__(cid=cid)
        
        self.questions = []
        self.name = None
        self.description = ''
        self.tags = []
        self.answer_type = 'String'
        self.constraints = None
        self.restrictions = None

        # What happens when an option is selected: valid values are None, Finalize, Exclude, Reset
        # None : nothing happens
        # Finalize : Hivemind is finalized, no new options or opinions can be added anymore
        # Exclude : The selected option is excluded from the results
        # Reset : All opinions are reset
        self.on_selection = None

    def add_question(self, question):
        if isinstance(question, str) and question not in self.questions:
            self.questions.append(question)

    def set_constraints(self, constraints):
        if not isinstance(constraints, dict):
            raise Exception('constraints must be a dict, got %s' % type(constraints))

        if 'specs' in constraints:
            specs = constraints['specs']
            if not isinstance(constraints['specs'], dict):
                raise Exception('constraint "specs" must be a dict, got %s' % type(specs))

            for key in specs:
                if specs[key] not in ['String', 'Integer', 'Float']:
                    raise Exception('Spec type must be String or Integer or Float, got %s' % specs[key])

        for constraint_type in ['min_length', 'max_length', 'min_value', 'max_value', 'decimals']:
            if constraint_type in constraints and not isinstance(constraints[constraint_type], (int, float)):
                raise Exception('Value of constraint %s must be a number' % constraint_type)

        for constraint_type in ['regex', 'true_value', 'false_value']:
            if constraint_type in constraints and not isinstance(constraints[constraint_type], str):
                raise Exception('Value of constraint %s must be a string' % constraint_type)

        for constraint_type in ['choices']:
            if constraint_type in constraints and not isinstance(constraints[constraint_type], list):
                raise Exception('Value of constraint %s must be a list' % constraint_type)

        for constraint_type in ['SIL', 'LAL']:
            if constraint_type in constraints and not (valid_address(constraints[constraint_type]) or valid_bech32_address(constraints[constraint_type])):
                raise Exception('Value of constraint %s must be a valid address' % constraint_type)

        if 'LAL' in constraints and 'xpub' not in constraints:
            raise Exception('Constraints that include a LAL must also have a xpub specified!')

        for constraint_type in ['block_height']:
            if constraint_type in constraints and not isinstance(constraints[constraint_type], int):
                raise Exception('Value of constraint %s must be a integer' % constraint_type)

        if all([key in ['min_length', 'max_length', 'min_value', 'max_value', 'decimals', 'regex', 'true_value', 'false_value', 'specs', 'choices', 'SIL', 'LAL', 'xpub', 'block_height'] for key in constraints.keys()]):
            self.constraints = constraints
        else:
            raise Exception('constraints contain an invalid key: %s' % constraints)

    def set_restrictions(self, restrictions):
        if not isinstance(restrictions, dict):
            raise Exception('Restrictions is not a dict , got %s instead' % type(restrictions))

        for key in restrictions.keys():
            if key not in ['addresses', 'options_per_address']:
                raise Exception('Invalid key in restrictions: %s' % key)

        if 'addresses' in restrictions:
            if not isinstance(restrictions['addresses'], list):
                raise Exception('addresses in restrictions must be a list, got %s instead' % type(restrictions['addresses']))

            for address in restrictions['addresses']:
                if not (valid_address(address=address) or valid_bech32_address(address=address)):
                    raise Exception('Address %s in restrictions is not valid!' % address)

        if 'options_per_address' in restrictions:
            if not isinstance(restrictions['options_per_address'], int) or restrictions['options_per_address'] < 1:
                raise Exception('options_per_address in restrictions must be a positive integer')

        self.restrictions = restrictions

    def info(self):
        """
        Get info about the hivemind question

        :return: A string containing info about the hivemind question
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

    def save(self):
        try:
            self.valid()
        except Exception as ex:
            raise Exception('Error: %s' % ex)
        else:
            return super(HivemindIssue, self).save()

    def valid(self):

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
        if self.answer_type not in ['String', 'Bool', 'Integer', 'Float', 'Hivemind', 'Image', 'Video', 'Complex', 'Address']:
            raise Exception('Invalid answer_type for Hivemind Issue: %s' % self.answer_type)

        # On_selection must be in allowed values
        if self.on_selection not in [None, 'Finalize', 'Exclude', 'Reset']:
            raise Exception('Invalid on_selection for Hivemind Issue: %s' % self.on_selection)