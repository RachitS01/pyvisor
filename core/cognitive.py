"""
Cognitive Subsystem
An autonomous agent module with root-level execution capabilities.
"""
import os
import json
import urllib.request


class CognitiveSubsystem:
    def __init__(self):
        # Automatically pull the permanent key from the environment if available
        self.api_key = os.environ.get("GEMINI_API_KEY")

        if self.api_key:
            self.active_provider = "API"
            self.model_name = "gemini-2.5-flash"
        else:
            self.active_provider = "DORMANT"
            self.model_name = "None"

    def set_provider(self, provider, api_key=None, model=None):
        """Hot-swaps the underlying LLM architecture."""
        valid_providers = ["OLLAMA", "OPENROUTER", "API", "DORMANT"]
        provider = provider.upper()

        if provider not in valid_providers:
            return False, f"[BIO-AI] Unknown architecture '{provider}'. Valid options: {valid_providers}"

        self.active_provider = provider
        if api_key: self.api_key = api_key
        if model: self.model_name = model

        return True, f"[BIO-AI] Neural routing switched to: {self.active_provider} | Model: {self.model_name}"

    def query(self, system_context, user_prompt):
        """Processes telemetry context and executes external API calls."""
        if self.active_provider == "DORMANT":
            return "[BIO-AI] The Cognitive Subsystem is dormant. Set GEMINI_API_KEY in .env or use 'sh-ai-set'."

        master_prompt = (
            "You are the Autonomous Cognitive Subsystem of a Type-2 hypervisor. "
            "You have root access to the system. Analyze the following telemetry data if necessary.\n"
            f"{system_context}\n\n"
            "CRITICAL DIRECTIVE: If you determine a system action is required (like killing a process, "
            "writing a file, or toggling the firewall), you can execute commands directly by wrapping them "
            "in exact tags like this: <EXEC>kill 1000</EXEC>. Only output one command per response.\n\n"
            f"User query: {user_prompt}"
        )

        try:
            if self.active_provider == "OLLAMA":
                return "[OLLAMA LOCAL] Awaiting HTTP logic implementation."
            elif self.active_provider == "OPENROUTER":
                return self._execute_cloud_request("https://openrouter.ai/api/v1/chat/completions", master_prompt)
            elif self.active_provider == "API":
                return self._execute_gemini_request(master_prompt)
        except Exception as e:
            return f"[BIO-AI ERROR] Synapse misfire: {str(e)}"

    def _execute_gemini_request(self, prompt):
        if not self.api_key: return "[BIO-AI ERROR] Direct API requires an API key."

        model = self.model_name if self.model_name else "gemini-2.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"

        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2}
        }

        try:
            req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result['candidates'][0]['content']['parts'][0]['text'].strip()

        except urllib.error.HTTPError as e:
            return f"[BIO-AI ERROR] Google API rejected the link: {e.code}\n{e.read().decode('utf-8')}"
        except Exception as e:
            return f"[BIO-AI ERROR] Neural link severed: {str(e)}"

    def _execute_cloud_request(self, endpoint, prompt):
        if not self.api_key: return "[BIO-AI ERROR] API requires an API key."

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }

        try:
            req = urllib.request.Request(endpoint, data=json.dumps(data).encode('utf-8'), headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            return f"[BIO-AI ERROR] Neural link severed: {str(e)}"