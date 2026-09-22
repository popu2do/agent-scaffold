"""
飞书日报自动推送脚本

使用 Playwright 自动化填写并提交飞书日报。

使用方式:
    # 首次运行，手动登录（会保存登录状态）
    python push_feishu_daily.py --login

    # 推送日报
    python push_feishu_daily.py --today "今日工作内容" --tomorrow "明日计划"

    # 使用不同的 ruleId
    python push_feishu_daily.py --rule-id "其他ruleId" --today "内容" --tomorrow "计划"

    # 从文件读取内容推送
    python push_feishu_daily.py --today-file today.txt --tomorrow-file tomorrow.txt

    # 包含需要协调的内容
    python push_feishu_daily.py --today "今日内容" --tomorrow "明日计划" --help-needed "需要协调的事项"

依赖安装:
    pip install playwright
    playwright install chromium
"""

import argparse
import os
import sys
import time
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

# 默认 ruleId（可通过 --rule-id 参数覆盖）
# 默认 ruleId（可通过环境变量 FEISHU_DAILY_RULE_ID 或 --rule-id 参数覆盖）
USER_RULEID = os.getenv("FEISHU_DAILY_RULE_ID", "")

# 浏览器用户数据目录（用于保存登录状态）
USER_DATA_DIR = Path(__file__).parent / ".tmp" / ".feishu_browser_data"


def get_report_url(rule_id: str) -> str:
    """根据 ruleId 生成日报页面 URL"""
    return f"https://oa.feishu.cn/report/record/detail?lang=zh-CN&open_in_browser=true&ruleId={rule_id}"


def ensure_browser_data_dir() -> None:
    """确保浏览器数据目录存在"""
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)


def login_and_save_session(rule_id: str = USER_RULEID) -> None:
    """
    手动登录飞书并保存会话。
    首次使用时运行此函数，扫码登录后会话会被保存。

    Args:
        rule_id: 日报规则 ID
    """
    ensure_browser_data_dir()

    print("=" * 50)
    print("飞书登录模式")
    print("=" * 50)
    print("浏览器将打开飞书登录页面，请扫码登录。")
    print("登录成功后，关闭浏览器窗口即可保存会话。")
    print("=" * 50)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=False,
            locale="zh-CN",
            viewport={"width": 1280, "height": 800},
        )

        page = context.new_page()
        page.goto(get_report_url(rule_id))

        print("\n请在浏览器中完成登录...")
        print("登录成功后，请手动关闭浏览器窗口。\n")

        try:
            page.wait_for_event("close", timeout=300000)
        except Exception:
            pass

        context.close()

    print("✅ 登录会话已保存！")
    print(f"   数据目录: {USER_DATA_DIR}")


def fill_editor(page, editor_index: int, content: str) -> None:
    """
    填充飞书富文本编辑器。

    Args:
        page: Playwright 页面对象
        editor_index: 编辑器索引（0=今日总结, 1=明日计划, 2=需要协调）
        content: 要填充的内容
    """
    editors = page.locator(".editor-kit-container")

    editor = editors.nth(editor_index)
    editor.click()
    time.sleep(0.3)

    page.keyboard.press("Control+a")
    time.sleep(0.1)

    lines = content.strip().split("\n")
    for index, line in enumerate(lines):
        page.keyboard.type(line, delay=10)
        if index < len(lines) - 1:
            page.keyboard.press("Enter")

    time.sleep(0.2)


