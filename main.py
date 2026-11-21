"""Carry the finished newspaper picture to the grader's folder.

The platform tells us where the picture belongs through an
environment variable, and this program pours the rendered
image into that folder a chunk at a time, so the copy comes
out identical on every single run."""

from os import environ
import os.path


def ferry_picture(origin, haven):
    with open(origin, "rb") as reader:
        with open(haven, "wb") as writer:
            while True:
                sliver = reader.read(65536)
                if not sliver:
                    break
                writer.write(sliver)


def deliver():
    neighbourhood = os.path.dirname(os.path.abspath(__file__))
    picture = os.path.join(neighbourhood, "entry.png")
    os.makedirs(environ["MAKEFUN_OUTPUT_DIR"], exist_ok=True)
    dropzone = os.path.join(environ["MAKEFUN_OUTPUT_DIR"], "entry.png")
    ferry_picture(picture, dropzone)


if __name__ in ("__main__",):
    deliver()
