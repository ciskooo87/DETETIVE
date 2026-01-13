import json
import streamlit as st
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="Pousada Aurora — Investigação",
    page_icon="🕵️",
    layout="wide",
)

CONTENT_PATH = Path(__file__).parent / "content" / "envelopes_ptbr.json"

def load_content():
    with open(CONTENT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def init_state():
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.started = False
        st.session_state.max_opened_envelope = 0
        st.session_state.notes = ""
        st.session_state.timeline = []
        st.session_state.suspects = {
            "Daniel Moreira": {"status": "Neutro", "notes": ""},
            "Laura Moreira": {"status": "Neutro", "notes": ""},
            "Proprietário (Sr. Álvaro)": {"status": "Neutro", "notes": ""},
        }
        st.session_state.decision_submitted = False
        st.session_state.decision = {
            "culprit": "",
            "method": "",
            "motive": "",
            "reasoning": "",
            "submitted_at": None,
        }

def badge(status: str) -> str:
    m = {
        "Neutro": "⚪",
        "Suspeito": "🟠",
        "Prioritário": "🔴",
        "Descartado": "🟢",
    }
    return m.get(status, "⚪")

content = load_content()
init_state()

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("### 🕵️ Pousada Aurora")
    st.caption("Investigação narrativa com abertura sequencial de evidências.")

    if not st.session_state.started:
        st.info("Clique em **Iniciar caso** para começar.")
        if st.button("▶️ Iniciar caso", use_container_width=True):
            st.session_state.started = True
            st.session_state.max_opened_envelope = 1
            st.rerun()
    else:
        st.success("Caso em andamento.")
        st.write(f"**Envelopes liberados:** 1 → {st.session_state.max_opened_envelope}")

        if st.button("🔄 Reiniciar caso", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    st.divider()
    st.markdown("### 📌 Suspeitos")
    for name, data in st.session_state.suspects.items():
        st.write(f"{badge(data['status'])} **{name}** — {data['status']}")

    st.divider()
    st.markdown("### 🧠 Regras rápidas")
    st.caption("1) Abra envelopes na ordem. 2) Registre hipóteses. 3) Envie sua decisão antes do fechamento.")

# ---------- MAIN ----------
st.title(content.get("case_title", "Caso"))

tabs = st.tabs(["📦 Envelopes", "🗒️ Caderno", "✅ Decisão", "🔒 Fechamento"])

# ---------- TAB 1: ENVELOPES ----------
with tabs[0]:
    if not st.session_state.started:
        st.warning("Inicie o caso pelo menu lateral.")
    else:
        left, right = st.columns([0.35, 0.65], gap="large")

        with left:
            st.subheader("Ordem de abertura")
            for env in content["envelopes"]:
                env_id = env["id"]
                allowed = env_id <= st.session_state.max_opened_envelope
                label = f"Envelope {env_id}"
                if allowed:
                    if st.button(f"📩 Abrir {label}", key=f"open_{env_id}", use_container_width=True):
                        st.session_state.current_env = env_id
                else:
                    st.button(f"🔒 {label} (bloqueado)", disabled=True, use_container_width=True)

            st.divider()
            st.caption("Liberação progressiva: ao confirmar leitura, libera o próximo.")

        with right:
            env_id = st.session_state.get("current_env", 1)
            env = next(e for e in content["envelopes"] if e["id"] == env_id)

            st.subheader(env["title"])
            st.markdown(env["body"])

            st.divider()
            col_a, col_b = st.columns([0.5, 0.5])

            with col_a:
                if st.button("✅ Confirmar leitura", use_container_width=True):
                    if st.session_state.max_opened_envelope == env_id and env_id < 6:
                        st.session_state.max_opened_envelope += 1
                    st.toast("Leitura confirmada. Próximo envelope liberado (se aplicável).")
                    st.rerun()

            with col_b:
                st.button("🧭 Voltar ao topo", use_container_width=True)

# ---------- TAB 2: NOTEBOOK ----------
with tabs[1]:
    if not st.session_state.started:
        st.warning("Inicie o caso para usar o caderno.")
    else:
        c1, c2 = st.columns([0.55, 0.45], gap="large")

        with c1:
            st.subheader("🗒️ Notas gerais do investigador")
            st.session_state.notes = st.text_area(
                "Registre hipóteses, contradições, dúvidas e próximos passos.",
                value=st.session_state.notes,
                height=260,
            )

            st.subheader("🕒 Linha do tempo")
            with st.form("timeline_form", clear_on_submit=True):
                t = st.text_input("Evento (ex: 00h05 — discussão na recepção)")
                submitted = st.form_submit_button("Adicionar evento")
                if submitted and t.strip():
                    st.session_state.timeline.append({"at": datetime.now().isoformat(), "event": t.strip()})
                    st.toast("Evento adicionado.")
            if st.session_state.timeline:
                for i, item in enumerate(reversed(st.session_state.timeline), start=1):
                    st.write(f"{i}. {item['event']}")

        with c2:
            st.subheader("🎯 Gestão de suspeitos")
            for name, data in st.session_state.suspects.items():
                st.markdown(f"**{name}**")
                new_status = st.selectbox(
                    "Status",
                    ["Neutro", "Suspeito", "Prioritário", "Descartado"],
                    index=["Neutro", "Suspeito", "Prioritário", "Descartado"].index(data["status"]),
                    key=f"status_{name}",
                )
                st.session_state.suspects[name]["status"] = new_status
                new_notes = st.text_area(
                    "Notas sobre este suspeito",
                    value=data["notes"],
                    key=f"notes_{name}",
                    height=90,
                )
                st.session_state.suspects[name]["notes"] = new_notes
                st.divider()

# ---------- TAB 3: DECISION ----------
with tabs[2]:
    if not st.session_state.started:
        st.warning("Inicie o caso para decidir.")
    else:
        st.subheader("✅ Decisão final (obrigatória antes do fechamento)")
        st.caption("Você só desbloqueia o Fechamento Oficial depois de enviar sua decisão.")

        unlocked_all = (st.session_state.max_opened_envelope >= 6)
        if not unlocked_all:
            st.warning("Você ainda não liberou todos os envelopes. Termine a leitura para decidir com base completa.")
        else:
            with st.form("decision_form"):
                culprit = st.selectbox(
                    "Quem é o culpado?",
                    ["", "Daniel Moreira", "Laura Moreira", "Proprietário (Sr. Álvaro)", "Outro/Indeterminado"],
                    index=0,
                )
                method = st.text_input("Como foi o crime? (método/objeto/dinâmica)")
                motive = st.text_input("Qual foi o motivo?")
                reasoning = st.text_area("Justificativa (por que sua hipótese explica melhor as provas?)", height=180)

                ok = st.form_submit_button("📌 Enviar decisão e desbloquear fechamento")
                if ok:
                    if not culprit or not method.strip() or not motive.strip() or not reasoning.strip():
                        st.error("Preencha todos os campos. Decisão incompleta não desbloqueia o fechamento.")
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
            st.markdown("### 📄 Sua decisão registrada")
            d = st.session_state.decision
            st.write(f"**Culpado:** {d['culprit']}")
            st.write(f"**Método:** {d['method']}")
            st.write(f"**Motivo:** {d['motive']}")
            st.write("**Justificativa:**")
            st.write(d["reasoning"])

# ---------- TAB 4: CLOSING ----------
with tabs[3]:
    st.subheader("🔒 Fechamento Oficial do Caso")
    if not st.session_state.started:
        st.warning("Inicie o caso.")
    elif not st.session_state.decision_submitted:
        st.info("Bloqueado até você enviar sua decisão final.")
    else:
        st.markdown(f"### {content['closing']['title']}")
        st.markdown(content["closing"]["body"])
        st.divider()
        st.caption("Fim do caso. Se você quiser, reinicie e tente novamente com outra hipótese.")
