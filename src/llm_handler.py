"""
LLM Handler for Ollama integration
"""
import logging
import requests
import json
from typing import Dict, Optional


class LLMHandler:
    """Handler for Ollama LLM API"""
    
    def __init__(self, config: Dict):
        """Initialize LLM handler with configuration"""
        self.base_url = config['ollama']['base_url']
        self.model = config['ollama']['model']
        self.timeout = config['ollama']['timeout']
        self.temperature = config['ollama']['temperature']
        self.max_tokens = config['ollama']['max_tokens']
        
        logging.info(f"LLM Handler initialized with model: {self.model}")
    
    def check_connection(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logging.info("Successfully connected to Ollama")
                return True
            else:
                logging.error(f"Ollama returned status code: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            logging.error("Cannot connect to Ollama. Is it running?")
            return False
        except Exception as e:
            logging.error(f"Error checking Ollama connection: {str(e)}")
            return False
    
    def list_models(self) -> list:
        """List available models in Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]
                logging.info(f"Available models: {models}")
                return models
            return []
        except Exception as e:
            logging.error(f"Error listing models: {str(e)}")
            return []
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """
        Generate response from LLM
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            Generated text or None if error
        """
        try:
            url = f"{self.base_url}/api/generate"
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            logging.info(f"Sending request to Ollama with model: {self.model}")
            logging.debug(f"Prompt length: {len(prompt)} characters")
            
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '')
                logging.info("Successfully generated response from LLM")
                logging.debug(f"Response length: {len(generated_text)} characters")
                return generated_text
            else:
                logging.error(f"Ollama API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logging.error("Request to Ollama timed out")
            return None
        except requests.exceptions.ConnectionError:
            logging.error("Cannot connect to Ollama. Ensure Ollama is running.")
            return None
        except Exception as e:
            logging.error(f"Error generating response: {str(e)}")
            return None
    
    def chat(self, messages: list) -> Optional[str]:
        """
        Chat-based generation with message history
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            Generated text or None if error
        """
        try:
            url = f"{self.base_url}/api/chat"
            
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            }
            
            logging.info(f"Sending chat request to Ollama")
            
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('message', {}).get('content', '')
                logging.info("Successfully generated chat response")
                return generated_text
            else:
                logging.error(f"Ollama chat API error: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"Error in chat generation: {str(e)}")
            return None
    
    def generate_with_template(self, template: Dict, **kwargs) -> Optional[str]:
        """
        Generate response using a prompt template
        
        Args:
            template: Dict with 'system' and 'user' keys
            **kwargs: Variables to format into the template
            
        Returns:
            Generated text or None if error
        """
        try:
            system_prompt = template.get('system', '')
            user_prompt = template['user'].format(**kwargs)
            
            return self.generate(user_prompt, system_prompt)
            
        except KeyError as e:
            logging.error(f"Missing template variable: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Error generating with template: {str(e)}")
            return None
    
    def stream_generate(self, prompt: str, system_prompt: Optional[str] = None):
        """
        Generate response with streaming (yields chunks)
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Yields:
            Text chunks as they're generated
        """
        try:
            url = f"{self.base_url}/api/generate"
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            logging.info("Starting streaming generation")
            
            response = requests.post(
                url,
                json=payload,
                stream=True,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            chunk = data.get('response', '')
                            if chunk:
                                yield chunk
                        except json.JSONDecodeError:
                            continue
            else:
                logging.error(f"Streaming error: {response.status_code}")
                yield None
                
        except Exception as e:
            logging.error(f"Error in streaming generation: {str(e)}")
            yield None