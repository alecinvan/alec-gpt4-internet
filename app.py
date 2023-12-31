from googleapiclient.discovery import build
from bs4 import BeautifulSoup
import requests
import openai
import gradio as gr
import os

# https://platform.openai.com/account/api-keys
openai.api_key = "YOUR_OPENAI_KEY"


class GoogleChat():    # GoogleChat类定义了一个聊天机器人的对象，包括了所需要的函数，我们一个一个的对函数说明一下
    def __init__(self):
        # 初始化一个谷歌自定义搜索API， 导入开发者密钥，这个密钥拥有进行身份验证以便调用Google Custom Search API. 同时创建了OpenAI GPT4模型用于生成机器人的回答
        self.service = build(
            # https://developers.google.com/custom-search/v1/introduction
            "customsearch", "v1", developerKey="YOUR_GOOGLE_DEVELOPER_KEY"
        )

    def _search(self, query):    # 这个搜索函数用于调用Google Custom Search API进行搜索，并返回搜索结果。
        # call google search api
        response = (
            self.service.cse()
            .list(
                q=query,
                cx="5694926faee674193", # https://programmablesearchengine.google.com/controlpanel/all  ， 在这个链接里生产Search engine ID ,拷贝过来
            )
            .execute()
        )
        return response['items']

    def _get_search_query(self, history, query):  # 函数根据历史聊天记录和用户提供的问题，生成一个最相关的搜索查询，以便从搜索结果中获取信息。
        # only use user messages
        # assistant messages and not relevant for response
        messages = [{"role": "system",
                     "content": "You are an assistant that helps to convert text into a web search engine query. "
                                "You output only 1 query for the latest message and nothing else."}]

        for message in history:
            messages.append({"role": "user", "content": message[0]})

        messages.append({"role": "user", "content": "Based on my previous messages, "
                                                    "what is the most relevant web search query for the text below?\n\n"
                                                    "Text: " + query + "\n\n"
                                                                       "Query:"})

        search_query = openai.ChatCompletion.create(。  #函数调用OpenAI的ChatCompletion.create方法
            model="gpt-3.5-turbo",     #因为它不需要复杂或长的文本处理，而且 ChatGPT API 比 GPT-4 快得多。
            messages=messages,
            temperature=0,
        )['choices'][0]['message']['content']

        return search_query.strip("\"")

    def run_text(self, history, query):
        search_query = self._get_search_query(history, query)

        print("Search query: ", search_query)

        # add system message to the front
        messages = [{"role": "system",
                     "content": "You are a search assistant that answers questions based on search results and "
                                "provides links to relevant parts of your answer."}]

        # unpack history into messages
        for message in history:
            messages.append({"role": "user", "content": message[0]})
            if message[1]:
                messages.append({"role": "assistant", "content": message[1]})

        # construct prompt from search results
        prompt = "Answer query using the information from the search results below: \n\n"
        results = self._search(search_query)
        for result in results:
            prompt += "Link: " + result['link'] + "\n"
            prompt += "Title: " + result['title'] + "\n"
            prompt += "Content: " + result['snippet'] + "\n\n"
        prompt += "Query: " + query
        messages.append({"role": "user", "content": prompt})
        # print(prompt)

        # generate response
        response = openai.ChatCompletion.create(
            model="gpt-4",  # change to gpt-3.5-turbo if don't have access
            messages=messages,
            temperature=0.4,
        )['choices'][0]['message']['content']

        # only add query and response to history
        # the context is not needed
        history.append((query, response))

        return history


if __name__ == '__main__':
    bot = GoogleChat()

    # ui
    with gr.Blocks(css="#chatbot .overflow-y-auto{height:500px}") as demo:
        chatbot = gr.Chatbot([], elem_id="chatbot", label="李飒的GPT-4可以上网的聊天机器人").style(height=160)
        with gr.Row():   #创建一个UI行，用于包含聊天输入框和“清除”按钮。
            with gr.Column(scale=0.85):
                txt = gr.Textbox(show_label=False, placeholder="您想了解什么?").style(
                    container=False)
            with gr.Column(scale=0.15, min_width=0):
                clear = gr.Button("Clear")

        txt.submit(bot.run_text, [chatbot, txt], chatbot)
        txt.submit(lambda: "", None, txt)
        clear.click(lambda: [], None, chatbot)
        demo.launch(share=True)

