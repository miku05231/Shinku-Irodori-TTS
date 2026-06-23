@echo off
set PYTHONIOENCODING=utf-8
set IRODORI_LORA=outputs\shinku_lora\checkpoint_final
set IRODORI_PORT=8088
uv run python api_server.py
