import json
import sys
from pathlib import Path
from tqdm import tqdm

# Função para construir árvore de pastas com arquivos
def construir_arvore(arquivos, base_path):
    raiz = {}

    for arquivo in arquivos:
        relativo = arquivo.relative_to(base_path)
        partes = relativo.parts

        ponteiro = raiz
        for parte in partes[:-1]:
            if parte not in ponteiro:
                ponteiro[parte] = {}
            ponteiro = ponteiro[parte]

        ponteiro[partes[-1]] = arquivo  # Guarda Path do arquivo

    return raiz

# Função recursiva para gerar HTML da árvore
def gerar_html_pasta(estrutura, projeto_path, descricoes, arquivos, barra_progresso=None):
    html = "<ul>"

    for chave, valor in estrutura.items():
        if isinstance(valor, dict):
            # Pasta: só mostra o nome da pasta, clicável para expandir
            html += f"""
            <li>
              <div class="toggle-text">📁 {chave}</div>
              <div class="detalhes">
                <div class="nested">
                  {gerar_html_pasta(valor, projeto_path, descricoes, arquivos, barra_progresso)}
                </div>
              </div>
            </li>
            """
        else:
            if barra_progresso:
                barra_progresso.update(1)

            nome = valor.name
            caminho = str(valor.relative_to(projeto_path))
            descricao = descricoes.get(nome, "Sem descrição definida.")

            referencias = []
            for arquivo in arquivos:
                try:
                    with open(arquivo, "r", encoding="utf-8") as f:
                        if nome in f.read():
                            referencias.append(str(arquivo.relative_to(projeto_path)))
                except:
                    continue

            # Conteúdo escondido que aparece ao clicar
            detalhes = f"""
            <p><strong>Caminho:</strong> {caminho}</p>
            <p><strong>Descrição:</strong> {descricao}</p>
            """

            if referencias:
                detalhes += "<p><strong>Referenciado em:</strong></p><ul>"
                for ref in referencias:
                    detalhes += f"<li>{ref}</li>"
                detalhes += "</ul>"
            else:
                detalhes += "<p><em>Sem referências encontradas.</em></p>"

            html += f"""
            <li>
              <div class="toggle-text">📄 {nome}</div>
              <div class="detalhes" style="display:none; margin-left: 1em;">
                {detalhes}
              </div>
            </li>
            """

    html += "</ul>"
    return html


def main():
    if len(sys.argv) < 2:
        print("❌ Uso: python main.py <caminho_do_projeto>")
        sys.exit(1)

    projeto_path = Path(sys.argv[1])
    if not projeto_path.exists():
        print(f"❌ Caminho '{projeto_path}' não encontrado.")
        sys.exit(1)

    # Carrega descrições
    with open("descricoes.json", encoding="utf-8") as f:
        descricoes = json.load(f)

    # Lista arquivos ignorando imagens grandes
    arquivos = list(projeto_path.rglob("*.*"))
    arquivos = [f for f in arquivos if f.is_file() and f.suffix.lower() not in ['.png', '.jpg', '.jpeg', '.gif', '.ico']]

    print("🔄 Construindo árvore e gerando manual...")

    # Construir árvore
    estrutura_arquivo = construir_arvore(arquivos, projeto_path)

    total_arquivos = len(arquivos)
    with tqdm(total=total_arquivos, desc="Arquivos processados") as barra:
        conteudo_html = gerar_html_pasta(estrutura_arquivo, projeto_path, descricoes, arquivos, barra_progresso=barra)

    # Carrega template
    with open("template.html", encoding="utf-8") as f:
        template = f.read()

    saida_final = template.replace("{{CONTEUDO}}", conteudo_html)

    # Salva
    Path("output").mkdir(exist_ok=True)
    with open("output/manual.html", "w", encoding="utf-8") as f:
        f.write(saida_final)

    print("✅ Manual gerado com sucesso em: output/manual.html")

if __name__ == "__main__":
    main()
