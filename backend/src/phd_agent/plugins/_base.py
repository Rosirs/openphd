"""Re-export BaseAgent for plugin authors. Kept thin per spec §4.4."""
from phd_agent.core.contract import BaseAgent

__all__ = ["BaseAgent"]
