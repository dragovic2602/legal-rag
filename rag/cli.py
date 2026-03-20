#!/usr/bin/env python3
# DEPRECATED: No longer the primary interface.
# Use Claude Code with the legal-rag MCP server (mcp_server.py + .mcp.json) instead.
# Kept for reference.
"""
Command Line Interface for Docling RAG Agent.

Enhanced CLI with colors, formatting, and improved user experience.
"""

import asyncio
import argparse
import logging
import os
import sys
from typing import List, Dict, Any
from datetime import datetime

from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext

from storage.db_utils import initialize_database, close_database, db_pool
from retrieval.search import search_knowledge_base
from generation.prompts import SYSTEM_PROMPT

# Load environment variables
load_dotenv(".env")

logger = logging.getLogger(__name__)

# ANSI color codes for better formatting
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


# Default agent — uses canonical search and shared system prompt
agent = Agent(
    'openai:gpt-4o-mini',
    system_prompt=SYSTEM_PROMPT,
    tools=[search_knowledge_base]
)


class RAGAgentCLI:
    """Enhanced CLI for interacting with the RAG Agent."""

    def __init__(self):
        """Initialize CLI."""
        self.message_history = []

    def print_banner(self):
        """Print welcome banner."""
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 60}")
        print("🤖 Docling RAG Knowledge Assistant")
        print("=" * 60)
        print(f"{Colors.WHITE}AI-powered document search with streaming responses")
        print(f"Type 'exit', 'quit', or Ctrl+C to exit")
        print(f"Type 'help' for commands")
        print("=" * 60 + f"{Colors.END}\n")

    def print_help(self):
        """Print help information."""
        help_text = f"""
{Colors.BOLD}Available Commands:{Colors.END}
  {Colors.GREEN}help{Colors.END}           - Show this help message
  {Colors.GREEN}clear{Colors.END}          - Clear conversation history
  {Colors.GREEN}stats{Colors.END}          - Show conversation statistics
  {Colors.GREEN}exit/quit{Colors.END}      - Exit the CLI

{Colors.BOLD}Usage:{Colors.END}
  Simply type your question and press Enter to chat with the agent.
  The agent will search the knowledge base and provide answers with source citations.

{Colors.BOLD}Features:{Colors.END}
  • Semantic search through embedded documents
  • Streaming responses in real-time
  • Conversation history maintained across turns
  • Source citations for all information

{Colors.BOLD}Examples:{Colors.END}
  - "What are the main topics in the knowledge base?"
  - "Tell me about [specific topic from your documents]"
  - "Summarize information about [subject]"
"""
        print(help_text)

    def print_stats(self):
        """Print conversation statistics."""
        message_count = len(self.message_history)
        print(f"\n{Colors.MAGENTA}{Colors.BOLD}📊 Session Statistics:{Colors.END}")
        print(f"  Messages in history: {message_count}")
        print(f"  Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Colors.BLUE}{'─' * 60}{Colors.END}\n")

    async def check_database(self) -> bool:
        """Check database connection."""
        try:
            await initialize_database()
            async with db_pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                if result == 1:
                    print(f"{Colors.GREEN}✓ Database connection successful{Colors.END}")
                    doc_count = await conn.fetchval("SELECT COUNT(*) FROM documents")
                    chunk_count = await conn.fetchval("SELECT COUNT(*) FROM chunks")
                    print(f"{Colors.GREEN}✓ Knowledge base ready: {doc_count} documents, {chunk_count} chunks{Colors.END}")
                    return True
            return False
        except Exception as e:
            print(f"{Colors.RED}✗ Database connection failed: {e}{Colors.END}")
            return False

    def extract_tool_calls(self, messages: List[Any]) -> List[Dict[str, Any]]:
        """Extract tool call information from messages."""
        from pydantic_ai.messages import ModelResponse, ToolCallPart

        tools_used = []
        for msg in messages:
            if isinstance(msg, ModelResponse):
                for part in msg.parts:
                    if isinstance(part, ToolCallPart):
                        tools_used.append({
                            'tool_name': part.tool_name,
                            'args': part.args,
                            'tool_call_id': part.tool_call_id
                        })
        return tools_used

    def format_tools_used(self, tools: List[Dict[str, Any]]) -> str:
        """Format tools used for display."""
        if not tools:
            return ""

        formatted = f"\n{Colors.MAGENTA}{Colors.BOLD}🛠 Tools Used:{Colors.END}\n"
        for i, tool in enumerate(tools, 1):
            tool_name = tool.get('tool_name', 'unknown')
            args = tool.get('args', {})

            formatted += f"  {Colors.CYAN}{i}. {tool_name}{Colors.END}"

            if args and isinstance(args, dict):
                key_args = []
                if 'query' in args:
                    query_preview = str(args['query'])[:50] + '...' if len(str(args['query'])) > 50 else str(args['query'])
                    key_args.append(f"query='{query_preview}'")
                if 'limit' in args:
                    key_args.append(f"limit={args['limit']}")
                if key_args:
                    formatted += f" ({', '.join(key_args)})"

            formatted += "\n"

        return formatted

    async def stream_chat(self, message: str) -> None:
        """Send message to agent and display streaming response."""
        try:
            print(f"\n{Colors.BOLD}🤖 Assistant:{Colors.END} ", end="", flush=True)

            async with agent.run_stream(
                message,
                message_history=self.message_history
            ) as result:
                async for text in result.stream_text(delta=True):
                    print(text, end="", flush=True)

                print()

                self.message_history = result.all_messages()

                new_messages = result.new_messages()
                tools_used = self.extract_tool_calls(new_messages)
                if tools_used:
                    print(self.format_tools_used(tools_used))

            print(f"{Colors.BLUE}{'─' * 60}{Colors.END}")

        except Exception as e:
            print(f"\n{Colors.RED}✗ Error: {e}{Colors.END}")

    async def run(self):
        """Run the CLI main loop."""
        self.print_banner()

        if not await self.check_database():
            print(f"{Colors.RED}Cannot connect to database. Please check your DATABASE_URL.{Colors.END}")
            return

        print(f"{Colors.GREEN}Ready to chat! Ask me anything about the knowledge base.{Colors.END}\n")

        try:
            while True:
                try:
                    user_input = input(f"{Colors.BOLD}You: {Colors.END}").strip()

                    if not user_input:
                        continue

                    if user_input.lower() in ['exit', 'quit', 'bye']:
                        print(f"{Colors.CYAN}👋 Thank you for using the knowledge assistant. Goodbye!{Colors.END}")
                        break
                    elif user_input.lower() == 'help':
                        self.print_help()
                        continue
                    elif user_input.lower() == 'clear':
                        self.message_history = []
                        print(f"{Colors.GREEN}✓ Conversation history cleared{Colors.END}")
                        continue
                    elif user_input.lower() == 'stats':
                        self.print_stats()
                        continue

                    await self.stream_chat(user_input)

                except KeyboardInterrupt:
                    print(f"\n{Colors.CYAN}👋 Goodbye!{Colors.END}")
                    break
                except EOFError:
                    print(f"\n{Colors.CYAN}👋 Goodbye!{Colors.END}")
                    break

        except Exception as e:
            print(f"{Colors.RED}✗ CLI error: {e}{Colors.END}")
        finally:
            await close_database()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Enhanced CLI for Docling RAG Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')
    parser.add_argument('--model', default=None,
                        help='Override LLM model (e.g., gpt-4o)')

    args = parser.parse_args()

    if args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.WARNING

    logging.basicConfig(level=log_level,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if not args.verbose:
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('httpcore').setLevel(logging.WARNING)
        logging.getLogger('openai').setLevel(logging.WARNING)

    if args.model:
        global agent
        agent = Agent(
            f'openai:{args.model}',
            system_prompt=SYSTEM_PROMPT,
            tools=[search_knowledge_base]
        )

    if not os.getenv("DATABASE_URL"):
        print(f"{Colors.RED}✗ DATABASE_URL environment variable is required{Colors.END}")
        sys.exit(1)

    if not os.getenv("OPENAI_API_KEY"):
        print(f"{Colors.RED}✗ OPENAI_API_KEY environment variable is required{Colors.END}")
        sys.exit(1)

    cli = RAGAgentCLI()

    try:
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        print(f"\n{Colors.CYAN}👋 Goodbye!{Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}✗ CLI startup error: {e}{Colors.END}")
        sys.exit(1)


if __name__ == "__main__":
    main()
