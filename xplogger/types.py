"""Types used in the package."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Union

NumType = Union[int, float]
ValueType = Union[str, int, float]
LogType = Dict[str, Any]
ConfigType = LogType
MetricType = LogType
InfoType = LogType
ParseLineFunctionType = Callable[[str], Optional[LogType]]
ComparisonOpType = Callable[[ValueType, ValueType], bool]
KeyMapType = Dict[str, str]
