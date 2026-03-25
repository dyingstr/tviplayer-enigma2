# TVI Player — Plugin para Enigma2/OpenVIX

Plugin para Enigma2 que permite ver os conteúdos gratuitos de VOD do [TVI Player](https://tviplayer.iol.pt/) diretamente na sua box.

## Funcionalidades

- Navegar pelos programas por categoria (Ficção, Entretenimento, Informação, CNN, Filmes)
- Ver a lista de episódios com data de emissão
- Reproduzir vídeos em qualidade original com controlos completos (pausa, avanço, recuo)

## Requisitos

- Box com **Enigma2 / OpenVIX** e Python 3 (ex: VU+ UNO 4K SE ou compatível)
- Ligação à internet
- Conta TVI Player (gratuita em [tviplayer.iol.pt](https://tviplayer.iol.pt/))

## Instalação

### Opção 1 — A partir do ficheiro `.ipk`

1. Faça o download do ficheiro `.ipk` da [página de releases](../../releases)
2. Copie para a box:
   ```bash
   scp enigma2-plugin-extensions-tviplayer_1.0.0_all.ipk root@<IP-DA-BOX>:/tmp/
   ```
3. Instale na box:
   ```bash
   opkg install /tmp/enigma2-plugin-extensions-tviplayer_1.0.0_all.ipk
   killall enigma2
   ```

### Opção 2 — Compilar a partir do código fonte

```bash
git clone https://github.com/dyingstr/tviplayer-enigma2.git
cd tviplayer-enigma2
bash build_ipk.sh
```

O ficheiro `.ipk` será criado na pasta raiz. Instale conforme descrito na Opção 1.

## Configuração

Crie o ficheiro `/etc/enigma2/tviplayer.json` na box com as suas credenciais:

```json
{
  "email": "o-seu-email@exemplo.com",
  "password": "a-sua-password"
}
```

```bash
vi /etc/enigma2/tviplayer.json
```

## Utilização

1. Abra o menu de **Plugins** na sua box
2. Selecione **TVI Player**
3. Escolha uma categoria
4. Selecione um programa e depois um episódio
5. O vídeo inicia automaticamente

### Controlos durante a reprodução

| Botão | Ação |
|---|---|
| OK | Mostrar/esconder barra de informação |
| Play/Pause | Pausar ou retomar |
| Stop (■) | Voltar à lista de episódios |
| ◄◄ / ►► | Recuar 10s / Avançar 30s |
| ← / → (seta) | Navegar na barra de tempo |

## Estrutura do Projeto

```
TVIPlayer/
├── usr/lib/enigma2/python/Plugins/Extensions/TVIPlayer/
│   ├── plugin.py       # Ponto de entrada do plugin
│   ├── api.py          # Cliente HTTP: autenticação, programas, episódios, stream
│   ├── screens.py      # Ecrãs da interface
│   ├── config.py       # Leitura das credenciais
│   └── thumbcache.py   # Cache de miniaturas
├── CONTROL/
│   └── control         # Metadados do pacote .ipk
└── build_ipk.sh        # Script de compilação
```

## Notas

- Os conteúdos são gratuitos e não têm DRM — apenas requerem autenticação no site
- O plugin não armazena nem transmite as credenciais para terceiros
- Testado em VU+ UNO 4K SE com OpenVIX

## Licença

Uso pessoal. Este plugin não é afiliado ao Grupo Media Capital / TVI.
