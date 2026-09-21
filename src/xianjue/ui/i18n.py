"""UI label translations for Chinese interface."""

_LABELS_ZH = {
    "Dashboard": "仪表盘",
    "Translate": "翻译",
    "Vocabulary": "词库",
    "Review": "背单词",
    "History": "历史",
    "Settings": "设置",
    "Source": "原文",
    "Source Text": "原文",
    "Result": "结果",
    "Translating...": "翻译中...",
    "Trigger Settings": "触发设置",
    "Sensitivity:": "灵敏度：",
    "Length:": "长度：",
    "Sensitive (10)": "敏感 (10)",
    "Balanced (30)": "平衡 (30)",
    "Conservative (100)": "克制 (100)",
    "Translation Engine": "翻译引擎",
    "Cloud (DeepSeek)": "云端 (DeepSeek)",
    "Local (Ollama)": "本地 (Ollama)",
    "API Key:": "API 密钥：",
    "Test": "测试",
    "Floating Window": "悬浮窗",
    "Pause countdown on hover": "悬停时暂停倒计时",
    "Hover shows original text": "悬停显示原文",
    "Show original text section (default off)": "显示原文区（默认关）",
    "Pause floating window when main window is active (Focus Mode)": "主界面激活时暂停悬浮窗（聚焦模式）",
    "Language": "语言",
    "UI Language": "系统语言",
    "Chinese": "中文",
    "English": "English",
    "Recent Translations": "最近翻译",
    "Translations": "翻译次数",
    "To Review": "待复习",
    "Day Streak": "连续天数",
    "Word": "单词",
    "Marked": "标记",
    "Context": "上下文",
    "Reps": "复习次数",
    "Next Review": "下次复习",
    "Time": "时间",
    "Engine": "引擎",
    "Due now": "现在复习",
    "Refresh": "刷新",
    "No words due for review.": "没有需要复习的单词。",
}


def tr(text: str, lang: str = "zh") -> str:
    """Translate a UI label based on the language setting."""
    if lang == "zh":
        return _LABELS_ZH.get(text, text)
    return text
