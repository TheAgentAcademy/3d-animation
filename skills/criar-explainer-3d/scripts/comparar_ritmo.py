#!/usr/bin/env python3
"""Comparar um intervalo de dois vídeos em uma folha de contato local e uma série temporal."""

import argparse
from bisect import bisect_right
from collections import Counter
from fractions import Fraction
import html
import json
from math import ceil
from pathlib import Path
import shutil
from statistics import median
import subprocess
import tempfile

from medir_referencia import extrair, sequencia, sonda

LADO = 64


def segundos(valor):
    try:
        t = Fraction(str(valor))
    except (ValueError, ZeroDivisionError):
        raise argparse.ArgumentTypeError(f"tempo inválido: {valor}") from None
    if t < 0:
        raise argparse.ArgumentTypeError("os tempos precisam ser positivos ou zero")
    return t


def ler_eventos(path, duracao):
    if not path:
        return []
    dados = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(dados, list):
        raise ValueError("o arquivo de eventos precisa conter uma lista")
    eventos = []
    for linha in dados:
        if (
            not isinstance(linha, dict)
            or not isinstance(linha.get("nome"), str)
            or not linha["nome"].strip()
        ):
            raise ValueError("cada evento precisa de um nome")
        e = {"nome": linha["nome"].strip()}
        for fonte in ("ref", "video"):
            if linha.get(fonte) is not None:
                t = segundos(linha[fonte])
                if t >= duracao:
                    raise ValueError(f"{e['nome']}: {fonte} fora da janela de comparação")
                e[fonte] = t
        if len(e) == 1:
            raise ValueError(f"{e['nome']}: inclua o instante de ref, video ou ambos")
        eventos.append(e)
    return eventos


def selecao_quadros(indices):
    # A árvore equilibrada evita o limite de expressão do FFmpeg em vídeos longos.
    if len(indices) == 1:
        return rf"eq(n\,{indices[0]})"
    if indices[-1] - indices[0] + 1 == len(indices):
        return rf"between(n\,{indices[0]}\,{indices[-1]})"
    meio = len(indices) // 2
    esquerda = selecao_quadros(indices[:meio])
    direita = selecao_quadros(indices[meio:])
    return rf"if(lt(n\,{indices[meio]})\,{esquerda}\,{direita})"


def miniaturas_visuais(video, trilha, indices, pasta):
    arquivos = {}
    for i in range(0, len(indices), 40):
        lote = pasta / f"grupo-{i // 40}"
        lote.mkdir()
        miniaturas = extrair(video, trilha, indices[i : i + 40], lote)
        arquivos.update({q: f"{lote.name}/{nome}" for q, nome in miniaturas.items()})
    return arquivos


def medir_quadros(video, trilha, indices):
    # Um único decode com a imagem reduzida por área, apenas nos índices necessários.
    selecao = selecao_quadros(indices)
    filtros = f"select={selecao},scale={LADO}:{LADO}:flags=area,format=gray"
    proc = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-nostdin",
            "-filter_threads",
            "1",
            "-i",
            str(video),
            "-map",
            f"0:{trilha}",
            "-an",
            "-vf",
            filtros,
            "-vsync",
            "0",
            "-c:v",
            "rawvideo",
            "-threads",
            "1",
            "-f",
            "rawvideo",
            "-",
        ],
        stdin=subprocess.DEVNULL,
        capture_output=True,
    )
    if proc.returncode:
        raise ValueError(proc.stderr.decode("utf-8", "replace")[-1200:])
    tamanho = LADO * LADO
    if len(proc.stdout) != len(indices) * tamanho:
        raise ValueError("a quantidade de quadros para medição divergiu da sondagem")
    return {q: proc.stdout[i * tamanho : (i + 1) * tamanho] for i, q in enumerate(indices)}


def contraste(pixels):
    # P90-P10 em cinza 8-bit, quantis empíricos por ordem, sem interpolar.
    hist = Counter(pixels)
    acumulado = 0
    p10 = None
    for tom in sorted(hist):
        acumulado += hist[tom]
        if p10 is None and acumulado >= ceil(len(pixels) * 0.1):
            p10 = tom
        if acumulado >= ceil(len(pixels) * 0.9):
            return tom - p10


