import asyncio
import json
import os
import pathlib
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Any

# Add project root to sys.path for direct execution
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI

from .enumerations import EffortType, MessageType, ModelType, VerbosityType
from .prompt import JSON_TOOLS, SYSTEM_PROMPT
from .tools import tools_func

load_dotenv(".env")


class SetMessagesError(Exception):
    pass


class ChatMemory:
    def __init__(self, prompt=SYSTEM_PROMPT):
        self.__ai_output: dict[str, Any] = {}
        self.__messages: dict[str, list[dict]] = {}
        self.__tool_msgs: dict[str, list[dict]] = {}
        self.init_msg = {
            "role": MessageType.DEVELOPER.value,
            "content": prompt,
        }
        self.__last_time: float

    def get_ai_output(self, channel_id: int):
        if channel_id not in self.__ai_output:
            return []

        return self.__ai_output[channel_id].output

    def get_tool_msgs(self, channel_id: int):
        if channel_id not in self.__tool_msgs:
            return []
        return self.__tool_msgs[channel_id]

    def get_messages(self, channel_id: int):
        if channel_id not in self.__messages:
            print(f"{channel_id} not found in memory")
            self.init_chat(channel_id)

        return self.__messages[channel_id]

    def reduce_context(self, channel_id: int):
        if len(self.__messages[channel_id]) < 20:
            return

        new_messages = [self.__messages[channel_id][0]]
        last_idx = len(self.__messages) - 1

        for idx, msg in enumerate(self.__messages[channel_id][10:], start=10):
            if msg["role"] == MessageType.USER.value:
                new_messages += self.__messages[channel_id][idx:last_idx]

        self.__messages[channel_id] = new_messages

    def get_last_time(self):
        return self.__last_time

    def _set_ai_output(self, ai_output, channel_id: int):
        self.__ai_output[channel_id] = ai_output

        if channel_id not in self.__messages:
            print(f"{channel_id} not found in memory")
            return False

        if channel_id not in self.__tool_msgs:
            self.__tool_msgs[channel_id] = ai_output.output.copy()
        else:
            self.__tool_msgs[channel_id] += ai_output.output.copy()

        self.__messages[channel_id] += ai_output.output.copy()

    def _clean_tool_msgs(self, channel_id: int):
        if channel_id not in self.__tool_msgs:
            print(f"{channel_id} not have tool messages")

        self.__tool_msgs[channel_id] = []

    def has_chat(self, channel_id: int) -> bool:
        return channel_id in self.__messages and len(self.__messages[channel_id]) > 0

    def delete_chat(self, channel_id: int) -> None:
        if channel_id in self.__messages:
            del self.__messages[channel_id]
        if channel_id in self.__tool_msgs:
            del self.__tool_msgs[channel_id]
        if channel_id in self.__ai_output:
            del self.__ai_output[channel_id]

    def init_chat(self, channel_id: int):
        self.set_messages([self.init_msg], channel_id)
        print(f"New chat for {channel_id}")

    def add_msg(self, message: str, role: str, channel_id: int):
        if channel_id not in self.__messages:
            self.init_chat(channel_id)

        if MessageType.has_value(role):
            self.__messages[channel_id].append(
                {
                    "role": role,
                    "content": message,
                }
            )
            print(f"New message from {role} added to chat of {channel_id}")
            return True

        print(f"Invalid role {role}, must be one of: {MessageType.list_values()}")
        return False

    def set_messages(self, messages: list[dict[str, str]], channel_id: int):
        if not isinstance(messages, list):
            raise SetMessagesError(f"messages must be a list, not {type(messages)}")

        for id, msg in enumerate(messages):
            if not MessageType.has_value(msg["role"]):
                raise SetMessagesError(
                    f"Invalid role {msg['role']} in the {id + 1} message, must be one of: {MessageType.list_values()}"
                )

        self.__messages[channel_id] = messages

    def _get_ai_msg(self, channel_id: int):
        ai_output = self.get_ai_output(channel_id)

        for item in ai_output:  # type: ignore
            try:
                if item.type == "message":
                    ans = item.content[0].text  # type: ignore
                    return ans

            except Exception as exc:
                print(f"Error retrieving AI message: {exc}")
                print(item)

        return "No Answer"

    def _purge_tool_msgs(self, channel_id: int):
        tool_msgs = self.get_tool_msgs(channel_id)
        messages = self.get_messages(channel_id)
        if tool_msgs:
            clean_messages = [m for m in messages if m not in tool_msgs]
            try:
                self.set_messages(clean_messages, channel_id)
            except SetMessagesError as exc:
                print(f"Error purging tool messages: {exc}")
            finally:
                self._clean_tool_msgs(channel_id)

    def _set_tool_output(self, call_id, function_out, channel_id: int):
        # Store as ephemeral tool output; do not persist in history
        if channel_id not in self.__messages:
            print(f"{channel_id} not found in memory")
            return False

        msg = {
            "type": "function_call_output",
            "call_id": call_id,
            "output": str(function_out),
        }

        if channel_id not in self.__tool_msgs:
            self.__tool_msgs[channel_id] = [msg]
        else:
            self.__tool_msgs[channel_id].append(msg)

        self.__messages[channel_id].append(msg)


