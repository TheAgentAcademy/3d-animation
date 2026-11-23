#!/usr/bin/env python3
"""Monta quadros de Blender, voz, efeitos e legendas em um MP4 local."""
import argparse
from dataclasses import dataclass
from fractions import Fraction
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import wave


def executar(comando, **opcoes):
    return subprocess.run([str(s) for s in comando], check=True, **opcoes)


def dados_midia(arquivo):
    dados = executar(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                      "-of", "json", arquivo], capture_output=True)
    return json.loads(dados.stdout)


def fluxo(dados, tipo):
    return next((s for s in dados["streams"] if s["codec_type"] == tipo), None)


def duracao(dados, stream):
    for valor in (stream.get("duration"), dados["format"].get("duration")):
        if valor and valor != "N/A":
            return float(valor)
    raise ValueError("O arquivo não informa sua duração.")


def abrir_visual(args):
    if args.video:
        arquivo = args.video.resolve(strict=True)
        info = dados_midia(arquivo)
        video = fluxo(info, "video")
        if not video:
            raise ValueError("O arquivo de entrada precisa de uma faixa de vídeo.")
        return (["-i", arquivo], video, duracao(info, video), fluxo(info, "audio") is not None)
    pasta = args.quadros.resolve(strict=True)
    fotos = [p for p in pasta.iterdir() if p.suffix == ".png"]
    if not fotos:
        raise ValueError("Nenhum quadro .png na pasta.")
    partes = []
    for foto in fotos:
        m = re.fullmatch(r"(.*?)(\d+)", foto.stem)
        if not m:
            raise ValueError(f"Esperava um número no fim de {foto.name}.")
        partes.append((int(m[2]), m[1], m[2], foto))
    partes.sort()
    primeiro, prefixo, digitos, arquivo = partes[0]
    largura = len(digitos)
    for offset, (indice, pre, num, _) in enumerate(partes):
        if indice != primeiro + offset or pre != prefixo or num != f"{indice:0{largura}d}":
            raise ValueError("A pasta precisa de uma sequência contínua de PNGs com um único prefixo.")
    padrao = str(pasta).replace("%", "%%") + os.sep + prefixo.replace("%", "%%") + f"%0{largura}d.png"
    fps = Fraction(args.fps or "24")
    if not 0 < fps <= 240:
        raise ValueError("FPS precisa ser positivo e de até 240.")
    return (["-framerate", str(fps), "-start_number", str(primeiro), "-i", padrao],
            fluxo(dados_midia(arquivo), "video"), len(partes) / float(fps), False)


@dataclass
class Trecho:
    inicio: float
    fim: float
    texto: str
    destaque: str


def ler_trechos(lista, total):
    if not isinstance(lista, list):
        raise ValueError("Cada trilha deve ser uma lista.")
    trechos = []
    for i, item in enumerate(lista, 1):
        if not isinstance(item, dict):
            raise ValueError(f"O trecho {i} precisa ser um objeto JSON.")
        inicio, fim = (float(item[chave]) for chave in ("inicio", "fim"))
        texto = item["texto"]
        destaque = item.get("destaque", "")
        if not isinstance(texto, str) or not texto.strip() or not isinstance(destaque, str):
            raise ValueError(f"Texto inválido no trecho {i}.")
        anterior = trechos[-1].fim if trechos else 0
        if not (anterior <= inicio < fim <= total + .001):
            raise ValueError(f"Intervalo inválido no trecho {i} ({inicio}–{fim}s; vídeo {total:.3f}s).")
        if destaque and destaque not in texto:
            raise ValueError(f"Destaque ausente do texto do trecho {i}.")
        trechos.append(Trecho(inicio, fim, texto.strip(), destaque))
    return trechos


def relogio(segundos, ass=False):
    base = 100 if ass else 1000
    seg, frac = divmod(round(segundos * base), base)
    hora, seg = divmod(seg, 3600)
    minuto, seg = divmod(seg, 60)
    if ass:
        return f"{hora}:{minuto:02d}:{seg:02d}.{frac:02d}"
    return f"{hora:02d}:{minuto:02d}:{seg:02d},{frac:03d}"


def estilo_texto(texto):
    return (texto.replace("\\", "＼").replace("{", "｛").replace("}", "｝")
            .replace("\r", "").replace("\n", r"\N"))


def gravar_legendas(pasta, trechos, video, estilo_legenda="frase", altura_legenda=0.74):
    largura = 1080
    w, h = int(video["width"]), int(video["height"])
    for dados in video.get("side_data_list", []):
        if abs(int(dados.get("rotation", 0))) % 180 == 90:
            w, h = h, w
            break
    altura = round(largura * h / w)
    tamanho = round(min(largura * .073, altura * .072))
    margem = round(largura * .115)
    estilo = (f"Style: Base,Arial,{tamanho},&H00FFFFFF,&H00FFFFFF,&H0015181C,&H60000000,"
              f"-1,0,0,0,100,100,0,0,1,{tamanho*.062:.1f},0.7,2,{margem},{margem},{round(altura*.18)},1")
    ancora = ""
    if estilo_legenda == "palavra":
        tamanho = round(min(largura * .081, altura * .043))
        fonte = Path(__file__).resolve().parents[1] / "assets" / "vila-legenda.ttf"
        fontes = pasta / "fontes"
        fontes.mkdir()
        shutil.copyfile(fonte, fontes / fonte.name)
        estilo = (f"Style: Base,Open Sans Extrabold,{tamanho},&H00FFFFFF,&H00FFFFFF,&H00101011,&H80000000,"
                  f"-1,0,0,0,100,100,0,0,1,{tamanho*.067:.1f},0.4,5,16,16,0,1")
        centro = round(altura * altura_legenda)
        ancora = rf"{{\an5\pos({largura//2},{centro})}}"
    linhas = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {largura}", f"PlayResY: {altura}",
        "ScaledBorderAndShadow: yes", "WrapStyle: 0", "", "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding", estilo, "", "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    srt = []
    for i, t in enumerate(trechos, 1):
        texto = estilo_texto(t.texto)
        if t.destaque:
            antes, palavra, depois = t.texto.partition(t.destaque)
            texto = (estilo_texto(antes) + r"{\1c&H67E8FF&}" + estilo_texto(palavra)
                     + r"{\1c&HFFFFFF&}" + estilo_texto(depois))
        entrada_texto = ancora
        if estilo_legenda == "palavra":
            if len(t.texto.split()) != 1:
                raise ValueError(f"A legenda {i} precisa de uma única palavra com tempos de entrada e saída.")
            assentar = min(85, max(12, round((t.fim - t.inicio) * 1000) - 24))
            pico = round(assentar * .35)
            entrada_texto += (rf"{{\fscx94\fscy94\t(0,{pico},\fscx108\fscy108)"
                              rf"\t({pico},{assentar},\fscx100\fscy100)}}")
        linhas.append(f"Dialogue: 0,{relogio(t.inicio,True)},{relogio(t.fim,True)},Base,,0,0,0,,{entrada_texto}{texto}")
        srt.append(f"{i}\n{relogio(t.inicio)} --> {relogio(t.fim)}\n{t.texto}\n\n")
    (pasta / "captions.ass").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    (pasta / "captions.srt").write_text("".join(srt), encoding="utf-8")


def motor_voz(modelo):
    if modelo:
        piper = shutil.which("piper")
        if not piper:
            raise ValueError("Instale o Piper e deixe o comando piper no PATH para usar --piper-modelo.")
        modelo = modelo.resolve(strict=True)
        Path(str(modelo) + ".json").resolve(strict=True)
        return lambda saida, texto: executar([piper, "-m", modelo, "-f", saida], input=(texto + "\n").encode())
    espeak = shutil.which("espeak-ng") or shutil.which("espeak")
    if espeak:
        return lambda saida, texto: executar([espeak, "-v", "pt-br", "-s", "165", "-w", saida, "--stdin"],
                                              input=texto.encode())
    if shutil.which("say"):
        vozes = executar(["say", "-v", "?"], capture_output=True, text=True).stdout
        voz = re.search(r"^(.+?)\s+pt[_-]BR\s+", vozes, re.M | re.I)
        if voz:
            return lambda saida, texto: executar(["say", "-v", voz[1].strip(), "-o", saida,
                "--file-format=WAVE", "--data-format=LEI16@24000", "-f", "-"], input=texto.encode())
    raise ValueError("Instale espeak-ng ou uma voz pt_BR para say, indique --piper-modelo, ou passe --voz arquivo.wav.")


