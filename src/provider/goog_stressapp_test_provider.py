import os
from typing import List, Union
import xml.etree.ElementTree as ET
from abc import ABCMeta, abstractproperty, abstractmethod
from six import add_metaclass
from pathlib import Path
from datetime import datetime

from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.lib.os_lib import OsCommandResult

from src.lib.content_configuration import ContentConfiguration
from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral
from src.provider.base_provider import BaseProvider
from src.lib.common_content_lib import CommonContentLib

@add_metaclass(ABCMeta)
class GoogStressAppTestProvider(BaseProvider):
    """Super class for OS-Specific Google Stress App Providers"""

    SAT_REPO_URL: str = "https://github.com/stressapptest/stressapptest"

    def __init__(self, log: str, cfg_opts: ET.ElementTree, os_obj: SutOsProvider):
        super(GoogStressAppTestProvider, self).__init__(log, cfg_opts, os_obj)
        self._install_collateral = InstallCollateral(log, os_obj, cfg_opts)

    def factory(log: str, cfg_opts: ET.ElementTree, os_obj: SutOsProvider):
        if os_obj.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNotImplementedError("This is currently only implemented for Linux. Please implement for {}".format(os_obj.os_type))
        else:
            return LinuxGoogStressAppTestProvider(log, cfg_opts, os_obj)

    @abstractmethod
    def install_app(self) -> None:
        """Installs Stress app test on SUT"""
        raise NotImplementedError

    def _get_cmd_string(self) -> str:
        """Creates command string from the relevant variables"""
        cmd: List[str] = [self.CMD, "-s {}".format(self.run_time), "-l {}".format(self.log_file)]

        if self.mbytes:
            cmd.append("-M {}".format(self.mbytes))
        if self.n_cpu_mem_threads:
            cmd.append("-m {}".format(self.n_cpu_mem_threads))

        return " ".join(cmd)

    def run_test(self, sync: bool = False) -> Union[None, OsCommandResult]:
        """Runs Stress app test
        :param sync: True to run test synchronously. False to run asynchronously."""
        cmd: str = self._get_cmd_string()

        self._log.info(f"Running {cmd}")
        if sync:
            return self._os.execute(cmd, self.run_time+10, cwd=self._app_location)
        else:
            self._os.execute_async(cmd, cwd=self._app_location)

    @property
    def mbytes(self) -> Union[int, None]:
        """Amount of RAM to use in Megabytes. Corresponds to -M flag.
        Default: Use all available RAM"""
        if self._mbytes:
            return self._mbytes
        else:
            return None

    @mbytes.setter
    def mbytes(self, v: Union[int, None]) -> None:
        """Sets Megabytes of RAM to use. Corresponds to -M flag
        :param v: Amount of RAM to use in megabytes"""
        self._mbytes = v

    @property
    def run_time(self) -> float:
        """Length of time to run test in Seconds. Corresponds to -S flag.
        App Defaults to 20 seconds"""
        if self._run_time:
            return self._run_time
        else:
            return 20

    @run_time.setter
    def run_time(self, v: float) -> None:
        """Set the time to run test. Corresponds to -S flag.
        :param v: Length of time to run test in seconds"""
        self._run_time = v

    @property
    def n_cpu_mem_threads(self) -> Union[int, None]:
        """Number of copy threads to run. Corresponds to -m flag.
        App defaults to one thread for each CPU."""
        if self._n_cpu_mem_threads:
            return self._n_cpu_mem_threads
        else:
            return None

    @n_cpu_mem_threads.setter
    def n_cpu_mem_threads(self, v: Union[int, None]) -> None:
        """Sets number of copy threads to run. Corresponds to -m flag
        :param v: number of copy threads to run during test. None to use one thread per CPU"""
        self._n_cpu_mem_threads = v

    @property
    def more_cpu_stress(self) -> bool:
        """Use more CPU-stressful memory copy. Corresponds to -W flag"""
        if self._more_cpu_stress is None:
            return False
        else:
            return self._more_cpu_stress

    @more_cpu_stress.setter
    def more_cpu_stress(self, v: bool) -> None:
        """Sets whether or not to use more CPU-stressful memory copy. Corresponds to -W flag
        :param v: True to use more stressful test"""
        self._more_cpu_stress = v

    @abstractproperty
    def log_file(self) -> str:
        """Logfile location. Corresponds to -l flag"""
        raise NotImplementedError

    @abstractproperty
    def CMD(self) -> str:
        """Base Command string"""
        raise NotImplementedError

    @abstractproperty
    def _app_location(self) -> str:
        """Path to Stress app test on SUT"""
        raise NotImplementedError


class LinuxGoogStressAppTestProvider(GoogStressAppTestProvider):
    """Linux-specific provider for Google Stress App test"""

    CMD: str = "./stressapptest"
    SAT_PATH: str = "/root/stressapptest"

    def __init__(self, log: str, cfg_opts: ET.ElementTree, os_obj: SutOsProvider):
        super(LinuxGoogStressAppTestProvider, self).__init__(log, cfg_opts, os_obj)
        self._log_file = None

    def install_app(self) -> None:
        """
        Installs git and make
        Clone Stress app repo
        Runs configure
        Runs make install
        :raises content_exceptions.TestSetupError: If any commands fail
        """
        self._install_collateral.yum_install("git")
        self._install_collateral.yum_install("make")

        self._log.info("Installing Google stresstest app")
        git_cmd: str = f"git clone {self.SAT_REPO_URL} {self.SAT_PATH}"
        git_res: OsCommandResult = self._os.execute(git_cmd, timeout=60)
        if git_res.cmd_failed():
            raise content_exceptions.TestSetupError(f"{git_cmd} failed with return code {git_res.return_code}.\nstderr:\n{git_res.stderr}")

        cfg_cmd: str = "./configure"
        cfg_res: OsCommandResult = self._os.execute(cfg_cmd, timeout=60, cwd=self.SAT_PATH)
        if cfg_res.cmd_failed():
            raise content_exceptions.TestSetupError(f"{cfg_cmd} failed with return code {cfg_res.return_code}.\nstderr:\n{cfg_res.stderr}")

        make_cmd: str = "make install"
        make_res: OsCommandResult = self._os.execute(make_cmd, timeout=60, cwd=self.SAT_PATH)
        if make_res.cmd_failed():
            raise content_exceptions.TestSetupError(f"{make_cmd} failed with return code {make_res.return_code}.\nstderr:\n{make_res.stderr}")

    @property
    def log_file(self) -> str:
        if not self._log_file:
            log_file_time: str = datetime.now().strftime("%Y%d%m_%H:%M:%S")
            self._log_file = Path(os.path.join(self._app_location, f"log_{log_file_time}")).as_posix()

        return self._log_file

    @property
    def _app_location(self) -> str:
        return Path(os.path.join(self.SAT_PATH, "src")).as_posix()
