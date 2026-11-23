#!/usr/bin/env python3
"""Mede o vídeo e gera uma folha de contato local usando FFmpeg e ffprobe."""

import argparse
import bisect
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from fractions import Fraction
from pathlib import Path


def comando(args):
    proc = subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode:
        raise ValueError(f"{Path(args[0]).name} falhou.\n{proc.stderr[-1800:].strip()}")
    return proc


def sonda(arquivo, *opcoes):
    args = ["ffprobe", "-v", "error", *opcoes, "-of", "json", str(arquivo)]
    return json.loads(comando(args).stdout)


def vizinho(valores, alvo):
    pos = bisect.bisect_left(valores, alvo)
    if pos == 0 or pos == len(valores):
        return min(pos, len(valores) - 1)
    if alvo - valores[pos - 1] <= valores[pos] - alvo:
        return pos - 1
    return pos


def sequencia(arquivo, video):
    dados = sonda(arquivo, "-select_streams", str(video["index"]), "-show_frames",
                  "-show_entries", "frame=best_effort_timestamp,duration,pkt_duration")
    quadros = dados.get("frames", [])
    if not quadros or any("best_effort_timestamp" not in q for q in quadros):
        raise ValueError("O vídeo precisa ter quadros decodificáveis com timestamps.")
    pts = [int(q["best_effort_timestamp"]) for q in quadros]
    if any(b < a for a, b in zip(pts, pts[1:])):
        raise ValueError("Timestamps regressivos. Remultiplexe uma cópia e tente novamente.")
    ultimo = quadros[-1]
    base = Fraction(video["time_base"])
    fim = pts[-1] + int(ultimo.get("duration", ultimo.get("pkt_duration", 0)))
    metodo = "timestamp e duração do último quadro"
    if fim <= pts[-1]:
        fim = int(video.get("start_pts", pts[0])) + int(video.get("duration_ts", 0))
        metodo = "fim informado pela faixa de vídeo"
    if fim <= pts[-1]:
        passo = next((b - a for a, b in zip(reversed(pts[:-1]), reversed(pts[1:]))
                      if b > a), 0)
        if not passo:
            try:
                passo = 1 / (Fraction(video["avg_frame_rate"]) * base)
            except (KeyError, ValueError, ZeroDivisionError):
                raise ValueError("A duração do último quadro não está disponível.") from None
        fim = pts[-1] + passo
        metodo = "intervalo estimado para o último quadro"
    return pts, base, (fim - pts[0]) * base, metodo


def detectar(arquivo, trilha, pts, base, limiar):
    # -copyts mantém a mesma origem dos timestamps colhidos no ffprobe.
    filtro = rf"scale=160:-2,select=gt(scene\,{limiar}),showinfo=checksum=0"
    args = ["ffmpeg", "-hide_banner", "-nostats", "-nostdin", "-copyts",
            "-filter_threads", "1", "-i", str(arquivo), "-map", f"0:{trilha}",
            "-vf", filtro, "-an", "-f", "null", "-"]
    log = comando(args).stderr
    relogio = re.search(r"config in time_base:\s*(\d+/\d+)", log)
    marcas = re.findall(r"\bn:\s*\d+\s+pts:\s*(-?\d+)\s+pts_time:", log)
    if not relogio:
        raise ValueError("FFmpeg não informou a base de tempo do detector de cenas.")
    escala = Fraction(relogio[1]) / base
    return sorted({vizinho(pts, int(tick) * escala) for tick in marcas} - {0})


def extrair(arquivo, trilha, indices, pasta):
    selecao = "+".join(rf"eq(n\,{indice})" for indice in indices)
    # dar inclui pixels não quadrados. As miniaturas usam pixels quadrados.
    escala = "scale=w='max(2,2*trunc(min(240,320*dar)/2))':h='max(2,2*trunc(min(320,240/dar)/2))'"
    padrao = str(pasta / "quadro-%04d.jpg")
    comando(["ffmpeg", "-v", "error", "-nostdin", "-filter_threads", "1", "-i", str(arquivo),
             "-map", f"0:{trilha}", "-an", "-vf", f"select={selecao},{escala},setsar=1",
             "-vsync", "0", "-c:v", "mjpeg", "-q:v", "3", "-start_number", "0", padrao])
    arquivos = sorted(pasta.glob("quadro-*.jpg"))
    if len(arquivos) != len(indices):
        raise ValueError(f"FFmpeg extraiu {len(arquivos)} de {len(indices)} miniaturas.")
    return {indice: arquivo.name for indice, arquivo in zip(indices, arquivos)}


def folha(pasta, nome, geral, grupos, fichas):
    def cartao(q):
        ficha = fichas[q]
        return (f'<figure><img src="{ficha["imagem"]}" alt="Quadro {q}">'
                f'<figcaption>{ficha["tempo_s"]:.3f} s · quadro {q}</figcaption></figure>')

    blocos = ['<h2>Ao longo do vídeo</h2><div class="grade">',
              "".join(cartao(q) for q in geral), "</div>", "<h2>Possíveis cortes</h2>"]
    if not grupos:
        blocos.append("<p>Nenhum grupo para revisão com os parâmetros escolhidos.</p>")
    for alvo, janela in grupos.items():
        blocos += [f'<h3>{fichas[alvo]["tempo_s"]:.3f} s · quadro {alvo}</h3>',
                   '<div class="grade">', "".join(cartao(q) for q in janela), "</div>"]
    titulo = html.escape(nome)
    pagina = f"""<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Quadros de {titulo}</title>
<style>body{{max-width:1150px;margin:24px auto;padding:0 16px;background:#172126;color:#fff;font:16px system-ui,sans-serif}}
.grade{{display:flex;flex-wrap:wrap;gap:12px}}figure{{margin:0}}img{{display:block;max-width:min(198px,85vw);max-height:260px}}
figcaption{{padding:4px 0;font-variant-numeric:tabular-nums}}h2{{margin-top:2rem}}</style>
<h1>{titulo}</h1><p>Tempo desde o primeiro quadro exibido. A numeração começa em zero.</p>
{''.join(blocos)}</html>"""
    (pasta / "contato.html").write_text(pagina, encoding="utf-8")


