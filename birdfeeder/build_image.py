import os
import subprocess
import sys
from datetime import datetime
from typing import List

import click

DEFAULT_ORGRANIZATION = "coinalpha"


def get_available_images() -> List[str]:
    """Read files in current directory and return `xxx` part from all Dockerfile.xxx."""
    images = [f.split(".")[1] for f in os.listdir(".") if f.startswith("Dockerfile.")]
    return images


def get_org_from_dockerfile(dockerfile: str) -> str:
    """Return organization name by reading Dockerfile `org` label."""
    with open(dockerfile) as fd:
        for line in fd:
            if line.startswith("LABEL org"):
                return line.split("=")[1].strip().strip('"')

    return DEFAULT_ORGRANIZATION  # fallback


def build_image(organization: str, dockerfile: str, image: str, tag: str) -> None:
    """Calls `docker build` to build an image."""
    cmd: str = f"docker build -t {organization}/{image}:{tag} -f {dockerfile} ."
    subprocess.check_call(cmd, shell=True)  # noqa: DUO116


def push_image(organization: str, image: str, image_tag: str) -> None:
    """Calls `docker push` to push an image."""
    subprocess.check_call(f"docker push {organization}/{image}:{image_tag}", shell=True)  # noqa: DUO116


@click.command()
@click.option("--push", is_flag=True, help="Push the new image to Docker Hub.")
@click.option(
    "--tag",
    help="Specify a tag to be used, instead of the default one. Default is to construct a tag using git revision.",
)
@click.argument("image")
def main(push, tag, image):
    """
    Build docker IMAGE.

    Expects to see Dockerfile.IMAGE in the current working directory.
    """
    available_images = get_available_images()
    if image not in available_images:
        click.echo(f"Bad image argument. Available images: {available_images}.")
        sys.exit(1)

    short_rev = subprocess.check_output("git rev-parse --short HEAD", shell=True).decode("utf8").strip()  # noqa: DUO116
    image_tag: str = tag or f"{datetime.utcnow().strftime('%Y%m%d')}.git-{short_rev}"

    dockerfile = f"Dockerfile.{image}"
    organization = get_org_from_dockerfile(dockerfile)
    build_image(organization, dockerfile, image, image_tag)

    if push:
        push_image(organization, image, image_tag)


if __name__ == '__main__':
    main()
