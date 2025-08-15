import json
import sys
from pathlib import Path
from tqdm import tqdm
import os
import google.generativeai as genai
import html

def gerar_descricao_com_gemini(caminho_arquivo, projeto_path):

    print(f"\n📄 Gerando descrição para: {caminho_arquivo.name}")
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Variável GEMINI_API_KEY não definida no ambiente.")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemma-3-27b-it')
        
        conteudo_arquivo = caminho_arquivo.read_text(encoding='utf-8', errors='ignore') or ""

        prompt_text = f"""
## SUA TAREFA
Sua tarefa é gerar uma descrição técnica e funcional para o arquivo de código-fonte fornecido no final deste prompt.

## DIRETRIZES PARA A DESCRIÇÃO
1.  **Público-Alvo:** Programador júnior ou alguém vendo o projeto pela primeira vez
2.  **Limite:** Máximo 1000 caracteres  

3.  **Foco:** Função principal do arquivo e como ele se conecta ao projeto
4.  **Tom:** Direto e didático, evitando jargões complexos
5.  **Formato:** Apenas texto puro, sem cabeçalhos ou formatações

## CÓDIGO-FONTE PARA ANÁLISE
- Nome do Arquivo: {caminho_arquivo.name}
- Caminho: {str(caminho_arquivo.relative_to(projeto_path))}

{conteudo_arquivo[:1000]}
"""
        
        resposta = model.generate_content(prompt_text)
        return resposta.text.strip()

    except Exception as e:
        print(f"⚠️ Erro ao gerar descrição: {e}")
        return f"Erro ao gerar descrição: {e}"
    
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
        ponteiro[partes[-1]] = arquivo
    return raiz

def gerar_html_pasta(estrutura, projeto_path, descricoes, arquivos, info_projeto, barra_progresso=None):
    html_content = "<ul>"
    for chave, valor in sorted(estrutura.items()):
        if isinstance(valor, dict):
            html_content += f"""
            <li>
              <div class='toggle-text'>📁 {chave}</div>
              <div class='detalhes' style='display:none;'>
                <div class='nested'>
                  {gerar_html_pasta(valor, projeto_path, descricoes, arquivos, info_projeto, barra_progresso)}
                </div>
              </div>
            </li>
            """
        else:
            if barra_progresso:
                barra_progresso.update(1)
                
            nome_arquivo = valor.name
            caminho_relativo = str(valor.relative_to(projeto_path))
            
            #---------------------------------- Verifica se precisa gerar nova descrição
            if nome_arquivo not in descricoes:
                descricao_gerada = gerar_descricao_com_gemini(valor, projeto_path)
                descricoes[nome_arquivo] = {
                    'descricao': descricao_gerada,
                    'referencia': ""  #----------------------------------Inicializa referência vazia
                }
                #----------------------------------Salva imediatamente no arquivo
                with open("descricoes.json", "w", encoding="utf-8") as f:
                    json.dump(descricoes, f, indent=4, ensure_ascii=False)
            
            #----------------------------------Obtém a descrição (agora garantido que existe)
            descricao = descricoes[nome_arquivo].get('descricao', "Sem descrição definida.")
            descricao_html = html.escape(descricao)  #----------------------------------ESCAPA AQUI
            
            #----------------------------------Busca por referências
            referencias = []
            for arq_ref in arquivos:
                if arq_ref == valor:
                    continue
                try:
                    with open(arq_ref, "r", encoding="utf-8", errors='ignore') as f:
                        if nome_arquivo in f.read():
                            referencias.append(str(arq_ref.relative_to(projeto_path)))
                except:
                    continue
            
            #----------------------------------Construindo a 22seção de detalhes
            detalhes = f"""
            <p><strong>Caminho:</strong> {caminho_relativo}</p>
            <p><strong>Descrição:</strong> {descricao_html}</p>
            """
            
            if referencias:
                detalhes += "<p><strong>Referenciado em:</strong></p><ul>"
                for ref in sorted(set(referencias)):
                    detalhes += f"<li>{ref}</li>"
                detalhes += "</ul>"
            else:
                detalhes += "<p><em>Sem referências encontradas.</em></p>"
            
            html_content += f"""
            <li>
              <div class='toggle-text'>📄 {nome_arquivo}</div>
              <div class='detalhes' style='display:none; margin-left: 1em;'>
                {detalhes}
              </div>
            </li>
            """
    return html_content + "</ul>"

def main():
    if len(sys.argv) < 2:
        print("❌ Uso: python main.py <caminho_do_projeto>")
        sys.exit(1)

    projeto_path = Path(sys.argv[1]).resolve()
    if not projeto_path.is_dir():
        print(f"❌ '{projeto_path}' não é um diretório válido.")
        sys.exit(1)

    #----------------------------------Informações básicas do projeto (agora definidas automaticamente)

    #----------------------------------Configurações iniciais
    Path("output").mkdir(exist_ok=True)
    if not Path("style.css").exists():
        Path("style.css").write_text("""
        details { margin-left: 20px; }
        summary { cursor: pointer; }
        .detalhes { padding: 10px; }
        """)

    #----------------------------------Processamento dos arquivos
    ignorar_ext = ['.png', '.jpg', '.pdf', '.jpeg', '.gif', '.svg', '.ico', '.webp', '.mp4', '.mp3','.dll', '.exe', '.pdb', '.so', '.a', '.o', '.class', '.jar', '.pyc', '.wasm','.lock', '.log', '.cache', '.tmp', '.swp','.json', '.md', '.txt', '.csv', '.db', '.sqlite', '.env', '.ini', '.yml', '.yaml','.html', '.xml','.targets', '.props', '.csproj', '.sln']
    ignorar_pastas = ['node_modules', 'bower_components', 'vendor','.git', '.github', '.vscode', '.idea', '.vs', 'dist', 'build', 'out', '.next', '.turbo', '.parcel-cache','__pycache__', 'venv', '.mypy_cache', 'bin', 'obj', '__tests__', 'tests', 'test', 'examples','coverage', '.coverage', 'reports']

    arquivos = [
        f for f in projeto_path.rglob("*")
        if f.is_file()
        and f.suffix.lower() not in ignorar_ext
        and not any(pasta in f.parts for pasta in ignorar_pastas)
    ]

    print(f"\n🔄 Processando {len(arquivos)} arquivos...")
    estrutura = construir_arvore(arquivos, projeto_path)

    descricoes = {}
    if Path("descricoes.json").exists():
        with open("descricoes.json", encoding="utf-8") as f:
            descricoes = json.load(f)

    with tqdm(total=len(arquivos), desc="Gerando documentação") as barra:
        conteudo_html = gerar_html_pasta(estrutura, projeto_path, descricoes, arquivos, projeto_path, barra)

    #----------------------------------Gerar HTML final
    template = Path("template.html").read_text(encoding="utf-8")
    with open("output/documentacao.html", "w", encoding="utf-8") as f:
        f.write(template.replace("{{CONTEUDO}}", conteudo_html))

    print("\n✅ Documentação gerada em: output/documentacao.html")

if __name__ == "__main__":
    main() 