def analisar(arquivo, pasta, args):
    info = sonda(arquivo, "-show_streams", "-show_format")
    trilhas = info.get("streams", [])
    video = next((t for t in trilhas if t.get("codec_type") == "video"
                  and not t.get("disposition", {}).get("attached_pic")), None)
    if not video:
        raise ValueError("Este arquivo não contém uma faixa de vídeo.")
    audio = [{k: t.get(k) for k in ("index", "codec_name", "channels", "sample_rate", "start_time")}
             for t in trilhas if t.get("codec_type") == "audio"]
    pts, base, duracao, metodo = sequencia(arquivo, video)
    geral = sorted({vizinho(pts, pts[0] + Fraction(i, args.amostras - 1) * (pts[-1] - pts[0]))
                    for i in range(args.amostras)} | {0, len(pts) - 1})
    cortes = detectar(arquivo, video["index"], pts, base, args.limiar)
    if args.max_cortes == 0:
        vistos = []
    elif len(cortes) <= args.max_cortes:
        vistos = cortes
    elif args.max_cortes == 1:
        vistos = [cortes[0]]
    else:
        vistos = [cortes[round(i * (len(cortes) - 1) / (args.max_cortes - 1))]
                  for i in range(args.max_cortes)]
    grupos = {q: list(range(max(0, q - 1), min(len(pts), q + 2))) for q in vistos}
    indices = sorted(set(geral).union(*grupos.values()))
    arquivos = extrair(arquivo, video["index"], indices, pasta)

    def ficha(q):
        dados = {"quadro": q, "pts": pts[q], "tempo_s": round(float((pts[q] - pts[0]) * base), 6)}
        if q in arquivos:
            dados["imagem"] = arquivos[q]
        return dados

    rotacao = next((s["rotation"] for s in video.get("side_data_list", []) if "rotation" in s),
                   int(video.get("tags", {}).get("rotate", 0)))
    largura, altura = video["width"], video["height"]
    if abs(rotacao) % 180 == 90:
        largura, altura = altura, largura
    resultado = {
        "arquivo": arquivo.name, "faixa_video": video["index"], "codec": video.get("codec_name"),
        "resolucao_codificada": [video["width"], video["height"]], "rotacao_graus": rotacao,
        "resolucao_apos_rotacao": [largura, altura], "aspecto_pixel": video.get("sample_aspect_ratio"),
        "fps_medio_declarado": video.get("avg_frame_rate"), "fps_nominal": video.get("r_frame_rate"),
        "total_quadros_decodificados": len(pts), "duracao_video_s": round(float(duracao), 6),
        "metodo_duracao": metodo, "duracao_container_s": info.get("format", {}).get("duration"),
        "base_de_tempo": str(base), "primeiro_pts": pts[0], "trilhas_de_audio": audio,
        "limiar_cortes": args.limiar, "cortes_candidatos": [ficha(q) for q in cortes],
        "amostras": [ficha(q) for q in geral],
        "vizinhos_dos_cortes": [{"corte": q, "quadros": [ficha(i) for i in janela]}
                                for q, janela in grupos.items()],
    }
    (pasta / "medidas.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n",
                                       encoding="utf-8")
    folha(pasta, arquivo.name, geral, grupos, {q: ficha(q) for q in indices})
    return len(pts), len(cortes)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("video", type=Path, help="MP4 ou outro vídeo local decodificável")
    p.add_argument("-o", "--saida", type=Path, help="pasta nova (padrão: NOME-analise na pasta atual)")
    p.add_argument("--amostras", type=int, default=12, help="de 2 a 48, distribuídas pelo tempo")
    p.add_argument("--limiar", type=float, default=0.32, help="sensibilidade do detector entre 0 e 1")
    p.add_argument("--max-cortes", type=int, default=12, help="de 0 a 32 grupos de quadros vizinhos")
    args = p.parse_args()
    if not (2 <= args.amostras <= 48 and 0 <= args.max_cortes <= 32 and 0 < args.limiar < 1):
        p.error("use --amostras de 2 a 48, --max-cortes de 0 a 32 e --limiar maior que 0 e menor que 1.")
    arquivo = args.video.expanduser().resolve()
    pasta = (args.saida or Path(f"{arquivo.stem}-analise")).expanduser().resolve()
    if not arquivo.is_file():
        p.error(f"arquivo de entrada ausente: {arquivo}")
    if pasta.exists():
        p.error(f"a saída já existe; escolha outra pasta: {pasta}")
    for dep in ("ffprobe", "ffmpeg"):
        if not shutil.which(dep):
            p.error(f"instale {dep} e confirme que está no PATH.")
    try:
        pasta.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".medir-", dir=pasta.parent) as temp:
            dados = Path(temp) / "resultado"
            dados.mkdir()
            n, nc = analisar(arquivo, dados, args)
            dados.rename(pasta)
    except (OSError, ValueError) as erro:
        p.exit(1, f"Erro: {erro}\n")
    print(f"Quadros: {n}. Possíveis cortes: {nc}. Abra {pasta / 'contato.html'}")


if __name__ == "__main__":
    main()