class AIClient:
    def __init__(
        self,
        api_key: str,
    ):
        self.__client = OpenAI(api_key=api_key)
        self.__async_client = AsyncOpenAI(api_key=api_key)

    async def _async_gen_ai_output(self, params: dict):
        ai_output = await self.__async_client.responses.create(**params)
        return ai_output

    def _gen_ai_output(self, params: dict):
        return self.__client.responses.create(**params)


class ToolRunner:
    def __init__(
        self,
        error_msg="Ha ocurrido un error inesperado",
    ):
        self.ERROR_MSG = error_msg

    def _run_functions(
        self,
        functions_called,
        channel_id: int,
        channel_obj,
        chat_memory: ChatMemory,
        odoo_manager,
        odoogpt,
    ) -> None:
        print(f"{len(functions_called)} functions need to be called!")

        with ThreadPoolExecutor() as executor:
            futures = []
            for tool in functions_called:
                function_name = tool.name
                print(f"function_name: {function_name}")

                function_to_call = tools_func[function_name]
                extra_args = json.loads(tool.arguments)
                function_args = {
                    **extra_args,
                    "odoogpt": odoogpt,
                    "channel_id": channel_obj,
                    "odoo_manager": odoo_manager,
                }
                if function_name == "create_lead":
                    function_args["chat"] = chat_memory.get_messages(channel_id)

                fa_str = str(function_args)
                print(
                    f"function_args: {fa_str[:100]}{'...' if len(fa_str) > 100 else ''}"
                )
                futures.append(executor.submit(function_to_call, **function_args))

            self.run_futures(futures, functions_called, channel_id, chat_memory)

    def _run_custom_tools(
        self,
        custom_tools_called,
        channel_id: int,
        channel_obj,
        chat_memory: ChatMemory,
        odoo_manager,
        odoogpt,
    ) -> None:
        print(f"{len(custom_tools_called)} custom tools need to be called!")

        with ThreadPoolExecutor() as executor:
            futures = []
            for tool in custom_tools_called:
                print(f"Custom tool name: {tool.name}")
                function_to_call = tools_func[tool.name]
                print(f"Custom tool input: {tool.input}")

                function_args = {
                    "tool_input": tool.input,
                    "odoogpt": odoogpt,
                    "channel_id": channel_obj,
                    "odoo_manager": odoo_manager,
                }
                if channel_id:
                    function_args["user_number"] = channel_id

                futures.append(executor.submit(function_to_call, **function_args))

            self.run_futures(futures, custom_tools_called, channel_id, chat_memory)

    def run_futures(
        self, futures, tools_called, channel_id: int, chat_memory: ChatMemory
    ):
        for future, tool in zip(futures, tools_called):
            try:
                function_out = future.result()
                print(f"{tool.name}: {function_out[:100]}")  # type: ignore
            except Exception as exc:
                print(f"{tool.name}: {exc}")
                function_out = self.ERROR_MSG

            chat_memory._set_tool_output(tool.call_id, function_out, channel_id)

    async def _async_run_functions(
        self,
        functions_called,
        channel_id: int,
        channel_obj,
        chat_memory: ChatMemory,
        odoo_manager,
        odoogpt,
    ) -> None:
        print(f"{len(functions_called)} function need to be called!")
        tasks = []
        for tool in functions_called:
            function_name = tool.name
            print(f"function_name: {function_name}")
            function_to_call = tools_func[function_name]  # type: ignore

            extra_args = json.loads(tool.arguments)
            function_args = {
                **extra_args,
                "odoogpt": odoogpt,
                "channel_id": channel_obj,
                "odoo_manager": odoo_manager,
            }
            if function_name == "create_lead":
                function_args["chat"] = chat_memory.get_messages(channel_id)

            fa_str = str(function_args)
            print(f"function_args: {fa_str[:100]}{'...' if len(fa_str) > 100 else ''}")
            tasks.append(function_to_call(**function_args))

        await self.run_coroutines(functions_called, tasks, channel_id, chat_memory)

    async def _async_run_custom_tools(  # type: ignore
        self,
        custom_tools_called,
        channel_id: int,
        channel_obj,
        chat_memory: ChatMemory,
        odoo_manager,
        odoogpt,
    ) -> None:
        print(f"{len(custom_tools_called)} custom tools need to be called!")

        tasks = []
        for tool in custom_tools_called:
            print(f"function_name: {tool.name}")
            function_to_call = tools_func[tool.name]  # type: ignore

            print(f"Input tool: {tool.input}")

            function_args = {
                "tool_input": tool.input,
                "odoogpt": odoogpt,
                "channel_id": channel_obj,
                "odoo_manager": odoo_manager,
            }
            if channel_id:
                function_args["user_number"] = channel_id

            tasks.append(function_to_call(**function_args))

        await self.run_coroutines(custom_tools_called, tasks, channel_id, chat_memory)

    async def run_coroutines(
        self, tools_called, tasks, channel_id: int, chat_memory: ChatMemory
    ):
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for tool, function_out in zip(tools_called, results):
            if isinstance(function_out, Exception):
                print(f"{tool.name}: {function_out}")
                function_out = self.ERROR_MSG  # type: ignore
            else:
                print(f"{tool.name}: {function_out[:100]}")  # type: ignore

            chat_memory._set_tool_output(tool.call_id, function_out, channel_id)


