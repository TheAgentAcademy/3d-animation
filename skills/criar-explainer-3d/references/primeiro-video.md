# Seu primeiro vídeo

## Para usar com um agente

Descompacte o pacote. A pasta criar-explainer-3d precisa conter o arquivo SKILL.md e as subpastas scripts, assets e references. Use um agente com acesso ao terminal do computador onde o Blender está instalado.

| Onde usar | Onde colocar a pasta |
|---|---|
| Claude Code, em um projeto | .claude/skills/criar-explainer-3d/ dentro do projeto |
| Codex, em um projeto | .agents/skills/criar-explainer-3d/ dentro do projeto |
| Outro agente com terminal | Abra a pasta descompactada e peça que leia SKILL.md e execute o pedido ali. |

Exemplo de pedido:

> Use a skill criar-explainer-3d para animar uma mão gigante colhendo as casas de uma rua. Abra direto na praça, use perspectiva, faça as coisas levantarem em sequência e sincronize as palavras à voz brasileira. Entregue o MP4 e a cena editável do Blender.

Outro para produzir algo inédito:

> Faça um Reel de 25 segundos mostrando como uma carta passa pela triagem e chega à caixa de correio certa. Crie uma cena nova. Acompanhe o mesmo envelope do começo ao fim, confira as etapas e entregue a animação com voz em português.

Fontes de instalação de skills: [Claude Code](https://code.claude.com/docs/en/skills) · [Codex](https://developers.openai.com/codex/skills/)

## Para executar no seu computador

Instale Python 3.9 ou superior, Blender e FFmpeg com ffprobe, libx264, AAC e libass. Blender 4.3.2 foi a versão usada nos exemplos. O pacote inclui quatro cenas e as respectivas locuções em português. A vila usa o motor EEVEE do Blender. Os três exemplos de maquete usam Cycles com CPU. Uma conta de narração ou renderização em nuvem é opcional.

Links oficiais: [Blender](https://www.blender.org/download/) · [FFmpeg](https://ffmpeg.org/download.html) · [Python](https://www.python.org/downloads/)

Abra o terminal na pasta criar-explainer-3d, onde aparece SKILL.md. Confira se executáveis respondem com a versão:

```sh
python3 --version
blender --version
ffmpeg -version
ffprobe -version
```

No Windows, use `py -3` no lugar de `python3` se esse for o lançador instalado. Se o Blender estiver fora do PATH, informe o caminho real com `--blender "C:/caminho/para/blender.exe"`. No macOS, o comando de produção também procura o Blender em Applications. Se FFmpeg estiver instalado fora do PATH, acrescente a pasta que contém ffmpeg e ffprobe ao PATH do terminal e reabra-o.

### Rodar um exemplo

```sh
python3 scripts/produzir.py --exemplo vila --saida meu-video
```

Abra **meu-video/final.mp4**. A cena editável está em **meu-video/cena.blend**. Legendas, entradas e os quadros individuais ficam ao lado. Para testar os outros formatos, troque `vila` por `fila` (personagens), `cisterna` (sistema montado em partes) ou `eremita` (trajetória de um animal). Use outro nome de pasta para cada execução. Para uma checagem rápida, acrescente `--quadro 1` e abra o PNG produzido.

A configuração de prévia privilegia rapidez. Para a saída vertical em 1080 × 1920 a 24 fps, acrescente `--qualidade final`. O tempo depende do computador e da cena. O exemplo principal usa 24 fps. Sua pasta de saída contém também o projeto de Blender com o céu e os modelos incorporados.

### Mudar a história

Para adaptar a ação da praça, siga references/vila.md. Para uma cena livre, copie assets/fila-unica.json e assets/fila-locucao.json para uma pasta do seu projeto. Dê um novo nome a cada um. Peça ao agente que adapte a ação, a câmera, os tempos, as falas e as legendas ao novo tema. Grave a locução no celular ou use a voz local descrita em montagem.md. A voz dos exemplos acompanha somente o roteiro correspondente.

```sh
python3 scripts/produzir.py --cena projeto/cena.json --roteiro projeto/locucao.json --voz projeto/minha-voz.m4a --saida projeto/filme-v1
```

### Se uma etapa parar

| O que aparece | Como seguir |
|---|---|
| Pasta de saída já existe | Escolha outro nome. Cada execução preserva a versão anterior. |
| ffmpeg ou ffprobe ausente | Instale ambos e verifique as versões no mesmo terminal que vai rodar o comando. |
| FFmpeg não reconhece o filtro ass/subtitles | Use uma distribuição com libass. No terminal, liste os filtros com ffmpeg -filters. |
| Falas passam do fim ou o vídeo não acompanha a voz | Meça a voz, ajuste falas e legendas no roteiro e ajuste os planos no JSON de cena. |
| Render terminou e a montagem falhou | Conserve os PNGs da pasta frames e siga o comando isolado de references/montagem.md. |
| Precisa ver o enquadramento | Em uma nova pasta, rode com --quadro e um número entre 1 e a duração em segundos multiplicada pelos fps. |

## Para repassar

Envie o arquivo compactado inteiro. A permissão em LICENSE.txt autoriza usar, modificar e redistribuir o material original gratuitamente. Modelos, músicas e vozes que alguém acrescentar conservam suas próprias licenças.
