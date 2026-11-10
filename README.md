# RFC 设计文档生成 Skill

根据需求文档和代码，按 RFC 模板生成 Markdown 技术方案设计文档。

## 安装

将整个 `story-ar-rfc` 文件夹放入 AI 工具的 Skills 目录，保留内部所有文件。

Codex 的安装位置：

```text
~/.codex/skills/story-ar-rfc/
```

运行环境：Python 3.10 及以上，无需安装第三方 Python 库。

## 使用

提供需求文字、PRD 文件或代码仓库路径，然后输入：

```text
使用 $story-ar-rfc，根据以下需求和代码编写 RFC 技术方案，输出到 outputs/需求_RFC.md。

需求：描述要解决的问题，或填写需求文件路径。
代码：填写相关代码仓库路径；没有代码可省略。
```

DSH 中将 `$story-ar-rfc` 换成 `/story-ar-rfc`。

生成结果为 `.md` 文件。可参考[示例需求](examples/request.md)。

## 检查安装

在本项目根目录执行：

```shell
python scripts/rfc_md.py selftest --work-dir work/selftest
```

输出 `selftest_pass: true` 表示生成工具自测通过。
