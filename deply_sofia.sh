echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
echo "Arquivo atualizador.sh iniciado!"
echo " "
echo "Verssão 1.03"
echo " "

GITHUB_TOKEN1=ghp_zLLRYR600etCmYoH3 \
  && GITHUB_TOKEN2=06sMBaJMLgC4k024QI1 \
  && rm -rf Sof-IA/ \
  && git clone https://$GITHUB_TOKEN1$GITHUB_TOKEN2@github.com/mauriciowebme/Sof-IA.git \
  && rsync -a Sof-IA/ app/ \
  && rm -r Sof-IA/ \
  && docker restart node_container

echo " "
echo "Arquivo atualizador.sh terminado com sucesso!"
echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "

