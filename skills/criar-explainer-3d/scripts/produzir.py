"""Produzir uma animação editável com Blender e FFmpeg. Python 3.9+."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import montar

SKILL = Path(__file__).resolve().parents[1]
ASSETS = SKILL / "assets"
SCRIPTS = SKILL / "scripts"
EXEMPLOS = {"vila": "vila", "fila": "fila-unica", "cisterna": "cisterna", "eremita": "eremita"}


def executavel(nome):
    resolvido = shutil.which(nome)
    if resolvido:
        return resolvido
    if nome == "blender" and sys.platform == "darwin":
        mac = Path("/Applications/Blender.app/Contents/MacOS/Blender")
        if mac.is_file():
            return str(mac)
    raise ValueError(f"Não encontrei {nome}. Confira references/primeiro-video.md e o PATH do terminal.")


def arquivo(path):
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise ValueError(f"Arquivo ausente: {path}")
    return path


def png_completo(caminho):
    """Conferir a assinatura e o marcador final gravado pelo Blender."""
    try:
        with caminho.open("rb") as imagem:
            if imagem.read(8) != b"\x89PNG\r\n\x1a\n":
                return False
            imagem.seek(-12, 2)
            return imagem.read() == b"\x00\x00\x00\x00IEND\xae\x42\x60\x82"
    except OSError:
        return False


def renderizar_vila(blender, saida, ultimo_quadro, threads):
    """Reiniciar o Blender entre blocos para liberar a memória do renderizador."""
    pasta = (saida / "frames").resolve()
    projeto = arquivo(saida / "cena.blend")
    comando = [blender, "-b", str(projeto)]
    if threads:
        comando += ["-t", str(threads)]
    comando += ["-o", str(pasta / "####")]
    inicio = 1
    tamanho = 12
    falhas_sem_progresso = 0
    while inicio <= ultimo_quadro:
        fim = min(inicio + tamanho - 1, ultimo_quadro)
        proc = subprocess.run([*comando, "-s", str(inicio), "-e", str(fim), "-a"])
        faltante = next((n for n in range(inicio, fim + 1)
                         if not png_completo(pasta / f"{n:04d}.png")), None)
        if faltante is None:
            inicio = fim + 1
            falhas_sem_progresso = 0
            continue
        falhas_sem_progresso = falhas_sem_progresso + 1 if faltante == inicio else 0
        detalhe = f"Blender retornou {proc.returncode} e o quadro {faltante} ficou incompleto."
        if falhas_sem_progresso >= 2:
            raise ValueError(f"{detalhe} Os quadros concluídos continuam em {pasta}.")
        print(f"{detalhe} Retomando a partir dele em blocos menores.", file=sys.stderr)
        inicio = faltante
        tamanho = 4


def executar(args):
    blender = executavel(args.blender)
    if args.quadro is None:
        for nome in ("ffmpeg", "ffprobe"):
            executavel(nome)
    exemplo = args.exemplo or "vila"
    if args.cena:
        if not args.roteiro:
            raise ValueError("Para uma cena própria, informe também --roteiro.")
        cena = arquivo(args.cena)
        roteiro = arquivo(args.roteiro)
    else:
        if args.roteiro:
            raise ValueError("Use --cena para combinar uma cena com --roteiro.")
        cena = arquivo(ASSETS / (EXEMPLOS[exemplo] + ".json"))
        roteiro = arquivo(ASSETS / (exemplo + "-locucao.json"))
    config = json.loads(cena.read_text(encoding="utf-8"))
    texto = json.loads(roteiro.read_text(encoding="utf-8-sig"))
    if not isinstance(texto, dict):
        raise ValueError("O roteiro deve ser um objeto JSON com listas de legendas e/ou fala.")
    fps = 24 if args.qualidade == "final" else int(config.get("fps", 24))
    if fps <= 0 or config["duration"] <= 0:
        raise ValueError("Duração e fps precisam ser positivos.")
    total = round(config["duration"] * fps) / fps
    legendas = montar.ler_trechos(texto.get("legendas", []), total)
    falas = montar.ler_trechos(texto["fala"], total) if "fala" in texto else legendas
    if args.threads is not None and args.threads < 1:
        raise ValueError("--threads precisa ser positivo.")
    if args.quadro is not None and not 1 <= args.quadro <= round(config["duration"] * fps):
        raise ValueError(f"Escolha --quadro de 1 a {round(config['duration'] * fps)}.")
    midia = None
    modelo = None
    if args.voz:
        midia = arquivo(args.voz)
    elif args.piper_modelo:
        modelo = arquivo(args.piper_modelo)
    elif not (args.tts or args.mudo or args.cena or args.quadro):
        midia = arquivo(ASSETS / (exemplo + "-voz.m4a"))
    elif args.cena and not (args.tts or args.mudo or args.quadro):
        raise ValueError("Escolha --voz, --piper-modelo, --tts ou --mudo para a produção nova.")
    efeitos = arquivo(args.efeitos) if args.efeitos else None
    if not (efeitos or args.cena or args.mudo or args.quadro):
        efeito_exemplo = ASSETS / (exemplo + "-efeitos.m4a")
        if efeito_exemplo.is_file():
            efeitos = efeito_exemplo
    if midia and not args.quadro:
        info = montar.dados_midia(midia)
        faixa = montar.fluxo(info, "audio")
        if not faixa or montar.duracao(info, faixa) > total + 0.10:
            raise ValueError("A duração da locução precisa caber no vídeo.")
    if not args.quadro and (modelo or args.tts):
        montar.motor_voz(modelo)
        if not falas:
            raise ValueError("Inclua uma trilha de fala para sintetizar voz.")
    diretor = config.get("modelo", "cena")
    diretores = {"vila": SCRIPTS / "filmar_vila.py", "cena": SCRIPTS / "cena_3d.py"}
    if diretor not in diretores:
        raise ValueError(f"Modelo de cena desconhecido: {diretor}. Use vila ou cena.")
    modelos_locais = {}
    for entidade in config["entities"] if diretor == "cena" else []:
        if entidade.get("type") != "glb":
            continue
        origem = arquivo(cena.parent / entidade["file"])
        if origem.suffix.lower() != ".glb":
            raise ValueError(f"O modelo precisa ser um GLB autocontido: {origem.name}")
        if origem not in modelos_locais:
            modelos_locais[origem] = Path("modelos") / f"{len(modelos_locais) + 1:02d}-{origem.name}"
        entidade["file"] = modelos_locais[origem].as_posix()
    saida = Path(args.saida).expanduser().resolve()
    saida.mkdir(parents=True, exist_ok=False)
    fontes = saida / "fontes"
    fontes.mkdir()
    cena_salva = fontes / "cena.json"
    if modelos_locais:
        (fontes / "modelos").mkdir()
        for origem, destino_relativo in modelos_locais.items():
            shutil.copyfile(origem, fontes / destino_relativo)
        cena_salva.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        shutil.copyfile(cena, cena_salva)
    shutil.copyfile(roteiro, fontes / "locucao.json")
    if midia:
        destino = fontes / ("voz" + midia.suffix)
        shutil.copyfile(midia, destino)
        midia = destino
    if not args.quadro and (modelo or args.tts):
        with tempfile.TemporaryDirectory(dir=saida) as temporario:
            sintetizada = montar.sintetizar(falas, Path(temporario), total, modelo)
            midia = fontes / "voz.wav"
            shutil.copyfile(sintetizada, midia)
    if efeitos:
        destino = fontes / ("efeitos" + efeitos.suffix)
        shutil.copyfile(efeitos, destino)
        efeitos = destino
    comando = [blender, "-b"]
    if args.threads:
        comando += ["-t", str(args.threads)]
    comando += ["--python-exit-code", "1", "-P", str(diretores[diretor]),
               "--", "--scene", str(cena_salva), "--out", str(saida)]
    if args.qualidade == "final":
        comando += ["--width", "1080", "--height", "1920", "--fps", "24", "--samples", "32"]
    if args.quadro:
        comando += ["--still", str(args.quadro)]
    elif diretor != "vila":
        comando += ["--render"]
    subprocess.run(comando, check=True)
    if args.quadro:
        print(f"Quadro de revisão e cena editável em {saida}")
        return
    if diretor == "vila":
        renderizar_vila(blender, saida, round(config["duration"] * fps), args.threads)
    comando = [sys.executable, str(SCRIPTS / "montar.py"), "--quadros", str(saida / "frames"),
               "--fps", str(fps), "--roteiro", str(roteiro), "--saida", str(saida / "final.mp4")]
    if texto.get("legendas"):
        comando += ["--srt", str(saida / "legendas.srt")]
    if midia:
        comando += ["--voz", str(midia)]
    if efeitos:
        comando += ["--efeitos", str(efeitos)]
    subprocess.run(comando, check=True)
    print(f"Vídeo: {saida / 'final.mp4'}\nBlender: {saida / 'cena.blend'}")
    if texto.get("legendas"):
        print(f"Legendas: {saida / 'legendas.srt'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", required=True, help="Pasta nova para esta versão.")
    entrada = parser.add_mutually_exclusive_group()
    entrada.add_argument("--exemplo", choices=EXEMPLOS)
    entrada.add_argument("--cena", help="JSON de cena próprio.")
    parser.add_argument("--roteiro", help="JSON com falas e legendas.")
    parser.add_argument("--qualidade", choices=["previa", "final"], default="previa",
                        help="Prévia usa a resolução/fps do JSON. Final usa 1080×1920 a 24 fps.")
    parser.add_argument("--quadro", type=int, help="Criar .blend e um quadro numerado a partir de 1.")
    parser.add_argument("--threads", type=int, help="Quantidade de threads usadas pelo Blender.")
    parser.add_argument("--blender", default="blender", help="Nome ou caminho ao executável.")
    voz = parser.add_mutually_exclusive_group()
    voz.add_argument("--voz", help="Narração já alinhada ao roteiro.")
    voz.add_argument("--piper-modelo", help="Modelo ONNX local para síntese com Piper.")
    voz.add_argument("--tts", action="store_true", help="Usar uma voz de sistema disponível.")
    voz.add_argument("--mudo", action="store_true", help="Produzir a versão sem locução.")
    parser.add_argument("--efeitos", help="Mix de efeitos a partir do instante zero.")
    args = parser.parse_args()
    try:
        executar(args)
    except FileExistsError as exc:
        parser.exit(2, f"A pasta já existe: {exc.filename}. Use uma nova pasta para a revisão.\n")
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f"Produção interrompida: {exc}\n")


if __name__ == "__main__":
    main()
