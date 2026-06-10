import os
import configparser
import subprocess

from install_master.core.docker_base import DockerBase


class MixinRclone(DockerBase):
    def rclone(self):
        """Instala e executa o rclone."""
        print("\nIniciando instalação rclone:")
        print(40*"*")
        print(40*"*")
        print("Para mais informações acesse: https://rclone.org")
        print(40*"*")
        print(40*"*")
        
        self.remove_container("rclone-setup")
        self.remove_container("rclone")

        conf_path = f"{self.install_principal}/rclone/config"
        run_args1 = [
            "--name", "rclone-setup",
            "-it",
            "-v", f"{conf_path}:/config/rclone",
            "--rm",
            "rclone/rclone:latest",
            "config",
        ]

        self.executar_comandos_run_OrAnd_dockerfile( run_cmd=run_args1 )
        
        # 1) Carrega o arquivo
        read_conf_path = os.path.join(conf_path, "rclone.conf")
        config = configparser.ConfigParser()
        config.read(read_conf_path)

        # 2) Para cada seção (remote), cria a pasta no host
        base_mount = f"{self.install_principal}/rclone/rclone_remotes"
        base_container = "/data"
        entrypoint = []
        for remote in config.sections():
            # remote é algo como 'gdrive', 'nextcloud', 'dropbox', etc.
            dest = os.path.join(base_mount, remote)
            dest_cont = os.path.join(base_container, remote)
            subprocess.run(["fusermount3", "-u", dest], check=False)
            os.makedirs(dest, exist_ok=True)
            os.chmod(dest, 0o777)
            entrypoint.append(f"mkdir -p {dest_cont} && chmod 777 {dest_cont}; ")
            # --no-update-config
            # entrypoint.append(f"rclone mount {remote}: /data/{remote} & ")
            # entrypoint.append(f"rclone mount {remote}: /data/{remote} --vfs-cache-mode=full & ")
            entrypoint.append(f"rclone mount {remote}: /data/{remote} "
                    f"--vfs-cache-mode=full "
                    f"--vfs-cache-max-size=10M "
                    f"--vfs-cache-max-age=1m "
                    f"--dir-cache-time=30s "
                    f"--poll-interval=30s "
                    f"& ")
        
        entrypoint.append("wait")
        # Concatena tudo numa única string
        entrypoint = "".join(entrypoint)
        print(entrypoint)
        
        pasta_cache = f"{self.install_principal}/rclone/cache"
        os.makedirs(pasta_cache, exist_ok=True)
        os.chmod(pasta_cache, 0o777)
        
        run_args = [
            "--name", "rclone",
            "--restart=unless-stopped",
            "--memory=256m",
            "--cpus=1",
            "-e", "RCLONE_CONFIG=/config/rclone/rclone.conf",
            "-v", f"{conf_path}:/config/rclone",
            "-v", f"{base_mount}:/data:shared",
            "-v", f"{pasta_cache}:/root/.cache/rclone",
            "-v", "/etc/passwd:/etc/passwd:ro",
            "-v", "/etc/group:/etc/group:ro",
            "--user", f"{os.getuid()}:{os.getgid()}",
            "--device", "/dev/fuse",
            "--cap-add", "SYS_ADMIN",
            "--security-opt", "apparmor:unconfined",
            "-d",
            "--entrypoint", "sh",
            "rclone/rclone:latest",
            "-c", entrypoint
        ]
        
        self.executar_comandos_run_OrAnd_dockerfile( run_cmd=run_args )
        self.cria_rede_docker(associar_container_nome='rclone', numero_rede=1)
