"""Utility functions relating to SSL encryption."""
import errno
import os

from OpenSSL import crypto

from mimic.Utils.Host import resolve_host

_COMMON_NAME = resolve_host()
_ORGANIZATION_NAME = "mimic"
_SERIAL_NUMBER = 0
_VALIDITY_START_IN_SECONDS = 0
_VALIDITY_END_IN_SECONDS = 10 * 365 * 24 * 60 * 60


def generate_ssl_certs(cert_file: str, key_file: str):
    """
    Generate SSL certificate and private key using RSA 4096 and SHA 512.

    Results are written out to files.

    Args:
        cert_file (str): Path to write certificate to
        key_file (str): Path to write private key to
    """
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 4096)

    cert = crypto.X509()
    cert.get_subject().O = _ORGANIZATION_NAME
    cert.get_subject().CN = _COMMON_NAME
    cert.set_serial_number(_SERIAL_NUMBER)
    cert.gmtime_adj_notBefore(_VALIDITY_START_IN_SECONDS)
    cert.gmtime_adj_notAfter(_VALIDITY_END_IN_SECONDS)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha512')

    _make_dirs(cert_file)
    with open(cert_file, "wt") as file:
        file.write(crypto.dump_certificate(
            crypto.FILETYPE_PEM, cert).decode('utf-8'))

    _make_dirs(key_file)
    with open(key_file, "wt") as file:
        file.write(crypto.dump_privatekey(
            crypto.FILETYPE_PEM, key).decode('utf-8'))


def ssl_certs_generated(cert_file: str, key_file: str) -> bool:
    """
    If the certificate and key files are generated.

    Args:
        cert_file (str): Path to certificate file
        key_file (str): Path to key file

    Returns:
        bool: Both certificate and key file exist
    """
    return os.path.exists(cert_file) and os.path.exists(key_file)


def _make_dirs(file_name: str):
    """
    Recursively make directories for a file.

    Args:
        file_name (str): Path to file
    """
    if not os.path.exists(os.path.dirname(file_name)):
        try:
            os.makedirs(os.path.dirname(file_name))
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise
