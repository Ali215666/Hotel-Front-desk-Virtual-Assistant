"""
Ollama client for interacting with local LLM models.
"""

import requests
from typing import Optional, AsyncGenerator
import httpx
import asyncio
import json


class OllamaClient:
    """Client for communicating with Ollama API."""
    
    def __init__(self, model_name: str = "hotel-qwen", base_url: str = "http://localhost:11434"):
        """
        Initialize the Ollama client.
        
        Args:
            model_name: Name of the Ollama model to use
            base_url: Base URL for Ollama API
        """
        self.model_name = model_name
        self.base_url = base_url
        self.generate_url = f"{base_url}/api/generate"
    
    def generate(self, prompt: str) -> str:
        """
        Generate a response from the model.
        
        Args:
            prompt: Constructed prompt for the model
            
        Returns:
            str: Assistant text output only
        """
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            response = requests.post(
                self.generate_url,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '').strip()
        
        except requests.Timeout:
            return "Error: Request timed out. Please try again."
        
        except requests.ConnectionError:
            return "Error: Could not connect to Ollama. Ensure Ollama is running on http://localhost:11434"
        
        except requests.HTTPError as e:
            return f"Error: HTTP {e.response.status_code} - {e.response.reason}"
        
        except requests.RequestException as e:
            return f"Error: {str(e)}"
        
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    async def generate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response from the model token-by-token.
        
        Args:
            prompt: Constructed prompt for the model
            
        Yields:
            str: Individual tokens/chunks of the response
        """
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": True
        }
        
        try:
            timeout = httpx.Timeout(120.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream('POST', self.generate_url, json=payload) as response:
                    if response.status_code != 200:
                        yield f"Error: HTTP {response.status_code}"
                        return
                    
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                if 'response' in chunk:
                                    token = chunk['response']
                                    if token:
                                        yield token
                                
                                # Check if this is the final chunk
                                if chunk.get('done', False):
                                    break
                            except json.JSONDecodeError:
                                continue
                            except Exception:
                                continue
        
        except httpx.TimeoutException:
            yield "Error: Request timed out. Please try again."
        
        except httpx.ConnectError:
            yield f"Error: Could not connect to Ollama. Ensure Ollama is running on {self.base_url}"
        
        except httpx.HTTPError as e:
            yield f"Error: HTTP error occurred - {str(e)}"
        
        except Exception as e:
            yield f"Unexpected error: {str(e)}"