def medir(video, inicio, duracao, tempos, visuais, pasta):
    info = sonda(video, "-show_streams")
    trilha = next(
        (
            t
            for t in info.get("streams", [])
            if t.get("codec_type") == "video" and not t.get("disposition", {}).get("attached_pic")
        ),
        None,
    )
    if not trilha:
        raise ValueError(f"{video.name}: faixa de vídeo ausente")
    pts, base, disponivel, _ = sequencia(video, trilha)
    if inicio + duracao > disponivel:
        raise ValueError(f"{video.name}: janela ultrapassa os {float(disponivel):.3f} s de imagem")

    def indice(t):
        return bisect_right(pts, pts[0] + (inicio + t) / base) - 1

    quadros = [indice(t) for t in tempos]
    pixels = medir_quadros(video, trilha["index"], sorted(set(quadros)))
    anterior = None
    serie = []
    movimentos, contrastes = [], []
    for t, q in zip(tempos, quadros):
        atual = pixels[q]
        movimento = None
        if anterior is not None:
            movimento = sum(abs(a - b) for a, b in zip(anterior, atual)) / len(atual)
            movimentos.append(movimento)
        amplitude = contraste(atual)
        contrastes.append(amplitude)
        serie.append(
            {
                "t": float(t),
                "q": q,
                "pts_s": float((pts[q] - pts[0]) * base),
                "variacao": round(movimento, 3) if movimento is not None else None,
                "contraste": amplitude,
            }
        )
        anterior = atual
    pasta.mkdir()
    miniaturas = miniaturas_visuais(video, trilha["index"], sorted({indice(t) for t in visuais}), pasta)
    imagens = [
        {
            "t": float(t),
            "q": indice(t),
            "pts_s": float((pts[indice(t)] - pts[0]) * base),
            "jpeg": pasta.name + "/" + miniaturas[indice(t)],
        }
        for t in visuais
    ]
    return {
        "arquivo": video.name,
        "inicio_s": float(inicio),
        "duracao_fonte_s": float(disponivel),
        "mediana_variacao": round(median(movimentos), 3),
        "mediana_contraste": median(contrastes),
        "amostras": serie,
        "pares": imagens,
    }


