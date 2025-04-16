import os
import base64
import re
import json
import csv
import pathlib
import streamlit as st
import streamlit.components.v1 as components 
import openai
from openai import AssistantEventHandler
from tools import TOOL_MAP
from typing_extensions import override
from dotenv import load_dotenv
import streamlit_authenticator as stauth

load_dotenv()

assistant_icon = "🤖" 
user_icon = "🧑‍🔬"      # st.image('A2logo_neg_small.png')
st.logo('a2bred_trans.png', link = None, icon_image = None)
st.sidebar.markdown("*Sandkasse for utprøving av KI.*")

# Define here is you want to use Azure or not (even in enviroment variables are available, you may not want to go that way)
useAzure = False
# Define the very first hidden message to the bot
initial_hidden_message = "Hei!"

# The following code parts are just to ensure that cursor focus stays in input field.
# Initialize the counter in session state
if 'counter' not in st.session_state:
    st.session_state.counter = 0

# Increment the counter each time the page is reloaded
st.session_state.counter += 1

def str_to_bool(str_input):
    if not isinstance(str_input, str):
        return False
    return str_input.lower() == "true"


# Load environment variables
openai_api_key = os.environ.get("OPENAI_API_KEY")
if openai_api_key:
    print ("Using OPENAI Key:" + openai_api_key[:7] + "..." + openai_api_key[-5:])
instructions = os.environ.get("RUN_INSTRUCTIONS", "")
enabled_file_upload_message = os.environ.get(
    "ENABLED_FILE_UPLOAD_MESSAGE", "Last opp et vedlegg her"
)
azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
azure_openai_key = os.environ.get("AZURE_OPENAI_KEY")
authentication_required = str_to_bool(os.environ.get("AUTHENTICATION_REQUIRED", False))

# Load authentication configuration
if authentication_required:
    if "credentials" in st.secrets:
        authenticator = stauth.Authenticate(
            st.secrets["credentials"].to_dict(),
            st.secrets["cookie"]["name"],
            st.secrets["cookie"]["key"],
            st.secrets["cookie"]["expiry_days"],
        )
    else:
        authenticator = None  # No authentication should be performed

client = None
if useAzure and azure_openai_endpoint and azure_openai_key:
    client = openai.AzureOpenAI(
        api_key=azure_openai_key,
        api_version="2024-05-01-preview",
        azure_endpoint=azure_openai_endpoint,
    )
else:
    client = openai.OpenAI(api_key=openai_api_key)


class EventHandler(AssistantEventHandler):
    @override
    def on_event(self, event):
        pass

    @override
    def on_text_created(self, text):
        st.session_state.current_message = ""
        with st.chat_message("Assistant", avatar=assistant_icon):
            st.session_state.current_markdown = st.empty()

    @override
    def on_text_delta(self, delta, snapshot):
        if snapshot.value:
            text_value = re.sub(
                r"\[(.*?)\]\s*\(\s*(.*?)\s*\)", "Download Link", snapshot.value
            )
            st.session_state.current_message = text_value
            st.session_state.current_markdown.markdown(
                st.session_state.current_message, True
            )

    @override
    def on_text_done(self, text):
        format_text = format_annotation(text)
        st.session_state.current_markdown.markdown(format_text, True)
        st.session_state.chat_log.append({"name": "assistant", "msg": format_text})

    @override
    def on_tool_call_created(self, tool_call):
        if tool_call.type == "code_interpreter":
            st.session_state.current_tool_input = ""
            with st.chat_message("Assistant", avatar=assistant_icon):
                st.session_state.current_tool_input_markdown = st.empty()

    @override
    def on_tool_call_delta(self, delta, snapshot):
        if 'current_tool_input_markdown' not in st.session_state:
            with st.chat_message("Assistant", avatar=assistant_icon):
                st.session_state.current_tool_input_markdown = st.empty()

        if delta.type == "code_interpreter":
            if delta.code_interpreter.input:
                st.session_state.current_tool_input += delta.code_interpreter.input
                input_code = f"### code interpreter\ninput:\n```python\n{st.session_state.current_tool_input}\n```"
                st.session_state.current_tool_input_markdown.markdown(input_code, True)

            if delta.code_interpreter.outputs:
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        pass

    @override
    def on_tool_call_done(self, tool_call):
        st.session_state.tool_calls.append(tool_call)
        if tool_call.type == "code_interpreter":
            if tool_call.id in [x.id for x in st.session_state.tool_calls]:
                return
            input_code = f"### code interpreter\ninput:\n```python\n{tool_call.code_interpreter.input}\n```"
            st.session_state.current_tool_input_markdown.markdown(input_code, True)
            st.session_state.chat_log.append({"name": "assistant", "msg": input_code})
            st.session_state.current_tool_input_markdown = None
            for output in tool_call.code_interpreter.outputs:
                if output.type == "logs":
                    output = f"### code interpreter\noutput:\n```\n{output.logs}\n```"
                    with st.chat_message("Assistant", avatar=assistant_icon):
                        st.markdown(output, True)
                        st.session_state.chat_log.append(
                            {"name": "assistant", "msg": output}
                        )
        elif (
            tool_call.type == "function"
            and self.current_run.status == "requires_action"
        ):
            with st.chat_message("Assistant", avatar=assistant_icon):
                msg = f"### Function Calling: {tool_call.function.name}"
                st.markdown(msg, True)
                st.session_state.chat_log.append({"name": "assistant", "msg": msg})
            tool_calls = self.current_run.required_action.submit_tool_outputs.tool_calls
            tool_outputs = []
            for submit_tool_call in tool_calls:
                tool_function_name = submit_tool_call.function.name
                tool_function_arguments = json.loads(
                    submit_tool_call.function.arguments
                )
                tool_function_output = TOOL_MAP[tool_function_name](
                    **tool_function_arguments
                )
                tool_outputs.append(
                    {
                        "tool_call_id": submit_tool_call.id,
                        "output": tool_function_output,
                    }
                )

            with client.beta.threads.runs.submit_tool_outputs_stream(
                thread_id=st.session_state.thread.id,
                run_id=self.current_run.id,
                tool_outputs=tool_outputs,
                event_handler=EventHandler(),
            ) as stream:
                stream.until_done()


