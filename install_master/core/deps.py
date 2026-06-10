import subprocess
import sys

from install_master.config import VERSAO_UBUNTU


def garantir_pip():
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("📦 pip não encontrado. Instalando...")
        subprocess.run(["sudo", "apt", "update"], check=False)
        subprocess.run(["sudo", "apt", "install", "-y", "python3-pip"], check=True)
        print("✅ pip instalado com sucesso.\n")


def ensure(module: str,
           apt_pkg: str | None = None,
           pip_pkg: str | None = None) -> None:
    import importlib

    try:
        importlib.import_module(module)
        return
    except ImportError:
        pass

    apt_pkg = apt_pkg or f"python3-{module.replace('.', '-')}"
    pip_pkg = pip_pkg or module

    try:
        subprocess.run(["sudo", "apt", "update", "-qq"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["sudo", "apt", "install", "-y", "--no-install-recommends",
                        apt_pkg], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        importlib.import_module(module)
        print(f"✓ {module} disponível via APT ({apt_pkg})")
        return
    except Exception:
        print(f"APT falhou para {apt_pkg}; tentando pip…")

    try:
        pip_cmd = ["sudo", sys.executable, "-m", "pip", "install", "--no-cache-dir", pip_pkg]
        if VERSAO_UBUNTU >= 24.04:
            pip_cmd.insert(5, "--break-system-packages")

        subprocess.run(pip_cmd, check=True)
        importlib.import_module(module)
        print(f"✓ {module} instalado via pip ({pip_pkg})")
        return
    except Exception:
        print(f"✗ Falha ao instalar {module} via pip ({pip_pkg})")


def instalar_dependencias():
    garantir_pip()

    ensure("mysql.connector",
           apt_pkg="python3-mysql.connector",
           pip_pkg="mysql-connector-python")

    ensure("yaml",
           apt_pkg="python3-yaml",
           pip_pkg="PyYAML")

    ensure("glances",
           apt_pkg="python3-glances",
           pip_pkg="glances[web]")