class Agent:
    def __init__(
        self,
        name="Odoo Agent",
        model=ModelType.GPT_5.value,
        prompt=SYSTEM_PROMPT,
    ):
        self.name = name
        self.model = model
        self.chat_memory = ChatMemory(prompt=prompt)
        self._ai_client = AIClient(os.getenv("OPENAI_API_KEY"))  # type: ignore
        self._tool_runner = ToolRunner()

    def process_msg(
        self,
        message: str,
        channel_id: int,
        channel_obj,
        odoo_manager=None,
        odoogpt=None,
    ) -> str | None:
        print(f"Running {self.model} with {len(JSON_TOOLS)} tools")

        self.chat_memory.add_msg(message, MessageType.USER.value, channel_id)

        while True:
            params = {
                "model": self.model,  # type: ignore
                "input": self.chat_memory.get_messages(channel_id),  # type: ignore
                "tools": JSON_TOOLS,  # type: ignore
            }
            if self.model == ModelType.GPT_5.value:  # type: ignore
                params["text"] = {"verbosity": VerbosityType.LOW.value}
                params["reasoning"] = {"effort": EffortType.LOW.value}

            ai_output = self._ai_client._gen_ai_output(params)
            self.chat_memory._set_ai_output(ai_output, channel_id)

            functions_called = [
                item
                for item in ai_output.output  # type: ignore
                if item.type == MessageType.FUNCTION_CALL.value
            ]

            custom_tools_called = [
                item
                for item in ai_output.output  # type: ignore
                if item.type == MessageType.CUSTOM_TOOL_CALL.value
            ]

            if not functions_called and not custom_tools_called:
                break

            if functions_called:
                self._tool_runner._run_functions(
                    functions_called,
                    channel_id,
                    channel_obj,
                    self.chat_memory,
                    odoo_manager,
                    odoogpt,
                )

            if custom_tools_called:
                self._tool_runner._run_custom_tools(
                    custom_tools_called,
                    channel_id,
                    channel_obj,
                    self.chat_memory,
                    odoo_manager,
                    odoogpt,
                )

        self.chat_memory._purge_tool_msgs(channel_id)
        ai_msg = self.chat_memory._get_ai_msg(channel_id)
        print(f"{self.name}: {ai_msg}")
        self.chat_memory.add_msg(ai_msg, MessageType.ASSISTANT.value, channel_id)
        self.chat_memory.reduce_context(channel_id)
        return ai_msg

    def verify_context_size(self, chat_id):
        if len(self.chat_memory.get_messages(chat_id)) > 20:
            self.chat_memory.delete_chat(chat_id)
            print("Chat memory exceeded limit, resetting chat.")
            return False

    async def async_process_msg(
        self,
        message: str,
        channel_id: int,
        channel_obj,
        odoo_manager,
        odoogpt,
    ) -> str | None:
        print(f"Running {self.name} with {len(JSON_TOOLS)} tools")

        self.chat_memory.add_msg(message, MessageType.USER.value, channel_id)

        while True:
            params = {
                "model": self.model,  # type: ignore
                "input": self.chat_memory.get_messages(channel_id),  # type: ignore
                "tools": JSON_TOOLS,  # type: ignore
            }
            if self.model == ModelType.GPT_5.value:  # type: ignore
                params["text"] = {"verbosity": VerbosityType.LOW.value}
                params["reasoning"] = {"effort": EffortType.MINIMAL.value}

            ai_output = await self._ai_client._async_gen_ai_output(params)
            self.chat_memory._set_ai_output(ai_output, channel_id)

            functions_called = [
                item
                for item in ai_output.output  # type: ignore
                if item.type == MessageType.FUNCTION_CALL.value
            ]

            custom_tools_called = [
                item
                for item in ai_output.output  # type: ignore
                if item.type == MessageType.CUSTOM_TOOL_CALL.value
            ]

            if not functions_called and not custom_tools_called:
                break

            if functions_called:
                await self._tool_runner._async_run_functions(
                    functions_called,
                    channel_id,
                    channel_obj,
                    self.chat_memory,
                    odoo_manager,
                    odoogpt,
                )

            if custom_tools_called:
                await self._tool_runner._async_run_custom_tools(
                    custom_tools_called,
                    channel_id,
                    channel_obj,
                    self.chat_memory,
                    odoo_manager,
                    odoogpt,
                )

        self.chat_memory._purge_tool_msgs(channel_id)
        ai_msg = self.chat_memory._get_ai_msg(channel_id)
        print(f"{self.name}: {ai_msg}")
        self.chat_memory.add_msg(ai_msg, MessageType.ASSISTANT.value, channel_id)
        self.chat_memory.reduce_context(channel_id)
        return ai_msg


agent = Agent()
