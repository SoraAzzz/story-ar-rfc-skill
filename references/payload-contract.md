# RFC生成输入

生成脚本使用标准库。模型撰写JSON，顶层恰为title、metadata、sections、apis。脚本不生成业务设计，也不自动打分。

- title：非空实际提案标题，替换模板首行。
- metadata：status、authors、created、updated、issue_pr五个非空字符串。状态仅可Draft/Reviewing/Approved/Rejected/Superseded，依据真实状态填写；日期使用真实YYYY-MM-DD，updated不得早于created。未提供作者可写“未提供”；缺少真实issue/PR只能以Draft生成，issue_pr写“待关联（正式提审前补齐）”。不借模板中的#123造链接。
- sections：恰好包含rfc-map.md中的16个键，每个值为非空Markdown正文，不含模板填写指令和xxx/TODO/TBD/单独省略号。可以包含说明性子标题、列表、Mermaid、示例代码和真实引用；不重复模板固定标题，不插入新顶级章，不自行添加Markdown表格。
- apis：实际API列表，可为空；为空时sections.interfaces必须具体说明不涉及原因与边界。有API时，每项恰好包含name、description、prototype、inputs、returns、errors、constraints、changes、example。

API中除inputs/returns外均为非空字符串；name不写换行、手工序号或Markdown标题。description为接口含义；prototype为可实现的签名或HTTP方法/路径；errors列实际错误码、检测条件及恢复；constraints说明鉴权、超时、幂等、并发、限制和版本等适用约束；changes解释新增/修改/删除及影响；example给可用参考调用代码或方法并说明必要前置。

inputs是五列二维字符串数组，returns是四列二维字符串数组。两者至少一行，全部单元格非空；没有入参/返回值时填一行不涉及说明，如inputs为[["不涉及","输入","不适用","此方法无入参","不适用"]]。表头由脚本从原模板读取，不由payload更改。单元格可含竖线，脚本负责转义；换行转为HTML br，其他Markdown按需转义。

API完整结构示意（不是完整可运行payload）：

```json
{
  "name": "查询任务列表",
  "description": "按当前可信租户查询任务。",
  "prototype": "GET /api/v1/tasks",
  "inputs": [["limit","输入","integer","可选；缺省20","1至100"]],
  "returns": [["items","Task[]","当前租户任务","0至limit条"]],
  "errors": "401未认证；403无权限；400参数错误；503依赖超时。",
  "constraints": "只读；租户从可信身份获取；仓储预算1秒。",
  "changes": "拟新增接口；现有接口保持原行为。",
  "example": "GET /api/v1/tasks?limit=20，携带已有认证凭据。"
}
```

build拒绝覆盖已有输出，显式--overwrite才可更新；输出须为.md，不能覆盖payload、模板或包内规则。check比对payload期望内容、模板结构、表头、元信息、围栏和明显占位符；没有业务需求推理或评分能力。缺issue/PR的Draft可通过结构检查，但报告review_ready为false，不能据此正式提审。

inspect输出模板和评分SHA与固定章节；selftest以结构夹具验证0/1/3个API、表格转义、模板指纹和非法输入，不代表真实业务评审通过。自检证据、来源、图源和JSON仅保存在工作目录。
