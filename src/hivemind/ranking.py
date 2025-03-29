#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import List, Dict, Any
from .option import HivemindOption
import logging

LOG = logging.getLogger(__name__)


class Ranking:
    """A class for managing ranked choice voting.

    This class handles both fixed and automatic ranking of options in the Hivemind protocol.
    It supports different ranking strategies including fixed rankings and automatic rankings
    based on proximity to a preferred choice.

    :ivar fixed: List of fixed ranked choices
    :vartype fixed: List[str] | None
    :ivar auto: The preferred choice for automatic ranking
    :vartype auto: str | None
    :ivar type: The type of ranking ('fixed', 'auto_high', or 'auto_low')
    :vartype type: str | None
    """

    def __init__(self) -> None:
        """Initialize a new Ranking instance.
        
        :return: None
        """
        self.fixed: List[str] | None = None
        self.auto: str | None = None
        self.type: str | None = None

    def set_fixed(self, ranked_choice: List[str]) -> None:
        """Set a fixed ranked choice.

        :param ranked_choice: A list of option cids in order of preference
        :type ranked_choice: List[str]
        :raises Exception: If ranked_choice is invalid
        :return: None
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
        :return: None
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
        :return: None
        """
        if not isinstance(choice, str):
            raise Exception('Invalid choice for auto ranking')

        self.auto = choice
        self.type = 'auto_low'
        self.fixed = None

    def get(self, options: List[HivemindOption] | None = None) -> List[str]:
        """Get the ranked choices.

        :param options: List of HivemindOptions, required for auto ranking
        :type options: List[HivemindOption] | None
        :return: A list of option cids in ranked order
        :rtype: List[str]
        :raises Exception: If ranking is not set or options are invalid for auto ranking
        """
        ranking = None
        if self.type is None:
            LOG.error('No ranking was set')
            raise Exception('No ranking was set')
        elif self.type == 'fixed':
            ranking = self.fixed
        elif self.type in ['auto_high', 'auto_low']:
            # auto complete the ranking based on given options
            if options is None:
                LOG.error('No options given for auto ranking')
                raise Exception('No options given for auto ranking')
            elif not isinstance(options, list) or not all(isinstance(option, HivemindOption) for option in options):
                LOG.error(f'Invalid list of options given for auto ranking: {options}')
                raise Exception('Invalid list of options given for auto ranking')

            try:
                choice = HivemindOption(cid=self.auto)

                if self.type == 'auto_high':
                    ranking = [option.cid().replace('/ipfs/', '') for option in sorted(options, key=lambda x: (abs(x.value - choice.value), -x.value))]
                elif self.type == 'auto_low':
                    ranking = [option.cid().replace('/ipfs/', '') for option in sorted(options, key=lambda x: (abs(x.value - choice.value), x.value))]

                LOG.info(f"Calculated ranking {self.type}: {ranking}")
            except Exception as e:
                LOG.error(f"Error during auto ranking calculation: {str(e)}")
                raise Exception(f"Error during auto ranking calculation: {str(e)}")

        return ranking

    def to_dict(self) -> Dict[str, Any]:
        """Convert ranking settings to dict for IPFS storage.

        :return: Ranking settings as a Dict
        :rtype: Dict[str, Any]
        """
        if self.type == 'fixed':
            return {'fixed': self.fixed}
        elif self.type == 'auto_high':
            return {'auto_high': self.auto}
        elif self.type == 'auto_low':
            return {'auto_low': self.auto}
