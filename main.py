import asyncio
import os

from loguru import logger

from src.ui.cli.formatting import display_logo
from src.utils.logging import setup_logger


async def main():
    if not os.path.exists(".env"):
        from config.setup import run_first_launch_setup

        run_first_launch_setup()

    setup_logger(level="INFO")
    display_logo()

    try:
        from src.api.client import WSPAsyncClient
        from src.core.registration import RegistrationLogic
        from src.core.scheduler import TimeScheduler
        from src.ui.cli.menu import CLI
    except Exception as e:
        logger.critical(f"Configuration Error: {e}")
        return

    cli = CLI()
    scheduler = TimeScheduler()
    registration_plan = {}

    async with WSPAsyncClient() as client:
        try:
            await client.login()
            subjects_data = await client.get_accruals()
            if not subjects_data:
                logger.warning("No subjects available for registration.")
                return

            subjects_ids = [s["id"] for s in subjects_data]
            logger.info(f"Found {len(subjects_ids)} subjects.")

            loaded_plan = cli.ask_to_load_plan()
            if loaded_plan:
                valid_plan = {k: v for k, v in loaded_plan.items() if k in subjects_ids}
                registration_plan = valid_plan

            if not registration_plan:
                for sub_id in subjects_ids:
                    try:
                        schedule = await client.get_schedule(sub_id)
                        ids = cli.interactive_subject_selection(schedule)
                        if ids:
                            registration_plan[sub_id] = ids
                    except Exception:
                        logger.exception(f"Error processing subject {sub_id}")

                if registration_plan:
                    cli.save_plan(registration_plan)

            if not registration_plan:
                logger.warning("No lessons selected. Exiting.")
                return

            if not cli.get_user_confirmation(registration_plan):
                logger.info("Cancelled by user.")
                return

            scheduler.sync_ntp()
            target_ts = scheduler.get_target_timestamp()
            await scheduler.wait_until_target(target_ts)

            logger.warning(">>> LAUNCHING REGISTRATION REQUESTS <<<")
            await RegistrationLogic.execute_sniper_attack(client, registration_plan)
            logger.success("All tasks dispatched.")

        except Exception as e:
            logger.critical(f"Critical Runtime Error: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye.")
