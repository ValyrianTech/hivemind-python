#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional, Dict, Any
from ipfs_dict_chain.IPFSDict import IPFSDict
from .ranking import Ranking


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
        ret = f'opinion info: {self.hivemind_id} question {self.question_index} -> {str(self.ranking.to_dict())}'

        return ret

    def load(self, cid: str) -> None:
        """Load the opinion from IPFS.

        This method handles the conversion of the stored ranking dictionary
        back into a Ranking object.

        :param cid: The IPFS hash to load
        :type cid: str
        """
        super(HivemindOpinion, self).load(cid=cid)

        # Initialize a new Ranking object if ranking is None
        if self.ranking is None:
            self.ranking = Ranking()
            return

        # Handle the case where ranking is a list (legacy format)
        if isinstance(self.ranking, list):
            ranked_choice = self.ranking
            self.ranking = Ranking()
            self.ranking.set_fixed(ranked_choice=ranked_choice)
            return

        # ipfs will store ranking as a dict, but we need to convert it back to a Ranking() object
        if isinstance(self.ranking, dict):
            ranking_dict = self.ranking  # Store the dict temporarily
            self.ranking = Ranking()  # Create new Ranking object
            
            if 'fixed' in ranking_dict:
                self.ranking.set_fixed(ranked_choice=ranking_dict['fixed'])
            elif 'auto_high' in ranking_dict:
                self.ranking.set_auto_high(choice=ranking_dict['auto_high'])
            elif 'auto_low' in ranking_dict:
                self.ranking.set_auto_low(choice=ranking_dict['auto_low'])
            # If none of the expected keys are present, ranking will remain empty

    def __repr__(self):
        return self._cid.replace('/ipfs/', '')