这段代码是一个使用OpenAI API的Streamlit应用程序，主要功能是创建一个交互式的聊天界面，用户可以通过这个界面与OpenAI的模型进行交互。以下是代码的主要部分的解释：

1. **环境变量加载**：使用`os`和`dotenv`库加载环境变量，这些变量包括OpenAI的API密钥、Azure的OpenAI端点和密钥、是否需要身份验证等。

2. **身份验证配置**：如果需要身份验证，该代码会加载`streamlit_authenticator`模块进行身份验证。

3. **OpenAI客户端初始化**：根据环境变量中的设置，初始化OpenAI客户端。

4. **事件处理器定义**：定义一个事件处理器类`EventHandler`，它继承自`AssistantEventHandler`。这个类用于处理与OpenAI模型交互过程中的各种事件，如文本创建、文本变化、工具调用创建等。

5. **线程和消息创建**：定义了`create_thread`和`create_message`函数，用于创建线程和消息。

6. **文件链接创建**：定义了`create_file_link`函数，用于创建文件下载链接。

7. **注释格式化**：定义了`format_annotation`函数，用于格式化注释。

8. **运行流**：定义了`run_stream`函数，用于运行一个流，即与OpenAI模型的交互过程。

9. **文件处理**：定义了`handle_uploaded_file`函数，用于处理用户上传的文件。

10. **聊天渲染**：定义了`render_chat`函数，用于渲染聊天界面。

11. **表单禁用**：定义了`disable_form`函数，用于禁用表单。

12. **登录**：定义了`login`函数，用于处理登录。

13. **主函数**：在主函数`main`中，首先进行了身份验证，然后创建了聊天输入框和文件上传器，接着处理用户的输入和上传的文件，最后渲染聊天界面。

总的来说，这段代码的主要目的是创建一个交互式的聊天界面，用户可以通过这个界面与OpenAI的模型进行交互，并且支持文件上传和下载。此外，还支持身份验证功能。这是一个非常实用的工具，可以用于各种与OpenAI模型交互的场景。

# gpt-assistants-api-ui

* 💬 OpenAI Assistants API chat UI
* 🛠️ It works easily by setting the ASSISTANT ID
* 📁 Supports file upload and file download
* 🏃 Supports Streaming API
* ~🪟 Support to Azure OpenAI~
  * ※ Cannot be used until Azure OpenAI Service supports Streaming API

<img width="1459" alt="スクリーンショット 2023-11-20 2 23 51" src="https://github.com/ryo-ma/gpt-assistants-api-ui/assets/6661165/5c288d51-196a-4919-bc4d-dc508146f58a">

## 🌟 Quick Start

1. 👤 Create an assistant on the OpenAI site & Get assistant ID (https://platform.openai.com/assistants)
2. 🔑 Get the API key from OpenAI (https://platform.openai.com/api-keys)
3. ⬇️ Clone the repository

    ```bash
    $ git clone https://github.com/ryo-ma/gpt-assistants-api-ui.git
    ```

4. 📦 Install dependencies

    ```bash
    $ poetry install
    ```

5. 🔑 Set environment variables

    ```bash
    OPENAI_API_KEY="sk-xxx"
    ASSISTANT_ID="asst_xxx"

    ASSISTANT_TITLE="Assistants API UI"
    ENABLED_FILE_UPLOAD_MESSAGE="Upload a file" # Leave empty to disable
   
    AUTHENTICATION_REQUIRED="False" # Must change to True if you require authentication
    ```
    If you use azure instead, set `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_KEY`

6. 🔑 Set Authentication configuration (optional)

   To set up authentication, create a [secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management) file `.streamlit/secrets.toml`  as below:

   ```toml
   [credentials]
   usernames = { jsmith = {failed_login_attempts = 0,  logged_in = false, name = "John Smith", password = "abc"}, rbriggs = {failed_login_attempts = 0,  logged_in = false, name = "R Briggs", password = "abc"}}
   
   [cookie]
   expiry_days = 30
   key = "some_signature_key"  # Must be string
   name = "some_cookie_name"
   ```
   Reference:  [Deploying Streamlit-Authenticator via Streamlit Community Cloud](https://discuss.streamlit.io/t/deploying-streamlit-authenticator-via-streamlit-community-cloud/39085)

7. 🏃‍️ Run the app

    ```bash
    $ poetry shell
    $ streamlit run app.py
    ```

## 🐳 Run the app using Docker

1. 👤 Create an assistant on the OpenAI site & Get assistant ID (https://platform.openai.com/assistants)
2. 🔑 Get the API key from OpenAI (https://platform.openai.com/api-keys)
3. ⬇️ Clone the repository

    ```bash
    $ git clone https://github.com/ryo-ma/gpt-assistants-api-ui.git
    ```
    
4. 🔑 Set environment variables

    Create a .env file.
   
    ```bash
    OPENAI_API_KEY="sk-xxx"
    ASSISTANT_ID="asst_xxx"

    ASSISTANT_TITLE="Assistants API UI"
    ENABLED_FILE_UPLOAD_MESSAGE="Upload a file" # Leave empty to disable
   
    AUTHENTICATION_REQUIRED="False" # Must change to True if you require authentication
    ```
    If you use Azure instead, set `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_KEY`

5. 🔑 Set Authentication configuration (optional)

   To set up authentication, create a [secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management) file `.streamlit/secrets.toml`  as below:

   ```toml
   [credentials]
   usernames = { jsmith = {failed_login_attempts = 0,  logged_in = false, name = "John Smith", password = "abc"}, rbriggs = {failed_login_attempts = 0,  logged_in = false, name = "R Briggs", password = "abc"}}
   
   [cookie]
   expiry_days = 30
   key = "some_signature_key"  # Must be string
   name = "some_cookie_name"
   ```
   Reference:  [Deploying Streamlit-Authenticator via Streamlit Community Cloud](https://discuss.streamlit.io/t/deploying-streamlit-authenticator-via-streamlit-community-cloud/39085)

6. 💽 Build image

    ```bash
    $ docker compose build
    ```

7. 🏃‍️ Run the app

    ```bash
    $ docker compose up
    ```
Access to [http://localhost:8501](http://localhost:8501).

## 🌐 Deploy to Streamlit Cloud
You can fork this repository and deploy the app to https://share.streamlit.io/. No need to run the app on your local machine.

> Don't forget to choose 3.10 as the Python version and set environment variables in the "Advanced settings" during deployment.

To use authentication with Streamlit Cloud, please use this TOML format:

```toml
# Environment variables
OPENAI_API_KEY="sk-xxx"
ASSISTANT_ID="asst_xxx"

ASSISTANT_TITLE="Assistants API UI"
ENABLED_FILE_UPLOAD_MESSAGE="Upload a file" # Leave empty to disable

AUTHENTICATION_REQUIRED="True"

# Authentication secrets
[credentials]
usernames = { jsmith = {failed_login_attempts = 0,  logged_in = false, name = "John Smith", password = "abc"}, rbriggs = {failed_login_attempts = 0,  logged_in = false, name = "R Briggs", password = "abc"}}

[cookie]
expiry_days = 30
key = "some_signature_key"  # Must be string
name = "some_cookie_name"
```
