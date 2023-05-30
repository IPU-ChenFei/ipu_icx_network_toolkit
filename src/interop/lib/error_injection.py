import time
from dtaf_core.providers.ac_power import AcPowerControlProvider
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration


class InjectErrors(object):
    """
    : This class has methods which will inject errors through error injection object of cscripts
    """

    def __init__(self, log, os_obj, cfg_opts, sdp, csp, run_time, reboot_timeout):
        self._log = log
        self._os = os_obj
        self.sut_os = self._os.os_type
        self._cfg = cfg_opts
        self._common_content_lib = CommonContentLib(self._log, self._os, self._cfg)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._sv = self.sv_object()
        self._sdp = sdp
        self._csp = csp
        self._run_time = run_time
        self._reboot_timeout = reboot_timeout

    def sv_object(self):
        """
            : method for getting sv object to determine sockets related information
        """
        try:
            import commlibs.utils.utils as utils
            _utils = utils
            sv = _utils.getSVComponent()
            return sv
        except ImportError:
            raise ImportError("CScripts library is not available! Please check configuration.")

    def inject_ce_errors(self, accelerator, delay=10):
        """
            : injects correctable errors into host
        """
        status = True
        self._log.info("Socket Information")
        self._log.info(self._csp.get_sockets())
        socket_count = len(self._csp.get_sockets())

        if socket_count == 0:
            self._log.error('No sockets connected..')
        try:
            if accelerator == "QAT":
                cnt = 0
                com_time = time.perf_counter() + self._run_time
                while time.perf_counter() < com_time:
                    cnt += 1
                    for socket in range(socket_count):
                        socket_object = self._sv.get_by_path("socket{}".format(socket))
                        devices = socket_object.uncore.hca.cpm.cpms
                        for device in range(len(devices)):
                            import platforms.SPR.spreidefs as ei
                            ei_obj = ei.spreidefs
                            self._log.info(
                                'Injecting Correctable Error in {0} socket -{1} {2} device '.format(socket, accelerator,
                                                                                                    device))
                            ei_obj.injectCpmError(ei, socket, device, 'ce', auto_answer='y')
                            time.sleep(delay)

            if accelerator == "DLB":
                cnt = 0
                com_time = time.perf_counter() + self._run_time
                while time.perf_counter() < com_time:
                    cnt += 1
                    for socket in range(socket_count):
                        socket_object = self._sv.get_by_path("socket{}".format(socket))
                        devices = socket_object.uncore.hca.hqm.hqms
                        for device in range(len(devices)):
                            import platforms.SPR.spreidefs as ei
                            ei_obj = ei.spreidefs
                            self._log.info(
                                'Injecting Correctable Error in socket{0} for {1} {2} device '.format(socket, device,
                                                                                                      accelerator))
                            ei_obj.injectHqmError(ei, socket, device, 'ce', auto_answer='y')
                            time.sleep(delay)

            if accelerator == "DSA":
                cnt = 0
                com_time = time.perf_counter() + self._run_time
                while time.perf_counter() < com_time:
                    cnt += 1
                    for socket in range(socket_count):
                        socket_object = self._sv.get_by_path("socket{}".format(socket))
                        devices = socket_object.uncore.dsas
                        for device in range(len(devices)):
                            import platforms.SPR.spreidefs as ei
                            ei_obj = ei.spreidefs
                            self._log.info(
                                'Injecting Correctable Error in socket{0} for {1} {2} device '.format(socket, device,
                                                                                                      accelerator))
                            ei_obj.injectDsaError(ei, socket, device, 'ce', auto_answer='y')
                            time.sleep(delay)

            if accelerator == "IAX":
                cnt = 0
                com_time = time.perf_counter() + self._run_time
                while time.perf_counter() < com_time:
                    cnt += 1
                    for socket in range(socket_count):
                        socket_object = self._sv.get_by_path("socket{}".format(socket))
                        devices = socket_object.uncore.iaxs
                        for device in range(len(devices)):
                            import platforms.SPR.spreidefs as ei
                            ei_obj = ei.spreidefs
                            self._log.info(
                                'Injecting Correctable Error in socket{0} for {1} {2} device '.format(socket, device,
                                                                                                      accelerator))
                            self._log.info("IAX Method Yet to be implemented")
                            # ei_obj.injectIaxError(ei, socket, device, 'ce', auto_answer='y')
                            time.sleep(delay)

            return status

        except Exception as ex:
            status = False
            self._log.error("An exception occurred in {0} correctable injection:'{1}'".format(accelerator, ex))
            return status
        finally:
            self._sdp.go()

    def inject_uce_errors(self, accelerator, delay=10):
        """
            : injects un-correctable errors into accelerators
        """
        status = True
        self._log.info("Socket Information")
        self._log.info(self._csp.get_sockets())
        socket_count = len(self._csp.get_sockets())
        if socket_count == 0:
            self._log.error('No sockets connected..')
        try:
            if accelerator == "DLB":
                cnt = 0
                com_time = time.perf_counter() + self._run_time
                while time.perf_counter() < com_time:
                    cnt += 1
                    for socket in range(socket_count):
                        socket_object = self._sv.get_by_path("socket{}".format(socket))
                        devices = socket_object.uncore.hca.hqm.hqms
                        for device in range(len(devices)):
                            import platforms.SPR.spreidefs as ei
                            ei_obj = ei.spreidefs
                            self._log.info(
                                'Injecting Un-Correctable Error in socket{0} for {1} {2} device '.format(socket, device,
                                                                                                         accelerator))
                            ei_obj.injectHqmError(ei, socket, device, 'uce', auto_answer='y')
                            if self._common_content_lib.check_os_alive():
                                self._log.info(
                                    "System reboot didn't happen after error injection in socket{0} for {1} {2} device ".format(
                                        socket, device, accelerator))
                            else:
                                self._log.info(
                                    "System has shutdown after error injection and waiting for OS to be alive")
                                self._common_content_lib.wait_for_os(self._reboot_timeout)
                                time.sleep(delay)

            if accelerator == "QAT":
                cnt = 0
                com_time = time.perf_counter() + self._run_time
                while time.perf_counter() < com_time:
                    cnt += 1
                    for socket in range(socket_count):
                        socket_object = self._sv.get_by_path("socket{}".format(socket))
                        devices = socket_object.uncore.hca.cpm.cpms
                        for device in range(len(devices)):
                            import platforms.SPR.spreidefs as ei
                            ei_obj = ei.spreidefs
                            self._log.info(
                                'Injecting Un-Correctable Error in socket{0} for {1} {2} device '.format(socket, device,
                                                                                                         accelerator))
                            ei_obj.injectCpmError(ei, socket, device, 'uce', auto_answer='y')
                            if self._common_content_lib.check_os_alive():
                                self._log.info(
                                    "System reboot didn't happen after error injection in socket{0} for {1} {2} device ".format(
                                        socket, device, accelerator))
                            else:
                                self._log.info(
                                    "System has shutdown after error injection and waiting for OS to be alive")
                                self._common_content_lib.wait_for_os(self._reboot_timeout)
                                time.sleep(delay)

            if accelerator == "DSA":
                cnt = 0
                com_time = time.perf_counter() + self._run_time
                while time.perf_counter() < com_time:
                    cnt += 1
                    for socket in range(socket_count):
                        socket_object = self._sv.get_by_path("socket{}".format(socket))
                        devices = socket_object.uncore.dsas
                        for device in range(len(devices)):
                            import platforms.SPR.spreidefs as ei
                            ei_obj = ei.spreidefs
                            self._log.info(
                                'Injecting Un-Correctable Error in socket{0} for {1} {2} device '.format(socket, device,
                                                                                                         accelerator))
                            ei_obj.injectDsaError(ei, socket, device, 'uce', auto_answer='y')
                            if self._common_content_lib.check_os_alive():
                                self._log.info(
                                    "System reboot didn't happen after error injection in socket{0} for {1} {2} device ".format(
                                        socket, device, accelerator))
                            else:
                                self._log.info(
                                    "System has shutdown after error injection and waiting for OS to be alive")
                                self._common_content_lib.wait_for_os(self._reboot_timeout)
                                time.sleep(delay)

            if accelerator == "IAX":
                cnt = 0
                com_time = time.perf_counter() + self._run_time
                while time.perf_counter() < com_time:
                    cnt += 1
                    for socket in range(socket_count):
                        socket_object = self._sv.get_by_path("socket{}".format(socket))
                        devices = socket_object.uncore.iaxs
                        for device in range(len(devices)):
                            import platforms.SPR.spreidefs as ei
                            ei_obj = ei.spreidefs
                            # self._log.info('Injecting Un-Correctable Error in socket{0} for {1} {2} device '.format(socket, device, accelerator))
                            self._log.info("Yet to be implemented")
                            # ei_obj.injectIaxError(ei, socket, device, 'uce', auto_answer='y')
                            if self._common_content_lib.check_os_alive():
                                self._log.info(
                                    "System reboot didn't happen after error injection in socket{0} for {1} {2} device ".format(
                                        socket, device, accelerator))
                            else:
                                self._log.info(
                                    "System has shutdown after error injection and waiting for OS to be alive")
                                self._common_content_lib.wait_for_os(self._reboot_timeout)
                                time.sleep(delay)
            return status

        except Exception as ex:
            status = False
            self._log.error(
                "An exception occurred in uncorrectable fatal error {0} injection:'{1}'".format(accelerator, ex))
            return status
        finally:
            self._sdp.go()