def sintetizar(trechos, pasta, total, modelo):
    if not trechos:
        raise ValueError("Inclua uma trilha de fala ou legendas no roteiro para a síntese.")
    falar = motor_voz(modelo)
    taxa = 24000
    saida = pasta / "locucao.wav"
    posicao = 0
    with wave.open(str(saida), "wb") as audio:
        audio.setparams((1, 2, taxa, 0, "NONE", "not compressed"))
        for i, t in enumerate(trechos, 1):
            amostra = pasta / f"frase{i}.wav"
            falar(amostra, t.texto)
            with wave.open(str(amostra), "rb") as wav:
                segundos = wav.getnframes() / wav.getframerate()
            janela = t.fim - t.inicio
            velocidade = max(1.0, segundos / janela)
            if velocidade > 1.28:
                raise ValueError(f"A fala {i} precisa de {segundos:.2f}s em uma janela de {janela:.2f}s. "
                                 "Encurte a frase ou amplie a janela.")
            filtro = f"atempo={velocidade:.6f}" if velocidade > 1.0001 else "anull"
            pcm = executar(["ffmpeg", "-v", "error", "-i", amostra, "-af", filtro, "-ar", str(taxa),
                            "-ac", "1", "-f", "s16le", "-"], capture_output=True).stdout
            inicio = round(t.inicio * taxa)
            maximo = round(t.fim * taxa) - inicio
            audio.writeframesraw(b"\x00\x00" * (inicio - posicao))
            pcm = pcm[:maximo * 2]
            audio.writeframesraw(pcm)
            posicao = inicio + len(pcm) // 2
        audio.writeframesraw(b"\x00\x00" * (round(total * taxa) - posicao))
    return saida


