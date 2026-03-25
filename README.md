# TVI Player — Enigma2/OpenVIX Plugin

*Enigma2 plugin to watch TVI Player VOD content (free and subscription) directly on your set-top box.*
*Plugin para Enigma2 para ver conteúdos de VOD do TVI Player (gratuitos e com conta) diretamente na sua box.*

---

## English

### Features
- Browse shows by category (Ficção, Entretenimento, Informação, CNN, Filmes)
- View episode list with air dates
- Play videos in full quality with full controls (pause, seek, fast-forward)

### Requirements
- Set-top box running **Enigma2 / OpenVIX** with Python 3 (e.g. VU+ UNO 4K SE or compatible)
- Internet connection
- TVI Player account (free at [tviplayer.iol.pt](https://tviplayer.iol.pt/))

### Installation

**Option 1 — From the `.ipk` file**

1. Download the `.ipk` from the [Releases page](../../releases)
2. Copy it to your box:
   ```bash
   scp enigma2-plugin-extensions-tviplayer_1.0.0_all.ipk root@<BOX-IP>:/tmp/
   ```
3. Install on the box:
   ```bash
   opkg install /tmp/enigma2-plugin-extensions-tviplayer_1.0.0_all.ipk
   killall enigma2
   ```

**Option 2 — Build from source**

```bash
git clone https://github.com/dyingstr/tviplayer-enigma2.git
cd tviplayer-enigma2
bash build_ipk.sh
```

### Configuration

Create the file `/etc/enigma2/tviplayer.json` on your box with your credentials:

```json
{
  "email": "your-email@example.com",
  "password": "your-password"
}
```

### Usage

1. Open the **Plugins** menu on your box
2. Select **TVI Player**
3. Choose a category, then a show, then an episode
4. The video starts automatically

| Button | Action |
|---|---|
| OK | Show/hide info bar |
| Play/Pause | Pause or resume |
| Stop (■) | Back to episode list |
| ◄◄ / ►► | Seek −10s / +30s |
| ← / → arrow | Navigate seek bar |

---

## Português

### Funcionalidades
- Navegar pelos programas por categoria (Ficção, Entretenimento, Informação, CNN, Filmes)
- Ver a lista de episódios com data de emissão
- Reproduzir vídeos em qualidade original com controlos completos (pausa, avanço, recuo)

### Requisitos
- Box com **Enigma2 / OpenVIX** e Python 3 (ex: VU+ UNO 4K SE ou compatível)
- Ligação à internet
- Conta TVI Player (gratuita em [tviplayer.iol.pt](https://tviplayer.iol.pt/))

### Instalação

**Opção 1 — A partir do ficheiro `.ipk`**

1. Faça o download do ficheiro `.ipk` na [página de releases](../../releases)
2. Copie para a box:
   ```bash
   scp enigma2-plugin-extensions-tviplayer_1.0.0_all.ipk root@<IP-DA-BOX>:/tmp/
   ```
3. Instale na box:
   ```bash
   opkg install /tmp/enigma2-plugin-extensions-tviplayer_1.0.0_all.ipk
   killall enigma2
   ```

**Opção 2 — Compilar a partir do código fonte**

```bash
git clone https://github.com/dyingstr/tviplayer-enigma2.git
cd tviplayer-enigma2
bash build_ipk.sh
```

### Configuração

Crie o ficheiro `/etc/enigma2/tviplayer.json` na box com as suas credenciais:

```json
{
  "email": "o-seu-email@exemplo.com",
  "password": "a-sua-password"
}
```

### Utilização

1. Abra o menu de **Plugins** na sua box
2. Selecione **TVI Player**
3. Escolha uma categoria, depois um programa e um episódio
4. O vídeo inicia automaticamente

| Botão | Ação |
|---|---|
| OK | Mostrar/esconder barra de informação |
| Play/Pause | Pausar ou retomar |
| Stop (■) | Voltar à lista de episódios |
| ◄◄ / ►► | Recuar 10s / Avançar 30s |
| ← / → (seta) | Navegar na barra de tempo |

---

## Notes / Notas

- Tested on VU+ UNO 4K SE with OpenVIX / Testado em VU+ UNO 4K SE com OpenVIX
- This plugin is not affiliated with Grupo Media Capital / TVI / Este plugin não é afiliado ao Grupo Media Capital / TVI