def escrever(pasta, dados):
    (pasta / "medidas.json").write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    ref, novo = dados["ref"], dados["video"]
    resumo = []
    for etiqueta, fonte in [("Referência", ref), ("Seu vídeo", novo)]:
        resumo.append(
            f"<tr><th>{etiqueta}</th><td>{html.escape(fonte['arquivo'])}</td>"
            f"<td>{fonte['mediana_variacao']:.1f}</td><td>{fonte['mediana_contraste']:.1f}</td></tr>"
        )
    eventos_html = []
    for e in dados["eventos"]:
        tempos = [f"{e[k]:.3f} s" if k in e else "—" for k in ("ref", "video")]
        atraso = f"{e['video'] - e['ref']:+.3f} s" if "video" in e and "ref" in e else "—"
        eventos_html.append(
            f"<tr><th>{html.escape(e['nome'])}</th><td>{tempos[0]}</td>"
            f"<td>{tempos[1]}</td><td>{atraso}</td></tr>"
        )
    tabela_eventos = ""
    if eventos_html:
        tabela_eventos = (
            "<h2>Eventos anotados</h2><table><tr><th>Evento</th><th>Referência</th>"
            "<th>Seu vídeo</th><th>Diferença de tempo</th></tr>" + "".join(eventos_html) + "</table>"
        )
    grupos = []
    for a, b in zip(ref["pares"], novo["pares"]):
        t = a["t"]
        marcadores = []
        for e in dados["eventos"]:
            rotulos = [s for k, s in [("ref", "referência"), ("video", "seu vídeo")] if e.get(k) == t]
            if rotulos:
                marcadores.append(html.escape(e["nome"]) + " (" + ", ".join(rotulos) + ")")
        grupos.append(f'<section><h3>{t:.3f} s</h3><p>{" · ".join(marcadores)}</p><div class="dupla">')
        for etiqueta, amostra in [("Referência", a), ("Seu vídeo", b)]:
            grupos.append(
                f'<figure><img loading="lazy" src="{amostra["jpeg"]}" alt="{etiqueta} em {t:.3f} s">'
                f"<figcaption>{etiqueta} · {amostra['pts_s']:.3f} s · q{amostra['q']}</figcaption></figure>"
            )
        grupos.append("</div></section>")
    linhas = []
    for a, b in zip(ref["amostras"], novo["amostras"]):
        vals = [a["variacao"], b["variacao"], a["contraste"], b["contraste"]]
        linhas.append(
            f"<tr><th>{a['t']:.3f} s</th>"
            + "".join("<td>—</td>" if v is None else f"<td>{v:.1f}</td>" for v in vals)
            + "</tr>"
        )
    duracao, passo = dados["duracao_s"], dados["passo_s"]
    pag = f"""<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ritmo e enquadramento</title><style>body{{max-width:1100px;margin:2rem auto;padding:0 1rem;font:16px system-ui;color:#17252c;background:#f5f3ea}}
h1,h2,h3,p,figure{{margin:.45rem 0}}table{{border-collapse:collapse;font-variant-numeric:tabular-nums}}th,td{{padding:6px;text-align:left;border-bottom:1px solid #b2bebc}}
.grade{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,305px),1fr));gap:12px}}.dupla{{display:grid;grid-template-columns:1fr 1fr;gap:6px}}img{{width:100%;height:210px;object-fit:contain;background:#17252c}}figcaption{{font-size:.78em}}section{{padding:8px;background:white}}details{{margin:1rem 0}}</style>
<h1>Ritmo e enquadramento</h1><p>Janela de {duracao:g} s, iniciando em {ref["inicio_s"]:g} s na referência e {novo["inicio_s"]:g} s no seu vídeo. Amostras a cada {passo:g} s.</p>
<table><tr><th>Fonte</th><th>Arquivo</th><th>Variação mediana</th><th>Contraste mediano</th></tr>{"".join(resumo)}</table>
<p>A variação mede mudança média de luminância de uma amostra para a seguinte. O contraste mede P90 − P10 da luminância em cada quadro. Ambos usam escala 0–255 e incluem legendas, cortes e iluminação.</p>
<details><summary>Série temporal completa</summary><table><tr><th>Janela</th><th>Variação ref.</th><th>Variação vídeo</th><th>Contraste ref.</th><th>Contraste vídeo</th></tr>{"".join(linhas)}</table></details>
{tabela_eventos}<h2>Quadros no mesmo instante relativo</h2><div class="grade">{"".join(grupos)}</div></html>"""
    (pasta / "comparacao.html").write_text(pag, encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("referencia", type=Path)
    p.add_argument("video", type=Path)
    p.add_argument(
        "--inicio-ref", type=segundos, default=Fraction(0), help="início na referência em segundos"
    )
    p.add_argument(
        "--inicio-video", type=segundos, default=Fraction(0), help="início no novo vídeo em segundos"
    )
    p.add_argument(
        "--duracao", type=segundos, required=True, help="extensão do intervalo comparado em segundos"
    )
    p.add_argument(
        "--passo", type=segundos, default=Fraction(1, 4), help="intervalo entre medições (padrão 0.25 s)"
    )
    p.add_argument(
        "--pares", type=int, default=10, help="pares visuais distribuídos na grade de amostragem (2–32)"
    )
    p.add_argument(
        "--eventos",
        type=Path,
        help="JSON de eventos anotados, com nome e tempos ref/video relativos à janela",
    )
    p.add_argument(
        "-o", "--saida", required=True, type=Path, help="nova pasta para relatório, dados e miniaturas"
    )
    a = p.parse_args()
    if a.passo <= 0 or a.duracao <= a.passo or not 2 <= a.pares <= 32:
        p.error("use 0 < passo < duração e de 2 a 32 pares")
    n = ceil(a.duracao / a.passo)
    if n > 1000:
        p.error("mais de mil medições; aumente --passo ou analise janelas menores")
    if any(not shutil.which(dep) for dep in ("ffmpeg", "ffprobe")):
        p.error("instale FFmpeg e ffprobe no PATH")
    a.referencia, a.video = a.referencia.expanduser().resolve(), a.video.expanduser().resolve()
    saida = a.saida.expanduser().resolve()
    if saida.exists() or any(not x.is_file() for x in (a.referencia, a.video)):
        p.error("informe dois arquivos locais e uma pasta de saída nova")
    try:
        eventos = ler_eventos(a.eventos, a.duracao)
        tempos = [i * a.passo for i in range(n)]
        visuais = {tempos[round(i * (n - 1) / (a.pares - 1))] for i in range(a.pares)}
        visuais.update(t for e in eventos for k, t in e.items() if k in ("ref", "video"))
        visuais = sorted(visuais)
        saida.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=saida.parent, prefix=".ritmo-") as tmp:
            pasta = Path(tmp) / "resultado"
            pasta.mkdir()
            dados = {
                "duracao_s": float(a.duracao),
                "passo_s": float(a.passo),
                "lado_medicao_px": LADO,
                "eventos": [
                    {k: float(v) if isinstance(v, Fraction) else v for k, v in e.items()} for e in eventos
                ],
            }
            dados["ref"] = medir(
                a.referencia, a.inicio_ref, a.duracao, tempos, visuais, pasta / "referencia"
            )
            dados["video"] = medir(a.video, a.inicio_video, a.duracao, tempos, visuais, pasta / "video")
            escrever(pasta, dados)
            pasta.rename(saida)
    except (ValueError, argparse.ArgumentTypeError, OSError) as exc:
        p.exit(1, f"Erro na comparação: {exc}\n")
    print(f"Abra {saida / 'comparacao.html'} · {n} instantes comparados")


if __name__ == "__main__":
    main()
