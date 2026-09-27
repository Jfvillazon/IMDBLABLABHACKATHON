"""Strict single-file multipart reader using standard-library header parsing.

Only browser form-data with exactly one binary `file` part is accepted. The
request has already been byte-limited and spooled by RepositoryBodyLimit. No
general MIME decoding, preambles, epilogues, nested multiparts or field parts.
"""
from contextlib import contextmanager
from email import policy
from email.message import Message
from email.parser import BytesHeaderParser
import re
import tempfile

from backend.services.repository_import import CHUNK, MAX_UPLOAD
from backend.services.workspaces import RepositoryError


@contextmanager
def multipart_file(body, content_type, storage):
    header = Message(policy=policy.default)
    header["Content-Type"] = content_type
    boundary = header.get_param("boundary")
    if (header.get_content_type() != "multipart/form-data" or not isinstance(boundary, str)
            or not re.fullmatch(r"[A-Za-z0-9'()+_,./:=?-]{1,70}", boundary)):
        raise RepositoryError(422, "Expected single-file multipart ZIP upload")
    delimiter = b"--" + boundary.encode("ascii")
    body.seek(0)
    if body.read(len(delimiter) + 2) != delimiter + b"\r\n":
        raise RepositoryError(422, "Invalid multipart opening boundary")
    raw_headers = bytearray()
    while True:
        line = body.readline(8193)
        raw_headers.extend(line)
        if len(raw_headers) > 8192 or not line.endswith(b"\r\n"):
            raise RepositoryError(422, "Invalid multipart headers")
        if line == b"\r\n":
            break
    headers = BytesHeaderParser(policy=policy.default).parsebytes(bytes(raw_headers))
    if (headers.defects or any(getattr(value, "defects", ()) for value in headers.values())
            or any(len(headers.get_all(key)) > 1 for key in headers.keys())
            or headers.get_content_disposition() != "form-data"
            or headers.get_param("name", header="content-disposition") != "file"
            or headers.get_filename() is None
            or headers.get("Content-Transfer-Encoding") is not None):
        raise RepositoryError(422, "Upload exactly one binary file using field 'file'")
    start = body.tell()
    body.seek(0, 2)
    length = body.tell()
    closing = b"\r\n" + delimiter + b"--"
    body.seek(max(start, length - len(closing) - 2))
    tail = body.read()
    if tail.endswith(closing + b"\r\n"):
        end = length - len(closing) - 2
    elif tail.endswith(closing):
        end = length - len(closing)
    else:
        raise RepositoryError(422, "Invalid or incomplete multipart closing boundary")
    size = end - start
    if size < 0:
        raise RepositoryError(422, "Invalid multipart upload")
    if size > MAX_UPLOAD:
        raise RepositoryError(413, "ZIP upload exceeds limit")
    body.seek(start)
    # Reject any embedded delimiter: this endpoint accepts exactly one part.
    marker = b"\r\n" + delimiter
    overlap = b""
    with tempfile.TemporaryFile(dir=str(storage)) as archive:
        remaining = size
        while remaining:
            chunk = body.read(min(CHUNK, remaining))
            if not chunk:
                raise RepositoryError(422, "Incomplete multipart upload")
            combined = overlap + chunk
            if marker in combined:
                raise RepositoryError(422, "Upload exactly one file and no form fields")
            overlap = combined[-len(marker):]
            archive.write(chunk)
            remaining -= len(chunk)
        archive.seek(0)
        yield archive, headers.get_filename()
