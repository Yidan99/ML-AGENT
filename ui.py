import json
import sys
from src.agents import build_agent_graph
from src.agents import AgentState
from langgraph.errors import InvalidUpdateError


def check_docker():
    """
    检测本地 Docker 服务和 my-ml-env 镜像是否可用。
    返回 (True, client) 或 (False, err)。
    """
    try:
        import docker
        client = docker.from_env()
        # ping 会检查 daemon 是否在运行
        client.ping()
        # 再检查镜像是否存在
        images = [img.tags for img in client.images.list()]
        if not any("my-ml-env:latest" in tag for tags in images for tag in tags):
            raise docker.errors.ImageNotFound("本地未找到 my-ml-env 镜像")
        return True, client
    except Exception as e:
        return False, e


# def interactive_ui():
#     # 1. Check Docker first
#     ok, info = check_docker()
#     if not ok:
#         print("❌ Docker environment issue detected:")
#         print(f"   {info}")
#         print("\nPlease ensure:")
#         print("  1. Docker Desktop is installed and running;")
#         print("  2. You have built the image by running `docker build -t my-ml-env .` in the project root directory;")
#         input("\nPress Enter to exit the program. Please fix the issue and try again.")
#         sys.exit(1)
#
#     print("🚀 Welcome to the Interactive ML LLM Agent System 🚀\n")
#     # print("check: 'cd D:/1PhD/AI_AGENT' and 'docker build -t my-ml-env'.")
#     instruction = input("👉 Please enter your ML task instruction:\n> ")
#     model_choice = input("\n🤖 Choose code LLM (deepseek / claude) [default: deepseek]:\n> ").strip().lower() or "deepseek"
#     agent_graph = build_agent_graph()
#     print("\n🔍 Agent is working on your task...\n")
#
#     # Initialize full state
#     agent_input = {
#         "instruction": instruction,
#         "web_results": "",
#         "context": "",
#         "code": "",
#         "output": "",
#         "error": "",
#         "retries": 0,
#         "trace": [],
#         "current_node": ""
#     }
#
#     last_trace = []
#     schema_keys = {"instruction","web_results","context","code","output","error","retries","trace","current_node"}
#
#     # Stream and display each step
#     for i, raw_state in enumerate(agent_graph.stream(agent_input)):
#         # Unwrap nested state if necessary
#         state = raw_state
#         keys = list(state.keys())
#         if len(keys) == 1 and keys[0] not in schema_keys and isinstance(state[keys[0]], dict):
#             state = state[keys[0]]
#
#         # get updated trace
#         trace = state.get("trace", [])
#         if trace:
#             step = trace[-1]
#             print(f"\nStep {i+1}: Node: {step.get('node', 'unknown')}")
#             for k, v in step.get("state", {}).items():
#                 if isinstance(v, str) and len(v) > 500:
#                     v = v[:500] + "...[truncated]"
#                 print(f"    {k}: {v}")
#         else:
#             print(f"\nStep {i+1}: Node: unknown (no trace yet)")
#         last_trace = trace
#
#     # Final output
#     print("\n✅ Final Output:")
#     final_state = raw_state
#     keys = list(final_state.keys())
#     if len(keys) == 1 and keys[0] not in schema_keys and isinstance(final_state[keys[0]], dict):
#         final_state = final_state[keys[0]]
#     print(final_state.get("output", "No output."))
#
#     # Save trace
#     with open('agent_trace.json', 'w', encoding='utf-8') as f:
#         json.dump(last_trace, f, ensure_ascii=False, indent=4)
#     print("\n📂 Agent trace saved to agent_trace.json.")


def interactive_ui():
    # 1. Check Docker first
    ok, info = check_docker()
    if not ok:
        print("❌ Docker environment issue detected:")
        print(f"   {info}")
        print("\nPlease ensure:")
        print("  1. Docker Desktop is installed and running;")
        print("  2. You have built the image by running `docker build -t my-ml-env .` in the project root directory;")
        input("\nPress Enter to exit the program. Please fix the issue and try again.")
        sys.exit(1)

    print("🚀 Welcome to the Interactive ML LLM Agent System 🚀\n")

    # model_choice = input("🤖 Choose LLM (deepseek/claude) [deepseek]:\n> ").strip().lower() or "deepseek"
    model_choice = "deepseek"

    instr = input("👉 Please enter your ML task instruction:\n> ")


    state = {"trace": []}

    agent_graph = build_agent_graph()
    print("\n🔍 Agent is working on your task...\n")

    agent_input = {
        "instruction": instr,
        "model_choice": model_choice,
        "trace": state.get("trace", [])
    }
    final_state = None

    for step_state in agent_graph.stream(agent_input):
        final_state = step_state
        trace = state.get("trace", [])
        if not trace:
            continue
        last = trace[-1]
        print(f"Step {len(trace)}: Node: {last['node']}")
        for k, v in last.get('state', {}).items():
            if isinstance(v, str) and len(v) > 1000:
                v = v[:1000] + "...[truncated]"
            print(f"    {k}: {v}")

        if step_state.get("_stop"):
            print("\n❗️ Process halted due to configuration error.\n")
            print(step_state.get('error', ''))
            break

    if final_state and not final_state.get("_stop"):

        if final_state["user_feedback"].get("user_decision") == "end":
            print(f"final_state:{final_state}")
            summary = final_state["user_feedback"].get("summary")
        else:
            summary = None
        print("\n✅ Final Output:\n", summary or "No output.")

        if final_state.get("error"):
            ans = input("The code execution returned an error. Retry debugging? (yes/no)\n> ")
            if ans.strip().lower().startswith('y'):
                interactive_ui()

    if final_state:
        with open('agent_trace.json', 'w', encoding='utf-8') as f:
            json.dump(state.get('trace', []), f, ensure_ascii=False, indent=2)
        print("\n📂 Trace saved to agent_trace.json.")


if __name__ == '__main__':
    interactive_ui()
