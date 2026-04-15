from pathlib import Path

def collect_input_files(folder, extensions):
    """返回 folder 下所有扩展名在 extensions 中的文件（不递归子文件夹）。"""
    return [f for f in sorted(folder.iterdir()) if f.is_file() and f.suffix.lower() in extensions]


def report_errors(errors, log_path):
    """
    打印失败汇总。
    - errors: [(filename, reason), ...]
    - log_path: 当 errors > 10 时写入的日志路径（传 None 则强制终端输出）
    返回是否写了 log 文件。
    """
    if not errors:
        return False

    THRESHOLD = 10
    print()
    if len(errors) <= THRESHOLD or log_path is None:
        print("失败文件：")
        for name, reason in errors:
            print("  · {} — {}".format(name, reason))
        return False
    else:
        print("失败文件（前 {} 条）：".format(THRESHOLD))
        for name, reason in errors[:THRESHOLD]:
            print("  · {} — {}".format(name, reason))
        remaining = len(errors) - THRESHOLD
        print("  （还有 {} 条，完整列表见 {}）".format(remaining, log_path))
        log_path.write_text(
            "\n".join("{}\t{}".format(name, reason) for name, reason in errors),
            encoding="utf-8",
        )
        return True