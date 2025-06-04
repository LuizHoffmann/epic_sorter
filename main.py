from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uuid
import random
import copy

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Substitua aqui pelos nomes das 40 músicas do EPIC
ITEMS = [
    "The Horse and the Infant", "Just a Man", "Full Speed Ahead", "Open Arms", "Warrior of the Mind",
    "Polyphemus", "Survive", "Remember Them", "My Goodbye",
    "Storm", "Luck Runs Out", "Keep Your Friends Close", "Ruthlessness",
    "Puppeteer", "Wouldn't You Like", "Done For", "There Are Other Ways",
    "The Underworld", "No Longer You", "Monster",
    "Suffering", "Different Beast", "Scylla", "Mutiny", "Thunder Bringer",
    "Legendary", "Little Wolf", "We'll Be Fine", "Love in Paradise", "God Games",
    "Not Sorry for Loving You", "Dangerous", "Charybdis", "Get in the Water", "Six Hundred Strike",
    "The Challenge", "Hold Them Down", "Odysseus", "I Can't Help but Wonder", "Would You Fall in Love with Me Again"
]

SESSIONS = {}

# ----------------------------
# Etapa 1: Gerar pilha de merges bottom-up
# ----------------------------
def build_merge_schedule(items):
    """Cria uma fila de merges recursivos com blocos reais."""
    schedule = []
    blocks = [[item] for item in items]

    while len(blocks) > 1:
        new_blocks = []
        for i in range(0, len(blocks), 2):
            if i + 1 < len(blocks):
                left = blocks[i]
                right = blocks[i + 1]
                merge = {
                    "left": left,
                    "right": right,
                    "result": []
                }
                schedule.append(merge)
                # Em vez de None, adicionamos um placeholder real
                new_blocks.append(merge["result"])
            else:
                new_blocks.append(blocks[i])
        blocks = new_blocks

    return schedule

# ----------------------------
# Rota inicial: cria a sessão
# ----------------------------
@app.get("/", response_class=HTMLResponse)
async def start(request: Request):
    session_id = str(uuid.uuid4())
    items = copy.deepcopy(ITEMS)
    random.shuffle(items)

    SESSIONS[session_id] = {
        "schedule": build_merge_schedule(items),
        "current": None,
        "stack": [],
        "final_result": None
    }

    return RedirectResponse(url=f"/merge/{session_id}")

# ----------------------------
# Etapa de merge
# ----------------------------
@app.get("/merge/{session_id}", response_class=HTMLResponse)
async def merge_step(request: Request, session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        return RedirectResponse(url="/")

    # Se finalizado
    if session["final_result"]:
        return templates.TemplateResponse("result.html", {
            "request": request,
            "result": session["final_result"]
        })

    # Se não há merge atual, pega o próximo da schedule
    if session["current"] is None:
        if not session["schedule"]:
            # Merge completo
            session["final_result"] = session["stack"].pop()
            return templates.TemplateResponse("result.html", {
                "request": request,
                "result": session["final_result"]
            })

        session["current"] = session["schedule"].pop(0)

    curr = session["current"]

    # Se um dos lados estiver vazio, descarte
    if not curr["left"]:
        curr["result"].extend(curr["right"])
        curr["right"] = []
    elif not curr["right"]:
        curr["result"].extend(curr["left"])
        curr["left"] = []

    # Se terminou o merge atual, empilha o resultado
    if not curr["left"] and not curr["right"]:
        result = curr["result"]
        session["current"] = None

        # Joga o resultado no topo da stack (bloco ordenado)
        session["stack"].append(result)

        return RedirectResponse(url=f"/merge/{session_id}")

    # Comparação interativa
    return templates.TemplateResponse("index.html", {
        "request": request,
        "session_id": session_id,
        "left": curr["left"][0],
        "right": curr["right"][0]
    })


# ----------------------------
# Escolha do usuário
# ----------------------------
@app.post("/choose/{session_id}", response_class=HTMLResponse)
async def choose(session_id: str, choice: str = Form(...)):
    session = SESSIONS.get(session_id)
    if not session or not session["current"]:
        return RedirectResponse(url="/")

    curr = session["current"]

    if choice == "left":
        curr["result"].append(curr["left"].pop(0))
    else:
        curr["result"].append(curr["right"].pop(0))

    return RedirectResponse(url=f"/merge/{session_id}", status_code=303)
