import os
import time
import asyncio
import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


class KeepAliveManager:
    """
    Background keep-alive service for hosting environments like Render free tier.
    Pings the public external URL if no incoming requests have occurred within
    the configured idle interval (default 30s), resetting the platform's sleep timer.
    """

    def __init__(self):
        self._last_activity: float = time.time()
        self._task: Optional[asyncio.Task] = None
        self._is_running: bool = False

    def record_activity(self) -> None:
        """Call whenever an incoming non-ping request arrives."""
        self._last_activity = time.time()

    @property
    def target_url(self) -> Optional[str]:
        """
        Public URL of the backend.
        Render automatically supplies RENDER_EXTERNAL_URL (e.g. https://service.onrender.com).
        Can be overridden via SELF_PING_URL or BACKEND_URL.
        """
        url = (
            os.getenv("SELF_PING_URL")
            or os.getenv("RENDER_EXTERNAL_URL")
            or os.getenv("BACKEND_URL")
        )
        if url:
            url = url.strip().rstrip("/")
            if not url.startswith("http://") and not url.startswith("https://"):
                url = f"https://{url}"
            return url
        return None

    @property
    def is_enabled(self) -> bool:
        """
        Determines if self-ping should be active.
        Enabled automatically on Render, or when SELF_PING_ENABLED=true or SELF_PING_URL is provided.
        """
        env_val = os.getenv("SELF_PING_ENABLED", "").lower().strip()
        if env_val in ("false", "0", "no", "off"):
            return False
        if env_val in ("true", "1", "yes", "on"):
            return True
        # Auto-enable if running on Render or if an external URL is configured
        return bool(
            os.getenv("RENDER_EXTERNAL_URL")
            or os.getenv("RENDER")
            or os.getenv("SELF_PING_URL")
        )

    @property
    def interval_seconds(self) -> int:
        try:
            return max(10, int(os.getenv("SELF_PING_INTERVAL_SECONDS", "30")))
        except ValueError:
            return 30

    @property
    def status_summary(self) -> dict:
        idle = max(0, int(time.time() - self._last_activity))
        return {
            "enabled": self.is_enabled,
            "running": self._is_running,
            "target_url": self.target_url,
            "interval_seconds": self.interval_seconds,
            "idle_seconds": idle,
        }

    async def _ping_loop(self) -> None:
        target = self.target_url or "http://localhost:8000"
        logger.info(
            f"[KeepAlive] Background task started. Target: {target}, "
            f"Idle check interval: {self.interval_seconds}s"
        )
        # Initial grace period so FastAPI finishes startup before first check
        await asyncio.sleep(15)

        while self._is_running:
            try:
                await asyncio.sleep(self.interval_seconds)
                idle_time = time.time() - self._last_activity

                # Only ping if no client request has arrived within the idle interval
                if idle_time >= self.interval_seconds:
                    base_url = self.target_url or "http://localhost:8000"
                    ping_url = f"{base_url}/health"

                    async with httpx.AsyncClient(timeout=10.0) as client:
                        resp = await client.get(
                            ping_url,
                            headers={
                                "User-Agent": "CrackDSA-KeepAlive-SelfPing/1.0",
                                "X-Self-Ping": "true",
                            },
                        )
                        logger.info(
                            f"[KeepAlive] Idle for {idle_time:.0f}s. "
                            f"Sent self-ping to {ping_url} -> Status {resp.status_code}"
                        )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[KeepAlive] Self-ping to {self.target_url} failed: {e}")

    def start(self) -> None:
        if not self.is_enabled:
            logger.info(
                "[KeepAlive] Self-ping is inactive (no RENDER_EXTERNAL_URL or SELF_PING_ENABLED=true). "
                "Set SELF_PING_ENABLED=true or SELF_PING_URL to activate."
            )
            return

        if self._is_running:
            return

        self._is_running = True
        self._last_activity = time.time()
        self._task = asyncio.create_task(self._ping_loop())

    def stop(self) -> None:
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info("[KeepAlive] Background keep-alive task stopped.")


# Singleton instance
keep_alive_manager = KeepAliveManager()
