import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO

# Configuração da página
st.set_page_config(
    page_title="ASPE - Auditoria de Segurança", layout="wide", page_icon="icone.png")

col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    st.image("logo.png", width=400)
    st.markdown(
        "Ferramenta de diagnóstico de segurança digital baseada em boas práticas e LGPD.")

# Carregamento do arquivo Excel


@st.cache_data
def carregar_perguntas(arquivo):
    df = pd.read_excel(arquivo)
    df = df.dropna(subset=["perfil", "texto", "peso", "recomendacao", "bloco"])
    return df


arquivo_excel = "Questoes.xlsx"
try:
    perguntas_df = carregar_perguntas(arquivo_excel)
except Exception as e:
    st.error(f"Erro ao carregar o arquivo: {e}")
    st.stop()

# Tela 1 – Seleção de perfil
st.header("1️⃣ Bem-vindo à ASPE")
perfil = st.selectbox("Selecione seu perfil para iniciar:",
                      sorted(perguntas_df["perfil"].unique()))

if perfil:
    perguntas_filtradas = perguntas_df[perguntas_df["perfil"] == perfil].reset_index(
        drop=True)
    blocos = perguntas_filtradas["bloco"].unique()

    st.header("2️⃣ Diagnóstico Interativo")
    respostas = []

    for bloco in blocos:
        st.subheader(f"📂 Bloco: {bloco}")
        bloco_perguntas = perguntas_filtradas[perguntas_filtradas["bloco"] == bloco]
        for i, row in bloco_perguntas.iterrows():
            st.subheader(f"{i+1}. {row['texto']}")
            resposta = st.radio("Selecione uma opção:", [
                "Sim", "Parcialmente", "Não"], key=f"q{i}")

            # resposta = st.radio(f"{row['texto']}", [
            #                   "Sim", "Parcialmente", "Não"], key=f"q{i}")
            respostas.append({
                "bloco": row["bloco"],
                "pergunta": row["texto"],
                "resposta": resposta,
                "peso": row["peso"],
                "recomendacao": row["recomendacao"]
            })

    nivelPdf = ""

    if st.button("📊 Ver Resultado"):
        st.header("3️⃣ Resultado do Diagnóstico")

        # Resultado geral
        total_peso = sum(r["peso"] * 2 for r in respostas)
        pontuacao = sum(
            r["peso"] * (2 if r["resposta"] ==
                         "Não" else 1 if r["resposta"] == "Parcialmente" else 0)
            for r in respostas
        )
        risco = round((pontuacao / total_peso) * 100)
        if risco <= 20:
            nivel = "🟢 Alta Maturidade"
            nivelPdf = "Alta Maturidade"
        elif risco <= 50:
            nivel = "🟡 Maturidade Intermediária"
            nivelPdf = "Maturidade Intermediária"
        else:
            nivel = "🔴 Baixa Maturidade"
            nivelPdf = "Baixa Maturidade"

        st.subheader("📊 Resultado Geral")
        st.metric(label="Percentual de Risco", value=f"{risco}%")
        st.success(f"Diagnóstico geral: {nivel}")

        # Maturidade por bloco
        st.subheader("📊 Maturidade por Bloco")
        respostas_por_bloco = {}
        maturidade_por_bloco = {}

        for r in respostas:
            respostas_por_bloco.setdefault(r["bloco"], []).append(r)

        for bloco, respostas_bloco in respostas_por_bloco.items():
            total_bloco = sum(r["peso"] * 2 for r in respostas_bloco)
            pontos_bloco = sum(
                r["peso"] * (2 if r["resposta"] ==
                             "Não" else 1 if r["resposta"] == "Parcialmente" else 0)
                for r in respostas_bloco
            )
            risco_bloco = round((pontos_bloco / total_bloco) * 100)
            if risco_bloco <= 20:
                nivel_bloco = "🟢 Alta Maturidade"
                nivel_bloco_pdf = "Alta Maturidade"
            elif risco_bloco <= 50:
                nivel_bloco = "🟡 Maturidade Intermediária"
                nivel_bloco_pdf = "Maturidade Intermediária"
            else:
                nivel_bloco = "🔴 Baixa Maturidade"
                nivel_bloco_pdf = "Baixa Maturidade"
            maturidade_por_bloco[bloco] = {
                "nivel": nivel_bloco_pdf, "risco": risco_bloco}
            st.markdown(
                f"**{bloco}** – {nivel_bloco} (risco - {risco_bloco}%)")

        # Recomendações
        st.subheader("📌 Recomendações por Bloco")
        for bloco, respostas_bloco in respostas_por_bloco.items():
            st.markdown(f"**🔍 {bloco}**")
            recomendacoes = [
                r for r in respostas_bloco if r["resposta"] != "Sim"]
            if recomendacoes:
                for r in recomendacoes:
                    st.markdown(f"- {r['pergunta']}\n  ➡️ {r['recomendacao']}")
            else:
                st.markdown("_Sem recomendações adicionais._")

        # PDF com fpdf2
        def gerar_grafico_pizza(respostas, titulo):
            contagem = {"Sim": 0, "Parcialmente": 0, "Não": 0}
            for r in respostas:
                contagem[r["resposta"]] += 1
            labels = list(contagem.keys())
            sizes = list(contagem.values())
            fig, ax = plt.subplots()
            ax.pie(sizes, labels=labels, autopct=lambda pct: f"{pct:.1f}%" if pct > 1 else "", startangle=90,
                   colors=["#4CAF50", "#FFC107", "#F44336"])
            ax.axis("equal")
            # plt.title(titulo)
            buffer = BytesIO()
            plt.savefig(buffer, format="png", bbox_inches="tight")
            plt.close(fig)
            buffer.seek(0)
            return buffer

        def gerar_pdf(perfil, nivel_geral, risco_geral, respostas, respostas_por_bloco, maturidade_por_bloco):
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.set_text_color(0, 102, 204)
            pdf.cell(0, 10, "ASPE - Auditoria de Segurança", ln=True, align="C")

            pdf.set_font("Arial", "", 12)
            pdf.set_text_color(0)
            pdf.ln(5)
            pdf.cell(0, 10, f"Perfil avaliado: {perfil}", ln=True)
            pdf.cell(
                0, 10, f"Diagnóstico geral: {nivel_geral} (risco {risco_geral}%)", ln=True)

            geral_img = gerar_grafico_pizza(
                respostas, "Distribuição Geral de Respostas")
            pdf.image(geral_img, x=55, w=100)
            pdf.ln(10)

            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Maturidade por Bloco", ln=True)
            pdf.set_font("Arial", "", 12)
            for bloco, info in maturidade_por_bloco.items():
                pdf.cell(
                    0, 8, f"{bloco}: {info['nivel']} (risco {info['risco']}%)", ln=True)

            pdf.add_page()

            grafico = 1
            for bloco, respostas_bloco in respostas_por_bloco.items():
                bloco_img = gerar_grafico_pizza(respostas_bloco, f"{bloco}")
                # pdf.add_page()
                pdf.set_font("Arial", "B", 14)
                pdf.cell(
                    0, 10, f"Distribuição de Respostas - {bloco}", ln=True)
                pdf.image(bloco_img, x=55, w=100)
                pdf.ln(10)
                if grafico % 2 == 0:
                    pdf.add_page()
                grafico += 1

            pdf.add_page()
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Recomendações por Bloco", ln=True)
            pdf.set_font("Arial", "", 11)
            for bloco, respostas_bloco in respostas_por_bloco.items():
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 8, f"{bloco}", ln=True)
                pdf.set_font("Arial", "", 11)
                recomendacoes = [
                    r for r in respostas_bloco if r["resposta"] != "Sim"]
                if recomendacoes:
                    for r in recomendacoes:
                        pdf.multi_cell(
                            0, 6, f"- {r['pergunta']}\n- {r['recomendacao']}")
                        pdf.ln(2)
                else:
                    pdf.cell(0, 6, "Sem recomendações adicionais.", ln=True)
                    pdf.ln(2)

            return pdf.output(dest="S")

        st.subheader("📄 Relatório em PDF")
        pdf_bytes = bytes(gerar_pdf(perfil, nivelPdf, risco, respostas,
                                    respostas_por_bloco, maturidade_por_bloco))
        st.download_button("📥 Baixar Relatório", data=pdf_bytes,
                           file_name="relatorio_aspe.pdf", mime="application/pdf")
