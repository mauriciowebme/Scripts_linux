import subprocess
import time


class ExecutaComandos:
    def __init__(self):
        pass

    def executar_comandos(self, comandos: list = [], ignorar_erros=False, exibir_resultados=True,
                          comando_direto=False, exibir_executando=True, intervalo: int = 0):
        resultados = {}
        for comando in comandos:
            if intervalo > 0:
                time.sleep(intervalo)
            resultados[comando] = []
            if exibir_resultados and exibir_executando:
                print("\n" + "*" * 40)
                if comando_direto:
                    print(" " * 5 + "---> Executando comando direto: <---")
                else:
                    print(" " * 5 + "---> Executando comando: <---")
                print(" " * 5 + f"{comando}")
                print("*" * 40 + "\n")

            if comando_direto:
                comando_convertido = comando.split()
                try:
                    subprocess.run(comando_convertido, check=True)
                except subprocess.CalledProcessError as e:
                    print(f"Erro ao executar o comando: {e}")
                    print(f"Código de saída: {e.returncode}")
                    resultados[comando] += [e.returncode]
            else:
                processo = subprocess.Popen(
                    comando,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                for linha in processo.stdout:
                    resultados[comando] += [linha]
                    if exibir_resultados:
                        print(linha, end="")

                processo.wait()
                if processo.returncode != 0:
                    print(f"\nErro ao executar comando: {comando}\n")
                    resultados[comando] += ['Erro:True']
                    for linha in processo.stderr:
                        print(linha, end="")
                    if not ignorar_erros:
                        print("Saindo...")
                        exit()

        return resultados
