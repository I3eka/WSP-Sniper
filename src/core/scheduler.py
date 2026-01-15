import asyncio
import time
from datetime import datetime

import ntplib
from loguru import logger

from config.settings import settings


class TimeScheduler:
    def __init__(self):
        self.time_offset = 0.0

    def sync_ntp(self) -> None:
        """Calculates offset between system time and NTP time."""
        try:
            client = ntplib.NTPClient()
            response = client.request("pool.ntp.org", version=3)
            ntp_time = response.tx_time
            system_time = time.time()
            self.time_offset = ntp_time - system_time
            logger.info(f"NTP Sync successful. Offset: {self.time_offset:.4f}s")
        except Exception as e:
            logger.warning(f"NTP Sync failed: {e}. Using system time.")
            self.time_offset = 0.0

    def get_corrected_time(self) -> float:
        return time.time() + self.time_offset

    def get_target_timestamp(self) -> float:
        """
        Parses the LOCAL target time string from settings.
        Converts user's local wall-clock time -> UTC timestamp.
        """
        now = datetime.now()
        today = now.date()

        time_str = settings.desired_time_local
        try:
            if "." in time_str:
                dt_time = datetime.strptime(time_str, "%H:%M:%S.%f").time()
            else:
                dt_time = datetime.strptime(time_str, "%H:%M:%S").time()
        except ValueError:
            logger.error(
                f"Invalid time format: {time_str}. Expected HH:MM:SS or HH:MM:SS.ffffff"
            )
            raise

        local_dt_naive = datetime.combine(today, dt_time)

        local_dt_aware = local_dt_naive.astimezone()
        target_timestamp = local_dt_aware.timestamp()

        logger.info(
            f"Local Target: {local_dt_aware} | UTC Timestamp: {target_timestamp}"
        )
        return target_timestamp

    async def wait_until_target(self, target_timestamp: float) -> None:
        """High-precision busy-wait loop for the last few seconds."""
        wait_seconds = target_timestamp - self.get_corrected_time()
        if wait_seconds > 0:
            logger.info(f"Waiting for {wait_seconds:.2f} seconds...")
        else:
            logger.warning("Target time has already passed! engaging immediately.")

        while True:
            current_corrected = self.get_corrected_time()
            remaining = target_timestamp - current_corrected

            if remaining <= 0:
                break

            if remaining > 2:
                await asyncio.sleep(remaining - 1)
            elif remaining > 0.1:
                await asyncio.sleep(0.05)
            else:
                await asyncio.sleep(0.001)
