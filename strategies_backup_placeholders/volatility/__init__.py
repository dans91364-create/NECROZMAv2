"""
Volatility Strategies

This category contains 24 volatility strategies.
"""

from .atr_breakout import AtrBreakout
from .bollinger_width import BollingerWidth
from .keltner_width import KeltnerWidth
from .donchian_breakout import DonchianBreakout
from .chaikin_volatility import ChaikinVolatility
from .historical_volatility import HistoricalVolatility
from .std_breakout import StdBreakout
from .atr_channel import AtrChannel
from .volatility_ratio import VolatilityRatio
from .mass_index import MassIndex
from .ulcer_index import UlcerIndex
from .rvi_volatility import RviVolatility
from .intraday_volatility import IntradayVolatility
from .parkinson_volatility import ParkinsonVolatility
from .garman_klass import GarmanKlass
from .rogers_satchell import RogersSatchell
from .yang_zhang import YangZhang
from .close_to_close import CloseToClose
from .true_range import TrueRange
from .normalized_atr import NormalizedAtr
from .volatility_stop import VolatilityStop
from .chandelier_exit import ChandelierExit
from .atr_trailing import AtrTrailing
from .volatility_squeeze import VolatilitySqueeze

__all__ = ['AtrBreakout', 'BollingerWidth', 'KeltnerWidth', 'DonchianBreakout', 'ChaikinVolatility', 'HistoricalVolatility', 'StdBreakout', 'AtrChannel', 'VolatilityRatio', 'MassIndex', 'UlcerIndex', 'RviVolatility', 'IntradayVolatility', 'ParkinsonVolatility', 'GarmanKlass', 'RogersSatchell', 'YangZhang', 'CloseToClose', 'TrueRange', 'NormalizedAtr', 'VolatilityStop', 'ChandelierExit', 'AtrTrailing', 'VolatilitySqueeze']
