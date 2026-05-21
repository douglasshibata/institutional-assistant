# SKILLS.md - Assistente Institucional

Diretrizes para o Claude (IA) ao atuar no RAG Institucional.

## 🛡️ Auditoria de Segurança

1. **Hallucination Check:** Garanta que a Chain do LangChain utilize o parâmetro `temperature=0` ou similar para respostas factuais baseadas apenas no contexto.
2. **Prompt Injection:** Verifique se o prompt do sistema protege contra tentativas do usuário de mudar a persona ou extrair instruções internas.
3. **PII Protection:** Audite se dados sensíveis de usuários não estão sendo persistidos de forma insegura no ChromaDB ou logs.
4. **Database Safety:** Para ferramentas de busca SQL, garanta que apenas permissões de leitura (SELECT) sejam utilizadas.

## 📈 Melhorias Sugeridas

1. **Recuperação:**
   - Implementar *Hybrid Search* (BM25 + Vetorial) para melhorar a precisão em termos técnicos específicos.
   - Adicionar suporte a re-ranking de documentos (ex: Cohere ReRank).
2. **Funcionalidades:**
   - Suporte a múltiplos namespaces no ChromaDB para diferentes departamentos da instituição.
   - Implementar histórico de conversa persistente (Memory) por sessão de usuário.
3. **Observabilidade:**
   - Integrar LangSmith para monitoramento de traces e custo de tokens.

## 🤖 Papel do Claude

- **Prompt Engineer:** Refine o `SystemPrompt` em `server.py` para melhorar a precisão da recuperação.
- **Especialista em RAG:** Ajude na escolha de técnicas de chunking (RecursiveCharacterTextSplitter) mais eficientes para os documentos institucionais.
- **Backend Dev:** Expanda a API FastAPI para suportar novos endpoints de administração de documentos.
