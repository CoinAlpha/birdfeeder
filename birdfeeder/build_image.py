import os
import subprocess
from datetime import datetime
from typing import List, Optional

import typer

DEFAULT_ORGANIZATION = "coinalpha"

app = typer.Typer()


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

    return DEFAULT_ORGANIZATION  # fallback


def build_image(organization: str, dockerfile: str, image: str, tag: str) -> None:
    """Calls `docker build` to build an image."""
    cmd: str = f"docker build -t {organization}/{image}:{tag} -f {dockerfile} ."
    subprocess.check_call(cmd, shell=True)  # noqa: DUO116


def push_image(organization: str, image: str, image_tag: str) -> None:
    """Calls `docker push` to push an image."""
    subprocess.check_call(f"docker push {organization}/{image}:{image_tag}", shell=True)  # noqa: DUO116


def get_short_rev() -> str:
    """Get current git revision in a short form."""
    short_rev = subprocess.check_output("git rev-parse --short HEAD", shell=True).decode("utf8").strip()  # noqa: DUO116
    return short_rev


def get_default_image_tag() -> str:
    """Construct a docker image tag using date and git short revision."""
    short_rev = get_short_rev()
    image_tag: str = f"{datetime.utcnow().strftime('%Y%m%d')}.git-{short_rev}"
    return image_tag


@app.command()
def main(
    image: Optional[str] = typer.Argument(None),  # noqa: B008
    push: bool = typer.Option(False, is_flag=True, help="Push the new image to Docker Hub."),  # noqa: B008
    tag: str = typer.Option(  # noqa: B008
        get_default_image_tag(),  # noqa: B008
        help="Specify a tag to be used, instead of the default one. "
        "Default is to construct a tag using current git revision (short).",
    ),
) -> None:
    """
    Build docker IMAGE.

    Expects to see Dockerfile.IMAGE in the current working directory.
    """
    available_images = get_available_images()
    if image not in available_images:
        typer.echo("Bad or missing image argument.\nTry --help' for help.\n\nAvailable images:")
        for i in available_images:
            typer.echo(f"- {i}")
        raise typer.Exit(code=1)

    dockerfile = f"Dockerfile.{image}"
    organization = get_org_from_dockerfile(dockerfile)
    build_image(organization, dockerfile, image, tag)

    if push:
        push_image(organization, image, tag)


if __name__ == '__main__':
    app()
