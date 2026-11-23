"""Introdução da fábula das aves. Quadro 1 corresponde a 0 s da montagem."""
import math
import random

import bpy
from mathutils import Vector

from aves import galinha
from locais import _Partes, _cor, arvore, casa, gramado, paisagem
from povo import pessoa

PLANOS = [('abertura', 0, 6)]
FPS = 24


def _moedas():
    rng = random.Random(268)
    b = _Partes()
    ouro = [_cor("Ouro claro",(252,206,56)),_cor("Ouro cunhado",(236,174,32)),
            _cor("Ouro pálido",(252,215,91)),_cor("Ouro no bordo",(193,137,43))]
    # Moedas deitadas em pilhas de alturas distintas, sobre uma pequena elevação amarela.
    b.copa((3.55,.12,.23),(1.48,.93,.49),ouro[:3],33)
    for j in range(97):
        a = rng.random()*math.tau
        r = math.sqrt(rng.random())
        x, y = 3.55+1.50*r*math.cos(a), .16+.96*r*math.sin(a)
        alt = max(.03,.65*(1-r**2))
        rad = rng.uniform(.112,.165)
        quantidade = rng.choice([1,1,2,3,3,4])
        for k in range(quantidade):
            cx, cy = x+rng.uniform(-.016,.016), y+rng.uniform(-.016,.016)
            z = alt + .037*k
            b.haste((cx,cy,z),(cx,cy,z+.035),rad,ouro[(j+k)%3],12)
            if k==quantidade-1:
                b.haste((cx,cy,z+.035),(cx,cy,z+.040),rad*.72,ouro[(j+k+1)%3],12)
    # Um brilho gira no primeiro plano para dar escala às moedas.
    return b.terminar("Tesouro do largo")


def _placa():
    b=_Partes()
    aro=_cor("Freijó da lousa",(104,65,41)); quadro=_cor("Lousa verde",(34,77,60))
    cantoneira=_cor("Bronze da lousa",(156,112,64))
    y=-.48
    b.caixa((0,y,.88),(2.72,.13,1.46),aro)
    b.caixa((0,y-.077,.88),(2.60,.044,1.34),quadro)
    for x in (-1.19,1.19):
        b.caixa((x,y+.044,.27),(.10,.11,.50),aro)
        b.caixa((x,y,.056),(.32,.35,.10),cantoneira)
    b.terminar("Lousa da praça")
    def texto(nome,txt,x,z,tam,material):
        data=bpy.data.curves.new(nome,"FONT")
        data.body=txt; data.align_x="CENTER";data.align_y="CENTER"
        data.extrude=.002;data.bevel_depth=.0006;data.size=tam
        data.materials.append(material)
        o=bpy.data.objects.new(nome,data);bpy.context.collection.objects.link(o)
        o.location=(x,y-.118,z);o.rotation_euler.x=math.pi/2
        # Os renderizadores externos leem malhas trianguladas. A placa segue editável
        # como objeto independente, também quando exportada para o projeto.
        deps=bpy.context.evaluated_depsgraph_get()
        ev=o.evaluated_get(deps)
        mesh=bpy.data.meshes.new_from_object(ev,depsgraph=deps)
        if not mesh.materials: mesh.materials.append(material)
        result=bpy.data.objects.new(nome+" — giz",mesh)
        bpy.context.collection.objects.link(result)
        result.location=o.location;result.rotation_euler=o.rotation_euler
        bpy.data.objects.remove(o,do_unlink=True)
        return result
    giz=_cor("Giz marfim",(248,238,213));verde=_cor("Giz de hortelã",(151,223,137));rosa=_cor("Giz coral",(255,146,120))
    texto("Pergunta", "POR QUÊ?", 0,1.29,.36,giz)
    li=texto("Renda alta","RICO",-.43,.84,.245,verde)
    lo=texto("Renda baixa","POBRE",-.40,.47,.245,rosa)
    for obj,t in [(li,4.16),(lo,4.52)]:
        normal=obj.scale.copy()
        obj.scale=(.001,)*3;obj.keyframe_insert(data_path="scale",frame=round((t-.15)*FPS)+1)
        obj.scale=normal;obj.keyframe_insert(data_path="scale",frame=round(t*FPS)+1)
    for j,(z,d,mat,tempo) in enumerate([(.82,.15,verde,4.29),(.49,-.15,rosa,4.64)]):
        p=_Partes()
        x1,x2=.24,.77
        p.haste((x1,y-.120,z),(x2,y-.120,z+d),.023,mat,6)
        p.pol([(x2+.09,y-.121,z+d+.04*(1 if d>0 else -1)),
               (x2-.111,y-.121,z+d+(0.02 if d>0 else .09)),
               (x2-.018,y-.121,z+d+(-.11 if d>0 else -.035))],mat)
        ar=p.terminar("Seta de giz")
        ar.scale=(.001,)*3;ar.keyframe_insert(data_path="scale",frame=round((tempo-.1)*FPS)+1)
        ar.scale=(1,)*3;ar.keyframe_insert(data_path="scale",frame=round(tempo*FPS)+1)