def submit_report(
    today_content: str,
    tomorrow_content: str,
    help_needed: str = "",
    rule_id: str = USER_RULEID,
) -> bool:
    """
    提交飞书日报。

    Args:
        today_content: 今日总结内容
        tomorrow_content: 明日计划内容
        help_needed: 需要协调与帮助的内容（可选）
        rule_id: 日报规则 ID（可选）

    Returns:
        bool: 是否提交成功
    """
    ensure_browser_data_dir()

    if not USER_DATA_DIR.exists() or not any(USER_DATA_DIR.iterdir()):
        print("❌ 错误: 未找到登录会话！")
        print("   请先运行: python push_feishu_daily.py --login")
        return False

    print("=" * 50)
    print("飞书日报推送")
    print("=" * 50)
    print(
        f"今日总结: {today_content[:50]}..."
        if len(today_content) > 50
        else f"今日总结: {today_content}"
    )
    print(
        f"明日计划: {tomorrow_content[:50]}..."
        if len(tomorrow_content) > 50
        else f"明日计划: {tomorrow_content}"
    )
    if help_needed:
        print(
            f"需要协调: {help_needed[:50]}..."
            if len(help_needed) > 50
            else f"需要协调: {help_needed}"
        )
    print("=" * 50)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=False,
            locale="zh-CN",
            viewport={"width": 1280, "height": 800},
        )

        page = context.new_page()

        try:
            print("📄 正在打开日报页面...")
            page.goto(get_report_url(rule_id), wait_until="networkidle", timeout=30000)
            time.sleep(2)

            if "passport" in page.url or "login" in page.url.lower():
                print("❌ 登录已过期，请重新运行: python push_feishu_daily.py --login")
                context.close()
                return False

            print("✏️ 正在填写今日总结...")
            fill_editor(page, 0, today_content)

            print("✏️ 正在填写明日计划...")
            fill_editor(page, 1, tomorrow_content)

            if help_needed:
                print("✏️ 正在填写需要协调内容...")
                fill_editor(page, 2, help_needed)

            print("🚀 正在提交日报...")

            submit_button = page.locator('button:has-text("提交")')
            submit_button.click()

            time.sleep(3)

            print("✅ 日报提交成功！")

            context.close()
            return True

        except PlaywrightTimeoutError as exc:
            print(f"❌ 超时错误: {exc}")
            context.close()
            return False
        except Exception as exc:
            print(f"❌ 发生错误: {exc}")
            context.close()
            return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="飞书日报自动推送脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 首次登录
  python push_feishu_daily.py --login

  # 直接输入内容推送
  python push_feishu_daily.py --today "完成了XXX功能开发" --tomorrow "继续优化YYY模块"

  # 从文件读取内容
  python push_feishu_daily.py --today-file today.txt --tomorrow-file tomorrow.txt
        """,
    )

    parser.add_argument(
        "--login", action="store_true", help="登录模式：打开浏览器扫码登录"
    )
    parser.add_argument(
        "--rule-id",
        type=str,
        default=USER_RULEID,
        help=f"日报规则 ID（默认: {USER_RULEID}）",
    )
    parser.add_argument("--today", type=str, help="今日总结内容")
    parser.add_argument("--tomorrow", type=str, help="明日计划内容")
    parser.add_argument("--today-file", type=str, help="从文件读取今日总结")
    parser.add_argument("--tomorrow-file", type=str, help="从文件读取明日计划")
    parser.add_argument(
        "--help-needed", type=str, default="", help="需要协调与帮助的内容"
    )

    args = parser.parse_args()

    if not args.rule_id:
        print("❌ 错误: 未指定 ruleId！请通过环境变量 FEISHU_DAILY_RULE_ID 或 --rule-id 参数指定。")
        sys.exit(1)

    if args.login:
        login_and_save_session(args.rule_id)
        return

    today_content = args.today
    if args.today_file:
        today_path = Path(args.today_file)
        if not today_path.exists():
            print(f"❌ 文件不存在: {args.today_file}")
            sys.exit(1)
        today_content = today_path.read_text(encoding="utf-8")

    tomorrow_content = args.tomorrow
    if args.tomorrow_file:
        tomorrow_path = Path(args.tomorrow_file)
        if not tomorrow_path.exists():
            print(f"❌ 文件不存在: {args.tomorrow_file}")
            sys.exit(1)
        tomorrow_content = tomorrow_path.read_text(encoding="utf-8")

    if not today_content:
        print("❌ 错误: 今日总结是必填项！")
        print("   使用 --help 查看帮助信息")
        sys.exit(1)

    if not tomorrow_content:
        tomorrow_content = ""

    success = submit_report(
        today_content, tomorrow_content, args.help_needed, args.rule_id
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
