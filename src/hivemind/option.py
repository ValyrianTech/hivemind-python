#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import logging
from ipfs_dict_chain.IPFSDict import IPFSDict
from .validators import valid_address, valid_bech32_address
from .issue import HivemindIssue

LOG = logging.getLogger(__name__)

class HivemindOption(IPFSDict):
    def __init__(self, cid=None):
        """Initialize a new HivemindOption

        :param cid: The IPFS multihash of the Option (optional)
        """
        self.value = None
        self.text = ''
        self._hivemind_issue = None
        self._answer_type = 'String'
        self.hivemind_id = None
        super().__init__(cid=cid)
        if cid is not None:
            self.set_hivemind_issue(hivemind_issue_hash=self.hivemind_id)

    def cid(self):
        return self._cid

    def load(self, cid):
        super().load(cid=cid)
        self.set_hivemind_issue(hivemind_issue_hash=self.hivemind_id)

    def set_hivemind_issue(self, hivemind_issue_hash):
        """Set the hivemind issue for this option

        :param hivemind_issue_hash: The IPFS hash of the hivemind issue
        """
        self.hivemind_id = hivemind_issue_hash
        issue = HivemindIssue(cid=hivemind_issue_hash)
        self._hivemind_issue = issue
        self._answer_type = issue.answer_type

    def set(self, value):
        self.value = value

        if not self.valid():
            raise Exception('Invalid value for answer type %s: %s' % (self._answer_type, value))

    def valid(self):
        if not isinstance(self._hivemind_issue, HivemindIssue):
            raise Exception('No hivemind question set on option yet! Must set the hivemind question first before setting the value!')

        if self._answer_type != self._hivemind_issue.answer_type:
            LOG.error('Option value is not the correct answer type, got %s but should be %s' % (self._answer_type, self._hivemind_issue.answer_type))
            return False

        if self._hivemind_issue.constraints is not None and 'choices' in self._hivemind_issue.constraints:
            valid_choice = False
            for choice in self._hivemind_issue.constraints['choices']:
                if choice['value'] == self.value:
                    valid_choice = True

            if not valid_choice:
                LOG.error('Option %s is not valid because this it is not in the allowed choices of this hiveminds constraints!' % self.value)
                raise Exception('Option %s is not valid because this it is not in the allowed choices of this hiveminds constraints!' % self.value)

        if self._answer_type == 'String' and self.is_valid_string_option():
            return True
        elif self._answer_type == 'Bool' and self.is_valid_bool_option():
            return True
        elif self._answer_type == 'Integer' and self.is_valid_integer_option():
            return True
        elif self._answer_type == 'Float' and self.is_valid_float_option():
            return True
        elif self._answer_type == 'Hivemind' and self.is_valid_hivemind_option():
            return True
        elif self._answer_type == 'Image' and isinstance(self.value, str):  # todo check for valid ipfs hash
            return True
        elif self._answer_type == 'Video' and isinstance(self.value, str):  # todo check for valid ipfs hash
            return True
        elif self._answer_type == 'Complex' and self.is_valid_complex_option():
            return True
        elif self._answer_type == 'Address' and self.is_valid_address_option():
            return True
        else:
            return False

    def is_valid_string_option(self):
        if not isinstance(self.value, str):
            return False

        if self._hivemind_issue.constraints is not None:
            if 'min_length' in self._hivemind_issue.constraints and len(self.value) < self._hivemind_issue.constraints['min_length']:
                return False
            elif 'max_length' in self._hivemind_issue.constraints and len(self.value) > self._hivemind_issue.constraints['max_length']:
                return False
            elif 'regex' in self._hivemind_issue.constraints and re.match(pattern=self._hivemind_issue.constraints['regex'], string=self.value) is None:
                return False

        return True

    def is_valid_float_option(self):
        if not isinstance(self.value, float):
            LOG.error('Option value %s is not a floating number value but instead is a %s' % (self.value, type(self.value)))
            return False

        if self._hivemind_issue.constraints is not None:
            if 'min_value' in self._hivemind_issue.constraints and self.value < self._hivemind_issue.constraints['min_value']:
                LOG.error('Option value is below minimum value: %s < %s' % (self.value, self._hivemind_issue.constraints['min_value']))
                return False
            elif 'max_value' in self._hivemind_issue.constraints and self.value > self._hivemind_issue.constraints['max_value']:
                LOG.error('Option value is above maximum value: %s > %s' % (self.value, self._hivemind_issue.constraints['max_value']))
                return False
            elif 'decimals' in self._hivemind_issue.constraints:
                decimals = self._hivemind_issue.constraints['decimals']
                # Convert to string with required number of decimals in case the number has trailing zeros
                value_as_string = f"{self.value:.{decimals}f}"

                if float(value_as_string) != self.value:
                    LOG.error('Option value does not have the correct number of decimals (%s): %s' % (self._hivemind_issue.constraints['decimals'], self.value))
                    return False

        return True

    def is_valid_integer_option(self):
        if not isinstance(self.value, int):
            LOG.error('Option value %s is not a integer value but instead is a %s' % (self.value, type(self.value)))
            return False

        if self._hivemind_issue.constraints is not None:
            if 'min_value' in self._hivemind_issue.constraints and self.value < self._hivemind_issue.constraints['min_value']:
                LOG.error('Option value is below minimum value: %s < %s' % (self.value, self._hivemind_issue.constraints['min_value']))
                return False
            elif 'max_value' in self._hivemind_issue.constraints and self.value > self._hivemind_issue.constraints['max_value']:
                LOG.error('Option value is above maximum value: %s > %s' % (self.value, self._hivemind_issue.constraints['max_value']))
                return False

        return True

    def is_valid_bool_option(self):
        if not isinstance(self.value, bool):
            LOG.error('Option value %s is not a boolean value but instead is a %s' % (self.value, type(self.value)))
            return False

        return True

    def is_valid_hivemind_option(self):
        try:
            isinstance(HivemindIssue(cid=self.value), HivemindIssue)
        except Exception as ex:
            LOG.error('IPFS hash %s is not a valid hivemind: %s' % (self.value, ex))
            return False

        return True

    def is_valid_complex_option(self):
        if not isinstance(self.value, dict):
            return False

        if 'specs' in self._hivemind_issue.constraints:
            for spec_key in self._hivemind_issue.constraints['specs']:
                if spec_key not in self.value:
                    return False

            for spec_key in self.value.keys():
                if spec_key not in self._hivemind_issue.constraints['specs']:
                    return False

            for spec_key, spec_value in self.value.items():
                if self._hivemind_issue.constraints['specs'][spec_key] == 'String' and not isinstance(spec_value, str):
                    return False
                elif self._hivemind_issue.constraints['specs'][spec_key] == 'Integer' and not isinstance(spec_value, int):
                    return False
                elif self._hivemind_issue.constraints['specs'][spec_key] == 'Float' and not isinstance(spec_value, float):
                    return False

        return True

    def is_valid_address_option(self):
        if 'SIL' in self._hivemind_issue.constraints or 'LAL' in self._hivemind_issue.constraints:
            address = self._hivemind_issue.constraints['SIL']
            block_height = self._hivemind_issue.constraints['block_height'] if 'block_height' in self._hivemind_issue.constraints else 0

            if 'SIL' in self._hivemind_issue.constraints:
                data = get_sil(address=address, block_height=block_height)
                if 'SIL' not in data:
                    LOG.error('Unable to retrieve SIL of %s to verify constraints op hivemind option' % address)
                    return False

                for item in data['SIL']:
                    if item[0] == self.value:  # assume data in SIL is valid
                        return True

                return False

            elif 'LAL' in self._hivemind_issue.constraints:
                xpub = self._hivemind_issue.constraints['xpub']
                data = get_lal(address=address, xpub=xpub, block_height=block_height)
                if 'LAL' not in data:
                    LOG.error('Unable to retrieve LAL of %s to verify constraints of hivemind option' % address)
                    return False

                for item in data['LAL']:
                    if item[1] == self.value:  # assume data in LAL is valid
                        return True

                return False

        return valid_address(self.value) or valid_bech32_address(self.value)

    def info(self):
        """
        Get info about the option

        :return: A string containing info about the option
        """
        info = f'Option hash: {self.cid}\n'
        info += f'Answer type: {self._answer_type}\n'
        info += f'Value: {self.value}\n'
        if self.text:
            info += f'Text: {self.text}\n'
        return info