def _bairro():
    paisagem()
    b=_Partes()
    rng=random.Random(42)
    pav=[_cor("Pavimento areia "+str(i),rgb) for i,rgb in enumerate([(224,207,171),(231,213,178),(235,218,185),(220,201,165)])]
    b.caixa((0,-1,-.006),(42,14,.052),_cor("Argamassa do piso",(139,153,102)))
    # Lages largas orientam a perspectiva no movimento lateral.
    for j in range(7):
        for i in range(-8,9):
            b.caixa(((i+.41*(j%2))*2.37,-6.7+j*1.76,.034),(2.343,1.733,.034),pav[rng.randrange(4)])
    b.terminar("Lajes da praça")
    for j,x in enumerate([-11,-7.4,-3.7,0,3.7,7.4,11]):
        gramado("Quintal",x,4.05,3.85,3.55)
        escala=1.16+.06*(j%2)
        cx=x+(.49 if j%2 else .16); angle=.16 if j%3!=1 else -.13
        house=casa("Chalé da praça",cx,4.38,0,angle,escala)
        house.location.z=.88
        # Estrutura escura exposta como nas casas enxaimel do plano da rua.
        m=_Partes(); esc=_cor("Enxaimel do largo",(91,64,49))
        f=-1.34
        for k in (-1,1):
            m.haste((k*1.38,f,.38),(k*1.38,f,2.56),.059,esc,6)
            m.haste((k*1.42,f,2.53),(k*.82,f,2.91),.04,esc,5)
            m.haste((k*.57,f,2.53),(0,f,3.33),.04,esc,5)
        m.caixa((0,f,2.52),(3.03,.075,.08),esc)
        fachada=m.terminar("Travamento da fachada",cx,4.38,angle)
        fachada.location.z=.88
        loja=_Partes()
        loja.caixa((0,0,.455),(2.66,2.23,.91),_cor("Cal das lojas",(236,213,167)))
        vidro=_cor("Vidro azul das lojas",(81,111,116));friso=_cor("Pedra clara das lojas",(236,224,192))
        for lado in (-1,1):
            loja.caixa((lado*.89,-1.135,.56),(.69,.065,.56),esc)
            loja.caixa((lado*.89,-1.175,.56),(.57,.025,.45),vidro)
            loja.caixa((lado*.89,-1.199,.56),(.026,.024,.46),friso)
            loja.caixa((lado*.89,-1.201,.56),(.58,.024,.026),friso)
            loja.caixa((lado*.89,-1.174,.25),(.77,.14,.066),esc)
            loja.caixa((lado*1.23,-1.15,.46),(.08,.10,.93),esc)
        porta=_cor("Porta verde da loja",(50,100,87))
        loja.caixa((0,-1.17,.45),(.49,.095,.80),esc)
        loja.caixa((0,-1.24,.43),(.40,.035,.74),porta)
        loja.caixa((.125,-1.275,.43),(.033,.05,.036),friso)
        loja.caixa((0,-1.18,.888),(2.81,.16,.13),esc)
        loja.terminar("Loja do largo",cx,4.38,angle,escala)
    for j,x in enumerate([-9,-5.4,-1.85,1.9,5.64,9.35]):
        arvore("Árvore da rua",x,3.10 if j%2 else 3.47,.72+.15*(j%3))
    _moedas()
    senhora=pessoa("Senhora do tesouro",3.58,.15,0,.06,1.06)
    senhora.location.z=.72
    trabalhador=pessoa("Trabalhador", -3.85,.04,1,-.15,1.07,"fome")
    trabalhador.location.z=.055
    tecido=_Partes()
    pano=_cor("Bolso gasto",(225,211,178));costura=_cor("Costura ocre",(153,122,81))
    verts=[(-.315,-.11,.84),(-.228,-.169,.91),(-.175,-.186,.84),(-.185,-.201,.73),(-.242,-.195,.70),(-.30,-.177,.74)]
    tecido.pol(verts,pano)
    for a,b in zip(verts[3:],verts[4:]): tecido.haste(a,b,.01,costura,5)
    bolso=tecido.terminar("Forro de bolso vazio")
    bolso.parent=trabalhador
    _placa()
    ave=galinha("A galinha da pergunta",-1.52,-.47,-.34,1.10,0)
    for t,ry,yaw in [(0,-.05,-.34),(3.66,-.06,-.34),(4.06,.08,-.14),(4.46,-.06,.21),(4.74,.04,.17),(5.33,-.025,-.31),(6,0,-.4)]:
        ave.rotation_euler.x=ry;ave.rotation_euler.z=yaw
        ave.keyframe_insert(data_path="rotation_euler",frame=round(t*FPS)+1)


