# Separador de Voz

Aplicativo desktop para Windows que extrai a faixa de áudio de um vídeo, separa
voz e instrumentos e salva somente a voz em um arquivo WAV.

## Instalação

1. Instale o Python 3.10 ou superior para Windows e marque **Add Python to PATH**.
2. Execute `instalar.bat` e aguarde a instalação das dependências.
3. Execute `iniciar.bat` para abrir o aplicativo.

Também é possível executar `iniciar.bat` diretamente: na primeira vez, ele
instala as dependências automaticamente. A cada inicialização, ele também
verifica se o Demucs está instalado e repara a instalação se necessário. Se a
instalação falhar, confira a conexão com a internet, execute `instalar.bat` e
tente novamente. É necessária uma conexão com a internet durante a instalação
e na primeira separação, quando o modelo de voz é baixado. O modelo fica em
cache para os próximos usos.

## Como usar

1. Clique em **Escolher vídeo...** e selecione o arquivo da música.
2. Confirme o destino do áudio (por padrão, ao lado do vídeo, com o sufixo
   `_voz.wav`) ou escolha outro.
3. Clique em **Separar voz**. A barra mostra a porcentagem estimada do
   processamento, e o WAV resultante contém a voz separada. A porcentagem pode
   ficar parada durante o carregamento ou o download inicial do modelo.

O aplicativo aceita vídeos com faixa de áudio que o FFmpeg consiga ler. A
separação usa o modelo `htdemucs` e pode levar alguns minutos, dependendo do
computador. O aplicativo não envia o vídeo para um serviço online: o
processamento é feito localmente.

## Desenvolvimento

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```