def create_thread(content, file):
    return client.beta.threads.create()


def create_message(thread, content, file):
    attachments = []
    if file is not None:
        attachments.append(
            {"file_id": file.id, "tools": [{"type": "code_interpreter"}, {"type": "file_search"}]}
        )
    client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=content, attachments=attachments
    )


def create_file_link(file_name, file_id):
    content = client.files.content(file_id)
    content_type = content.response.headers["content-type"]
    b64 = base64.b64encode(content.text.encode(content.encoding)).decode()
    link_tag = f'<a href="data:{content_type};base64,{b64}" download="{file_name}">Download Link</a>'
    return link_tag


def format_annotation(text):
    citation_map = {}
    citations = []
    text_value = text.value
    for index, annotation in enumerate(text.annotations):
        text_value = text_value.replace(annotation.text, f" [{index}]")

        if file_citation := getattr(annotation, "file_citation", None):
            cited_file = client.files.retrieve(file_citation.file_id)
            if cited_file.filename in citation_map.keys():
                citation_map[cited_file.filename] += f",[{index}]"
            else:
                citation_map[cited_file.filename] = f"[{index}]"
            #if hasattr(file_citation, 'quote'):
            #    citations.append(
            #        f"[{index}] {file_citation.quote} from {cited_file.filename}"
            #    )
        elif file_path := getattr(annotation, "file_path", None):
            link_tag = create_file_link(
                annotation.text.split("/")[-1],
                file_path.file_id,
            )
            text_value = re.sub(r"\[(.*?)\]\s*\(\s*(.*?)\s*\)", link_tag, text_value)
    for filename in citation_map.keys():
        pretty_filename = filename
        if "_" in filename and not filename.startswith('CV') and not filename.startswith('A'):
            pretty_filename = filename.split("_", 1)[1]  # Split on the first underscore and take the second part (Removes internal serial number)
        if filename == map_file_to_source(filename):
            citations.append(
                f"{citation_map[filename]}: {pretty_filename}"
            )
        else:
            citations.append(
                    f"{citation_map[filename]}: [{pretty_filename}]({map_file_to_source(filename)})"
            )
    text_value += "\n\n" + "<br>".join(citations)
    return text_value


def run_stream(user_input, file, selected_assistant_id):
    if "thread" not in st.session_state:
        st.session_state.thread = create_thread(user_input, file)
    create_message(st.session_state.thread, user_input, file)
    with client.beta.threads.runs.stream(
        thread_id=st.session_state.thread.id,
        assistant_id=selected_assistant_id,
        event_handler=EventHandler(),
    ) as stream:
        stream.until_done()


def handle_uploaded_file(uploaded_file):
    file = client.files.create(file=uploaded_file, purpose="assistants")
    return file


def render_chat():
    for chat in st.session_state.chat_log:
        if chat["name"] == "assistant":
            theavatar = assistant_icon
        else:
            theavatar = user_icon
        with st.chat_message(chat["name"], avatar=theavatar):
            st.markdown(chat["msg"], True)


if "tool_call" not in st.session_state:
    st.session_state.tool_calls = []

if "chat_log" not in st.session_state:
    st.session_state.chat_log = []

if "in_progress" not in st.session_state:
    st.session_state.in_progress = False

if "just_started" not in st.session_state:
    st.session_state.just_started = True


def disable_form():
    st.session_state.in_progress = True


def login():
    if st.session_state["authentication_status"] is False:
        st.error("Username/password is incorrect")
    elif st.session_state["authentication_status"] is None:
        st.warning("Please enter your username and password")


def reset_chat():
    st.session_state.chat_log = []
    st.session_state.in_progress = False
    st.session_state.just_started = True

