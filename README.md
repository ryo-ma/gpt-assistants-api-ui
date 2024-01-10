# gpt-assistants-api-ui

* 💬 OpenAI Assistants API chat UI
* 🛠️ It works easily by setting the ASSISTANT ID
* 📁 Supports file upload and file download

![UI Screenshot](https://github.com/ryo-ma/gpt-assistants-api-ui/assets/6661165/5c288d51-196a-4919-bc4d-dc508146f58a)

### 🌐 Deploy to Streamlit
You can fork this repository and deploy it to https://share.streamlit.io/ by setting the environment variables `OPENAI_API_KEY` and `ASSISTANT_ID` in the "Secrets" tab.
> Don't forget to choose 3.10 as the Python version in the "Advanced settings" during deployment.

## 🌟 Quick Start

1. 📦 Install dependencies

    ```
    $ poetry install
    ```

2. 🔑 Set environment variables

    ```
    OPENAI_API_KEY="sk-xxx"
    ASSISTANT_ID="asst_xxx"

    ASSISTANT_TITLE="Assistants API UI"
    ENABLED_FILE_UPLOAD_MESSAGE="Upload a file"
    ```

3. 🏃‍️ Run the app

    ```
    $ poetry shell
    $ streamlit run streamlit_app.py
    ```
