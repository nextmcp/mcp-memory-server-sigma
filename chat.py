#!/usr/bin/env python3
"""
chat.py - Simple Interactive Chat Client for LiteLLM Proxy

A lightweight CLI tool to chat with AI via LiteLLM proxy.

Usage:
    uv run chat.py <api-key> [environment] [model]
    
Examples:
    uv run chat.py sk-xxx
    uv run chat.py sk-xxx staging gpt-4o-mini
    uv run chat.py sk-xxx production gpt-4o
"""

# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests",
#     "rich",
# ]
# ///

import sys
import requests
from typing import List, Dict, Optional
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()


class ChatClient:
    """Simple chat client for LiteLLM proxy"""
    
    ENVIRONMENTS = {
        'staging': 'https://api.staging.example.com',
        'dev': 'https://api.dev.example.com',
        'production': 'https://api.production.example.com',
    }
    
    # gpt-4o-mini
    def __init__(self, api_key: str, environment: str = 'staging', model: str = 'claude-sonnet-4-5'):
        self.api_key = api_key
        self.environment = environment
        self.model = model
        self.base_url = self.ENVIRONMENTS.get(environment)
        
        if not self.base_url:
            raise ValueError(f"Invalid environment. Use: {', '.join(self.ENVIRONMENTS.keys())}")
        
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        self.history: List[Dict[str, str]] = []
    
    def send_message(self, message: str) -> Optional[str]:
        """Send a message and get response"""
        self.history.append({'role': 'user', 'content': message})
        
        try:
            response = requests.post(
                f'{self.base_url}/v1/chat/completions',
                headers=self.headers,
                json={
                    'model': self.model,
                    'messages': self.history,
                    'max_tokens': 2000,
                    'temperature': 0.7
                },
                timeout=60
            )
            
            if response.status_code == 200:
                reply = response.json()['choices'][0]['message']['content']
                self.history.append({'role': 'assistant', 'content': reply})
                return reply
            else:
                console.print(f"[red]Error {response.status_code}:[/red] {response.text}")
                return None
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            return None
    
    def clear_history(self):
        """Clear conversation history"""
        self.history = []


def print_welcome(client: ChatClient):
    """Print welcome banner"""
    console.print(Panel.fit(
        f"[bold cyan]💬 AI Chat[/bold cyan]\n\n"
        f"Environment: [yellow]{client.environment}[/yellow]\n"
        f"Model: [green]{client.model}[/green]\n\n"
        f"[dim]Type your message or use:[/dim]\n"
        f"  /clear - Clear history\n"
        f"  /quit  - Exit",
        border_style="cyan"
    ))


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        console.print("[red]Usage:[/red] uv run chat.py <api-key> [environment] [model]")
        console.print("\n[bold]Examples:[/bold]")
        console.print("  uv run chat.py sk-xxx")
        console.print("  uv run chat.py sk-xxx staging gpt-4o-mini")
        sys.exit(1)
    
    api_key = sys.argv[1]
    environment = sys.argv[2] if len(sys.argv) > 2 else 'staging'
    model = sys.argv[3] if len(sys.argv) > 3 else 'gpt-4o-mini'
    
    try:
        client = ChatClient(api_key, environment, model)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    
    print_welcome(client)
    console.print()
    
    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")
            
            if not user_input.strip():
                continue
            
            # Handle commands
            if user_input.lower() in ['/quit', '/exit', '/q']:
                console.print("\n[yellow]Goodbye! 👋[/yellow]")
                break
            
            if user_input.lower() in ['/clear', '/c']:
                client.clear_history()
                console.print("[green]✓ History cleared[/green]")
                continue
            
            if user_input.lower() in ['/help', '/h']:
                console.print("\n[bold]Commands:[/bold]")
                console.print("  /clear  - Clear conversation history")
                console.print("  /switch - Switch to a different model")
                console.print("  /quit   - Exit chat")
                console.print("  /help   - Show this help")
                continue
            
            if user_input.lower().startswith('/switch'):
                parts = user_input.split(maxsplit=1)
                if len(parts) > 1:
                    new_model = parts[1].strip()
                    client.model = new_model
                    console.print(f"[green]✓ Switched to {new_model}[/green]")
                else:
                    current = client.model
                    new_model = Prompt.ask(
                        "\n[bold]Enter model name[/bold]",
                        default=current
                    )
                    if new_model and new_model != current:
                        client.model = new_model
                        console.print(f"[green]✓ Switched to {new_model}[/green]")
                continue
            
            # Send message
            console.print("\n[dim]Thinking...[/dim]")
            response = client.send_message(user_input)
            
            if response:
                console.print(f"\n[bold green]AI[/bold green]")
                console.print(Markdown(response))
        
        except KeyboardInterrupt:
            console.print("\n\n[yellow]Interrupted. Type /quit to exit.[/yellow]")
        except EOFError:
            console.print("\n\n[yellow]Goodbye! 👋[/yellow]")
            break


if __name__ == '__main__':
    main()
