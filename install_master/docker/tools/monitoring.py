import os
import textwrap
import time
import subprocess

from install_master.core.docker_base import DockerBase


class MixinMonitoring(DockerBase):
    def iniciar_monitoramento(self):
        print("Iniciando instalação de monitoramento com Prometheus, Node Exporter e Grafana.")
        conteudo = textwrap.dedent("""\
        global:
          scrape_interval: 5s
          evaluation_interval: 5s

        scrape_configs:
          - job_name: 'prometheus'
            static_configs:
              - targets: ['mon_prometheus:9090']

          - job_name: 'node_exporter'
            static_configs:
              - targets: ['mon_node-exporter:9100']
        """)

        caminho_prometheus = f'{self.install_principal}/monitoramento/prometheus/prometheus.yml'
        os.makedirs(os.path.dirname(caminho_prometheus), exist_ok=True)
        os.chmod(os.path.dirname(caminho_prometheus), 0o777)
        if not os.path.exists(caminho_prometheus):
            with open(caminho_prometheus, 'w') as f:
                f.write(conteudo)
        
        caminho_grafana = f'{self.install_principal}/monitoramento/grafana'
        os.makedirs(caminho_grafana, exist_ok=True)
        os.chmod(caminho_grafana, 0o777)
        
        # -p 9090:9090 \
        # -p 9100:9100 \
        comandos = [
            f"""docker run -d \
            --name mon_prometheus \
            --restart=unless-stopped \
            --memory=256m \
            --cpus=1 \
            -v {caminho_prometheus}:/etc/prometheus/prometheus.yml \
            prom/prometheus
            """,
            f"""docker run -d \
            --name mon_node-exporter \
            --restart=unless-stopped \
            --memory=256m \
            --cpus=1 \
            prom/node-exporter
            """,
            f"""docker run -d \
            --name mon_grafana \
            --restart=unless-stopped \
            --memory=256m \
            --cpus=1 \
            -p 3000:3000 \
            -v {caminho_grafana}:/var/lib/grafana \
            grafana/grafana
            """,
        ]
        self.remove_container('mon_prometheus')
        self.remove_container('mon_node-exporter')
        self.remove_container('mon_grafana')
        self.executar_comandos(comandos)
        self.cria_rede_docker(associar_container_nome='mon_prometheus', numero_rede=1)
        self.cria_rede_docker(associar_container_nome='mon_node-exporter', numero_rede=1)
        self.cria_rede_docker(associar_container_nome='mon_grafana', numero_rede=1)
        
        print('Acesse o Grafana em http://<seu_ip>:3000')
        print('Usuario e Senha padrão: admin/admin')
        resposta = input('Deseja ver um exemplo de json para o Grafana?: S ou N: ')
        if resposta.lower() == 's':
            print(textwrap.dedent("""\
            {
                "annotations": {
                    "list": [
                    {
                        "builtIn": 1,
                        "datasource": {
                        "type": "grafana",
                        "uid": "-- Grafana --"
                        },
                        "enable": true,
                        "hide": true,
                        "iconColor": "rgba(0, 211, 255, 1)",
                        "name": "Annotations & Alerts",
                        "type": "dashboard"
                    }
                    ]
                },
                "editable": true,
                "fiscalYearStartMonth": 0,
                "graphTooltip": 0,
                "id": 1,
                "links": [],
                "panels": [
                    {
                    "datasource": {
                        "type": "prometheus",
                        "uid": "belsuah7zhqm8d"
                    },
                    "fieldConfig": {
                        "defaults": {
                        "color": {
                            "mode": "palette-classic"
                        },
                        "custom": {
                            "axisBorderShow": false,
                            "axisCenteredZero": false,
                            "axisColorMode": "text",
                            "axisLabel": "",
                            "axisPlacement": "auto",
                            "barAlignment": 0,
                            "barWidthFactor": 0.6,
                            "drawStyle": "line",
                            "fillOpacity": 0,
                            "gradientMode": "none",
                            "hideFrom": {
                            "legend": false,
                            "tooltip": false,
                            "viz": false
                            },
                            "insertNulls": false,
                            "lineInterpolation": "smooth",
                            "lineStyle": {
                            "fill": "solid"
                            },
                            "lineWidth": 1,
                            "pointSize": 5,
                            "scaleDistribution": {
                            "type": "linear"
                            },
                            "showPoints": "auto",
                            "spanNulls": false,
                            "stacking": {
                            "group": "A",
                            "mode": "none"
                            },
                            "thresholdsStyle": {
                            "mode": "off"
                            }
                        },
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                            {
                                "color": "green"
                            },
                            {
                                "color": "red",
                                "value": 80
                            }
                            ]
                        }
                        },
                        "overrides": []
                    },
                    "gridPos": {
                        "h": 8,
                        "w": 12,
                        "x": 0,
                        "y": 0
                    },
                    "id": 1,
                    "options": {
                        "legend": {
                        "calcs": [],
                        "displayMode": "list",
                        "placement": "bottom",
                        "showLegend": true
                        },
                        "tooltip": {
                        "hideZeros": false,
                        "mode": "single",
                        "sort": "none"
                        }
                    },
                    "pluginVersion": "12.0.0",
                    "targets": [
                        {
                        "datasource": {
                            "type": "prometheus",
                            "uid": "felsgfpj8hg5cb"
                        },
                        "disableTextWrap": false,
                        "editorMode": "code",
                        "expr": "100 - (avg by(instance)(\r\n        rate(node_cpu_seconds_total{mode=\"idle\"}[30s])\r\n      ) * 100)",
                        "fullMetaSearch": false,
                        "includeNullMetadata": true,
                        "legendFormat": "CPU",
                        "range": true,
                        "refId": " CPU",
                        "useBackend": false
                        },
                        {
                        "datasource": {
                            "type": "prometheus",
                            "uid": "felsgfpj8hg5cb"
                        },
                        "editorMode": "code",
                        "expr": "100 * (\r\n  1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)\r\n)",
                        "hide": false,
                        "instant": false,
                        "legendFormat": "RAM",
                        "range": true,
                        "refId": "RAM usada"
                        },
                        {
                        "datasource": {
                            "type": "prometheus",
                            "uid": "felsgfpj8hg5cb"
                        },
                        "editorMode": "code",
                        "expr": "100 * (\r\n  1 - (node_memory_SwapFree_bytes / ignoring(job,instance) node_memory_SwapTotal_bytes)\r\n)\r\n\r\n",
                        "hide": false,
                        "instant": false,
                        "legendFormat": "SWAP",
                        "range": true,
                        "refId": "SWAP"
                        }
                    ],
                    "title": "Painel principal",
                    "type": "timeseries"
                    },
                    {
                    "datasource": {
                        "type": "prometheus",
                        "uid": "belsuah7zhqm8d"
                    },
                    "fieldConfig": {
                        "defaults": {
                        "color": {
                            "mode": "palette-classic"
                        },
                        "custom": {
                            "axisBorderShow": false,
                            "axisCenteredZero": false,
                            "axisColorMode": "text",
                            "axisLabel": "",
                            "axisPlacement": "auto",
                            "barAlignment": 0,
                            "barWidthFactor": 0.6,
                            "drawStyle": "line",
                            "fillOpacity": 0,
                            "gradientMode": "none",
                            "hideFrom": {
                            "legend": false,
                            "tooltip": false,
                            "viz": false
                            },
                            "insertNulls": false,
                            "lineInterpolation": "smooth",
                            "lineWidth": 1,
                            "pointSize": 5,
                            "scaleDistribution": {
                            "type": "linear"
                            },
                            "showPoints": "auto",
                            "spanNulls": false,
                            "stacking": {
                            "group": "A",
                            "mode": "none"
                            },
                            "thresholdsStyle": {
                            "mode": "off"
                            }
                        },
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                            {
                                "color": "green"
                            },
                            {
                                "color": "red",
                                "value": 80
                            }
                            ]
                        },
                        "unit": "decmbytes"
                        },
                        "overrides": []
                    },
                    "gridPos": {
                        "h": 8,
                        "w": 12,
                        "x": 12,
                        "y": 0
                    },
                    "id": 2,
                    "options": {
                        "legend": {
                        "calcs": [],
                        "displayMode": "list",
                        "placement": "bottom",
                        "showLegend": true
                        },
                        "tooltip": {
                        "hideZeros": false,
                        "mode": "single",
                        "sort": "none"
                        }
                    },
                    "pluginVersion": "12.0.0",
                    "targets": [
                        {
                        "editorMode": "code",
                        "expr": "rate(node_disk_read_bytes_total{device!~\"^(loop|ram|fd|sr0).*\"}[10s]) / 1024 / 1024",
                        "legendFormat": "Leitura",
                        "range": true,
                        "refId": "A"
                        },
                        {
                        "datasource": {
                            "type": "prometheus",
                            "uid": "felsgfpj8hg5cb"
                        },
                        "editorMode": "code",
                        "expr": "rate(node_disk_written_bytes_total{device!~\"^(loop|ram|fd|sr0).*\"}[10s]) / 1024 / 1024\r\n",
                        "hide": false,
                        "instant": false,
                        "legendFormat": "Escrita",
                        "range": true,
                        "refId": "B"
                        }
                    ],
                    "title": "DISCO",
                    "type": "timeseries"
                    }
                ],
                "preload": false,
                "refresh": "auto",
                "schemaVersion": 41,
                "tags": [],
                "templating": {
                    "list": []
                },
                "time": {
                    "from": "now-5m",
                    "to": "now"
                },
                "timepicker": {},
                "timezone": "browser",
                "title": "Principal dashboard",
                "uid": "e5dc7514-6689-4a2c-a78f-3be4a3be041e",
                "version": 4
            }
            """))
