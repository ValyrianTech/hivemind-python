#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Ranking:
    def __init__(self):
        self.fixed = None
        self.auto = None
        self.type = None

    def set_fixed(self, ranked_choice):
        """
        Set a fixed ranked choice

        :param ranked_choice: List - a list of option cids
        """
        self.fixed = ranked_choice
        self.type = 'fixed'

    def set_auto_high(self, choice):
        """
        Set the ranking to auto high, meaning the ranking will be calculated at runtime by given options, ordered by the values closest to preferred choice
        In case 2 options are equally distant to preferred choice, the higher option has preference

        :param choice: String - option cid of the preferred choice
        """
        self.auto = choice
        self.type = 'auto_high'

    def set_auto_low(self, choice):
        """
        Set the ranking to auto high, meaning the ranking will be calculated at runtime by given options, ordered by the values closest to preferred choice
        In case 2 options are equally distant to preferred choice, the lower option has preference

        :param choice: String - option cid of the preferred choice
        """
        self.auto = choice
        self.type = 'auto_low'

    def get(self, options=None):
        """
        Get the ranked choices

        :param options: List of HivemindOptions, only needed for auto ranking
        :return: A list of option cids
        """
        if self.type == 'fixed':
            return self.fixed
        elif self.type == 'auto_high' or self.type == 'auto_low':
            if options is None:
                raise Exception('Options are required for auto ranking')

            ranked_choice = []
            for option in options:
                if option.value == self.auto:
                    ranked_choice.append(option.cid)

            return ranked_choice
        else:
            return []

    def to_dict(self):
        """
        Convert ranking settings to dict to store in a ipfs object

        :return: Dict - ranking settings as a dict
        """
        ranking_dict = {'type': self.type}
        if self.type == 'fixed':
            ranking_dict['fixed'] = self.fixed
        elif self.type == 'auto_high' or self.type == 'auto_low':
            ranking_dict['auto'] = self.auto

        return ranking_dict
