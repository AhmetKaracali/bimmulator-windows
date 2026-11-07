"""Vehicle input mailboxes in the BO03 replay fixture's shared guest RAM."""

import mmap
import os
from contextlib import contextmanager
from struct import Struct


RAM_SIZE = 64 * 1024 * 1024
FIXTURE_PAGE = 0x01000000
MAILBOX_OFFSET = 0x800
SPEED_OFFSET = MAILBOX_OFFSET + 8
WORD = Struct("<I")


def create_ram(path):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as ram:
        ram.truncate(RAM_SIZE)


@contextmanager
def open_rpm_mailbox(path):
    with path.open("r+b") as ram:
        if os.fstat(ram.fileno()).st_size != RAM_SIZE:
            raise ValueError("expected the GSS probe's 64 MiB shared RAM file")
        with mmap.mmap(ram.fileno(), SPEED_OFFSET + 2 * WORD.size, offset=FIXTURE_PAGE) as page:
            yield page


def write_rpm(page, rpm):
    WORD.pack_into(page, MAILBOX_OFFSET, round(rpm / 10) + 1)


def read_applied_rpm(page):
    encoded, = WORD.unpack_from(page, MAILBOX_OFFSET + WORD.size)
    return (encoded - 1) * 10 if encoded else None


def write_speed(page, speed_kph):
    WORD.pack_into(page, SPEED_OFFSET, round(speed_kph * 10) + 1)
