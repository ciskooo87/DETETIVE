import json
import io
from pathlib import Path
from datetime import datetime

import streamlit as st
from PIL import Image, UnidentifiedImageError

# ---------------------------
# Config
# ---------------------------
st.set_page_config(
    page_title="Detetive — Casos Interativos",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ROOT = Path(__file__).parent
CASES_DIR = ROOT / "content" / "cases"
ASSETS = ROOT / "assets" / "images"

BRAND = {
    "studio": "Aurora Narrative Games",
    "tagline": "Casos interativos. Decida antes da verdade.",
}

# ---------------------------
# CSS — mobile UX + sticky header
# ---------------------------
st.markdown(
    """
<style>
.block-container { padding-top: 1rem; padding-bottom: 1.25rem; }
.stButton button { padding: 0.65rem 0.95rem; border-radius: 12px; }

.main .block-container > div:first-child {
  position: sticky;
  top: 0;
  z-index: 999;
  background: var(--background-color);
  backdrop-filter: blur(10px);
  padding-top: 0.25rem;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid rgba(128,128,128,0.25);
}

@media (max-width: 768px) {
  h1 { font-size: 1.6rem !important; }
  h2 { font-size: 1.25rem !important; }
  h3 { font-size: 1.05rem !important; }
  .block-container { padding-left: 0.9rem; padding-right: 0.9rem; }
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------
# Helpers — Cases
# ---------------------------
def list_cases() -> list[dict]:
    """Returns list of cases with slug + title."""
    if not CASES_DIR.exists():
        return []
    cases = []
    for p in sorted(CASES_DIR.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            slug = data.get("case", {}).get("slug") or p.stem
            title = data.get("case", {}).get("title") or slug
            cases.append({"slug": slug, "title": title, "path": p})
        except Exception:
            continue
    return cases

def load_case(case_path: Path) -> dict:
    if not case_path.exists():
        st.error(f"Arquivo do caso não encontrado: {case_path}")
        st.stop()
    return json.loads(case_path.read_text(encoding="utf-8"))

def pick_image(case_slug: str, stem: str) -> Path | None:
    # Busca em assets/images/<slug>/<stem>.<ext>
    base = ASSETS / case_slug
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = base / f"{stem}.{ext}"
        if p.exists():
            return p
    return None

def safe_image(path: Path | None, caption: str | None = None):
    if not path or not path.exists():
        return
    try:
        data = path.read_bytes()
        img = Image.open(io.BytesIO(data))
        img.verify()
        img = Image.open(io.BytesIO(data))
        st.image(img, use_container_width=True, caption=caption)
    except (UnidentifiedImageError, OSError, ValueError):
        with st.container(border=True):
            st.caption("Imagem indisponível (arquivo inválido).")
            st.code(str(path))

def badge(status: str) -> str:
    m = {"Neutro": "⚪", "Suspeito": "🟠", "Prioritário": "🔴", "Descartado": "🟢"}
    return m.get(status, "⚪")

# ---------------------------
# State
# ---------------------------
def init_state():
    if "initialized" in st.session_state:
        return
    st.session_state.initialized = True

    st.session_state.case_slug = None
    st.session_state.nav_page = "🏠 Início"

    # gameplay
    st.session_state.started = False
    st.session_state.current_env = 1
    st.session_state.max_opened_envelope = 0

    st.session_state.notes = ""
    st.session_state.timeline = []
    st.session_state.hypotheses = []

    st.session_state.suspects = {}  # será preenchido pelo caso
    st.session_state.decision_submitted = False
    st.session_state.decision = {
        "culprit": "",
        "method": "",
        "motive": "",
        "reasoning": "",
        "submitted_at": None,
    }

def reset_gameplay_for_case(case_data: dict):
    """Reseta apenas o progresso do jogo quando troca/inicia caso."""
    st.session_state.started = False
    st.session_state.current_env = 1
    st.session_state.max_opened_envelope = 0

    st.session_state.notes = ""
    st.session_state.timeline = []
    st.session_state.hypotheses = []

    # suspects: do caso (ou fallback)
    suspects = case_data.get("case", {}).get("suspects") or [
        "Daniel Moreira", "Laura Moreira", "Proprietário (Sr. Álvaro)"
    ]
    st.session_state.suspects = {s: {"status": "Neutro", "notes": ""} for s in suspects}

    st.session_state.decision_submitted = False
    st.session_state.decision = {
        "culprit": "",
        "method": "",
        "motive": "",
        "reasoning": "",
        "submitted_at": None,
    }

def go(page_name: str):
    st.session_state.nav_page = page_name
    st.rerun()

def require_case_loaded(case_data: dict):
    if not case_data:
        st.warning("Selecione um caso no menu (☰).")
        st.stop()

def require_started():
    if not st.session_state.started:
        st.warning("Inicie o caso pelo menu (☰) para acessar esta área.")
        st.stop()

def can_open(env_id: int) -> bool:
    return env_id <= st.session_state.max_opened_envelope

def all_unlocked() -> bool:
    return st.session_state.max_opened_envelope >= 6

def envelope_by_id(case_data: dict, env_id: int) -> dict:
    return next(e for e in case_data["envelopes"] if e["id"] == env_id)

# ---------------------------
# Boot
# ---------------------------
init_state()

cases = list_cases()
if not cases:
    st.error("Nenhum caso encontrado em content/cases/. Adicione ao menos um JSON.")
    st.stop()

# Determine current case
if st.session_state.case_slug is None:
    st.session_state.case_slug = cases[0]["slug"]

selected_case = next((c for c in cases if c["slug"] == st.session_state.case_slug), cases[0])
case_data = load_case(selected_case["path"])
case_slug = selected_case["slug"]

# Load images map for this case
IMG = {
    "cover": pick_image(case_slug, "cover"),
    1: pick_image(case_slug, "envelope1"),
    2: pick_image(case_slug, "envelope2"),
    3: pick_image(case_slug, "envelope3"),
    4: pick_image(case_slug, "envelope4"),
    5: pick_image(case_slug, "envelope5"),
    6: pick_image(case_slug, "envelope6"),
    "closing": pick_image(case_slug, "closing"),
}

# Ensure suspects initialized (first load)
if not st.session_state.suspects:
    reset_gameplay_for_case(case_data)

# ---------------------------
# Sticky TOP BAR with menu
# ---------------------------
top = st.container()
with top:
    colA, colB, colC = st.columns([0.5, 0.25, 0.25])
    with colA:
        st.caption(f"© {BRAND['studio']}")
    with colB:
        if st.session_state.started:
            prog = st.session_state.max_opened_envelope / 6
            st.progress(prog, text=f"{int(prog*100)}%")
        else:
            st.caption(BRAND["tagline"])
    with colC:
        with st.popover("☰ Menu", use_container_width=True):
            st.markdown("### Caso")
            options = {c["title"]: c["slug"] for c in cases}
            titles = list(options.keys())
            current_title = next((c["title"] for c in cases if c["slug"] == st.session_state.case_slug), titles[0])
            new_title = st.selectbox("Selecione", titles, index=titles.index(current_title))

            new_slug = options[new_title]
            if new_slug != st.session_state.case_slug:
                st.session_state.case_slug = new_slug
                # recarrega caso e reseta gameplay
                new_case = next((c for c in cases if c["slug"] == new_slug), cases[0])
                new_case_data = load_case(new_case["path"])
                reset_gameplay_for_case(new_case_data)
                st.session_state.nav_page = "🏠 Início"
                st.rerun()

            st.divider()

            pages = ["🏠 Início", "📦 Envelopes", "🗒️ Caderno", "✅ Decisão", "🔒 Fechamento"]
            current = st.session_state.nav_page
            idx = pages.index(current) if current in pages else 0
            sel = st.radio("Ir para", pages, index=idx)
            if sel != st.session_state.nav_page:
                st.session_state.nav_page = sel
                st.rerun()

            st.divider()

            if not st.session_state.started:
                if st.button("▶️ Iniciar caso", use_container_width=True):
                    st.session_state.started = True
                    st.session_state.max_opened_envelope = 1
                    st.session_state.current_env = 1
                    st.session_state.nav_page = "📦 Envelopes"
                    st.rerun()
            else:
                if st.button("🗒️ Abrir Caderno", use_container_width=True):
                    st.session_state.nav_page = "🗒️ Caderno"
                    st.rerun()
                if st.button("🔄 Reiniciar este caso", use_container_width=True):
                    reset_gameplay_for_case(case_data)
                    st.session_state.nav_page = "🏠 Início"
                    st.rerun()

st.divider()

# ---------------------------
# Pages
# ---------------------------
def page_home():
    require_case_loaded(case_data)
    title = case_data.get("case", {}).get("title", "Caso")
    subtitle = case_data.get("case", {}).get("subtitle", "Investigação narrativa com decisão bloqueando o fechamento.")

    st.markdown(f"# {title}")
    st.caption(subtitle)
    safe_image(IMG.get("cover"))

    with st.container(border=True):
        st.markdown("### Como funciona")
        st.markdown(
            "- Você recebe **envelopes** com contexto, depoimentos e provas.\n"
            "- As informações são liberadas em **ordem controlada**.\n"
            "- Você registra hipóteses, prioriza suspeitos e toma uma decisão final.\n"
            "- O **fechamento oficial** fica bloqueado até você enviar sua conclusão."
        )
        st.warning("Regra central: você só vê o fechamento **depois de decidir**.")

    if not st.session_state.started:
        st.info("Abra o **☰ Menu** e clique em **Iniciar caso**.")
    else:
        st.success("Caso iniciado. Vá para **Envelopes**.")

def page_envelopes():
    require_case_loaded(case_data)
    require_started()

    st.markdown("## 📦 Envelopes")
    st.caption("Abra na ordem. Confirme leitura para liberar o próximo.")

    with st.container(border=True):
        st.markdown("### Ordem de abertura")
        for env in case_data["envelopes"]:
            env_id = env["id"]
            allowed = can_open(env_id)
            short = env["title"].split("—")[-1].strip()
            label = f"Envelope {env_id} — {short}"
            if allowed:
                if st.button(f"📩 Abrir {label}", key=f"open_{case_slug}_{env_id}", use_container_width=True):
                    st.session_state.current_env = env_id
                    st.rerun()
            else:
                st.button(f"🔒 {label}", disabled=True, use_container_width=True)

    env_id = st.session_state.current_env
    env = envelope_by_id(case_data, env_id)

    st.divider()
    safe_image(IMG.get(env_id))
    st.markdown(f"### {env['title']}")
    st.markdown(env["body"])

    st.divider()

    if st.button("✅ Confirmar leitura", use_container_width=True):
        if st.session_state.max_opened_envelope == env_id and env_id < 6:
            st.session_state.max_opened_envelope += 1
        st.toast("Leitura confirmada.")
        st.rerun()

    next_id = min(env_id + 1, 6)
    next_allowed = can_open(next_id)
    if env_id >= 6:
        st.button("➡️ Próximo envelope (fim)", disabled=True, use_container_width=True)
    else:
        if st.button(f"➡️ Próximo envelope (Envelope {next_id})", disabled=not next_allowed, use_container_width=True):
            st.session_state.current_env = next_id
            st.rerun()

    if st.button("🗒️ Abrir Caderno do Investigador", use_container_width=True):
        go("🗒️ Caderno")

    # CTA: final do envelope 6 -> decisão
    if env_id == 6:
        st.warning("Você chegou ao último envelope. Próximo passo: declarar sua conclusão.")
        if st.button("✅ Ir para minha decisão", use_container_width=True):
            go("✅ Decisão")

    with st.popover("🧠 Hipótese rápida"):
        txt = st.text_input("Escreva curto e objetivo", key=f"hyp_fast_{case_slug}")
        if st.button("Salvar hipótese", use_container_width=True) and txt.strip():
            st.session_state.hypotheses.append({"at": datetime.now().isoformat(), "text": txt.strip()})
            st.toast("Hipótese registrada.")
            st.rerun()

def page_notebook():
    require_case_loaded(case_data)
    require_started()

    st.markdown("## 🗒️ Caderno do Investigador")
    st.caption("Hipóteses provisórias. Mudança de opinião é maturidade analítica.")

    with st.container(border=True):
        st.markdown("### Notas gerais")
        st.session_state.notes = st.text_area(
            "Registre hipóteses, contradições, dúvidas e próximos passos.",
            value=st.session_state.notes,
            height=180,
        )

    st.divider()
    with st.container(border=True):
        st.markdown("### 🧩 Hipóteses rápidas")
        if not st.session_state.hypotheses:
            st.caption("Nenhuma hipótese registrada ainda.")
        else:
            for item in reversed(st.session_state.hypotheses[-15:]):
                st.markdown(f"- {item['text']}")

    st.divider()
    with st.container(border=True):
        st.markdown("### 🕒 Linha do tempo")
        with st.form(f"timeline_form_{case_slug}", clear_on_submit=True):
            t = st.text_input("Evento (ex: 00h05 — discussão na recepção)")
            ok = st.form_submit_button("Adicionar")
            if ok and t.strip():
                st.session_state.timeline.append({"at": datetime.now().isoformat(), "event": t.strip()})
                st.toast("Evento adicionado.")
                st.rerun()

        if st.session_state.timeline:
            for i, item in enumerate(reversed(st.session_state.timeline[-12:]), start=1):
                st.write(f"{i}. {item['event']}")
        else:
            st.caption("Sem eventos ainda.")

    st.divider()
    with st.container(border=True):
        st.markdown("### 🎯 Suspeitos")
        for name, data in st.session_state.suspects.items():
            st.markdown(f"**{name}** {badge(data['status'])}")
            new_status = st.selectbox(
                "Status",
                ["Neutro", "Suspeito", "Prioritário", "Descartado"],
                index=["Neutro", "Suspeito", "Prioritário", "Descartado"].index(data["status"]),
                key=f"status_{case_slug}_{name}",
            )
            st.session_state.suspects[name]["status"] = new_status
            st.session_state.suspects[name]["notes"] = st.text_area(
                "Notas (provas e lógica)",
                value=data["notes"],
                key=f"notes_{case_slug}_{name}",
                height=80,
                placeholder="Ex: Digitais na arma + janela temporal + ruptura narrativa…",
            )
            st.divider()

def page_decision():
    require_case_loaded(case_data)
    require_started()

    st.markdown("## ✅ Decisão final")
    st.caption("O fechamento oficial só libera depois da sua conclusão.")

    if not all_unlocked():
        st.warning("Você ainda não liberou todos os envelopes. Termine o Envelope 6 para decidir.")
        return

    st.warning("Momento da decisão: preencha tudo. Sem campos vazios.")

    suspects_list = [""] + list(st.session_state.suspects.keys()) + ["Outro/Indeterminado"]

    with st.container(border=True):
        with st.form(f"decision_form_{case_slug}"):
            culprit = st.selectbox("Quem é o culpado?", suspects_list, index=0)
            method = st.text_input("Como foi o crime? (método/objeto/dinâmica)")
            motive = st.text_input("Qual foi o motivo?")
            reasoning = st.text_area(
                "Justificativa (por que sua hipótese explica melhor as provas?)",
                height=160,
            )
            ok = st.form_submit_button("📌 Enviar decisão")
            if ok:
                if not culprit or not method.strip() or not motive.strip() or not reasoning.strip():
                    st.error("Preencha todos os campos.")
                else:
                    st.session_state.decision_submitted = True
                    st.session_state.decision = {
                        "culprit": culprit,
                        "method": method.strip(),
                        "motive": motive.strip(),
                        "reasoning": reasoning.strip(),
                        "submitted_at": datetime.now().isoformat(),
                    }
                    st.success("Decisão registrada. Fechamento desbloqueado.")
                    st.rerun()

    if st.session_state.decision_submitted:
        st.divider()
        d = st.session_state.decision
        with st.container(border=True):
            st.markdown("### 📄 Sua decisão registrada")
            st.write(f"**Culpado:** {d['culprit']}")
            st.write(f"**Método:** {d['method']}")
            st.write(f"**Motivo:** {d['motive']}")
            st.write("**Justificativa:**")
            st.write(d["reasoning"])

def page_closing():
    require_case_loaded(case_data)
    require_started()

    st.markdown("## 🔒 Fechamento Oficial do Caso")
    if not st.session_state.decision_submitted:
        st.info("Bloqueado até você enviar sua decisão.")
        return

    safe_image(IMG.get("closing"))
    st.markdown("### A verdade não espera por consenso.")

    with st.container(border=True):
        st.markdown(f"## {case_data['closing']['title']}")
        st.markdown(case_data["closing"]["body"])

    st.caption("Fim do caso. Troque de caso no Menu (☰) para jogar outro.")

# ---------------------------
# Router
# ---------------------------
page = st.session_state.nav_page

if page == "🏠 Início":
    page_home()
elif page == "📦 Envelopes":
    page_envelopes()
elif page == "🗒️ Caderno":
    page_notebook()
elif page == "✅ Decisão":
    page_decision()
else:
    page_closing()
