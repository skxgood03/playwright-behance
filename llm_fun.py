from qwen_agent.agents import Assistant

# Define LLM
llm_cfg = {
    'model': 'Qwen/Qwen3-8B',

    # Use the endpoint provided by Alibaba Model Studio:
    # 'model_type': 'qwen_dashscope',
    # 'api_key': os.getenv('DASHSCOPE_API_KEY'),

    # Use a custom endpoint compatible with OpenAI API:
    'model_server': 'http://10.7.100.85:8000/v1',  # api_base
    'api_key': 'EMPTY',

    # Other parameters:
    # 'generate_cfg': {
    #         # Add: When the response content is `<think>this is the thought</think>this is the answer;
    #         # Do not add: When the response has been separated by reasoning_content and content.
    #         'thought_in_content': True,
    #     },
}

# Define Tools
tools = [
    # {
    #  "mcpServers": {
    #      "blender": {
    #          "command": "uvx",
    #          "args": ["blender-mcp"]
    #          }
    #      }
    #  }
    {"mcpServers": {
        "amap-maps": {
            "command": "npx",
            "args": ["-y", "@amap/amap-maps-mcp-server"],
            "env": {"AMAP_MAPS_API_KEY": "5a1607e8cb92878c2c151fbc8da90ce5"
                    }
        }
    }
    }
]

# Define Agent
bot = Assistant(llm=llm_cfg, function_list=tools)

# Streaming generation
messages = []
while True:
    user_input = input("请输入指令（输入 exit 退出）：")
    if user_input.strip().lower() == "exit":
        break
    messages.append({'role': 'user', 'content': user_input})
    for responses in bot.run(messages=messages):
        # pass
        print(responses)
