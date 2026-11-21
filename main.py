"""Put the finished front page where the grader looks for it."""

from os import environ, makedirs, path


def usher_front_page_to_grader():
    newsroom = path.dirname(path.abspath(__file__))
    satchel = path.join(newsroom, "entry.png")
    dropbox = environ["MAKEFUN_OUTPUT_DIR"]
    makedirs(dropbox, exist_ok=True)
    parcel = path.join(dropbox, "entry.png")
    with open(satchel, "rb") as inbound, open(parcel, "wb") as outbound:
        for morsel in iter(lambda: inbound.read(65536), b""):
            outbound.write(morsel)


usher_front_page_to_grader()
