#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .option import HivemindOption

class Ranking(object):
    def __init__(self):
        self.fixed = None
        self.auto = None
        self.type = None

    def set_fixed(self, ranked_choice):
        """
        Set a fixed ranked choice

        :param ranked_choice: List - a list of option cids
        """
        if not isinstance(ranked_choice, list) or not all(isinstance(item, str) for item in ranked_choice):
            raise Exception('Invalid ranked choice')

        self.fixed = ranked_choice
        self.type = 'fixed'
        self.auto = None

    def set_auto_high(self, choice):
        """
        Set the ranking to auto high, meaning the ranking will be calculated at runtime by given options, ordered by the values closest to preferred choice
        In case 2 options are equally distant to preferred choice, the higher option has preference

        :param choice: String - option cid of the preferred choice
        """
        if not isinstance(choice, str):
            raise Exception('Invalid choice for auto ranking')

        self.auto = choice
        self.type = 'auto_high'
        self.fixed = None

    def set_auto_low(self, choice):
        """
        Set the ranking to auto high, meaning the ranking will be calculated at runtime by given options, ordered by the values closest to preferred choice
        In case 2 options are equally distant to preferred choice, the lower option has preference

        :param choice: String - option cid of the preferred choice
        """
        if not isinstance(choice, str):
            raise Exception('Invalid choice for auto ranking')

        self.auto = choice
        self.type = 'auto_low'
        self.fixed = None

    def get(self, options=None):
        """
        Get the ranked choices

        :param options: List of HivemindOptions, only needed for auto ranking
        :return: A list of option cids
        """
        ranking = None
        if self.type is None:
            raise Exception('No ranking was set')
        elif self.type == 'fixed':
            ranking = self.fixed
        elif self.type in ['auto_high', 'auto_low']:
            # auto complete the ranking based on given options
            if options is None:
                raise Exception('No options given for auto ranking')
            elif not isinstance(options, list) or not all(isinstance(option, HivemindOption) for option in options):
                raise Exception('Invalid list of options given for auto ranking')

            choice = HivemindOption(cid=self.auto)
            if self.type == 'auto_high':
                ranking = [option.cid() for option in sorted(options, key=lambda x: (abs(x.value - choice.value), -x.value))]

            elif self.type == 'auto_low':
                ranking = [option.cid() for option in sorted(options, key=lambda x: (abs(x.value - choice.value), x.value))]

        return ranking

    def to_dict(self):
        """
        Convert ranking settings to dict to store in a ipfs object

        :return: Dict - ranking settings as a dict
        """
        if self.type == 'fixed':
            return {'fixed': self.fixed}
        elif self.type == 'auto_high':
            return {'auto_high': self.auto}
        elif self.type == 'auto_low':
            return {'auto_low': self.auto}