def montar(args):
    for programa in ("ffmpeg", "ffprobe"):
        if not shutil.which(programa):
            raise ValueError(f"Instale {programa} e deixe-o no PATH.")
    if args.fps and args.video:
        raise ValueError("--fps descreve a cadência de --quadros. Para --video, vale a cadência de origem.")
    if not math.isfinite(args.ganho_efeitos) or not -96 <= args.ganho_efeitos <= 0:
        raise ValueError("Escolha --ganho-efeitos entre -96 e 0 dB.")
    entrada, info, total, tem_audio = abrir_visual(args)
    roteiro = json.loads(args.roteiro.read_text(encoding="utf-8-sig")) if args.roteiro else {}
    if not isinstance(roteiro, dict):
        raise ValueError("O roteiro precisa ser um objeto JSON com as trilhas de tempo.")
    estilo_legenda = getattr(args, "estilo_legenda", None) or roteiro.get("estilo_legenda", "frase")
    if estilo_legenda not in ("frase", "palavra"):
        raise ValueError("O estilo de legenda precisa ser frase ou palavra.")
    altura_legenda = float(roteiro.get("altura_legenda", .74))
    if not 0 < altura_legenda < 1:
        raise ValueError("altura_legenda é a posição vertical do centro do texto, entre 0 e 1.")
    legendas = ler_trechos(roteiro.get("legendas", []), total)
    if args.srt and not legendas:
        raise ValueError("Forneça legendas no roteiro para exportar um SRT.")
    saidas = [p.resolve() for p in (args.saida, args.srt) if p]
    if args.saida.suffix.lower() != ".mp4" or (args.srt and args.srt.suffix.lower() != ".srt"):
        raise ValueError("Use a extensão .mp4 para o vídeo e .srt para as legendas.")
    if len(set(saidas)) != len(saidas) or any(p.exists() for p in saidas):
        raise ValueError("Escolha nomes de saída distintos e que ainda não existam.")
    for destino in saidas:
        destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="montagem-", dir=saidas[0].parent) as temporario:
        pasta = Path(temporario)
        gravar_legendas(pasta, legendas, info, estilo_legenda, altura_legenda)
        voz = args.voz
        if args.tts or args.piper_modelo:
            fala = ler_trechos(roteiro["fala"], total) if "fala" in roteiro else legendas
            voz = sintetizar(fala, pasta, total, args.piper_modelo)
        comando = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", *entrada]
        proximo = 1
        voz_stream = "0:a:0" if tem_audio else None
        if voz:
            voz = voz.resolve(strict=True)
            dados = dados_midia(voz)
            faixa = fluxo(dados, "audio")
            if not faixa or duracao(dados, faixa) > total + .10:
                raise ValueError("A locução precisa ser uma faixa de áudio com duração que caiba no vídeo.")
            comando += ["-i", voz]
            voz_stream = f"{proximo}:a:0"
            proximo += 1
        tamanho = f"{total:.9f}"
        audio = (f"[{voz_stream}]aresample=48000,loudnorm=I=-16:TP=-1.8:LRA=9,aresample=48000,"
                 f"aformat=channel_layouts=stereo,apad,atrim=duration={tamanho}[principal]"
                 if voz_stream else f"anullsrc=r=48000:cl=stereo,atrim=duration={tamanho}[principal]")
        if args.efeitos:
            comando += ["-i", args.efeitos.resolve(strict=True)]
            audio += (f";[{proximo}:a:0]aresample=48000,aformat=channel_layouts=stereo,"
                      f"volume={args.ganho_efeitos}dB[fx];[principal][fx]amix=inputs=2:duration=first:"
                      "normalize=0,alimiter=limit=0.84:level=0:latency=1[mix]")
        else:
            audio += ";[principal]anull[mix]"
        filtros_video = ["pad=ceil(iw/2)*2:ceil(ih/2)*2"]
        if legendas:
            filtro_legenda = "ass=captions.ass"
            if estilo_legenda == "palavra":
                filtro_legenda += ":fontsdir=fontes"
            filtros_video.append(filtro_legenda)
        temporario_mp4 = pasta / "montagem.mp4"
        comando += ["-filter_complex", audio, "-map", "0:v:0", "-map", "[mix]", "-vf", ",".join(filtros_video),
                    "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "144k", "-ar", "48000", "-movflags", "+faststart",
                    "-t", tamanho, temporario_mp4]
        if args.video:
            comando[-1:-1] = ["-fps_mode:v", "passthrough"]
        executar(comando, cwd=pasta)
        if args.srt:
            shutil.copyfile(pasta / "captions.srt", saidas[1])
        temporario_mp4.replace(saidas[0])
    print(f"{saidas[0]} ({total:.3f}s)")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    visual = p.add_mutually_exclusive_group(required=True)
    visual.add_argument("--quadros", type=Path, help="Pasta de PNGs numerados consecutivamente.")
    visual.add_argument("--video", type=Path, help="Vídeo pronto. Preserva o áudio se nenhuma voz for indicada.")
    p.add_argument("--fps", help="Cadência dos quadros, inclusive 30000/1001. Padrão 24.")
    p.add_argument("--roteiro", type=Path, help="JSON com legendas e, opcionalmente, fala.")
    p.add_argument("--estilo-legenda", choices=["frase", "palavra"],
                   help="Sobrescreve o estilo_legenda do roteiro. Palavra requer tempos por palavra.")
    audio = p.add_mutually_exclusive_group()
    audio.add_argument("--voz", type=Path, help="Locução gravada e já sincronizada.")
    audio.add_argument("--tts", action="store_true", help="Gera voz offline com espeak-ng, espeak ou say.")
    audio.add_argument("--piper-modelo", type=Path, help="Modelo .onnx pt_BR local do Piper.")
    p.add_argument("--efeitos", type=Path, help="Faixa de efeitos previamente alinhada ao vídeo.")
    p.add_argument("--ganho-efeitos", type=float, default=-12, help="Ganho dos efeitos em dB (padrão -12).")
    p.add_argument("--saida", required=True, type=Path, help="Novo arquivo .mp4.")
    p.add_argument("--srt", type=Path, help="Novo arquivo .srt para edição.")
    try:
        montar(p.parse_args())
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError, wave.Error, ZeroDivisionError) as erro:
        p.exit(1, f"Montagem interrompida: {erro}\n")


if __name__ == "__main__":
    main()
