import logging
import os
import docker
from flask_restful import Resource

logger = logging.getLogger('electric.status.{0}'.format(__name__))

class StatusResource(Resource):
    def __init__(self):
        self.docker_cli = docker.from_env()

    def _systemctl_running(self, name):
        return os.system("systemctl is-active %s > /dev/null" % (name,))

    def is_dnsmasq_running(self):
        """If dnsmasq is running or not, returns true / false"""
        return self._systemctl_running("dnsmasq") == 0

    def is_docker_running(self):
        """Check if the docker server is running"""
        return self._systemctl_running("docker") == 0

    def is_hostapd_running(self):
        """Check if the hostapd service is up"""
        return self._systemctl_running("hostapd") == 0

    def check_docker_image_exists(self):
        """Check if the scornflake/electric-pi image has been downloaded already and what version is it?"""
        try:
            image = self.docker_cli.images.get("scornflake/electric-pi")
            return True
        except docker.errors.ImageNotFound:
            pass
        return False

    def check_docker_container_created(self):
        """Check if the container for the iCharger service has been created"""
        try:
            cont = self.docker_cli.containers.get("electric-pi")
            return True
        except docker.errors.NotFound:
            pass
        return False

    def check_docker_image_running(self):
        """Checks to see if the created container is actually running"""
        try:
            cont = self.docker_cli.containers.get("electric-pi")
            return cont.status == "running"
        except docker.errors.NotFound:
            pass
        return False

    def get_server_status(self):
        """Calls into the running container to obtain the status of the iCharger service"""
        return {}

    def get(self):
        # simply check for the correct configuration of required system resources and return this
        # in a dict
        res = dict()

        res["dnsmasq"] = {
            "running": self.is_dnsmasq_running()
        }

        res["hostapd"] = {
            "running": self.is_hostapd_running()
        }

        image_running = self.check_docker_image_running()
        res["docker"] = {
            "running": self.is_docker_running(),
            "image_exists": self.check_docker_image_exists(),
            "container_created": self.check_docker_container_created(),
            "container_running": image_running
        }

        server_status = {}
        if image_running:
            server_status = self.get_server_status()

        res["server_status"] = server_status

        return res