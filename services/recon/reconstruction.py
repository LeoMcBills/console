import common.logger as logger
import common.runtime as rt
import numpy as np
import os
from os import path

from recon.kspaceFiltering.kspace_filtering import *

from recon.B0Correction import B0Corrector
import recon.DICOM.DICOM_utils as DICOM
from recon.ismrmrd.numpy_to_ismrmrd import create_ismrmrd

from recon.image_filters import denoise

log = logger.get_logger()

import common.queue as queue
from common.constants import *
import common.task as task
from common.types import ScanTask

import services.recon.utils as utils
import time


def run_reconstruction_cartesian(self, folder: str, task: ScanTask):
    """
    Runs the reconstruction pipeline for Cartesian sampling
    """

    fnames = os.listdir(folder)
    if not fnames:
        log.error(f"Folder {folder} is empty.")
        return

    # TODO: Load the k-space data
    kData = np.load(folder + "rawdata" + "/kSpace.npy")  # TODO: Zach
    kTraj = np.genfromtxt(
        r"%s/%s/trajectory.csv" % (folder), delimiter=","  # TODO: Zach
    )  # pe_table a lot by 2 # check rotation

    if kTraj.shape[0] > 2:
        kTraj = np.rot90(kTraj)
    # grad_delay_correction(kData, kTraj, delayT, param)

    filterType = "fermi"
    kData = kFilter(kData, filterType, center_correction=True)
    log.info(f"kSpace {filterType} filtering finished.")

    #TODO(Zach, Shounak): Use the trajectory information and B0 map
    fname_B0_map = list(filter(lambda x: "B0" in x, fnames))
    Y = np.ndarray
    kt = np.ndarray
    df = np.load(path.join(folder, fname_B0_map[0])) if fname_B0_map else None
    Lx = 1
    nonCart = None
    params = None
    b0_corrector = B0Corrector(Y, kt, df, Lx, nonCart, params)
    iData = b0_corrector()
    log.info(f"B0 correction finished.")

    # denoising strength from the user interface? - provided by json
    try:
        iData = denoise.remove_gaussian_noise_complex(iData, method="gaussian_filter")
        log.info(f"Finished image denoising.")
    except ValueError:
        log.error(f"Image denoising failed.")

    # TODO(Lavanya): Write the DICOM file to the folder
    DICOM.write_dicom(iData, task, folder)
    log.info(f"DICOM writting finished.")

    # TODO(Radhika): Write ISMRMRD file to the folder
    create_ismrmrd(folder, kData, task)


def run_reconstruction(folder: str, task: ScanTask) -> bool:
    """
    Perform the reconstruction of the scan contained in the given folder. Scan information such
    as sequence, protocol name, patient information and system information can be found in the
    task object.
    """
    log.info(f"Folder where the task is = {folder}")
    log.info(f"JSON information = {task}")

    log.info(f"Starting reconstruction.")

    if task.processing.recon_mode == "bypass":
        return True

    if task.processing.recon_mode == "fake_dicoms":
        utils.generate_fake_dicoms(folder, task)
        time.sleep(2)
        return True

    run_reconstruction_cartesian(folder, task)

    return True
