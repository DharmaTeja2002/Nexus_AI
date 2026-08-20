import openai
from src.core.config import settings

class LLMClient:
    def __init__(self):
        # We no longer hardcode the client on startup. We will instantiate it dynamically per request!
        pass

    async def generate_rag_response(self, question: str, context_chunks: list, provider: str = "groq") -> str:
        provider = provider.lower()
        
        # --- DYNAMIC ROUTER ---
        if provider == "gemini":
            client = openai.AsyncOpenAI(
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                api_key=settings.GEMINI_API_KEY or "missing_key"
            )
            model_name = "gemini-1.5-flash"
        else: # Default to Groq
            client = openai.AsyncOpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=settings.GROQ_API_KEY or "missing_key"
            )
            model_name = "llama3-8b-8192" # Fixed 404 error model name!
        if not context_chunks:
            # Condition 1: No documents uploaded or found
            system_prompt = (
                "You are Nexus AI, a brilliant and helpful corporate intelligence assistant. "
                "The user asked a question, but there are no uploaded documents matching this topic. "
                "You must answer their question using your general knowledge of the world. "
                "IMPORTANT: At the very end of your response, you MUST append this exact note on a new line: "
                "\n\n*(Note: This was answered generally from outside world knowledge since no specific documents were found).* "
            )
            user_prompt = f"Question: {question}"
        else:
            # Condition 2: Documents were uploaded and found
            context_str = "\n\n---\n\n".join([c['content'] for c in context_chunks])
            system_prompt = (
                "You are Nexus AI, a smart corporate intelligence assistant. "
                "You have been provided with context snippets extracted from the user's uploaded files. "
                "Answer the user's question based ONLY on these documents, but explain it in a generalized, conversational, and easy-to-understand way. "
                "Use bullet points and paragraphs to format your response nicely."
            )
            user_prompt = f"Context:\n{context_str}\n\nQuestion: {question}"
        
        try:
            response = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3 # Slightly higher temperature for better conversational flow
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error connecting to LLM ({provider}): {str(e)}"
