Intruçõpes de uso

# Para executar 

#atualizador do sistema
wget --no-cache -O - https://raw.githubusercontent.com/mauriciowebme/Scripts_linux/main/atualizador.sh | sudo bash
curl -s -H 'Cache-Control: no-cache' https://raw.githubusercontent.com/mauriciowebme/Scripts_linux/main/atualizador.sh | sudo bash

#criando tarefa no inicializar
wget --no-cache -O - https://raw.githubusercontent.com/mauriciowebme/Scripts_linux/main/inicializar.sh | sudo bash

#instalador do docker 
wget --no-cache -O - https://raw.githubusercontent.com/mauriciowebme/Scripts_linux/main/instala_docker.sh | sudo bash