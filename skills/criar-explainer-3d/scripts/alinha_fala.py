"""Criar voz e legendas por palavra a partir da mesma leitura de um roteiro no Piper."""

import argparse
import json
import math
from pathlib import Path
import string
import tempfile
import wave

from montar import ler_trechos, relogio


def leitura(voz, texto, escala):
    import numpy as np
    from piper.config import SynthesisConfig

    config = SynthesisConfig(length_scale=escala)
    partes = list(voz.synthesize(texto, syn_config=config, include_alignments=True))
    if not partes:
        raise ValueError(f"O sintetizador devolveu silêncio em «{texto}».")
    audio = np.concatenate([parte.audio_int16_array for parte in partes])
    inicios = []
    base = 0
    for parte in partes:
        if not parte.phoneme_alignments:
            raise ValueError("O modelo deve oferecer alinhamento de fonemas.")
        cursor = base
        nova = True
        for marca in parte.phoneme_alignments:
            fonema = marca.phoneme
            if fonema.isspace():
                nova = True
            elif nova and fonema not in "^$,.!?;:()—…":
                inicios.append(cursor)
                nova = False
            cursor += marca.num_samples
        base += len(parte.audio_int16_array)
    amostra = np.abs(audio.astype(np.int32))
    audiveis = np.flatnonzero(amostra > max(55, amostra.max() * 0.011))
    if len(audiveis) == 0:
        raise ValueError(f"Não houve voz audível em «{texto}».")
    taxa = voz.config.sample_rate
    esquerda = max(0, audiveis[0] - round(taxa * 0.035))
    direita = min(len(audio), audiveis[-1] + round(taxa * 0.065))
    return audio[esquerda:direita], [max(0, ponto - esquerda) for ponto in inicios]


def montar_locucao(args, pasta):
    try:
        import numpy as np
        from piper import PiperVoice
    except ImportError as erro:
        raise ValueError(
            "Use um ambiente Python com piper-tts e numpy. Versão testada do Piper: 1.8.0."
        ) from erro
    entrada = json.loads(args.roteiro.read_text(encoding="utf-8-sig"))
    falas = ler_trechos(entrada["fala"], args.duracao)
    if not falas:
        raise ValueError("Informe uma lista de fala com inicio, fim e texto.")
    marcas = entrada.get("destaques", [])
    if not isinstance(marcas, list) or not all(isinstance(x, str) for x in marcas):
        raise ValueError("destaques precisa ser uma lista de palavras.")
    destaques = {x.casefold().strip(string.punctuation) for x in marcas}
    modelo = args.modelo.expanduser().resolve(strict=True)
    Path(str(modelo) + ".json").resolve(strict=True)
    voz = PiperVoice.load(modelo, include_alignments=True)
    taxa = voz.config.sample_rate
    pcm = np.zeros(round(args.duracao * taxa), dtype=np.int16)
    legendas = []
    for i, frase in enumerate(falas, 1):
        origem = round(frase.inicio * taxa)
        limite = round(frase.fim * taxa) - origem
        escala = 1.05
        for tentativa in range(4):
            audio, inicios = leitura(voz, frase.texto, escala)
            if len(audio) <= limite:
                break
            escala = min(escala * 0.97, escala * limite / len(audio) * 0.96)
            if escala < 0.78 or tentativa == 3:
                raise ValueError(f"Frase {i} passa da janela; aumente o fim ou encurte o texto.")
        palavras = frase.texto.split()
        if len(inicios) != len(palavras):
            raise ValueError(
                f"A pronúncia alterou a contagem de palavras na frase {i}. "
                "Escreva números, símbolos e siglas como deverão ser falados."
            )
        pcm[origem : origem + len(audio)] = audio
        tempos = [round((origem + x) / taxa, 3) for x in inicios]
        ultimo = round(min(frase.fim, (origem + len(audio)) / taxa + 0.085), 3)
        for palavra, a, b in zip(palavras, tempos, [*tempos[1:], ultimo]):
            if b <= a:
                raise ValueError(f"Dois fonemas começam juntos na frase {i}. Revise o texto.")
            trecho = {"inicio": a, "fim": b, "texto": palavra}
            if palavra.casefold().strip(string.punctuation) in destaques:
                trecho["destaque"] = palavra
            legendas.append(trecho)
    with wave.open(str(pasta / "voz.wav"), "wb") as arq:
        arq.setparams((1, 2, taxa, 0, "NONE", "not compressed"))
        arq.writeframes(pcm.astype("<i2", copy=False).tobytes())
    roteiro = dict(entrada, estilo_legenda="palavra", legendas=legendas)
    (pasta / "locucao.json").write_text(
        json.dumps(roteiro, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    srt = "".join(
        f"{i}\n{relogio(x['inicio'])} --> {relogio(x['fim'])}\n{x['texto']}\n\n"
        for i, x in enumerate(legendas, 1)
    )
    (pasta / "legendas.srt").write_text(srt, encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--roteiro", type=Path, required=True, help="JSON com trilha fala e lista opcional destaques."
    )
    p.add_argument(
        "--modelo", type=Path, required=True, help="Modelo local .onnx com o seu .onnx.json ao lado."
    )
    p.add_argument("--duracao", type=float, required=True, help="Duração total do vídeo, em segundos.")
    p.add_argument(
        "--saida", type=Path, required=True, help="Pasta nova para voz.wav, locucao.json e legendas.srt."
    )
    args = p.parse_args()
    pasta = args.saida.expanduser().resolve()
    if not math.isfinite(args.duracao) or args.duracao <= 0:
        p.error("--duracao precisa ser positiva.")
    if pasta.exists():
        p.error("--saida deve ser uma pasta nova.")
    try:
        pasta.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".voz-", dir=pasta.parent) as temp:
            arquivos = Path(temp) / "entrega"
            arquivos.mkdir()
            montar_locucao(args, arquivos)
            arquivos.rename(pasta)
    except (OSError, ValueError, KeyError, TypeError) as erro:
        p.exit(1, f"Locução interrompida: {erro}\n")
    print(f"Voz e legendas alinhadas em {pasta}")


if __name__ == "__main__":
    main()
