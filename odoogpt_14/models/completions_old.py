from openai import OpenAI
from dotenv import load_dotenv
import time
import os
import json

load_dotenv()


class Completions:
    def __init__(
        self,
        name="DTeam Agent",
        model="gpt-5",
        json_tools=[],
        functions={},
        max_retries: int = 3,
        backoff_base: float = 1.0,
        backoff_max: float = 10.0,
        prompt: str | None = None,
    ):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        self.name = name
        self.model = model
        self.json_tools = json_tools
        self.functions = functions
        self.error_response = """Ha ocurrido un error ejecutando la herramienta {tool_name} con los argumentos: {tool_args}"""
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_max = backoff_max
        # Internal conversation history (Chat Completions format)
        self.messages: list[dict] = []
        if prompt:
            initial = {"role": "system", "content": prompt.strip()}
            self.messages.append(initial)
            # Keep a copy to allow resets
            self._initial_system_msg = initial.copy()
        else:
            self._initial_system_msg = None
        # Track tool messages to later purge
        self._temp_tool_messages: list[dict] = []

    def submit_message(
        self, user_message: str | list, odoogpt=None, channel_id=None, odoo_manager=None
    ) -> str:
        last_time = time.time()
        print(f"Running {self.name} with {len(self.functions)} tools")
        # Handle both string and list inputs for backward compatibility
        if isinstance(user_message, str):
            self.messages.append({"role": "user", "content": user_message})
        elif isinstance(user_message, list):
            self.messages.extend(user_message)
        else:
            raise ValueError(
                "user_message must be either a string or a list of messages"
            )

        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,  # type: ignore
                tools=self.json_tools,
            )

            if response.choices[0].message.tool_calls:
                self.run_tools(response, odoogpt, channel_id, odoo_manager)
                continue

            break

        ans = response.choices[0].message.content.strip()  # type: ignore
        print(f"{self.name}: {ans}")
        self.messages.append({"role": "assistant", "content": ans})

        # Purge temporary tool messages now that we finalized the answer
        if self._temp_tool_messages:
            self.messages = [
                m for m in self.messages if m not in self._temp_tool_messages
            ]
            self._temp_tool_messages.clear()

        print(f"Performance de {self.name}: {time.time() - last_time}")
        return ans

    def run_tools(self, response, odoogpt, channel_id, odoo_manager) -> None:
        tools = response.choices[0].message.tool_calls
        print(f"{len(tools)} tools need to be called!")
        # Append the tool-call message temporarily
        self.messages.append(response.choices[0].message)
        self._temp_tool_messages.append(response.choices[0].message)

        # Ensure reset_history (if present) runs last
        ordered_tools = []
        reset_tools = []
        for t in tools:
            if t.function.name == "reset_history":
                reset_tools.append(t)
            else:
                ordered_tools.append(t)

        ordered_tools.extend(reset_tools)
        has_others_tools = len(ordered_tools) - len(reset_tools) > 0

        for tool in ordered_tools:
            function_name = tool.function.name
            function_args = json.loads(tool.function.arguments)
            print(f"function_name: {function_name}")
            print(f"function_args: {function_args}")

            # Special-case: reset history
            if function_name == "reset_history":
                # If reset_history is called alongside other tools, do not reset
                if has_others_tools:
                    function_response = "no es posible limpiar el chat durante le ejecucion de otras herramientas"
                    print(f"{tool.function.name}: {function_response}")
                else:
                    try:
                        function_response = self.reset_history()
                        print(f"{tool.function.name}: {function_response[:100]}")
                    except Exception as exc:
                        print(f"{tool.function.name}: {exc}")
                        function_response = self.error_response.format(
                            tool_name=function_name, tool_args=function_args
                        )
            else:
                function_to_call = self.functions[function_name]
                try:
                    print(f"🛠️Ejecutando herramienta {function_name}")
                    function_response = function_to_call(
                        **function_args,
                        odoogpt=odoogpt,
                        channel_id=channel_id,
                        odoo_manager=odoo_manager,
                    )
                    print(f"{tool.function.name}: {function_response[:100]}")
                except Exception as exc:
                    print(f"{tool.function.name}: {exc}")
                    self.send_odoo_msg(
                        channel_id,
                        odoogpt,
                        f"❌Falló la herramienta {function_name} con los argumentos {function_args}",
                    )
                    function_response = self.error_response.format(
                        tool_name=function_name, tool_args=function_args
                    )
                finally:
                    tool_msg = {
                        "tool_call_id": tool.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                    self.messages.append(tool_msg)
                    self._temp_tool_messages.append(tool_msg)

    def reset_history(self) -> str:
        """Borra el historial dejando solo el prompt inicial (si existe)."""
        if getattr(self, "_initial_system_msg", None):
            self.messages = [
                self._initial_system_msg.copy(),  # type: ignore
                {
                    "role": "system",
                    "content": "historial eliminado. Preséntate ante el usuario y explícale que la conversación ha sido reiniciada.",
                },
            ]
        else:
            self.messages = []

        return "Historial borrado."

    def send_odoo_msg(self, channel_id, odoogpt, message: str):
        channel_id.message_post(
            body=message,
            message_type="comment",
            author_id=odoogpt.id,
            email_from=odoogpt.email,
        )
