"""outpost tests"""
from shutil import rmtree
from tempfile import mkdtemp
from time import sleep

import yaml
from channels.testing import ChannelsLiveServerTestCase
from docker import DockerClient, from_env
from docker.models.containers import Container
from docker.types.healthcheck import Healthcheck

from authentik import __version__
from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow, FlowDesignation
from authentik.outposts.controllers.docker import DockerController
from authentik.outposts.models import (
    DockerServiceConnection,
    Outpost,
    OutpostType,
    default_outpost_config,
)
from authentik.outposts.tasks import outpost_local_connection
from authentik.providers.proxy.models import ProxyProvider
from tests.e2e.utils import get_docker_tag


class OutpostDockerTests(ChannelsLiveServerTestCase):
    """Test Docker Controllers"""

    def _start_container(self, ssl_folder: str) -> Container:
        client: DockerClient = from_env()
        container = client.containers.run(
            image="library/docker:dind",
            detach=True,
            network_mode="host",
            remove=True,
            privileged=True,
            healthcheck=Healthcheck(
                test=["CMD", "docker", "info"],
                interval=5 * 100 * 1000000,
                start_period=5 * 100 * 1000000,
            ),
            environment={"DOCKER_TLS_CERTDIR": "/ssl"},
            volumes={
                f"{ssl_folder}/": {
                    "bind": "/ssl",
                }
            },
        )
        while True:
            container.reload()
            status = container.attrs.get("State", {}).get("Health", {}).get("Status")
            if status == "healthy":
                return container
            sleep(1)

    def setUp(self):
        super().setUp()
        self.ssl_folder = mkdtemp()
        self.container = self._start_container(self.ssl_folder)
        # Ensure that local connection have been created
        outpost_local_connection()
        self.provider: ProxyProvider = ProxyProvider.objects.create(
            name="test",
            internal_host="http://localhost",
            external_host="http://localhost",
            authorization_flow=Flow.objects.create(
                name="foo", slug="foo", designation=FlowDesignation.AUTHORIZATION
            ),
        )
        authentication_kp = CertificateKeyPair.objects.create(
            name="docker-authentication",
            # pylint: disable=consider-using-with
            certificate_data=open(f"{self.ssl_folder}/client/cert.pem", encoding="utf8").read(),
            # pylint: disable=consider-using-with
            key_data=open(f"{self.ssl_folder}/client/key.pem", encoding="utf8").read(),
        )
        verification_kp = CertificateKeyPair.objects.create(
            name="docker-verification",
            # pylint: disable=consider-using-with
            certificate_data=open(f"{self.ssl_folder}/client/ca.pem", encoding="utf8").read(),
        )
        self.service_connection = DockerServiceConnection.objects.create(
            url="https://localhost:2376",
            tls_verification=verification_kp,
            tls_authentication=authentication_kp,
        )
        self.outpost: Outpost = Outpost.objects.create(
            name="test",
            type=OutpostType.PROXY,
            service_connection=self.service_connection,
            _config=default_outpost_config(self.live_server_url),
        )
        self.outpost.providers.add(self.provider)
        self.outpost.save()

    def tearDown(self) -> None:
        super().tearDown()
        self.container.kill()
        try:
            rmtree(self.ssl_folder)
        except PermissionError:
            pass

    def test_docker_controller(self):
        """test that deployment requires update"""
        controller = DockerController(self.outpost, self.service_connection)
        controller.up()
        controller.down()

    def test_docker_static(self):
        """test that deployment requires update"""
        controller = DockerController(self.outpost, self.service_connection)
        manifest = controller.get_static_deployment()
        compose = yaml.load(manifest, Loader=yaml.SafeLoader)
        self.assertEqual(compose["version"], "3.5")
        self.assertEqual(
            compose["services"]["authentik_proxy"]["image"],
            f"goauthentik.io/dev-proxy:{get_docker_tag()}",
        )
