from django.shortcuts import render, redirect
from .models import Pergunta
import random
from django.views.decorators.cache import never_cache

REGRAS = {
    'F': {
        'pontos_acerto': 1,
        'pontos_erro': 0,
        'meta_vitoria': 10,
        'max_rodadas': 15,
    },
    'M': {
        'pontos_acerto': 2,
        'pontos_erro': -1,
        'meta_vitoria': 15,
        'max_rodadas': 12,
    },
    'D': {
        'pontos_acerto': 3,
        'pontos_erro': -2,
        'meta_vitoria': 20,
        'max_rodadas': 10,
    }
}

    
DESCRICOES = {
    'F': {
        "titulo": "Modo fácil",
        "texto": "Ideal para principiantes. No hay penalización por error y el ritmo es más tranquilo."
    },
    'M': {
        "titulo": "Modo médio",
        "texto": "Modo equilibrado. Los errores restan puntos y exige mayor atención."
    },
    'D': {
        "titulo": "Modo Difícil",
        "texto": "Para jugadores experimentados. Alta penalización por error y menos rondas."
    }
}

@never_cache
def jogar_turno(request):
    if request.method == "POST" and "continuar" in request.POST:

        if request.session.get("vencedor_pendente"):
            request.session["fim_jogo"] = True
            request.session["resultado"] = request.session.pop("vencedor_pendente")
            request.session.modified = True
            return redirect("jogar_turno")
    
        jogador_atual = request.session["jogador_atual"]
        
        if jogador_atual == 2:
            request.session["rodadas"] += 1

        request.session["jogador_atual"] = 2 if jogador_atual == 1 else 1

        request.session["mostrar_resultado"] = False
        request.session["pergunta_atual"] = None
        request.session.pop("resposta_usuario", None)
        request.session.pop("tipo_resultado", None)
        request.session.setdefault("nome_j1", "Jogador 1")
        request.session.setdefault("nome_j2", "Jogador 2")

        request.session.modified = True
        return redirect("jogar_turno")

    if "nivel_escolhido" not in request.session:
        return redirect("escolher_nivel")

    if "pos_jogador1" not in request.session:
        request.session["pos_jogador1"] = 0
        request.session["pos_jogador2"] = 0
        request.session["jogador_atual"] = 1

        nivel = request.session.get("nivel_escolhido", "F")

        ids = list(Pergunta.objects.filter(nivel=nivel).values_list("id", flat=True))
        random.shuffle(ids)
        request.session["perguntas_restantes"] = ids
        request.session["rodadas"] = 1
        request.session["pergunta_atual"] = None
        request.session["respondidas_j1"] = 0
        request.session["respondidas_j2"] = 0
        request.session["acertos_j1"] = 0
        request.session["acertos_j2"] = 0
        request.session["fim_jogo"] = False
        request.session["resultado"] = None
        request.session["morte_subita"] = False

    jogador_atual = request.session["jogador_atual"]
    mensagem = None

    if request.method == "POST" and not request.POST.get("continuar"):
        resposta = request.POST.get("resposta")
        jogador_atual = request.session["jogador_atual"]

        if jogador_atual == 1:
            nome_atual = request.session.get("nome_j1", "Jogador 1")
        else:
            nome_atual = request.session.get("nome_j2", "Jogador 2")

        nivel = request.session.get("nivel_escolhido", "F")
        regras = REGRAS[nivel]

        # avalia a pergunta atual
        pergunta_id = request.session.get("pergunta_atual")
        
        if pergunta_id:
            pergunta = Pergunta.objects.get(id=pergunta_id)

            # 🔥 TEMPO ESGOTADO
            if resposta is None:
                request.session["mensagem"] = f"¡{nome_atual} perdió el turno!"
                request.session["tipo_resultado"] = "tempo"
                pontos = regras['pontos_erro']

            elif resposta == pergunta.resposta_correta:
                request.session["tipo_resultado"] = "acerto"
                pontos = regras['pontos_acerto']

                if jogador_atual == 1:
                    request.session["acertos_j1"] += 1
                else:
                    request.session["acertos_j2"] += 1

            else:
                request.session["tipo_resultado"] = "erro"
                pontos = regras['pontos_erro']

            

            if jogador_atual == 1:
                nova_pontuacao = request.session["pos_jogador1"] + pontos
                request.session["pos_jogador1"] = max(0, nova_pontuacao)
                request.session["respondidas_j1"] += 1
            else:
                nova_pontuacao = request.session["pos_jogador2"] + pontos
                request.session["pos_jogador2"] = max(0, nova_pontuacao)
                request.session["respondidas_j2"] += 1

            if jogador_atual == 2:

                p1 = request.session["pos_jogador1"]
                p2 = request.session["pos_jogador2"]
            
        #Só verifica fim de jogo quando a rodada termina
            if jogador_atual == 2:
                if request.session.get("morte_subita"):
                    request.session["rodadas_morte_subita"] = request.session.get("rodadas_morte_subita", 0) + 1
                # =========================
                # SE ESTIVER EM MORTE SÚBITA
                # =========================
                if request.session.get("morte_subita"):

                    rodadas_ms = request.session.get("rodadas_morte_subita", 1)

                    if p1 > p2:
                        request.session["vencedor_pendente"] = f"¡{request.session['nome_j1']} es la ganador(a)!"
                    
                    elif p2 > p1:
                        request.session["vencedor_pendente"] = f"¡{request.session['nome_j2']} es la ganador(a)!"

                    else:
                        if rodadas_ms >= 5:
                            request.session["fim_jogo"] = True
                            request.session["resultado"] = "¡Empate!"

                # =========================
                # JOGO NORMAL
                # =========================
                else:

                    # META DE VITÓRIA
                    if p1 >= regras['meta_vitoria'] or p2 >= regras['meta_vitoria']:

                        if p1 > p2:
                            request.session["fim_jogo"] = True
                            request.session["resultado"] = f"¡{request.session['nome_j1']} es la ganador(a)!"

                        elif p2 > p1:
                            request.session["fim_jogo"] = True
                            request.session["resultado"] = f"¡{request.session['nome_j2']} es la ganador(a)!"
                        else:
                            request.session["morte_subita"] = True
                            request.session["rodadas_morte_subita"] = 0

                    # LIMITE DE RODADAS
                    elif request.session["rodadas"] == regras['max_rodadas']:

                        if p1 > p2:
                            request.session["vencedor_pendente"] = f"¡{request.session['nome_j1']} es la ganador(a)!"
                        elif p2 > p1:
                            request.session["vencedor_pendente"] = f"¡{request.session['nome_j2']} es la ganador(a)!"
                        else:
                            request.session["morte_subita"] = True
                            request.session["rodadas_morte_subita"] = 0


            # sempre mostra o resultado após responder
            request.session["mostrar_resultado"] = True
            request.session["resposta_usuario"] = resposta

            request.session.modified = True
            return redirect("jogar_turno")


    # se estiver mostrando resultado, mantém a mesma pergunta
    if request.session.get("mostrar_resultado"):
        pergunta = Pergunta.objects.get(id=request.session["pergunta_atual"])

    # senão escolhe próxima pergunta normalmente
    elif (
        not request.session.get("fim_jogo")
        and request.session["perguntas_restantes"]
        and (
            request.session["rodadas"] <= REGRAS[request.session.get("nivel_escolhido", "F")]["max_rodadas"]
            or request.session.get("morte_subita")
        )
    ):
        pergunta_id = request.session["perguntas_restantes"].pop(0)
        request.session["pergunta_atual"] = pergunta_id
        request.session.modified = True
        pergunta = Pergunta.objects.get(id=pergunta_id)

    else:
        pergunta = None


    # 🔥 CÁLCULO DO TEMPO AQUI
    nivel = request.session.get("nivel_escolhido", "F")
    morte_subita = request.session.get("morte_subita", False)

    if nivel == "F":  # Fácil
        tempo = 30 if not morte_subita else 20
    elif nivel == "M":  # Médio
        tempo = 20 if not morte_subita else 15
    else:  # Difícil
        tempo = 15 if not morte_subita else 10

    request.session["tempo_pergunta"] = tempo
    regras = REGRAS[nivel]
    descricao = DESCRICOES[nivel]
     
    return render(request, "tabuleiro.html", {
        "nome_j1": request.session.get("nome_j1"),
        "nome_j2": request.session.get("nome_j2"),
        "nome_atual": request.session["nome_j1"] if request.session["jogador_atual"] == 1 else request.session["nome_j2"],
        "mostrar_resultado": request.session.get("mostrar_resultado"),
        "resposta_usuario": request.session.get("resposta_usuario"),
        "pergunta": pergunta,
        "pos_jogador1": request.session["pos_jogador1"],
        "pos_jogador2": request.session["pos_jogador2"],
        "jogador_atual": request.session["jogador_atual"],
        "mensagem": mensagem,
        "fim_jogo": request.session.get("fim_jogo"),
        "resultado": request.session.get("resultado"),
        "respondidas_j1": request.session["respondidas_j1"],
        "respondidas_j2": request.session["respondidas_j2"],
        "acertos_j1": request.session["acertos_j1"],
        "acertos_j2": request.session["acertos_j2"],
        "tipo_resultado": request.session.get("tipo_resultado"),
        "rodada_exibicao": request.session["rodadas"],
        "max_rodadas": REGRAS[request.session.get("nivel_escolhido", "F")]["max_rodadas"],
        "nivel_escolhido": request.session.get("nivel_escolhido"),
        "morte_subita": request.session.get("morte_subita"),
        "nivel": nivel,
        "regras": regras,
        "descricao": descricao,
    }) 

def novo_jogo(request):
    request.session.flush()
    return redirect("jogar_turno")

def escolher_nivel(request):
        if request.method == "POST":
            nivel = request.POST.get("nivel")
            nome_j1 = request.POST.get("nome_j1")
            nome_j2 = request.POST.get("nome_j2")

            request.session.flush()

            request.session["nivel_escolhido"] = nivel
            request.session["nome_j1"] = nome_j1
            request.session["nome_j2"] = nome_j2

            return redirect("instrucoes")
        
        return render(request, "escolher_nivel.html")

@never_cache
def instrucoes(request):
    if not request.session.get("nivel_escolhido"):
        return redirect("escolher_nivel")
    
    if "pos_jogador1" in request.session:
        return redirect("jogar_turno")
    
    nivel = request.session.get("nivel_escolhido")

    if not nivel:
        return redirect("escolher_nivel")

    regras = REGRAS[nivel]
    descricao = DESCRICOES[nivel]

    return render(request, "instrucoes.html", {
        "nivel": nivel,
        "regras": regras,
        "descricao": descricao,
    })

def cancelar_nivel(request):
    request.session.flush()
    return redirect("escolher_nivel")

