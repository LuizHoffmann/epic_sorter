from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import random

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Static (opcional)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Lista original de músicas
original_list = [
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

# Sessão global temporária (sem login)
SESSIONS = {}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    session_id = str(id(request))  # ID simplificado

    if session_id not in SESSIONS:
        items = original_list.copy()
        random.shuffle(items)
        SESSIONS[session_id] = {"stack": [(items, [])], "result": None}

    return RedirectResponse(url=f"/sort/{session_id}")

@app.get("/sort/{session_id}", response_class=HTMLResponse)
async def sort_step(request: Request, session_id: str):
    state = SESSIONS.get(session_id)

    if not state or not state["stack"]:
        return templates.TemplateResponse("result.html", {"request": request, "result": state["result"]})

    lista, acumulado = state["stack"][-1]

    if len(lista) <= 1:
        SESSIONS[session_id]["stack"].pop()
        if SESSIONS[session_id]["stack"]:
            SESSIONS[session_id]["stack"][-1][1].extend(lista)
            return RedirectResponse(url=f"/sort/{session_id}")
        else:
            SESSIONS[session_id]["result"] = acumulado + lista
            return RedirectResponse(url=f"/sort/{session_id}")

    mid = len(lista) // 2
    esquerda = lista[:mid]
    direita = lista[mid:]

    SESSIONS[session_id]["stack"].pop()
    SESSIONS[session_id]["stack"].append(([], acumulado))
    SESSIONS[session_id]["stack"].append((direita, []))
    SESSIONS[session_id]["stack"].append((esquerda, []))

    return RedirectResponse(url=f"/compare/{session_id}")

@app.get("/compare/{session_id}", response_class=HTMLResponse)
async def compare(request: Request, session_id: str):
    state = SESSIONS[session_id]

    # Se o resultado final já estiver pronto
    if state.get("result"):
        return RedirectResponse(url=f"/sort/{session_id}")

    # Se temos menos de dois blocos, terminamos um merge
    while len(state["stack"]) >= 2 and (not state["stack"][-1][0] or not state["stack"][-2][0]):
        right = state["stack"].pop()
        left = state["stack"].pop()
        merged = left[0] + right[0]
        state["stack"][-1][1].extend(merged)

    if len(state["stack"]) < 2:
        # Se só sobrou o bloco acumulado final
        state["result"] = state["stack"][-1][1] + state["stack"][-1][0]
        return RedirectResponse(url=f"/sort/{session_id}")

    left = state["stack"][-2][0]
    right = state["stack"][-1][0]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "session_id": session_id,
        "left": left[0],
        "right": right[0]
    })

@app.post("/choose/{session_id}", response_class=HTMLResponse)
async def choose(session_id: str, choice: str = Form(...)):
    state = SESSIONS[session_id]
    left = state["stack"][-2][0]
    right = state["stack"][-1][0]
    result = state["stack"][-3][1]

    if choice == "left":
        result.append(left.pop(0))
    else:
        result.append(right.pop(0))

    return RedirectResponse(url=f"/compare/{session_id}", status_code=303)
