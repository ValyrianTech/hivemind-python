#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import List, Optional, Union
from .option import HivemindOption
import logging

LOG = logging.getLogger(__name__)

class Ranking:
    """A class for managing ranked choice voting.

    This class handles both fixed and automatic ranking of options in the Hivemind protocol.
    It supports different ranking strategies including fixed rankings and automatic rankings
    based on proximity to a preferred choice.

    :ivar fixed: List of fixed ranked choices
    :type fixed: Optional[List[str]]
    :ivar auto: The preferred choice for automatic ranking
    :type auto: Optional[str]
    :ivar type: The type of ranking ('fixed', 'auto_high', or 'auto_low')
    :type type: Optional[str]
    """

    def __init__(self) -> None:
        """Initialize a new Ranking instance."""
        self.fixed: Optional[List[str]] = None
        self.auto: Optional[str] = None
        self.type: Optional[str] = None

    def set_fixed(self, ranked_choice: List[str]) -> None:
        """Set a fixed ranked choice.

        :param ranked_choice: A list of option cids in order of preference
        :type ranked_choice: List[str]
        :raises Exception: If ranked_choice is invalid
        """
        if not isinstance(ranked_choice, list) or not all(isinstance(item, str) for item in ranked_choice):
            raise Exception('Invalid ranked choice')

        self.fixed = ranked_choice
        self.type = 'fixed'
        self.auto = None

    def set_auto_high(self, choice: str) -> None:
        """Set the ranking to auto high.
        
        The ranking will be calculated at runtime by given options, ordered by the values
        closest to preferred choice. In case 2 options are equally distant to preferred
        choice, the higher option has preference.

        :param choice: Option cid of the preferred choice
        :type choice: str
        :raises Exception: If choice is invalid
        """
        if not isinstance(choice, str):
            raise Exception('Invalid choice for auto ranking')

        self.auto = choice
        self.type = 'auto_high'
        self.fixed = None

    def set_auto_low(self, choice: str) -> None:
        """Set the ranking to auto low.
        
        The ranking will be calculated at runtime by given options, ordered by the values
        closest to preferred choice. In case 2 options are equally distant to preferred
        choice, the lower option has preference.

        :param choice: Option cid of the preferred choice
        :type choice: str
        :raises Exception: If choice is invalid
        """
        if not isinstance(choice, str):
            raise Exception('Invalid choice for auto ranking')

        self.auto = choice
        self.type = 'auto_low'
        self.fixed = None

    def get(self, options: Optional[List[HivemindOption]] = None) -> List[str]:
        """Get the ranked choices.

        :param options: List of HivemindOptions, required for auto ranking
        :type options: Optional[List[HivemindOption]]
        :return: A list of option cids in ranked order
        :rtype: List[str]
        :raises Exception: If ranking is not set or options are invalid for auto ranking
        """
        ranking = None
        if self.type is None:
            LOG.error('No ranking was set')
            raise Exception('No ranking was set')
        elif self.type == 'fixed':
            LOG.info(f"Using fixed ranking: {self.fixed}")
            ranking = self.fixed
        elif self.type in ['auto_high', 'auto_low']:
            LOG.info(f"Processing auto ranking type: {self.type}, preferred option: {self.auto}")
            # auto complete the ranking based on given options
            if options is None:
                LOG.error('No options given for auto ranking')
                raise Exception('No options given for auto ranking')
            elif not isinstance(options, list) or not all(isinstance(option, HivemindOption) for option in options):
                LOG.error(f'Invalid list of options given for auto ranking: {options}')
                raise Exception('Invalid list of options given for auto ranking')

            LOG.info(f"Auto ranking with {len(options)} options: {[option.cid() for option in options]}")
            
            try:
                choice = HivemindOption(cid=self.auto)
                LOG.info(f"Preferred choice loaded: {choice.cid()}, value: {choice.value}")
                
                if self.type == 'auto_high':
                    LOG.info("Using auto_high sorting (higher values preferred when equidistant)")
                    ranking = [option.cid() for option in sorted(options, key=lambda x: (abs(x.value - choice.value), -x.value))]
                elif self.type == 'auto_low':
                    LOG.info("Using auto_low sorting (lower values preferred when equidistant)")
                    ranking = [option.cid() for option in sorted(options, key=lambda x: (abs(x.value - choice.value), x.value))]
                
                LOG.info(f"Final auto ranking result: {ranking}")
            except Exception as e:
                LOG.error(f"Error during auto ranking calculation: {str(e)}")
                raise Exception(f"Error during auto ranking calculation: {str(e)}")

        return ranking

    def to_dict(self) -> dict:
        """Convert ranking settings to dict for IPFS storage.

        :return: Ranking settings as a dict
        :rtype: dict
        """
        if self.type == 'fixed':
            LOG.info(f"Converting fixed ranking to dict: {{'fixed': {self.fixed}}}")
            return {'fixed': self.fixed}
        elif self.type == 'auto_high':
            LOG.info(f"Converting auto_high ranking to dict: {{'auto_high': {self.auto}}}")
            return {'auto_high': self.auto}
        elif self.type == 'auto_low':
            LOG.info(f"Converting auto_low ranking to dict: {{'auto_low': {self.auto}}}")
            return {'auto_low': self.auto}