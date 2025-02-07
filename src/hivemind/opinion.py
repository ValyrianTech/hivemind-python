#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ipfs_dict_chain.IPFSDict import IPFSDict
from .ranking import Ranking
from .option import HivemindOption


class HivemindOpinion(IPFSDict):
    def __init__(self, cid=None):
        """
        Constructor of the Opinion object

        :param cid: The ipfs hash of the Opinion object (optional)
        """
        self.hivemind_id = None
        self.question_index = 0
        self.ranking = Ranking()

        super(HivemindOpinion, self).__init__(cid=cid)

    def get(self):
        # override the get method because it contains a non JSON serializable object
        return {'hivemind_id': self.hivemind_id,
                'question_index': self.question_index,
                'ranking': self.ranking.to_dict()}

    def set_question_index(self, question_index):
        self.question_index = question_index

    # def get_unranked_option_ids(self):
    #     """
    #     Get the list of option ids that have not been ranked yet
    #
    #     :return: A list of option ids that have not been ranked yet
    #     """
    #     unranked = []
    #     for option_id in self._hivemind_issue.options:
    #         if option_id not in self.ranked_choice:
    #             unranked.append(option_id)
    #
    #     return sorted(unranked)

    def info(self):
        """
        Get the details of this Opinion object in string format

        :return: the details of this Opinion object in string format
        """
        ret = ''
        for i, option_hash in enumerate(self.ranking.get()):
            option = HivemindOption(cid=option_hash)
            ret += '\n%s: %s' % (i+1, option.value)

        return ret

    # def is_complete(self, ranked_choice=None):
    #     """
    #     Is this Opinion complete? Meaning are all option hashes present in the ranked_choice?
    #
    #     :param ranked_choice: An optional list of option hashes
    #     :return: True or False
    #     """
    #     if ranked_choice is None:
    #         ranked_choice = self.ranked_choice
    #
    #     return all(option_id in ranked_choice for option_id in self._hivemind_issue.options)

    # def valid(self):
    #     """
    #     Is the Opinion object a valid opinion? Meaning are all option hashes in the ranked_choice valid?
    #
    #     :return: True or False
    #     """
    #     if self.contains_duplicates() is True:
    #         return False
    #
    #     return True
    #
    # def contains_duplicates(self):
    #     """
    #     Does the Opinion object have duplicate option hashes in ranked_choice?
    #
    #     :return: True or False
    #     """
    #     return len([x for x in self.ranked_choice if self.ranked_choice.count(x) >= 2]) > 0

    def load(self, cid):
        super(HivemindOpinion, self).load(cid=cid)

        # ipfs will store ranking as a dict, but we need to convert it back to a Ranking() object
        if not isinstance(self.ranking, dict):
            return

        if 'fixed' in self.ranking:
            ranked_choice = self.ranking['fixed']
            self.ranking = Ranking()
            self.ranking.set_fixed(ranked_choice=ranked_choice)
        elif 'auto_high' in self.ranking:
            choice = self.ranking['auto_high']
            self.ranking = Ranking()
            self.ranking.set_auto_high(choice=choice)
        elif 'auto_low' in self.ranking:
            choice = self.ranking['auto_low']
            self.ranking = Ranking()
            self.ranking.set_auto_low(choice=choice)