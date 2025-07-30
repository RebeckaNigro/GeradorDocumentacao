import os
import google.generativeai as genai

def testar_conexao_gemini():
    print("🔌 Testando conexão com a API Gemini...")
    
    # Nunca coloque a chave diretamente no código!
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Erro: Configure a variável de ambiente GEMINI_API_KEY")
        print("👉 Execute no terminal ANTES de rodar o script:")
        print("Windows: $env:GEMINI_API_KEY='sua-chave'")
        print("Linux/Mac: export GEMINI_API_KEY='sua-chave'")
        return False

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemma-3-27b-it')
        resposta = model.generate_content("Responda 'OK'")
        
        print("✅ Conexão bem-sucedida! Resposta:", resposta.text)
        return True
        
    except Exception as e:
        print(f"❌ Falha na conexão: {type(e).__name__} - {str(e)}")
        return False

if __name__ == "__main__":
    testar_conexao_gemini()