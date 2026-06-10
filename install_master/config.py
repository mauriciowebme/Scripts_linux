import os


def get_ubuntu_version() -> float:
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("VERSION_ID"):
                    version_str = line.split("=")[1].strip().replace('"', '')
                    return float(version_str)
    except Exception:
        pass
    return 0.0


VERSAO_UBUNTU = get_ubuntu_version()

INSTALL_PRINCIPAL = '/install_principal'
BDS_PATH = os.path.join(INSTALL_PRINCIPAL, 'bds')
REDES_DOCKER = ['_traefik', 'interno']
ATMOZ_SFTP_CONF = os.path.join(INSTALL_PRINCIPAL, 'atmoz_sftp', 'users.conf')
