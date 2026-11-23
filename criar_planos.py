"""Executar com o Python do Blender 4.3+, a partir de qualquer pasta."""
import argparse
import math
from pathlib import Path
import subprocess
import sys

import bpy

RAIZ = Path(__file__).resolve().parent
FONTES = RAIZ / "fontes"
sys.path.insert(0, str(FONTES))


def inventario():
    import tomadas
    import abertura
    outros = {nome: (tomadas, inicio, fim) for nome, inicio, fim in tomadas.PLANOS}
    return {'abertura': (abertura, 0., 6.), 'vila-mao': (None, 6., 13.), **outros}


def parametros():
    parser = argparse.ArgumentParser(description="Criar cenas editáveis com o Blender.")
    parser.add_argument("--plano", default="todos", help="Nome mostrado em --listar, ou todos.")
    parser.add_argument("--listar", action="store_true", help="Imprime o nome de cada plano.")
    parser.add_argument("--destino", type=Path, default=RAIZ / "cenas-geradas")
    parser.add_argument("--substituir", action="store_true", help="Autoriza substituir os .blend gerados.")
    return parser.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])



def aplicar_panorama(cena, noite=False):
    """Mapear a foto na cúpula e a incorporar para o Workbench abrir offline."""
    cupula = next((o for o in cena.objects if o.get('ceu_panoramico')), None)
    if cupula is None:
        return
    caminho = FONTES / ('ceu-noite.jpg' if noite else 'ceu-foto.jpg')
    foto = bpy.data.images.load(str(caminho), check_existing=True)
    foto.pack()
    foto.filepath = '//' + caminho.name
    mat = bpy.data.materials.new('Céu fotográfico')
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = foto
    emissao = nodes.new('ShaderNodeEmission')
    mat.node_tree.links.new(tex.outputs['Color'], emissao.inputs['Color'])
    mat.node_tree.links.new(emissao.outputs[0], nodes.get('Material Output').inputs['Surface'])
    nodes.active = tex
    mesh = cupula.data
    mesh.materials.clear()
    mesh.materials.append(mat)
    uv = mesh.uv_layers.new(name='Panorama')
    for face in mesh.polygons:
        amostras = []
        for idx in face.loop_indices:
            v = mesh.vertices[mesh.loops[idx].vertex_index].co.normalized()
            lon = (.02 + math.atan2(v.y,v.x)/(2*math.pi)) % 1
            lat = .5 + math.asin(max(-1., min(1.,v.z)))/math.pi
            amostras.append((idx,lon,lat))
        longitudes = [lon for _,lon,_ in amostras]
        na_emenda = max(longitudes)-min(longitudes) > .5
        for idx,lon,lat in amostras:
            uv.data[idx].uv = (lon + int(na_emenda and lon < .5), lat)


def ajustes_de_edicao(cena, nome, manter_renderizador=False):
    cena.name = nome
    if not manter_renderizador:
        cena.render.engine = 'BLENDER_WORKBENCH'
        sombreado = cena.display.shading
        sombreado.light = 'STUDIO'
        sombreado.studio_light = 'paint.sl'
        sombreado.color_type = 'TEXTURE'
        sombreado.show_specular_highlight = False
        sombreado.show_shadows = False
        sombreado.shadow_intensity = .35
        sombreado.show_cavity = False
        sombreado.background_type = 'WORLD'
        cena.view_settings.view_transform = 'Standard'
    cena.render.resolution_x = 720
    cena.render.resolution_y = 1280
    cena.render.resolution_percentage = 100
    cena.render.image_settings.file_format = 'PNG'
    cena.render.film_transparent = False
    cena.render.filepath = '//../quadros/' + nome + '/####'
    cena.frame_set(cena.frame_start)
    for tela in bpy.data.screens:
        for area in tela.areas:
            if area.type == 'VIEW_3D':
                for espaco in area.spaces:
                    if espaco.type == 'VIEW_3D':
                        espaco.region_3d.view_perspective = 'CAMERA'
                        espaco.shading.color_type = 'MATERIAL' if manter_renderizador else 'TEXTURE'
                        espaco.overlay.show_overlays = False


def gerar(nome, origem, destino):
    if nome == 'vila-mao':
        original = (RAIZ / 'cenas' / 'vila-mao.blend').resolve()
        if original == destino.resolve():
            raise ValueError('Escolha uma pasta de saída diferente para a cópia da vila.')
        bpy.ops.wm.open_mainfile(filepath=str(original))
        cena = bpy.context.scene
        ajustes_de_edicao(cena, nome, manter_renderizador=True)
    else:
        if nome not in origem:
            raise ValueError('Plano desconhecido. Veja os nomes com --listar.')
        modulo, inicio, fim = origem[nome]
        bpy.ops.wm.read_factory_settings(use_empty=True)
        cena = modulo.construir(0 if nome == 'abertura' else nome)
        aplicar_panorama(cena, noite=nome == 'jantar')
        ajustes_de_edicao(cena, nome)
        cena["inicio_na_montagem_s"] = inicio
        cena["fim_na_montagem_s"] = fim
    cena.timeline_markers.new("Início", frame=cena.frame_start)
    cena.timeline_markers.new("Fim", frame=cena.frame_end)
    bpy.context.preferences.filepaths.save_version = 0
    destino.parent.mkdir(exist_ok=True, parents=True)
    # Não remapear os caminhos relativos já definidos para a nova cena.
    bpy.ops.wm.save_as_mainfile(filepath=str(destino), compress=True, relative_remap=False)


def main():
    args = parametros()
    planos = inventario()
    if args.listar:
        for nome, (_, inicio, fim) in planos.items():
            print(f"{nome}  {inicio:.2f}–{fim:.2f} s")
        return
    saida = args.destino.resolve()
    nomes = list(planos) if args.plano == 'todos' else [args.plano]
    bloqueados = [saida / (n+'.blend') for n in nomes if (saida / (n+'.blend')).exists()]
    if bloqueados and not args.substituir:
        raise ValueError(f"A saída já existe: {bloqueados[0]}. Use uma pasta nova ou --substituir.")
    if args.plano != 'todos':
        gerar(args.plano, planos, saida / (args.plano + '.blend'))
        return
    # Cada plano tem uma cena e suas coleções próprias. Reiniciar o Blender
    # também libera geometrias e texturas antes de construir o próximo plano.
    for nome in nomes:
        comando = [bpy.app.binary_path, '-b', '-t', '2', '--python-exit-code', '1',
                   '-P', str(Path(__file__).resolve()), '--', '--plano', nome,
                   '--destino', str(saida)]
        if args.substituir:
            comando.append('--substituir')
        subprocess.run(comando, check=True)


if __name__ == '__main__':
    main()
