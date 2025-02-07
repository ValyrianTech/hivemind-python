#!/usr/bin/env python
# -*- coding: utf-8 -*-
from itertools import combinations
import time

from ipfs_dict_chain import IPFSDict
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

class HivemindState(IPFSDictChain):
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

    def hivemind_issue(self):
        return self._hivemind_issue

    def get_options(self):
        return [HivemindOption(cid=option_cid) for option_cid in self.options]

    def set_hivemind_issue(self, issue_hash):
        self.hivemind_id = issue_hash
        self._hivemind_issue = HivemindIssue(cid=self.hivemind_id)
        self.opinions = [{} for _ in range(len(self._hivemind_issue.questions))]

    def add_predefined_options(self):
        options = {}

        if self._hivemind_issue.answer_type == 'Bool':
            true_option = HivemindOption()
            true_option.set_hivemind_issue(self.hivemind_id)
            true_option.set(value=True)
            true_option.text = self._hivemind_issue.constraints['true_value']
            true_option_hash = true_option.save()
            if isinstance(true_option, HivemindOption) and true_option.valid():
                if true_option_hash not in self.options:
                    self.options.append(true_option_hash)
                    options[true_option_hash] = true_option.get()

            false_option = HivemindOption()
            false_option.set_hivemind_issue(self.hivemind_id)
            false_option.set(value=False)
            false_option.text = self._hivemind_issue.constraints['false_value']
            false_option_hash = false_option.save()
            if isinstance(false_option, HivemindOption) and false_option.valid():
                if false_option_hash not in self.options:
                    self.options.append(false_option_hash)
                    options[false_option_hash] = false_option.get()

        elif 'choices' in self._hivemind_issue.constraints:
            for choice in self._hivemind_issue.constraints['choices']:
                option = HivemindOption()
                option.set_hivemind_issue(self.hivemind_id)
                option.set(value=choice['value'])
                option.text = choice['text']
                option_hash = option.save()
                if isinstance(option, HivemindOption) and option.valid():
                    if option_hash not in self.options:
                        self.options.append(option_hash)
                        options[option_hash] = option.get()

        return options

    def load(self, cid):
        super(HivemindState, self).load(cid=cid)
        self._hivemind_issue = HivemindIssue(cid=self.hivemind_id)

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
            return

        if not isinstance(self._hivemind_issue, HivemindIssue) or address is None or signature is None:
            return

        if not verify_message(message='%s%s' % (timestamp, option_hash), address=address, signature=signature):
            raise Exception('Can not add option: Signature is not valid')

        if self._hivemind_issue.restrictions is not None and 'addresses' in self._hivemind_issue.restrictions:
            if address not in self._hivemind_issue.restrictions['addresses']:
                raise Exception('Can not add option: there are address restrictions on this hivemind issue and address %s is not allowed to add options' % address)
            elif address is None or signature is None:
                raise Exception('Can not add option: no address or signature given')

        if self._hivemind_issue.restrictions is not None and 'options_per_address' in self._hivemind_issue.restrictions:
            number_of_options = len(self.options_by_participant(address=address))
            if number_of_options >= self._hivemind_issue.restrictions['options_per_address']:
                raise Exception('Can not add option: address %s already added too many options: %s' % (address, number_of_options))

        option = HivemindOption(cid=option_hash)
        if isinstance(option, HivemindOption) and option.valid():
            if option_hash not in self.options:
                # Signature is already verified, but it is possible an old signature is re-used
                try:
                    self.add_signature(address=address, timestamp=timestamp, message=option_hash, signature=signature)
                except Exception as ex:
                    raise Exception('Invalid signature: %s' % ex)

                self.options.append(option_hash)

    def options_by_participant(self, address):
        option_cids = [option_cid for option_cid in self.signatures['options'] if address in self.signatures['options'][option_cid]]
        return option_cids

    def add_opinion(self, timestamp, opinion_hash, signature, address):
        if self.final is True:
            return

        opinion = HivemindOpinion(cid=opinion_hash)
        if not verify_message(address=address, message='%s%s' % (timestamp, opinion_hash), signature=signature):
            raise Exception('Signature is invalid')

        if isinstance(opinion, HivemindOpinion) and not any(option_hash not in self.options for option_hash in opinion.ranking.get(options=self.get_options())):
            try:
                self.add_signature(address=address, timestamp=timestamp, message=opinion_hash, signature=signature)
            except Exception as ex:
                raise Exception('Invalid signature: %s' % ex)

            self.opinions[opinion.question_index][address] = {'opinion_cid': opinion_hash, 'timestamp': int(time.time())}

        else:
            raise Exception('Opinion is invalid')

    def get_opinion(self, opinionator, question_index=0):
        """
        Get the Opinion object of a certain opinionator

        :param opinionator: The opinionator
        :param question_index: The index of the question in the HivemindQuestion (default=0)
        :return: An Opinion object
        """
        opinion = None
        if opinionator in self.opinions[question_index]:
            opinion = HivemindOpinion(cid=self.opinions[question_index][opinionator]['opinion_cid'])

        return opinion

    def get_weight(self, opinionator):
        """
        Get the weight of an Opinion
        Default weight is 1.0 unless a specific weight has been specified in the restrictions

        :param opinionator: The opinionator
        :return: The weight of the Opinion (type float)
        """
        weight = 1.0
        if opinionator in self._hivemind_issue.restrictions and 'weight' in self._hivemind_issue.restrictions[opinionator]:
            weight = self._hivemind_issue.restrictions[opinionator]['weight']

        return weight

    def info(self):
        """
        Print the details of the hivemind
        """
        ret = "================================================================================="
        ret += '\nHivemind id: ' + self.hivemind_id
        ret += '\nHivemind main question: ' + self._hivemind_issue.questions[0]
        ret += '\nHivemind description: ' + self._hivemind_issue.description
        if self._hivemind_issue.tags is not None:
            ret += '\nHivemind tags: ' + ' '.join(self._hivemind_issue.tags)
        ret += '\nAnswer type: ' + self._hivemind_issue.answer_type
        if self._hivemind_issue.constraints is not None:
            ret += '\nOption constraints: ' + str(self._hivemind_issue.constraints)
        ret += '\n' + "================================================================================="
        ret += '\n' + self.options_info()

        for i, question in enumerate(self._hivemind_issue.questions):
            ret += '\nHivemind question %s: %s' % (i, self._hivemind_issue.questions[i])
            ret += '\n' + self.opinions_info(question_index=i)

            results = self.calculate_results(question_index=i)
            ret += '\n' + self.results_info(results=results, question_index=i)

        return ret

    def options_info(self):
        """
        Get detailed information about the options as a formatted string

        :return: A string containing all information about the options
        """
        ret = "Options"
        ret += "\n======="
        for i, option_hash in enumerate(self.options):
            ret += '\nOption %s:' % (i + 1)
            option = HivemindOption(cid=option_hash)
            ret += '\n' + option.info()
            ret += '\n'

        return ret

    def opinions_info(self, question_index=0):
        """
        Print out a list of the Opinions of the hivemind
        """
        ret = "Opinions"
        ret += "\n========"
        # opinion_data is a list containing [opinion_hash, signature of '/ipfs/opinion_hash', timestamp]
        for opinionator, opinion_data in self.opinions[question_index].items():
            ret += '\nTimestamp: %s' % opinion_data['timestamp']
            opinion = HivemindOpinion(cid=opinion_data['opinion_cid'])
            ret += '\n' + opinion.info()
            ret += '\n'

        return ret

    def calculate_results(self, question_index=0):
        """
        Calculate the results of the hivemind
        """
        LOG.info('Calculating results for question %s...' % question_index)

        # if selection mode is 'Exclude', we must exclude previously selected options from the results
        if self._hivemind_issue.on_selection == 'Exclude':
            selected_options = [selection[question_index] for selection in self.selected]
            available_options = [option_hash for option_hash in self.options if option_hash not in selected_options]
        else:
            available_options = self.options

        results = {option: {'win': 0, 'loss': 0, 'unknown': 0, 'score': 0} for option in available_options}

        for a, b in combinations(available_options, 2):
            for opinionator in self.opinions[question_index]:
                winner = compare(a, b, self.opinions[question_index][opinionator]['opinion_cid'])
                weight = self.get_weight(opinionator=opinionator)
                if winner == a:
                    results[a]['win'] += weight
                    results[b]['loss'] += weight
                elif winner == b:
                    results[b]['win'] += weight
                    results[a]['loss'] += weight
                elif winner is None:
                    results[a]['unknown'] += weight
                    results[b]['unknown'] += weight

        # Calculate scores for each option
        for option_id in results:
            if results[option_id]['win'] + results[option_id]['loss'] + results[option_id]['unknown'] > 0:
                results[option_id]['score'] = results[option_id]['win'] / float(results[option_id]['win'] + results[option_id]['loss'] + results[option_id]['unknown'])

        results_info = self.results_info(results=results, question_index=question_index)
        for line in results_info.split('\n'):
            LOG.info(line)

        return results

    def get_score(self, option_hash, question_index=0):
        results = self.calculate_results(question_index=question_index)
        return results[option_hash]['score']

    def get_sorted_options(self, question_index=0):
        """
        Get the list of Options as sorted by the hivemind

        :return: A list of Option objects sorted by highest score
        """

        results = self.calculate_results(question_index=question_index)
        return [HivemindOption(cid=option[0]) for option in sorted(results.items(), key=lambda x: x[1]['score'], reverse=True)]

    def consensus(self, question_index=0):
        results = self.calculate_results(question_index=question_index)

        sorted_options = self.get_options(question_index=question_index)
        if len(sorted_options) == 0:
            return None
        elif len(sorted_options) == 1:
            return sorted_options[0].value
        # Make sure the consensus is not tied between the first two options
        elif len(sorted_options) >= 2 and results[sorted_options[0].cid()]['score'] > results[sorted_options[1].cid()]['score']:
            return sorted_options[0].value
        else:
            return None

    def ranked_consensus(self, question_index=0):
        return [option.value for option in self.get_options(question_index=question_index)]

    def get_consensus(self, question_index=0, consensus_type='Single'):
        if consensus_type == 'Single':
            return self.consensus(question_index=question_index)
        elif consensus_type == 'Ranked':
            return self.ranked_consensus(question_index=question_index)
        else:
            raise NotImplementedError('Unknown consensus_type: %s' % consensus_type)

    def results_info(self, results, question_index=0):
        """
        Print out the results of the hivemind
        """
        ret = 'Hivemind id: ' + self.hivemind_id + '\n'
        ret += self._hivemind_issue.questions[question_index]
        ret += '\nResults:\n========'
        i = 0

        # if selection mode is 'Exclude', we must exclude previously selected options from the results
        if self._hivemind_issue.on_selection == 'Exclude':
            selected_options = [selection[question_index] for selection in self.selected]
            available_options = [option_hash for option_hash in self.options if option_hash not in selected_options]
        else:
            available_options = self.options

        for option_hash, option_result in sorted(results.items(), key=lambda x: x[1]['score'], reverse=True):
            if option_hash not in available_options:
                continue

            i += 1
            option = HivemindOption(cid=option_hash)
            ret += '\n%s: (%g%%) : %s' % (i, round(option_result['score']*100, 2), option.value)

        ret += '\nContributions:'
        ret += '\n================'
        for opinionator, contribution in self.contributions(results=results, question_index=question_index).items():
            ret += '\n%s: %s' % (opinionator, contribution)
        ret += '\n================'

        return ret

    def contributions(self, results, question_index):
        deviances = {}
        total_deviance = 0
        multipliers = {}

        # sort the option hashes by highest score
        option_hashes_by_score = [option[0] for option in sorted(results.items(), key=lambda x: x[1]['score'], reverse=True)]

        # sort the opinionators by the timestamp of their opinion
        opinionators_by_timestamp = [opinionator for opinionator, opinion_data in sorted(self.opinions[question_index].items(), key=lambda x: x[1]['timestamp'])]

        for i, opinionator in enumerate(opinionators_by_timestamp):
            deviance = 0
            opinion = HivemindOpinion(cid=self.opinions[question_index][opinionator]['opinion_cid'])

            # Todo, something is wrong here messing up the contribution scores
            #
            # Calculate the 'early bird' multiplier (whoever gives their opinion first gets the highest multiplier, value is between 0 and 1), if opinion is an empty list, then multiplier is 0
            multipliers[opinionator] = 1 - (i/float(len(opinionators_by_timestamp))) if len(opinion.ranking.get(options=self.get_options())) > 0 else 0

            # Calculate the deviance of the opinion, the closer the opinion is to the final result, the lower the deviance
            for j, option_hash in enumerate(option_hashes_by_score):
                if option_hash in opinion.ranking.get(options=self.get_options()):
                    deviance += abs(j - opinion.ranking.get(options=self.get_options()).index(option_hash))
                else:
                    deviance += len(option_hashes_by_score)-j

            total_deviance += deviance
            deviances[opinionator] = deviance

        if total_deviance != 0:  # to avoid divide by zero
            contributions = {opinionator: (1-(deviances[opinionator]/float(total_deviance)))*multipliers[opinionator] for opinionator in deviances}
        else:  # everyone has perfect opinion, but contributions should still be multiplied by the 'early bird' multiplier
            contributions = {opinionator: 1*multipliers[opinionator] for opinionator in deviances}

        return contributions

    def select_consensus(self):
        """
        Mark the current consensus as being 'selected'

        :return: a list containing the option with highest consensus for each question
        """
        # Get the option hash with highest consensus for each question
        selection = [self.get_options(question_index=question_index)[0].cid() for question_index in range(len(self._hivemind_issue.questions))]
        self.selected.append(selection)

        if self._hivemind_issue.on_selection is None:
            return
        elif self._hivemind_issue.on_selection == 'Finalize':
            # The hivemind is final, no more options or opinions can be added
            self.final = True
        elif self._hivemind_issue.on_selection == 'Exclude':
            # The selected option is excluded from future results
            pass
        elif self._hivemind_issue.on_selection == 'Reset':
            # All opinions are reset
            self.opinions = [{}]
        else:
            raise NotImplementedError('Unknown selection mode: %s' % self._hivemind_issue.on_selection)

        self.save()
        return selection

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
            self.signatures[address] = {message: {signature: timestamp}}
        elif message not in self.signatures[address]:
            self.signatures[address].update({message: {signature: timestamp}})
        else:
            timestamps = [int(key) for key in self.signatures[address][message].values()]

            if timestamp > max(timestamps):
                self.signatures[address][message][signature] = timestamp
            else:
                raise Exception('Invalid timestamp: must be more recent than any previous signature timestamp')

    def update_participant_name(self, timestamp, name, address, signature):
        # Only need to update name if it is not known yet or if it has changed
        if address not in self.participants or name != self.participants[address]['name']:
            if verify_message(address=address, message='%s%s' % (timestamp, name), signature=signature) is True:
                # First try to add the signature, if the timestamp is not the most recent it will throw an exception
                # This is to prevent a reused signature attack
                try:
                    self.add_signature(address=address, timestamp=timestamp, message=name, signature=signature)
                except Exception as ex:
                    raise Exception('%s' % ex)

                self.participants[address] = {'name': name}
            else:
                raise Exception('Invalid signature')