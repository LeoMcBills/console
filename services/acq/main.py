import sys

sys.path.append("/opt/mri4all/console/external/")

import signal
import asyncio
import time
import common.logger as logger
import common.runtime as rt
import common.helper as helper

rt.set_service_name("acq")
log = logger.get_logger()

from common.version import mri4all_version
import common.queue as queue
from common.constants import *

main_loop = None  # type: helper.AsyncTimer # type: ignore


def process_acquisition(scan_name: str) -> bool:
    log.info("Performing acquisition...")
    # TODO: Process actual case!
    time.sleep(3)
    log.info("Acquisition completed")

    if not queue.move_task(mri4all_paths.DATA_ACQ + "/" + scan_name, mri4all_paths.DATA_QUEUE_RECON):
        log.error(f"Failed to move scan {scan_name} to recon queue. Critical Error.")
    return True


def run_acquisition_loop():
    """
    Main processing function that is called continuously by the main loop
    """
    selected_scan = queue.get_scan_ready_for_acq()
    if selected_scan:
        log.info(f"Processing scan: {selected_scan}")
        rt.set_current_task_id(selected_scan)

        if not queue.move_task(mri4all_paths.DATA_QUEUE_ACQ + "/" + selected_scan, mri4all_paths.DATA_ACQ):
            log.error(f"Failed to move scan {selected_scan} to acq folder. Unable to run acquisition.")
        else:
            process_acquisition(selected_scan)

        rt.clear_current_task_id()

    if helper.is_terminated():
        return


async def terminate_process(signalNumber, frame) -> None:
    """
    Triggers the shutdown of the service
    """
    log.info("Shutdown requested")
    # Note: main_loop can be read here because it has been declared as global variable
    if "main_loop" in globals() and main_loop.is_running:
        main_loop.stop()
    helper.trigger_terminate()


def prepare_acq_service() -> bool:
    """
    Prepare the acquisition service
    """
    log.info("Preparing for acquisition...")

    # Clear the data acquisition folder, in case a previous instance has crashed
    if not queue.clear_folder(mri4all_paths.DATA_ACQ):
        return False

    return True


def run(test_all_sequences: bool = False):
    log.info(f"-- MRI4ALL {mri4all_version.get_version_string()} --")
    log.info("Acquisition service started")

    if not prepare_acq_service():
        log.error("Error while preparing acquisition service. Terminating.")
        sys.exit()

    # Register system signals to be caught
    signals = (signal.SIGTERM, signal.SIGINT)
    for s in signals:
        helper.loop.add_signal_handler(s, lambda s=s: asyncio.create_task(terminate_process(s, helper.loop)))

    # Start the timer that will periodically trigger the scan of the task folder
    global main_loop
    main_loop = helper.AsyncTimer(0.1, run_acquisition_loop)
    try:
        main_loop.run_until_complete(helper.loop)
    except Exception as e:
        log.exception(e)
    finally:
        # Finish all asyncio tasks that might be still pending
        remaining_tasks = helper.asyncio.all_tasks(helper.loop)  # type: ignore[attr-defined]
        if remaining_tasks:
            helper.loop.run_until_complete(helper.asyncio.gather(*remaining_tasks))

    log.info("Acquisition service terminated")
    log.info("-------------")
    sys.exit()


if __name__ == "__main__":
    run()
