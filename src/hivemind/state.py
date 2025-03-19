#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import List, Dict, Optional, Any
from ipfs_dict_chain.IPFSDictChain import IPFSDictChain
from itertools import combinations
import logging

from .issue import HivemindIssue
from .option import HivemindOption
from .opinion import HivemindOpinion
from bitcoin.signmessage import VerifyMessage, BitcoinMessage

LOG = logging.getLogger(__name__)


def verify_message(message: str, address: str, signature: str) -> bool:
    """Verify a signed message using Bitcoin's message verification.
    
    Args:
        message: The message that was signed
        address: The Bitcoin address that signed the message
        signature: The base64-encoded signature
        
    Returns:
        bool: True if the signature is valid, False otherwise
    """
    try:
        return VerifyMessage(address, BitcoinMessage(message), signature)
    except Exception as ex:
        LOG.error('Error verifying message: %s' % ex)
        return False


class HivemindState(IPFSDictChain):
    """A class representing the current state of a Hivemind voting issue.

    This class manages the state of a voting issue, including options, opinions,
    and voting results. It handles the addition of new options and opinions,
    calculates voting results, and manages restrictions on who can vote.

    :ivar hivemind_id: The IPFS hash of the associated hivemind issue
    :type hivemind_id: str | None
    :ivar _hivemind_issue: The associated hivemind issue object
    :type _hivemind_issue: HivemindIssue | None
    :ivar option_cids: List of option CIDs
    :type option_cids: List[str]
    :ivar opinion_cids: List of dictionaries containing opinions for each question
    :type opinion_cids: List[Dict[str, Any]]
    :ivar signatures: Dictionary mapping addresses to their signatures
    :type signatures: Dict[str, str]
    :ivar participants: Dictionary mapping addresses to their participation data
    :type participants: Dict[str, Any]
    :ivar selected: List of options that have been selected
    :type selected: List[str]
    :ivar final: Whether the hivemind is finalized
    :type final: bool
    """

    def __init__(self, cid: Optional[str] = None) -> None:
        """Initialize a new HivemindState.

        :param cid: The IPFS multihash of the state
        :type cid: Optional[str]
        """
        self.hivemind_id: str | None = None
        self._hivemind_issue: HivemindIssue | None = None
        self.option_cids: List[str] = []
        self.opinion_cids: List[Dict[str, Any]] = [{}]
        self.signatures: Dict[str, str] = {}
        self.participants: Dict[str, Any] = {}
        self.selected: List[str] = []
        self.final: bool = False

        super(HivemindState, self).__init__(cid=cid)
        self._options: List[HivemindOption] = [HivemindOption(cid=option_cid) for option_cid in self.option_cids]

        self._opinions: List = []
        self._rankings: List = []
        for question_index in range(len(self.opinion_cids)):
            opinions = []
            rankings = {}
            for participant, opinion_data in self.opinion_cids[question_index].items():
                opinion = HivemindOpinion(cid=opinion_data['opinion_cid'])
                opinions.append(opinion)
                rankings[opinion_data['opinion_cid']] = opinion.ranking.get(options=self._options)

            self._opinions.append(opinions)
            self._rankings.append(rankings)

    def hivemind_issue(self) -> Optional[HivemindIssue]:
        """Get the associated hivemind issue.

        :return: The associated hivemind issue object
        :rtype: Optional[HivemindIssue]
        """
        return self._hivemind_issue

    def get_options(self) -> List[HivemindOption]:
        """Get list of hivemind options.

        :return: List of HivemindOption objects
        :rtype: List[HivemindOption]
        """
        return self._options

    def set_hivemind_issue(self, issue_hash: str) -> None:
        """Set the associated hivemind issue.

        :param issue_hash: IPFS hash of the hivemind issue
        :type issue_hash: str
        """
        self.hivemind_id = issue_hash
        self._hivemind_issue = HivemindIssue(cid=self.hivemind_id)
        self.opinion_cids = [{} for _ in range(len(self._hivemind_issue.questions))]

    def add_predefined_options(self) -> Dict[str, Dict[str, Any]]:
        """Add predefined options to the hivemind state.

        :return: Dictionary mapping option CIDs to their data
        :rtype: Dict[str, Dict[str, Any]]
        """
        options = {}

        if self._hivemind_issue.answer_type == 'Bool':
            true_option = HivemindOption()
            true_option.set_hivemind_issue(self.hivemind_id)
            true_option.text = self._hivemind_issue.constraints['true_value']
            true_option.set(value=True)
            true_option_hash = true_option.save()
            if isinstance(true_option, HivemindOption) and true_option.valid():
                if true_option_hash not in self.option_cids:
                    self.option_cids.append(true_option_hash)
                    options[true_option_hash] = {'value': true_option.value, 'text': true_option.text}

            false_option = HivemindOption()
            false_option.set_hivemind_issue(self.hivemind_id)
            false_option.text = self._hivemind_issue.constraints['false_value']
            false_option.set(value=False)
            false_option_hash = false_option.save()
            if isinstance(false_option, HivemindOption) and false_option.valid():
                if false_option_hash not in self.option_cids:
                    self.option_cids.append(false_option_hash)
                    options[false_option_hash] = {'value': false_option.value, 'text': false_option.text}

        elif 'choices' in self._hivemind_issue.constraints:
            for choice in self._hivemind_issue.constraints['choices']:
                option = HivemindOption()
                option.set_hivemind_issue(self.hivemind_id)
                option.text = choice['text']
                option.set(value=choice['value'])
                option_hash = option.save()
                if isinstance(option, HivemindOption) and option.valid():
                    if option_hash not in self.option_cids:
                        self.option_cids.append(option_hash)
                        options[option_hash] = {'value': option.value, 'text': option.text}

        return options

    def load(self, cid: str) -> None:
        """Load the hivemind state from IPFS.

        :param cid: The IPFS multihash of the state
        :type cid: str
        """
        super(HivemindState, self).load(cid=cid)
        self._hivemind_issue = HivemindIssue(cid=self.hivemind_id)

        # Only initialize opinions if they don't exist
        if not hasattr(self, 'opinion_cids') or self.opinion_cids is None:
            self.opinion_cids = [{} for _ in range(len(self._hivemind_issue.questions))]

    def add_option(self, timestamp: int, option_hash: str, address: Optional[str] = None, signature: Optional[str] = None) -> None:
        """Add an option to the hivemind state.

        :param timestamp: Unix timestamp
        :type timestamp: int
        :param option_hash: The IPFS multihash of the option
        :type option_hash: str
        :param address: The address that supports the option (optional)
        :type address: Optional[str]
        :param signature: The signature of the message (optional)
        :type signature: Optional[str]
        :raises Exception: If the option is invalid or restrictions are not met
        """
        if self.final is True:
            raise Exception('Can not add option: hivemind issue is finalized')

        if not isinstance(self._hivemind_issue, HivemindIssue):
            return

        # Check for address restrictions
        has_address_restrictions = (self._hivemind_issue.restrictions is not None and
                                    'addresses' in self._hivemind_issue.restrictions)

        # If we have address restrictions, require address and signature
        if has_address_restrictions:
            if address is None or signature is None:
                raise Exception('Can not add option: no address or signature given')
            elif address not in self._hivemind_issue.restrictions['addresses']:
                raise Exception('Can not add option: there are address restrictions on this hivemind issue and address %s is not allowed to add options' % address)

        # If address and signature are provided, verify the signature regardless of restrictions
        if address is not None and signature is not None:
            if not verify_message(message='%s%s' % (timestamp, option_hash), address=address, signature=signature):
                raise Exception('Can not add option: Signature is not valid')

        if self._hivemind_issue.restrictions is not None and 'options_per_address' in self._hivemind_issue.restrictions:
            number_of_options = len(self.options_by_participant(address=address))
            if number_of_options >= self._hivemind_issue.restrictions['options_per_address']:
                raise Exception('Can not add option: address %s already added too many options: %s' % (address, number_of_options))

        option = self.get_option(cid=option_hash)
        if isinstance(option, HivemindOption) and option.valid():
            if option_hash in self.option_cids:
                raise Exception("Option already exists")
            # Only add signature if both address and signature are provided
            if address is not None and signature is not None:
                self.add_signature(address=address, timestamp=timestamp, message=option_hash, signature=signature)
            self.option_cids.append(option_hash)

    def options_by_participant(self, address: str) -> List[str]:
        """Get the options added by a participant.

        :param address: The participant's address
        :type address: str
        :return: List of option CIDs
        :rtype: List[str]
        """
        # Track which options were added by this address by checking signatures
        participant_options = []
        if address in self.signatures:
            for option_hash in self.option_cids:
                # Check if this address has signed this option
                if option_hash in self.signatures[address]:
                    participant_options.append(option_hash)
        return participant_options

    def add_opinion(self, timestamp: int, opinion_hash: str, signature: str, address: str) -> None:
        """Add an opinion to the hivemind state.

        :param timestamp: Unix timestamp
        :type timestamp: int
        :param opinion_hash: The IPFS multihash of the opinion
        :type opinion_hash: str
        :param signature: The signature of the message
        :type signature: str
        :param address: The address of the opinionator
        :type address: str
        :raises Exception: If the opinion is invalid or restrictions are not met
        """
        if self.final is True:
            return

        opinion = self.get_opinion(cid=opinion_hash)
        if not verify_message(address=address, message='%s%s' % (timestamp, opinion_hash), signature=signature):
            raise Exception('Signature is invalid')

        # Check address restrictions
        if self._hivemind_issue.restrictions is not None and 'addresses' in self._hivemind_issue.restrictions:
            if address not in self._hivemind_issue.restrictions['addresses']:
                raise Exception('Can not add opinion: there are address restrictions on this hivemind issue and address %s is not allowed to add opinions' % address)

        # Log the opinion details for debugging
        LOG.info(f"Opinion details - hivemind_id: {opinion.hivemind_id}, question_index: {opinion.question_index}")
        LOG.info(f"Opinion ranking type: {type(opinion.ranking)}")
        if hasattr(opinion.ranking, 'type'):
            LOG.info(f"Ranking type: {opinion.ranking.type}")
        if hasattr(opinion.ranking, 'fixed'):
            LOG.info(f"Ranking fixed: {opinion.ranking.fixed}")
        if hasattr(opinion.ranking, 'auto'):
            LOG.info(f"Ranking auto: {opinion.ranking.auto}")

        # Get the ranking as a list of options
        try:
            # For auto rankings, we need to calculate the ranking based on the options
            LOG.info(f"Getting ranking options with {len(self._options)} available options")
            ranking_options = opinion.ranking.get(options=self._options)
            LOG.info(f"Ranking options: {ranking_options}")
        except Exception as e:
            LOG.error(f"Error getting ranking options: {str(e)}")
            raise Exception(f"Error validating opinion: {str(e)}")

        # Check if all options in the ranking exist in the state
        # Strip '/ipfs/' prefix from option hashes if present for comparison
        normalized_ranking_options = [option_hash.replace('/ipfs/', '') if option_hash.startswith('/ipfs/') else option_hash
                                      for option_hash in ranking_options]
        normalized_state_options = [option_hash.replace('/ipfs/', '') if option_hash.startswith('/ipfs/') else option_hash
                                    for option_hash in self.option_cids]

        LOG.info(f"Normalized ranking options: {normalized_ranking_options}")
        LOG.info(f"Normalized state options: {normalized_state_options}")

        invalid_options = [option_hash for option_hash in normalized_ranking_options
                           if option_hash not in normalized_state_options]
        if invalid_options:
            LOG.error(f"Invalid options found: {invalid_options}")
            LOG.error(f"Available options: {normalized_state_options}")
            raise Exception(f"Opinion is invalid: contains options that do not exist in the hivemind state: {invalid_options}")

        if not invalid_options:
            try:
                self.add_signature(address=address, timestamp=timestamp, message=opinion_hash, signature=signature)
            except Exception as ex:
                raise Exception('Invalid signature: %s' % ex)

            # Ensure we have enough dictionaries in the opinions list
            while len(self.opinion_cids) <= opinion.question_index:
                self.opinion_cids.append({})

            self.opinion_cids[opinion.question_index][address] = {'opinion_cid': opinion_hash, 'timestamp': timestamp}

            while len(self._rankings) <= opinion.question_index:
                self._rankings.append({})

            self._rankings[opinion.question_index][opinion_hash] = ranking_options

    def get_weight(self, opinionator: str) -> float:
        """Get the weight of an opinion.

        :param opinionator: The participant's address
        :type opinionator: str
        :return: The weight of the opinion
        :rtype: float
        """
        weight = 1.0

        if self._hivemind_issue.restrictions is not None and 'addresses' in self._hivemind_issue.restrictions:
            weight = 0.0  # Default weight if there are addresses in restrictions
            for address in self._hivemind_issue.restrictions['addresses']:
                if address.startswith(opinionator):
                    weight = 1.0
                    # Check if the address has a weight specification (e.g., "address@2")
                    if '@' in address:
                        parts = address.split('@', 1)
                        try:
                            specified_weight = float(parts[1].strip())
                            if specified_weight >= 0:
                                weight = specified_weight
                        except ValueError:
                            # If weight parsing fails, use default weight
                            pass
                    break

        return weight

    def info(self) -> str:
        """Get the information of the hivemind.

        :return: A string containing the information of the hivemind
        :rtype: str
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

    def options_info(self) -> str:
        """Get the information of the options.

        :return: A string containing the information of the options
        :rtype: str
        """
        ret = "Options"
        ret += "\n======="
        for i, option_hash in enumerate(self.option_cids):
            ret += '\nOption %s:' % (i + 1)
            option = self.get_option(cid=option_hash)
            ret += '\n' + option.info()
            ret += '\n'

        return ret

    def opinions_info(self, question_index: int = 0) -> str:
        """Get the information of the opinions.

        :param question_index: The index of the question (default=0)
        :type question_index: int
        :return: A string containing the information of the opinions
        :rtype: str
        """
        ret = "Opinions"
        ret += "\n========"
        # opinion_data is a list containing [opinion_hash, signature of '/ipfs/opinion_hash', timestamp]
        for opinionator, opinion_data in self.opinion_cids[question_index].items():
            ret += '\nTimestamp: %s' % opinion_data['timestamp']
            opinion = self.get_opinion(cid=opinion_data['opinion_cid'])
            ret += '\n' + opinion.info()
            ret += '\n'

        return ret

    def calculate_results(self, question_index: int = 0) -> Dict[str, Dict[str, float]]:
        """Calculate the results of the hivemind.

        :param question_index: Index of the question to calculate results for
        :type question_index: int
        :return: Dictionary mapping option CIDs to their scores
        :rtype: Dict[str, Dict[str, float]]
        :raises Exception: If question_index is invalid
        """
        # if selection mode is 'Exclude', we must exclude previously selected options from the results
        if self._hivemind_issue.on_selection == 'Exclude':
            selected_options = [selection[question_index] for selection in self.selected]
            available_options = [option_hash for option_hash in self.option_cids if option_hash not in selected_options]
        else:
            available_options = self.option_cids

        results = {option: {'win': 0, 'loss': 0, 'unknown': 0, 'score': 0} for option in available_options}

        for a, b in combinations(available_options, 2):
            for opinionator in self.opinion_cids[question_index]:
                winner = self.compare(a, b, self.opinion_cids[question_index][opinionator]['opinion_cid'])
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

    def get_score(self, option_hash: str, question_index: int = 0) -> float:
        """Get the score of an option.

        :param option_hash: The IPFS multihash of the option
        :type option_hash: str
        :param question_index: The index of the question (default=0)
        :type question_index: int
        :return: The score of the option
        :rtype: float
        """
        results = self.calculate_results(question_index=question_index)
        return results[option_hash]['score']

    def get_sorted_options(self, question_index: int = 0) -> List[HivemindOption]:
        """Get the sorted list of options.

        :param question_index: The index of the question (default=0)
        :type question_index: int
        :return: List of HivemindOption objects sorted by highest score
        :rtype: List[HivemindOption]
        """
        results = self.calculate_results(question_index=question_index)
        return [self.get_option(cid=option[0]) for option in sorted(results.items(), key=lambda x: x[1]['score'], reverse=True)]

    def consensus(self, question_index: int = 0) -> Any:
        """Get the consensus of the hivemind.

        :param question_index: The index of the question (default=0)
        :type question_index: int
        :return: The consensus value
        :rtype: Any
        """
        results = self.calculate_results(question_index=question_index)

        sorted_options = self.get_sorted_options(question_index=question_index)
        if len(sorted_options) == 0:
            return None
        elif len(sorted_options) == 1:
            return sorted_options[0].value
        # Make sure the consensus is not tied between the first two options
        elif len(sorted_options) >= 2 and results[sorted_options[0].cid().replace('/ipfs/', '')]['score'] > results[sorted_options[1].cid().replace('/ipfs/', '')]['score']:
            return sorted_options[0].value
        else:
            return None

    def ranked_consensus(self, question_index: int = 0) -> List[Any]:
        """Get the ranked consensus of the hivemind.

        :param question_index: The index of the question (default=0)
        :type question_index: int
        :return: List of consensus values
        :rtype: List[Any]
        """
        return [option.value for option in self.get_sorted_options(question_index=question_index)]

    def get_consensus(self, question_index: int = 0, consensus_type: str = 'Single') -> Any:
        """Get the consensus of the hivemind.

        :param question_index: The index of the question (default=0)
        :type question_index: int
        :param consensus_type: The type of consensus (default='Single')
        :type consensus_type: str
        :return: The consensus value
        :rtype: Any
        :raises NotImplementedError: If consensus_type is unknown
        """
        if consensus_type == 'Single':
            return self.consensus(question_index=question_index)
        elif consensus_type == 'Ranked':
            return self.ranked_consensus(question_index=question_index)
        else:
            raise NotImplementedError('Unknown consensus_type: %s' % consensus_type)

    def results_info(self, results: Dict[str, Dict[str, float]], question_index: int = 0) -> str:
        """Get the results information of the hivemind.

        :param results: Dictionary mapping option CIDs to their scores
        :type results: Dict[str, Dict[str, float]]
        :param question_index: The index of the question (default=0)
        :type question_index: int
        :return: A string containing the results information
        :rtype: str
        """
        ret = 'Hivemind id: ' + self.hivemind_id + '\n'
        ret += self._hivemind_issue.questions[question_index]
        ret += '\nResults:\n========'
        i = 0

        # if selection mode is 'Exclude', we must exclude previously selected options from the results
        if self._hivemind_issue.on_selection == 'Exclude':
            selected_options = [selection[question_index] for selection in self.selected]
            available_options = [option_hash for option_hash in self.option_cids if option_hash not in selected_options]
        else:
            available_options = self.option_cids

        for option_hash, option_result in sorted(results.items(), key=lambda x: x[1]['score'], reverse=True):
            if option_hash not in available_options:
                continue

            i += 1
            option = self.get_option(cid=option_hash)
            ret += '\n%s: (%g%%) : %s' % (i, round(option_result['score'] * 100, 2), option.value)

        ret += '\nContributions:'
        ret += '\n================'
        for opinionator, contribution in self.contributions(results=results, question_index=question_index).items():
            ret += '\n%s: %s' % (opinionator, contribution)
        ret += '\n================'

        return ret

    def contributions(self, results: Dict[str, Dict[str, float]], question_index: int = 0) -> Dict[str, float]:
        """Get the contributions of the participants.

        :param results: Dictionary mapping option CIDs to their scores
        :type results: Dict[str, Dict[str, float]]
        :param question_index: The index of the question (default=0)
        :type question_index: int
        :return: Dictionary mapping participant addresses to their contributions
        :rtype: Dict[str, float]
        """
        deviances = {}
        total_deviance = 0
        multipliers = {}

        # sort the option hashes by highest score
        option_hashes_by_score = [option[0] for option in sorted(results.items(), key=lambda x: x[1]['score'], reverse=True)]

        # sort the opinionators by the timestamp of their opinion
        opinionators_by_timestamp = [opinionator for opinionator, opinion_data in sorted(self.opinion_cids[question_index].items(), key=lambda x: x[1]['timestamp'])]

        for i, opinionator in enumerate(opinionators_by_timestamp):
            deviance = 0

            # Calculate the 'early bird' multiplier (whoever gives their opinion first gets the highest multiplier, value is between 0 and 1), if opinion is an empty list, then multiplier is 0
            ranking = self._rankings[question_index][self.opinion_cids[question_index][opinionator]['opinion_cid']]
            multipliers[opinionator] = 1 - (i / float(len(opinionators_by_timestamp))) if len(ranking) > 0 else 0

            # Calculate the deviance of the opinion, the closer the opinion is to the final result, the lower the deviance
            for j, option_hash in enumerate(option_hashes_by_score):
                if option_hash in ranking:
                    deviance += abs(j - ranking.index(option_hash))
                else:
                    deviance += len(option_hashes_by_score) - j

            total_deviance += deviance
            deviances[opinionator] = deviance

        if total_deviance != 0:  # to avoid divide by zero
            contributions = {opinionator: (1 - (deviances[opinionator] / float(total_deviance))) * multipliers[opinionator] for opinionator in deviances}
        else:  # everyone has perfect opinion, but contributions should still be multiplied by the 'early bird' multiplier
            contributions = {opinionator: 1 * multipliers[opinionator] for opinionator in deviances}

        return contributions

    def select_consensus(self) -> List[str]:
        """Select the consensus of the hivemind.

        :return: List of option CIDs that have been selected
        :rtype: List[str]
        """
        # Get the option hash with highest consensus for each question
        selection = [self.get_sorted_options(question_index=question_index)[0].cid() for question_index in range(len(self._hivemind_issue.questions))]
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
            self.opinion_cids = [{}]
        else:
            raise NotImplementedError('Unknown selection mode: %s' % self._hivemind_issue.on_selection)

        self.save()
        return selection

    def add_signature(self, address: str, timestamp: int, message: str, signature: str) -> None:
        """Add a signature to the hivemind state.

        :param address: The address of the participant
        :type address: str
        :param timestamp: Unix timestamp
        :type timestamp: int
        :param message: The message that was signed
        :type message: str
        :param signature: The signature of the message
        :type signature: str
        :raises Exception: If the signature is invalid
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

    def update_participant_name(self, timestamp: int, name: str, address: str, signature: str, message: str) -> None:
        """Update the name of a participant.

        :param timestamp: Unix timestamp
        :type timestamp: int
        :param name: The new name of the participant
        :type name: str
        :param address: The address of the participant
        :type address: str
        :param signature: The signature of the message
        :type signature: str
        :param message: The message that was signed
        :type message: str
        :raises Exception: If the signature is invalid
        """
        # Only need to update name if it is not known yet or if it has changed
        if address not in self.participants or name != self.participants[address]['name']:
            if verify_message(address=address, message=message, signature=signature) is True:
                # First try to add the signature, if the timestamp is not the most recent it will throw an exception
                # This is to prevent a reused signature attack
                try:
                    self.add_signature(address=address, timestamp=timestamp, message=name, signature=signature)
                except Exception as ex:
                    raise Exception('%s' % ex)

                self.participants[address] = {'name': name}
            else:
                raise Exception('Invalid signature')

    def compare(self, a, b, opinion_hash):
        """
        Helper function to compare 2 Option objects against each other based on a given Opinion

        :param a: The first Option object
        :param b: The second Option object
        :param opinion_hash: The Opinion object
        :return: The Option that is considered better by the Opinion
        If one of the Options is not given in the Opinion object, the other option wins by default
        If both Options are not in the Opinion object, None is returned
        """
        opinion = self.get_opinion(cid=opinion_hash)
        ranked_choice = self._rankings[opinion.question_index][opinion_hash]

        if a in ranked_choice and b in ranked_choice:
            if ranked_choice.index(a) < ranked_choice.index(b):
                return a
            elif ranked_choice.index(a) > ranked_choice.index(b):
                return b
        elif a in ranked_choice:
            return a
        elif b in ranked_choice:
            return b
        else:
            return None

    def get_option(self, cid: str) -> Optional[HivemindOption]:
        """Get an option by its CID.

        :param cid: The IPFS multihash of the option
        :type cid: str
        :return: The option object
        :rtype: Optional[HivemindOption]
        """
        # Check if the option is already in the state
        for option in self._options:
            if cid.replace('/ipfs/', '') in option.cid():
                return option

        return HivemindOption(cid=cid)

    def get_opinion(self, cid: str) -> Optional[HivemindOpinion]:
        """Get an opinion by its CID.

        :param cid: The IPFS multihash of the opinion
        :type cid: str
        :return: The opinion object
        :rtype: Optional[HivemindOpinion]
        """
        # Check if the opinion is already in the state
        for question_index in range(len(self._opinions)):
            for opinion in self._opinions[question_index]:
                if cid.replace('/ipfs/', '') in opinion.cid():
                    return opinion

        return HivemindOpinion(cid=cid)
