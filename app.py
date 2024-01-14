import os
import time
import base64
import re
import json

import streamlit as st
import openai
from openai.types.beta.threads import MessageContentImageFile
from tools import TOOL_MAP


api_key = os.environ.get("OPENAI_API_KEY")
client = openai.OpenAI(api_key=api_key)
assistant_id = os.environ.get("ASSISTANT_ID")
instructions = os.environ.get("RUN_INSTRUCTIONS", "")
assistant_title = os.environ.get("ASSISTANT_TITLE", "Assistants API UI")
enabled_file_upload_message = os.environ.get("ENABLED_FILE_UPLOAD_MESSAGE", "Upload a file")


def create_thread(content, file):
    messages = [
        {
            "role": "user",
            "content": content,
        }
    ]
    if file is not None:
        messages[0].update({"file_ids": [file.id]})
    thread = client.beta.threads.create(messages=messages)
    return thread


def create_message(thread, content, file):
    file_ids = []
    client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=content, file_ids=file_ids
    )
    if file is not None:
        file_ids.append(file.id)


def create_run(thread):
    run = client.beta.threads.runs.create(
        thread_id=thread.id, assistant_id=assistant_id, instructions=instructions
    )
    return run


def create_file_link(file_name, file_id):
    content = client.files.content(file_id)
    content_type = content.response.headers["content-type"]
    b64 = base64.b64encode(content.text.encode(content.encoding)).decode()
    link_tag = f'<a href="data:{content_type};base64,{b64}" download="{file_name}">Download Link</a>'
    return link_tag


def get_message_value_list(messages):
    messages_value_list = []
    for message in messages:
        message_content = ""
        print(message)
        if not isinstance(message, MessageContentImageFile):
            message_content = message.content[0].text
            annotations = message_content.annotations
        else:
            image_file = client.files.retrieve(message.file_id)
            messages_value_list.append(
                f"Click <here> to download {image_file.filename}"
            )
        citations = []
        for index, annotation in enumerate(annotations):
            message_content.value = message_content.value.replace(
                annotation.text, f" [{index}]"
            )

            if file_citation := getattr(annotation, "file_citation", None):
                cited_file = client.files.retrieve(file_citation.file_id)
                citations.append(
                    f"[{index}] {file_citation.quote} from {cited_file.filename}"
                )
            elif file_path := getattr(annotation, "file_path", None):
                link_tag = create_file_link(
                    annotation.text.split("/")[-1], file_path.file_id
                )
                message_content.value = re.sub(
                    r"\[(.*?)\]\s*\(\s*(.*?)\s*\)", link_tag, message_content.value
                )

        message_content.value += "\n" + "\n".join(citations)
        messages_value_list.append(message_content.value)
        return messages_value_list


def get_message_list(thread, run):
    completed = False
    while not completed:
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        print("run.status:", run.status)
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        print("messages:", "\n".join(get_message_value_list(messages)))
        if run.status == "completed":
            completed = True
        else:
            time.sleep(1)

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    return get_message_value_list(messages)


def get_response(user_input, file):
    if "thread" not in st.session_state:
        st.session_state.thread = create_thread(user_input, file)
    else:
        create_message(st.session_state.thread, user_input, file)
    run = create_run(st.session_state.thread)
    run = client.beta.threads.runs.retrieve(
        thread_id=st.session_state.thread.id, run_id=run.id
    )

    while run.status == "in_progress":
        print("run.status:", run.status)

        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread.id, run_id=run.id
        )
        run_steps = client.beta.threads.runs.steps.list(
            thread_id=st.session_state.thread.id, run_id=run.id
        )
        print("run_steps:", run_steps)
        for step in run_steps.data:
            if hasattr(step.step_details, "tool_calls"):
                for tool_call in step.step_details.tool_calls:
                    if (
                        hasattr(tool_call, "code_interpreter")
                        and tool_call.code_interpreter.input != ""
                    ):
                        input_code = f"### code interpreter\ninput:\n```python\n{tool_call.code_interpreter.input}\n```"
                        print(input_code)
                        if (
                            st.session_state.tool_call is None
                            or st.session_state.tool_call.id != tool_call.id
                        ):
                            st.session_state.tool_call = tool_call
                            with st.chat_message("Assistant"):
                                st.markdown(
                                    input_code,
                                    True,
                                )
                                st.session_state.chat_log.append(
                                    {
                                        "name": "assistant",
                                        "msg": input_code,
                                    }
                                )

    if run.status == "requires_action":
        print("run.status:", run.status)
        run = execute_action(run, st.session_state.thread)

    return "\n".join(get_message_list(st.session_state.thread, run))


def execute_action(run, thread):
    tool_outputs = []
    for tool_call in run.required_action.submit_tool_outputs.tool_calls:
        tool_id = tool_call.id
        tool_function_name = tool_call.function.name
        print(tool_call.function.arguments)

        tool_function_arguments = json.loads(tool_call.function.arguments)

        print("id:", tool_id)
        print("name:", tool_function_name)
        print("arguments:", tool_function_arguments)

        tool_function_output = TOOL_MAP[tool_function_name](**tool_function_arguments)
        print("tool_function_output", tool_function_output)
        tool_outputs.append({"tool_call_id": tool_id, "output": tool_function_output})

    run = client.beta.threads.runs.submit_tool_outputs(
        thread_id=thread.id,
        run_id=run.id,
        tool_outputs=tool_outputs,
    )
    return run


def handle_uploaded_file(uploaded_file):
    file = client.files.create(file=uploaded_file, purpose="assistants")
    return file


def render_chat():
    for chat in st.session_state.chat_log:
        with st.chat_message(chat["name"]):
            st.markdown(chat["msg"], True)


if "tool_call" not in st.session_state:
    st.session_state.tool_call = None

if "chat_log" not in st.session_state:
    st.session_state.chat_log = []

if "in_progress" not in st.session_state:
    st.session_state.in_progress = False


def disable_form():
    st.session_state.in_progress = True


def main():
    st.title(assistant_title)
    user_msg = st.chat_input(
        "Message", on_submit=disable_form, disabled=st.session_state.in_progress
    )
    if enabled_file_upload_message:
        uploaded_file = st.sidebar.file_uploader(
            enabled_file_upload_message,
            type=[
                "txt",
                "pdf",
                "png",
                "jpg",
                "jpeg",
                "csv",
                "json",
                "geojson",
                "xlsx",
                "xls",
            ],
            disabled=st.session_state.in_progress,
        )
    else:
        uploaded_file = None
    if user_msg:
        render_chat()
        with st.chat_message("user"):
            st.markdown(user_msg, True)
        st.session_state.chat_log.append({"name": "user", "msg": user_msg})
        file = None
        if uploaded_file is not None:
            file = handle_uploaded_file(uploaded_file)
        with st.spinner("Wait for response..."):
            response = get_response(user_msg, file)
        with st.chat_message("Assistant"):
            st.markdown(response, True)

        st.session_state.chat_log.append({"name": "assistant", "msg": response})
        st.session_state.in_progress = False
        st.session_state.tool_call = None
        st.rerun()
    render_chat()


if __name__ == "__main__":
    main()