def _camada_camera():
    sc=bpy.context.scene
    c=bpy.data.cameras.new("Lente da abertura");cam=bpy.data.objects.new("Câmera da abertura",c)
    bpy.context.collection.objects.link(cam); sc.camera=cam
    c.sensor_fit="VERTICAL";c.sensor_height=32;c.clip_end=150;c.lens=36
    # Olho em metros, ponto observado e distância focal. Intervalos curtos dão a
    # panorâmica rápida, a distância inicial mantém o rosto legível no celular.
    alvos=[
      (0,(3.69,-3.87,1.68),(3.59,.15,1.62),37),
      (1.33,(3.60,-4.20,1.72),(3.55,.16,1.51),36),
      (1.70,(3.28,-4.65,1.77),(3.31,.17,1.50),33),
      (2.07,(-3.58,-5.83,1.58),(-3.82,.04,1.13),35),
      (2.95,(-3.77,-5.21,1.44),(-3.84,.04,1.10),36),
      (3.48,(-3.69,-5.40,1.48),(-3.79,.05,1.13),36),
      (3.86,(-.33,-7.39,1.63),(-.19,-.31,1.40),32),
      (4.28,(-.29,-7.64,1.68),(-.21,-.32,1.43),32),
      (4.82,(-.21,-8.17,2.08),(-.15,-.12,1.60),33),
      (5.35,(-.05,-10.40,2.92),(-.05,.26,1.76),34),
      (5.97,(0,-16.0,4.8),(0,.68,2.05),33)
    ]
    idx=0
    for f in range(1,145):
        t=(f-1)/FPS
        while idx<len(alvos)-2 and alvos[idx+1][0]<t: idx+=1
        a,b=alvos[idx:idx+2];u=max(0,min(1,(t-a[0])/(b[0]-a[0])));u=u*u*(3-2*u)
        eye,tar=Vector(a[1]).lerp(Vector(b[1]),u),Vector(a[2]).lerp(Vector(b[2]),u)
        cam.location=eye;cam.rotation_euler=(tar-eye).to_track_quat("-Z","Y").to_euler();c.lens=a[3]*(1-u)+b[3]*u
        cam.keyframe_insert(data_path="location",frame=f);cam.keyframe_insert(data_path="rotation_euler",frame=f);c.keyframe_insert(data_path="lens",frame=f)
    return cam


def construir(indice=0):
    """Adicionar cenário e câmera à cena vazia configurada pelo montador."""
    sc=bpy.context.scene
    # O renderizador e o Blender em uma instalação nova abrem com Cube/Camera/Light.
    # Este é o construtor de um plano inteiro e assume a propriedade da cena.
    for obj in list(sc.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    sc.frame_start,sc.frame_end=1,144
    sc.render.fps=24
    _bairro()
    _camada_camera()
    sc.frame_set(1)
    return sc
