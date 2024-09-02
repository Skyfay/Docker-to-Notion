from container import Container

def main():

    # Tests
    # Container().get_remote_image_info(image_name="docker.io/vaultwarden/server:latest")
    # Container().get_local_image_digest(image_name="docker.io/vaultwarden/server:latest")

    # Worker
    Container().get_running_containers()


if __name__ == "__main__":
    main()