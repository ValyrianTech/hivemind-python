#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional, Dict, Any, List
from ipfs_dict_chain.IPFSDict import IPFSDict
from .ranking import Ranking
from .option import HivemindOption


class HivemindOpinion(IPFSDict):
    """A class representing a voter's opinion in the Hivemind protocol.

    This class handles the storage and management of a voter's ranked choices
    for a particular hivemind issue question.

    :ivar hivemind_id: The IPFS hash of the associated hivemind issue
    :type hivemind_id: Optional[str]
    :ivar question_index: The index of the question this opinion is for
    :type question_index: int
    :ivar ranking: The ranking of options for this opinion
    :type ranking: Ranking
    """

    def __init__(self, cid: Optional[str] = None) -> None:
        """Initialize a new HivemindOpinion.

        :param cid: The IPFS hash of the Opinion object
        :type cid: Optional[str]
        """
        self.hivemind_id: Optional[str] = None
        self.question_index: int = 0
        self.ranking: Ranking = Ranking()

        super(HivemindOpinion, self).__init__(cid=cid)

    def get(self) -> Dict[str, Any]:
        """Get a JSON-serializable representation of this opinion.

        Overrides the get method because it contains a non-JSON-serializable object.

        :return: Dictionary containing the opinion data
        :rtype: Dict[str, Any]
        """
        return {
            'hivemind_id': self.hivemind_id,
            'question_index': self.question_index,
            'ranking': self.ranking.to_dict()
        }

    def set_question_index(self, question_index: int) -> None:
        """Set the question index for this opinion.

        :param question_index: The index of the question
        :type question_index: int
        """
        self.question_index = question_index

    def info(self) -> str:
        """Get the details of this Opinion object in string format.

        :return: Formatted string containing the opinion details
        :rtype: str
        """
        ret = ''
        for i, option_hash in enumerate(self.ranking.get()):
            option = HivemindOption(cid=option_hash)
            ret += '\n%s: %s' % (i+1, option.value)
        return ret

    def load(self, cid: str) -> None:
        """Load the opinion from IPFS.

        This method handles the conversion of the stored ranking dictionary
        back into a Ranking object.

        :param cid: The IPFS hash to load
        :type cid: str
        """
        super(HivemindOpinion, self).load(cid=cid)

        # ipfs will store ranking as a dict, but we need to convert it back to a Ranking() object
        if isinstance(self.ranking, dict):
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