#!/usr/bin/env python
# -*- coding: utf-8 -*-
from helpers.ipfshelpers import IPFSDict
from validators.validators import valid_address, valid_bech32_address


class HivemindOption(IPFSDict):
    def __init__(self, cid=None):
        """
        Constructor of the Option object

        :param cid: The IPFS multihash of the Option (optional)
        """
        self._cid = cid
        self.hivemind_id = None
        self._hivemind_issue = None  # set as a private member because it is not json encodable and members of an IPFSDict starting with '_' are ignored when saving
        self._answer_type = None  # can be 'String', 'Bool', 'Integer', 'Float', 'Hivemind', 'Image', 'Video', 'Complex', 'Address'

        self.value = None
        self.text = None

        super(HivemindOption, self).__init__(cid=cid)

    def set_hivemind_issue(self, hivemind_issue_hash):
        self.hivemind_id = hivemind_issue_hash

    def set(self, value):
        self.value = value

    def valid(self):
        if self._answer_type == 'String':
            return self.is_valid_string_option()
        elif self._answer_type == 'Float':
            return self.is_valid_float_option()
        elif self._answer_type == 'Integer':
            return self.is_valid_integer_option()
        elif self._answer_type == 'Bool':
            return self.is_valid_bool_option()
        elif self._answer_type == 'Hivemind':
            return self.is_valid_hivemind_option()
        elif self._answer_type == 'Complex':
            return self.is_valid_complex_option()
        elif self._answer_type == 'Address':
            return self.is_valid_address_option()
        else:
            return True

    def is_valid_string_option(self):
        if not isinstance(self.value, str):
            return False

        if self._hivemind_issue.constraints is not None:
            if 'min_length' in self._hivemind_issue.constraints and len(self.value) < self._hivemind_issue.constraints['min_length']:
                return False
            elif 'max_length' in self._hivemind_issue.constraints and len(self.value) > self._hivemind_issue.constraints['max_length']:
                return False
            elif 'regex' in self._hivemind_issue.constraints and not re.match(self._hivemind_issue.constraints['regex'], self.value):
                return False
            elif 'choices' in self._hivemind_issue.constraints and self.value not in self._hivemind_issue.constraints['choices']:
                return False

        return True

    def is_valid_float_option(self):
        if not isinstance(self.value, (int, float)):
            return False

        if self._hivemind_issue.constraints is not None:
            if 'min_value' in self._hivemind_issue.constraints and self.value < self._hivemind_issue.constraints['min_value']:
                return False
            elif 'max_value' in self._hivemind_issue.constraints and self.value > self._hivemind_issue.constraints['max_value']:
                return False
            elif 'decimals' in self._hivemind_issue.constraints:
                decimals = str(self.value)[::-1].find('.')
                if decimals > self._hivemind_issue.constraints['decimals']:
                    return False

        return True

    def is_valid_integer_option(self):
        if not isinstance(self.value, int):
            return False

        if self._hivemind_issue.constraints is not None:
            if 'min_value' in self._hivemind_issue.constraints and self.value < self._hivemind_issue.constraints['min_value']:
                return False
            elif 'max_value' in self._hivemind_issue.constraints and self.value > self._hivemind_issue.constraints['max_value']:
                return False

        return True

    def is_valid_bool_option(self):
        if not isinstance(self.value, bool):
            return False

        if self._hivemind_issue.constraints is not None:
            if 'true_value' in self._hivemind_issue.constraints and self.value is True and str(self.value) != self._hivemind_issue.constraints['true_value']:
                return False
            elif 'false_value' in self._hivemind_issue.constraints and self.value is False and str(self.value) != self._hivemind_issue.constraints['false_value']:
                return False

        return True

    def is_valid_hivemind_option(self):
        return True

    def is_valid_complex_option(self):
        if not isinstance(self.value, dict):
            return False

        if self._hivemind_issue.constraints is not None and 'specs' in self._hivemind_issue.constraints:
            specs = self._hivemind_issue.constraints['specs']
            for key in specs:
                if key not in self.value:
                    return False
                elif specs[key] == 'String' and not isinstance(self.value[key], str):
                    return False
                elif specs[key] == 'Integer' and not isinstance(self.value[key], int):
                    return False
                elif specs[key] == 'Float' and not isinstance(self.value[key], (int, float)):
                    return False

        return True

    def is_valid_address_option(self):
        if not isinstance(self.value, str):
            return False
        elif not (valid_address(self.value) or valid_bech32_address(self.value)):
            return False

        return True

    def info(self):
        """
        Get all details of the Option as a formatted string
        """
        info_string = 'Option:\n'
        info_string += '  Value: %s\n' % self.value
        if self.text is not None:
            info_string += '  Text: %s\n' % self.text

        return info_string
