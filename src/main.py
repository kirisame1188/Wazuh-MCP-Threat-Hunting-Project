from fastmcp import FastMCP
import requests
import os
import urllib3
import json
from dotenv import load_dotenv

# --- 1. 設定與初始化區 ---
# 載入上一層資料夾的 .env 設定
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# 忽略 SSL 安全警告 (因為是實驗環境)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 初始化 MCP Server，名稱改為 Threat Hunter 比較帥氣
mcp = FastMCP("Wazuh-Threat-Hunter")

# 讀取環境變數
HOST = os.getenv("WAZUH_API_HOST")
PORT = os.getenv("WAZUH_API_PORT", "55000")
USER = os.getenv("WAZUH_API_USERNAME")
PASS = os.getenv("WAZUH_API_PASSWORD")
BASE_URL = f"https://{HOST}:{PORT}"

# --- 2. 輔助函式區 ---
def get_token():
    """取得 Wazuh JWT Token"""
    try:
        resp = requests.get(
            f"{BASE_URL}/security/user/authenticate", 
            auth=(USER, PASS), 
            verify=False, 
            timeout=5
        )
        if resp.status_code == 200:
            return resp.json()['data']['token']
        return None
    except Exception as e:
        return None

# --- 3. AI 工具定義區 (Tools) ---

@mcp.tool()
def list_agents() -> str:
    """列出所有受監控的主機 (Agents) 及其連線狀態。
    當使用者問「有哪些電腦受監控？」或是「檢查 Agent 狀態」時使用此工具。
    """
    token = get_token()
    if not token: 
        return "錯誤: 無法連線至 Wazuh API，請檢查帳號密碼或網路連線。"
    
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(f"{BASE_URL}/agents", headers=headers, verify=False, params={"pretty": "true"})
        if resp.status_code == 200:
            data = resp.json().get('data', {}).get('affected_items', [])
            # 直接回傳 JSON 結構，讓 Claude 展現它的分析能力
            return json.dumps(data, indent=2, ensure_ascii=False)
        else:
            return f"API 回傳錯誤: {resp.status_code} - {resp.text}"
    except Exception as e:
        return f"發生例外錯誤: {str(e)}"

@mcp.tool()
def get_infrastructure_status() -> str:
    """獲取目前的資安基礎設施概況 (Infrastructure Status)。
    當使用者問「目前的資安態勢如何？」或「系統狀況總覽」時使用。
    """
    token = get_token()
    if not token: 
        return "錯誤: 無法連線至 Wazuh API"
    
    headers = {"Authorization": f"Bearer {token}"}
    try:
        # 取得 Agent 的統計數據 (多少個 Active, 多少個 Disconnected)
        resp = requests.get(f"{BASE_URL}/agents/summary/status", headers=headers, verify=False)
        if resp.status_code == 200:
            summary = resp.json().get('data', {})
            return f"【資安態勢報告】\n{json.dumps(summary, indent=2, ensure_ascii=False)}"
        else:
            return f"查詢失敗: {resp.status_code}"
    except Exception as e:
        return f"發生錯誤: {str(e)}"

# --- 4. 啟動區 ---
if __name__ == "__main__":
    mcp.run()