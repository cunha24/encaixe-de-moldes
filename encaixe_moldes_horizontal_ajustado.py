
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import ezdxf
import io
from matplotlib.backends.backend_pdf import PdfPages

st.title("Sistema de Encaixe Otimizado de Moldes")

tecido_largura = st.number_input("Digite a largura do tecido (cm):", min_value=10, max_value=1000, step=1, value=160)
uploaded_file = st.file_uploader("Envie seu arquivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.write("Pré-visualização dos dados:", df.head())

    retangulos = []
    for _, row in df.iterrows():
        for _ in range(int(row['quantidade'])):
            retangulos.append({
                'comprimento': row['comprimento'],
                'largura': row['largura'],
                'descricao': row['descricao'],
                'area': row['comprimento'] * row['largura']
            })

    retangulos.sort(key=lambda r: r['area'], reverse=True)

    ocupados = []
    layout = []
    espacamento = 2
    altura_total = 0

    def cabe_em(x, y, w, h):
        if x + w > tecido_largura:
            return False
        for r in ocupados:
            if not (x + w <= r['x'] or r['x'] + r['largura'] <= x or
                    y + h <= r['y'] or r['y'] + r['comprimento'] <= y):
                return False
        return True

    def encontrar_posicao(w, h):
        for y in range(0, 10000, 1):
            for x in range(0, int(tecido_largura - w + 1), 1):
                if cabe_em(x, y, w, h):
                    return x, y
        return None, None

    for r in retangulos:
        w, h = r['largura'], r['comprimento']
        x, y = encontrar_posicao(w, h)
        rotacionado = False

        if x is None:
            w, h = h, w
            x, y = encontrar_posicao(w, h)
            if x is not None:
                rotacionado = True
            else:
                st.error("Não foi possível encaixar uma peça. Aumente a largura do tecido ou reduza tamanhos.")
                break

        layout.append({'x': x, 'y': y, 'largura': w, 'comprimento': h, 'descricao': r['descricao'], 'rotacionado': rotacionado})
        ocupados.append({'x': x, 'y': y, 'largura': w + espacamento, 'comprimento': h + espacamento})
        altura_total = max(altura_total, y + h)

    tecido_usado_metros = (altura_total + 100) / 100
    st.success(f"Comprimento total de tecido necessário: {tecido_usado_metros:.2f} metros")

    fig, ax = plt.subplots(figsize=(10, 10))
    for r in layout:
        rect = plt.Rectangle((r['x'], -r['y']), r['largura'], -r['comprimento'], edgecolor='black', facecolor='lightblue')
        ax.add_patch(rect)
        texto = f"{r['descricao']}\n{r['comprimento']}x{r['largura']}"
        ax.text(r['x'] + r['largura']/2, -r['y'] - r['comprimento']/2, texto, fontsize=6, ha='center', va='center')

    ax.set_xlim(0, tecido_largura)
    ax.set_ylim(-altura_total - 100, 0)
    ax.set_aspect('equal')
    st.pyplot(fig)

    # Exportar para PDF
    pdf_buffer = io.BytesIO()
    with PdfPages(pdf_buffer) as pdf:
        pdf.savefig(fig, bbox_inches='tight')
        pdf.close()
    st.download_button("Baixar Visualização em PDF", data=pdf_buffer.getvalue(), file_name="visualizacao_moldes.pdf")

    if st.button("Exportar DXF"):
        doc = ezdxf.new()
        msp = doc.modelspace()
        for r in layout:
            x0, y0 = r['x'], -r['y']
            x1, y1 = x0 + r['largura'], y0 - r['comprimento']
            msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)])
            texto = f"{r['descricao']}\n{r['comprimento']}x{r['largura']}"
            msp.add_text(texto, dxfattribs={'height': 5}).set_pos((x0 + r['largura']/2, y0 - r['comprimento']/2), align='CENTER')

        dxf_stream = io.BytesIO()
        doc.write(dxf_stream)
        st.download_button("Baixar Arquivo DXF", data=dxf_stream.getvalue(), file_name="moldes_otimizados.dxf")
