#!/usr/bin/env python
# -*- coding: utf-8 -*-
from helpers.ipfshelpers import IPFSDict
from .ranking import Ranking


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
        return self.ranking.get()

    def set_question_index(self, question_index):
        self.question_index = question_index

    def info(self):
        """
        Get the details of this Opinion object in string format

        :return: the details of this Opinion object in string format
        """
        info_string = 'Opinion:\n'
        info_string += '  Question index: %s\n' % self.question_index
        info_string += '  Ranking: %s\n' % self.ranking.get()

        return info_string