@st.cache_data
def map_file_to_source(thefile):
    mapfilename = st.session_state.mapfile_name
    #print("Checking "+mapfilename)
    if pathlib.Path(mapfilename).exists():
        #print("Reading the sourcemap file " + mapfilename)
        with open(mapfilename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if '\\' in row['Filename']:
                    thisfilename = row['Filename'].split('\\')[-1] #os.path.basename(row['Filename'])
                else:
                    thisfilename = row['Filename']
                if thisfilename == thefile:
                    return row['URL']
    else:
        print(f"Unable to load {mapfilename}!")
    return thefile #Not found

def load_chat_screen(assistant_id, assistant_title):
    if enabled_file_upload_message:
        uploaded_file = st.sidebar.file_uploader(
            enabled_file_upload_message,
            type=[
                "txt",
                "pdf",
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

    # Add welcome-image on left hand side
    imagefile = "image_" + assistant_id + ".jpg"
    if not pathlib.Path(imagefile).exists():
        imagefile = "image_default.jpg"
    st.sidebar.image(imagefile, caption="Velkommen!")

    st.title(assistant_title if assistant_title else "")
    user_msg = st.chat_input(
        "Din melding her...", on_submit=disable_form, disabled=st.session_state.in_progress
    )
    if st.session_state.just_started and not user_msg:
        user_msg = initial_hidden_message
    
    if user_msg:
        file = None
        if not st.session_state.just_started:
            render_chat()
            with st.chat_message("user", avatar=user_icon):
                st.markdown(user_msg, True)
            st.session_state.chat_log.append({"name": "user", "msg": user_msg})
            if uploaded_file is not None:
                file = handle_uploaded_file(uploaded_file)
        st.session_state.just_started = False
        run_stream(user_msg, file, assistant_id)
        st.session_state.in_progress = False
        st.session_state.tool_call = None
        st.rerun()

    render_chat()

    # Reset focus on input field
    components.html(
        f"""
            <div>some hidden container</div>
            <p>{st.session_state.counter}</p>
            <script>
                var textarea = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
                if (textarea) {{
                    textarea.focus();
                }}
            </script>
        """,
        height=0,
    )

def authenticate_password(some_password):
    if some_password != os.environ.get("USER_PASSWORD", None):
        return False
    return True

some_password = st.text_input("Logg inn med hemmelig passord her:", type="password")


def main():
    # Retrieve the assistant ID from the URL parameter if provided
    # You can read query params using key notation
    assistant_id_from_url = None
    try:
        assistant_id_from_url = st.query_params["assistant"]
        print(f"Assistant {assistant_id_from_url} indicated in URL.")
    except Exception as e:
        print("Assistant was not defined in URL.")
    # query_params = st_script_run_context.get_script_run_ctx().query_params
    # assistant_id_from_url = query_params.get("assistant", [None])[0]  # Using [0] to get the first element

    # Check if multi-agent settings are defined
    multi_agents = os.environ.get("OPENAI_ASSISTANTS", None)
    single_agent_id = os.environ.get("ASSISTANT_ID", None)
    single_agent_title = os.environ.get("ASSISTANT_TITLE", "Assistants API UI")

    if (
        authentication_required
        and "credentials" in st.secrets
        and authenticator is not None
    ):
        authenticator.login()
        if not st.session_state["authentication_status"]:
            login()
            return
        else:
            authenticator.logout(location="sidebar")

    # Determine if an assistant ID is pre-selected by URL parameter
    if assistant_id_from_url:
        if multi_agents:
            assistants_json = json.loads(multi_agents)
            assistants_object = {f'{obj["title"]}': obj for obj in assistants_json}
            for title, assistant in assistants_object.items():
                if assistant["id"] == assistant_id_from_url:
                    # selected_assistant = assistant_id_from_url
                    single_agent_id = assistant_id_from_url
                    single_agent_title = title
                    print(f"Går for URL-valgt agent {single_agent_title}({single_agent_id})!")
                    break

    if not authenticate_password(some_password):
        st.error("Ugyldig/feil passord. Ingen aksess.")
        st.stop()
    else:
        if single_agent_id:
            st.success("Du er logget inn!", icon=":material/thumb_up:")
        else:
            st.success("Du er logget inn! Vennligst velg ønsket assistent i venstre meny!", icon=":material/thumb_up:")

    if single_agent_id:
        st.session_state['mapfile_name'] = single_agent_id + "_sourcemap.csv"
        st.cache_data.clear()
        load_chat_screen(single_agent_id, single_agent_title)
    elif multi_agents:
        assistants_json = json.loads(multi_agents)
        assistants_object = {f'{obj["title"]}': obj for obj in assistants_json}
        selected_assistant = st.sidebar.selectbox(
            "Velg din KI-assistent:",
            list(assistants_object.keys()),
            index=None,
            placeholder="Velg en assistent her...",
            on_change=reset_chat,  # Call the reset function on change
        )
        if selected_assistant:
            st.session_state['mapfile_name'] = assistants_object[selected_assistant]["id"] + "_sourcemap.csv"
            st.cache_data.clear()
            load_chat_screen(
                assistants_object[selected_assistant]["id"],
                assistants_object[selected_assistant]["title"],
            )
    else:
        st.error("No assistant configurations defined in environment variables.")

if __name__ == "__main__":
    main()
