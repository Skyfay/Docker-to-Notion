from container import Container

def main():

    Container().get_remote_image_info(image_name="docker.io/vaultwarden/server:latest")
    Container().get_local_image_digest(image_name="docker.io/vaultwarden/server:latest")


if __name__ == "__main__":
    main()