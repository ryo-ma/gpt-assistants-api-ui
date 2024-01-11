# gpt-assistants-api-ui

* 💬 OpenAI Assistants API chat UI
* 🛠️ It works easily by setting the ASSISTANT ID
* 📁 Supports file upload and file download

<img width="1459" alt="スクリーンショット 2023-11-20 2 23 51" src="https://github.com/ryo-ma/gpt-assistants-api-ui/assets/6661165/5c288d51-196a-4919-bc4d-dc508146f58a">

## 🌟 Quick Start

1. 📦 Install dependencies

    ```bash
    $ poetry install
    ```

2. 🔑 Set environment variables

    ```bash
    OPENAI_API_KEY="sk-xxx"
    ASSISTANT_ID="asst_xxx"

    ASSISTANT_TITLE="Assistants API UI"
    ENABLED_FILE_UPLOAD_MESSAGE="Upload a file" # Leave empty to disable
    ```

3. 🏃‍️ Run the app

    ```bash
    $ poetry shell
    $ streamlit run app.py
    ```

## 🌐 Deploy to Streamlit Cloud
You can fork this repository and deploy the app to https://share.streamlit.io/. No need to run the app on your local machine.

> Don't forget to choose 3.10 as the Python version and set environment variables in the "Advanced settings" during deployment.
