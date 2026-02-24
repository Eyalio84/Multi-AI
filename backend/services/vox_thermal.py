"""VOX Thermal Monitor — device temperature tracking for Android/Termux.

Reads battery temperature via termux-battery-status command and provides
warnings when the device is getting too hot during sustained voice sessions.
"""
import asyncio
import json
from typing import Optional


class ThermalMonitor:
    """Monitor device temperature via Termux battery API."""

    def __init__(self, threshold: float = 42.0):
        self.threshold = threshold
        self._last_reading: Optional[dict] = None

    async def get_temperature(self) -> dict:
        """Read battery temperature via Termux API.

        Returns:
            dict with temperature (float), status (str), health (str)
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                "termux-battery-status",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5.0)
            data = json.loads(stdout.decode())
            reading = {
                "temperature": data.get("temperature", 0),
                "status": data.get("status", "unknown"),
                "health": data.get("health", "unknown"),
                "percentage": data.get("percentage", -1),
                "plugged": data.get("plugged", "unknown"),
            }
            self._last_reading = reading
            return reading
        except asyncio.TimeoutError:
            return self._fallback("timeout")
        except FileNotFoundError:
            return self._fallback("termux-api not installed")
        except json.JSONDecodeError:
            return self._fallback("invalid response")
        except Exception as e:
            return self._fallback(str(e))

    def _fallback(self, reason: str) -> dict:
        return {
            "temperature": 0,
            "status": "unavailable",
            "health": "unknown",
            "percentage": -1,
            "plugged": "unknown",
            "error": reason,
        }

    async def check(self) -> dict:
        """Check temperature and return with warning flag."""
        info = await self.get_temperature()
        temp = info.get("temperature", 0)
        warning = temp >= self.threshold if temp > 0 else False
        suggestion = ""
        if warning:
            if temp >= 45:
                suggestion = "Device is very hot. Consider pausing the voice session to cool down."
            else:
                suggestion = "Device is warm. Monitor closely."

        return {
            **info,
            "warning": warning,
            "threshold": self.threshold,
            "suggestion": suggestion,
        }


# Singleton
thermal_monitor = ThermalMonitor()
