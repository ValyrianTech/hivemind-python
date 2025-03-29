#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Dict, Any
from ipfs_dict_chain.IPFSDict import IPFSDict
from .ranking import Ranking


class HivemindOpinion(IPFSDict):
    """A class representing a voter's opinion in the Hivemind protocol.

    This class handles the storage and management of a voter's ranked choices
    for a particular hivemind issue question.

    :ivar hivemind_id: The IPFS hash of the associated hivemind issue
    :vartype hivemind_id: str | None
    :ivar question_index: The index of the question this opinion is for
    :vartype question_index: int
    :ivar ranking: The ranking of options for this opinion
    :vartype ranking: Ranking
    """

    def __init__(self, cid: str | None = None) -> None:
        """Initialize a new HivemindOpinion.

        :param cid: The IPFS hash of the Opinion object
        :type cid: str | None
        :return: None
        """
        self.hivemind_id: str | None = None
        self.question_index: int = 0
        self.ranking: Ranking = Ranking()

        super(HivemindOpinion, self).__init__(cid=cid)

    def to_dict(self) -> Dict[str, Any]:
        """Get a JSON-serializable representation of this opinion.

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
        :return: None
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
        :return: None
        """
        super(HivemindOpinion, self).load(cid=cid)

        # Initialize a new Ranking object if ranking is None
        if self.ranking is None:
            self.ranking = Ranking()
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

    def __repr__(self) -> str:
        """Return a string representation of the opinion.

        :return: The IPFS CID of the opinion without the '/ipfs/' prefix
        :rtype: str
        """
        return self._cid.replace('/ipfs/', '')

    def save(self) -> str:
        """Save the opinion to IPFS.

        This method handles the conversion of the Ranking object into a JSON-serializable
        dictionary before saving the opinion to IPFS.

        :return: The IPFS hash of the saved opinion
        :rtype: str
        """
        # Convert the ranking object to a dict before saving
        tmp_ranking = self.ranking if self.ranking is not None else Ranking()
        if isinstance(self.ranking, Ranking):
            self.ranking = self.ranking.to_dict()
        opinion_cid = super(HivemindOpinion, self).save()
        # Restore the ranking object
        self.ranking = tmp_ranking

        return opinion_cid
