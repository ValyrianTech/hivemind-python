#!/usr/bin/env python
# -*- coding: utf-8 -*-
from itertools import combinations
import time

from helpers.ipfshelpers import IPFSDict
from helpers.loghelpers import LOG
from helpers.messagehelpers import verify_message
from inputs.inputs import get_sil
from linker.linker import get_lal


def compare(a, b, opinion_hash):
    """
    Helper function to compare 2 Option objects against each other based on a given Opinion

    :param a: The first Option object
    :param b: The second Option object
    :param opinion_hash: The Opinion object
    :return: The Option that is considered better by the Opinion
    If one of the Options is not given in the Opinion object, the other option wins by default
    If both Options are not in the Opinion object, None is returned
    """
    ranked_choice = opinion_hash.get()
    if ranked_choice is None:
        return None

    try:
        index_a = ranked_choice.index(a.cid)
    except ValueError:
        index_a = -1

    try:
        index_b = ranked_choice.index(b.cid)
    except ValueError:
        index_b = -1

    if index_a == -1 and index_b == -1:
        return None
    elif index_a == -1:
        return b
    elif index_b == -1:
        return a
    elif index_a < index_b:
        return a
    else:
        return b


class HivemindState(IPFSDict):
    def __init__(self, cid=None):
        self.hivemind_id = None
        self._hivemind_issue = None
        self.options = []
        self.opinions = [{}]  # opinions are recorded for each question separately
        self.signatures = {}
        self.participants = {}
        self.selected = []  # A list of options that have been selected by the hivemind
        self.final = False  # if set to True, no more options or opinions can be added

        super(HivemindState, self).__init__(cid=cid)

    @property
    def hivemind_issue(self):
        return self._hivemind_issue

    def get_options(self):
        return self.options

    def set_hivemind_issue(self, issue_hash):
        self.hivemind_id = issue_hash
        self.opinions = [{} for _ in range(len(self._hivemind_issue.questions))]

    def add_predefined_options(self):
        if self._hivemind_issue.constraints is not None and 'choices' in self._hivemind_issue.constraints:
            for choice in self._hivemind_issue.constraints['choices']:
                option = HivemindOption()
                option.set_hivemind_issue(self.hivemind_id)
                option.set(choice)
                self.options.append(option)

    def add_option(self, timestamp, option_hash, address, signature):
        """
        Add an option to the hivemind state

        If the hivemind issue has restrictions on addresses, then the address and signature are required

        :param timestamp: Int - a unix timestamp
        :param option_hash: String - The IPFS multihash of the option
        :param address: String - The address that supports the option (optional)
        :param signature: String - The signature of the message: '<timestamp>'+'/ipfs/<option_hash>' by the address
        """
        if self.final is True:
            raise Exception('This hivemind has been finalized, no more options can be added!')

        if self._hivemind_issue.restrictions is not None:
            if address is None or signature is None:
                raise Exception('This hivemind has restrictions on addresses, an address and signature are required!')

            if 'addresses' in self._hivemind_issue.restrictions and address not in self._hivemind_issue.restrictions['addresses']:
                raise Exception('Address %s is not allowed to add options to this hivemind!' % address)

            if 'options_per_address' in self._hivemind_issue.restrictions:
                if address not in self.participants:
                    self.participants[address] = {'options': [], 'opinions': []}

                if len(self.participants[address]['options']) >= self._hivemind_issue.restrictions['options_per_address']:
                    raise Exception('Address %s has already added the maximum number of options (%d) to this hivemind!' % (address, self._hivemind_issue.restrictions['options_per_address']))

            # Verify the signature
            message = str(timestamp) + '/ipfs/' + option_hash
            if verify_message(message=message, address=address, signature=signature) is not True:
                raise Exception('Invalid signature!')

            # Add the signature to the signatures dict
            if address not in self.signatures:
                self.signatures[address] = []

            self.signatures[address].append({'timestamp': timestamp,
                                          'message': message,
                                          'signature': signature})

            # Add the option to the participants dict
            if address not in self.participants:
                self.participants[address] = {'options': [], 'opinions': []}

            self.participants[address]['options'].append(option_hash)

        self.options.append(option_hash)

    def options_by_participant(self, address):
        if address in self.participants:
            return self.participants[address]['options']
        else:
            return []

    def add_opinion(self, timestamp, opinion_hash, signature, address):
        if self.final is True:
            raise Exception('This hivemind has been finalized, no more opinions can be added!')

        if self._hivemind_issue.restrictions is not None:
            if 'addresses' in self._hivemind_issue.restrictions and address not in self._hivemind_issue.restrictions['addresses']:
                raise Exception('Address %s is not allowed to add opinions to this hivemind!' % address)

            # Verify the signature
            message = str(timestamp) + '/ipfs/' + opinion_hash
            if verify_message(message=message, address=address, signature=signature) is not True:
                raise Exception('Invalid signature!')

            # Add the signature to the signatures dict
            if address not in self.signatures:
                self.signatures[address] = []

            self.signatures[address].append({'timestamp': timestamp,
                                          'message': message,
                                          'signature': signature})

            # Add the opinion to the participants dict
            if address not in self.participants:
                self.participants[address] = {'options': [], 'opinions': []}

            self.participants[address]['opinions'].append(opinion_hash)

        self.opinions[opinion_hash.question_index][address] = opinion_hash

    def get_opinion(self, opinionator, question_index=0):
        """
        Get the Opinion object of a certain opinionator

        :param opinionator: The opinionator
        :param question_index: The index of the question in the HivemindQuestion (default=0)
        :return: An Opinion object
        """
        if opinionator in self.opinions[question_index]:
            return self.opinions[question_index][opinionator]
        else:
            return None

    def get_weight(self, opinionator):
        """
        Get the weight of an Opinion
        Default weight is 1.0 unless a specific weight has been specified in the restrictions

        :param opinionator: The opinionator
        :return: The weight of the Opinion (type float)
        """
        if self._hivemind_issue.restrictions is not None and 'weights' in self._hivemind_issue.restrictions and opinionator in self._hivemind_issue.restrictions['weights']:
            return self._hivemind_issue.restrictions['weights'][opinionator]
        else:
            return 1.0

    def info(self):
        """
        Print the details of the hivemind
        """
        info_string = 'Hivemind state:\n'
        info_string += '  Options: %d\n' % len(self.options)
        info_string += '  Opinions: %d\n' % len(self.opinions)
        info_string += '  Selected: %s\n' % self.selected
        info_string += '  Final: %s\n' % self.final

        return info_string

    def options_info(self):
        """
        Get detailed information about the options as a formatted string

        :return: A string containing all information about the options
        """
        info_string = 'Options:\n'
        for option in self.options:
            info_string += option.info()

        return info_string

    def opinions_info(self, question_index=0):
        """
        Print out a list of the Opinions of the hivemind
        """
        info_string = 'Opinions for question %d:\n' % question_index
        for opinionator in self.opinions[question_index]:
            info_string += '  %s: %s\n' % (opinionator, self.opinions[question_index][opinionator].get())

        return info_string

    def calculate_results(self, question_index=0):
        """
        Calculate the results of the hivemind
        """
        scores = {}
        for option in self.options:
            scores[option.cid] = {'wins': 0, 'losses': 0}

        for option_a, option_b in combinations(self.options, 2):
            if option_a.cid in self.selected or option_b.cid in self.selected:
                continue

            wins_a = 0
            wins_b = 0
            for opinionator in self.opinions[question_index]:
                opinion = self.opinions[question_index][opinionator]
                winner = compare(option_a, option_b, opinion)
                if winner == option_a:
                    wins_a += self.get_weight(opinionator)
                elif winner == option_b:
                    wins_b += self.get_weight(opinionator)

            if wins_a > wins_b:
                scores[option_a.cid]['wins'] += 1
                scores[option_b.cid]['losses'] += 1
            elif wins_b > wins_a:
                scores[option_b.cid]['wins'] += 1
                scores[option_a.cid]['losses'] += 1

        return scores

    def get_score(self, option_hash, question_index=0):
        results = self.calculate_results(question_index=question_index)
        if option_hash in results:
            return results[option_hash]['wins'] - results[option_hash]['losses']
        else:
            return None

    def get_sorted_options(self, question_index=0):
        """
        Get the list of Options as sorted by the hivemind

        :return: A list of Option objects sorted by highest score
        """
        results = self.calculate_results(question_index=question_index)
        sorted_options = []
        for option in self.options:
            if option.cid not in self.selected:
                sorted_options.append((option, results[option.cid]['wins'] - results[option.cid]['losses']))

        sorted_options.sort(key=lambda x: x[1], reverse=True)
        return [x[0] for x in sorted_options]

    def consensus(self, question_index=0):
        sorted_options = self.get_sorted_options(question_index=question_index)
        if len(sorted_options) > 0:
            return sorted_options[0]
        else:
            return None

    def ranked_consensus(self, question_index=0):
        return self.get_sorted_options(question_index=question_index)

    def get_consensus(self, question_index=0, consensus_type='Single'):
        if consensus_type == 'Single':
            return self.consensus(question_index=question_index)
        elif consensus_type == 'Ranked':
            return self.ranked_consensus(question_index=question_index)
        else:
            raise Exception('Invalid consensus type: %s' % consensus_type)

    def results_info(self, results, question_index=0):
        """
        Print out the results of the hivemind
        """
        info_string = 'Results for question %d:\n' % question_index
        sorted_options = []
        for option in self.options:
            if option.cid not in self.selected:
                sorted_options.append((option, results[option.cid]['wins'] - results[option.cid]['losses']))

        sorted_options.sort(key=lambda x: x[1], reverse=True)

        for option, score in sorted_options:
            info_string += '  %s: %d\n' % (option.value, score)

        return info_string

    def contributions(self, results, question_index):
        contributions = {}
        for option_a, option_b in combinations(self.options, 2):
            if option_a.cid in self.selected or option_b.cid in self.selected:
                continue

            for opinionator in self.opinions[question_index]:
                opinion = self.opinions[question_index][opinionator]
                winner = compare(option_a, option_b, opinion)
                if winner == option_a:
                    if opinionator not in contributions:
                        contributions[opinionator] = {'wins': 0, 'losses': 0}

                    if results[option_a.cid]['wins'] - results[option_a.cid]['losses'] > results[option_b.cid]['wins'] - results[option_b.cid]['losses']:
                        contributions[opinionator]['wins'] += 1
                    else:
                        contributions[opinionator]['losses'] += 1

                elif winner == option_b:
                    if opinionator not in contributions:
                        contributions[opinionator] = {'wins': 0, 'losses': 0}

                    if results[option_b.cid]['wins'] - results[option_b.cid]['losses'] > results[option_a.cid]['wins'] - results[option_a.cid]['losses']:
                        contributions[opinionator]['wins'] += 1
                    else:
                        contributions[opinionator]['losses'] += 1

        return contributions

    def select_consensus(self):
        """
        Mark the current consensus as being 'selected'

        :return: a list containing the option with highest consensus for each question
        """
        selected_options = []
        for question_index in range(len(self._hivemind_issue.questions)):
            consensus = self.consensus(question_index=question_index)
            if consensus is not None:
                self.selected.append(consensus.cid)
                selected_options.append(consensus)

                if self._hivemind_issue.on_selection == 'Finalize':
                    self.final = True
                elif self._hivemind_issue.on_selection == 'Reset':
                    self.opinions = [{} for _ in range(len(self._hivemind_issue.questions))]

        return selected_options

    def add_signature(self, address, timestamp, message, signature):
        """
        Add a new name signature to the hivemind state
        Note: nonce should be a timestamp, and must be higher than all existing signature nonces

        :param address: String - address of the participant
        :param timestamp: Int - timestamp of the signature
        :param message: String - the message (this can be a option cid, opinion cid or a name
        :param signature: String - signature of 'timestamp+message' by the address
        """
        if address not in self.signatures:
            self.signatures[address] = []

        # Check if this timestamp is higher than all existing timestamps
        for existing_signature in self.signatures[address]:
            if existing_signature['timestamp'] >= timestamp:
                raise Exception('Timestamp must be higher than all existing timestamps!')

        self.signatures[address].append({'timestamp': timestamp,
                                      'message': message,
                                      'signature': signature})

    def update_participant_name(self, timestamp, name, address, signature):
        # First check if this address is allowed to participate
        if self._hivemind_issue.restrictions is not None and 'addresses' in self._hivemind_issue.restrictions and address not in self._hivemind_issue.restrictions['addresses']:
            raise Exception('Address %s is not allowed to participate in this hivemind!' % address)

        # Then verify the signature
        message = str(timestamp) + name
        if verify_message(message=message, address=address, signature=signature) is not True:
            raise Exception('Invalid signature!')

        # Add the signature to the signatures dict
        self.add_signature(address=address, timestamp=timestamp, message=message, signature=signature)

        # Finally update the name
        if address not in self.participants:
            self.participants[address] = {'options': [], 'opinions': [], 'name': name}
        else:
            self.participants[address]['name'] = name
