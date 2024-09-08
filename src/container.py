import docker
import requests
import subprocess
import json

class Container:
    def __init__(self) -> None:
        self.docker = docker.from_env()

    def get_running_containers(self) -> list:
        containers = self.docker.containers.list()
        container_data = []
        for container in containers:
            container_info = {
                "name": container.name,
                "image": container.image.tags[0] if container.image.tags else "N/A"
            }
            container_data.append(container_info)
        return container_data


    def get_local_image_digest(self,image_name: str) -> str:
        try:
            # Docker-Inspektionsinformationen abrufen
            image_info = subprocess.check_output(["docker", "inspect", image_name])
            image_info_json = json.loads(image_info)

            local_digest = image_info_json[0]['RepoDigests'][0].split('@')[1]
            local_tag = image_info_json[0]['RepoTags'][0].split(':')[1]
            local_version = image_info_json[0]['Config']['Labels'].get("org.opencontainers.image.version", "unknown")

            print("Debug | Local Digest: " + local_digest + " Local Tag: " + local_tag + " Local Version: " + local_version )
            return local_digest, local_tag, local_version

        except Exception as e:
            print(f"Error fetching local image info: {e}")
            return None, None, None


    def get_remote_image_info(self,image_name: str) -> str:
        try:
            remote_digest = subprocess.check_output(["crane", "digest", image_name]).decode().strip()

            remote_version_info = subprocess.check_output(["crane", "config", image_name])
            remote_version = json.loads(remote_version_info)['config']['Labels'].get("org.opencontainers.image.version",
                                                                                 "unknown")
            print("Debug | Remote Digest: " + remote_digest + " Remote Version: " + remote_version)
            return remote_digest, remote_version

        except Exception as e:
            print(f"Error fetching remote image info: {e}")
            return None, None

    def get_remote_image_latest(self, image_name: str) -> str:
        try:
            # Entferne den aktuellen Tag (alles nach dem ':') und setze 'latest' als neuen Tag
            if ':' in image_name:
                image_name_latest = image_name.split(':')[0] + ':latest'
            else:
                image_name_latest = image_name + ':latest'

            # Führe crane config aus, um die Konfigurationsinformationen für den latest Tag zu erhalten
            remote_version_latest_info = subprocess.check_output(["crane", "config", image_name_latest])
            remote_version_latest = json.loads(remote_version_latest_info)['config']['Labels'].get(
                "org.opencontainers.image.version", "unknown")

            print("Debug | Remote Version latest: " + remote_version_latest)
            return remote_version_latest

        except Exception as e:
            print(f"Error fetching remote version latest info: {e}")
            return None
