# Story AR RFC

根据业务需求、PRD、IR/SR/AR或代码资料，自动编写可供评审的RFC技术方案，输出Markdown。项目包含完整的AI Skill、原始RFC模板、评分细则，以及仅依赖Python标准库的生成和检查工具。

设计质量、文档质量、测试设计质量沿用Story DOCX版同版评分标准。RFC版按自己的章节落实要求，保留模板结构及接口表格。

## 能做什么

- 从用户角色、场景、痛点和价值出发，明确目标与非目标。
- 说明现有代码架构与方案的关系，形成模块、接口、数据、性能和异常设计。
- 覆盖ICSL安全设计、日志/监控/追踪、部署/升级/回滚、健康检查及运维说明。
- 给出扩展方向、兼容策略和有效测试用例，说明测试门禁与验收判据。
- 按原模板生成六大章节、实际API小节和附录，保留原五列/四列接口表模式。

AI负责理解需求和编写设计；Python脚本负责套用结构及检查。脚本自身不会调用模型API，也不会根据一段需求自动推理完整方案。结构自测不代表业务设计、评分或ICSL认证通过。

## 目录

```text
story-ar-rfc/
├── SKILL.md                       # AI Skill入口
├── agents/openai.yaml             # 展示与调用配置
├── assets/
│   ├── reference.md               # 原始RFC提案模板
│   └── manifest.json              # 模板及评分文件的SHA-256
├── references/
│   ├── design-quality.md          # 与DOCX版一致的完整评分细则
│   ├── rfc-map.md                 # 评分与RFC章节映射
│   └── payload-contract.md        # 生成输入说明
├── scripts/rfc_md.py              # 生成、检查和结构自测
├── examples/request.md            # 可直接交给AI的需求示例
├── .gitattributes                 # 换行与指纹文件保护
└── .gitignore                     # 排除生成物和本地缓存
```

## 使用Skill

把本项目作为完整Skill交给支持本地Skill的AI工具，入口为[SKILL.md](SKILL.md)。安装或复制时保留`agents`、`assets`、`references`和`scripts`目录，不只复制入口文件。

在Codex中调用：

```text
使用 $story-ar-rfc，根据我提供的需求与代码资料，按RFC模板自动编写Markdown技术方案。
评分标准与Story DOCX版一致；明确设计假设和未解决问题，直接给我RFC文件。
```

DSH中使用`/story-ar-rfc`。可从[示例需求](examples/request.md)开始，也可指定自己的需求文件与代码仓库。缺少实际作者、issue/PR或审批信息时按草案处理，不填造信息。

## 运行生成工具

需要Python **3.10及以上**，无需安装第三方Python库。在项目根目录执行下列命令，`python`应为本机已确认可用的解释器；在Codex等提供依赖工具的环境中使用其返回的解释器路径。

查看模板结构和指纹、运行结构自测：

```shell
python scripts/rfc_md.py inspect
python scripts/rfc_md.py selftest --work-dir work/selftest
```

根据[输入约定](references/payload-contract.md)，由AI把设计整理到`work/rfc-payload.json`，然后生成并检查：

```shell
python scripts/rfc_md.py build --input work/rfc-payload.json --output outputs/example_RFC.md
python scripts/rfc_md.py check --input work/rfc-payload.json --doc outputs/example_RFC.md --report work/structural-check.json
```

重复生成已有文件时，确认要更新后给`build`加`--overwrite`。输出文件不能覆盖Skill内部资产、规则或输入文件。`check`不通过时返回非零退出码，并在报告中给出结构问题。

无真实issue/PR的草案可通过结构检查，但`review_ready`为`false`；正式提审前需补齐。最终还要核对需求覆盖、图文一致性、接口可实施性、测试可观测性及可复现性。

## 评分标准

完整规则见[设计与评分要求](references/design-quality.md)，落章方式见[RFC章节映射](references/rfc-map.md)。

- 设计质量：A需求满足、B方案可行、C易用性、D DFX、E扩展性。
- 文档质量：2.1要素完整、2.2易于理解。
- 测试设计质量：正常、异常与边界、参数组合或不变量，以及性能/兼容/组件协作。
- 设计质量与测试设计质量各使用0%、30%、60%、80%、100%五档，80%档保留评分原文“第二档前提”；综合举证质量扣档最多向下两档。
- Top2是评审选样规则，不要求一次生成两篇。未定义维度权重，不合并虚构总分。

## 维护模板与规则

`assets/reference.md`和`references/design-quality.md`按原始字节计算指纹。`.gitattributes`对这两个文件禁用Git文本换行转换，使跨平台检出后仍可通过校验。不要移除这两条规则，或让编辑器自动转换这两个文件的换行。

更新RFC模板时，核对章节、接口表头及生成映射，再更新资产清单并运行自测；只替换SHA不能完成模板适配。更新评分时，从DOCX版同步整份`design-quality.md`，确认条款一致并更新清单中的SHA。生成物和工作记录保存在`work/`与`outputs/`，已列入忽略规则。

## 上传GitHub

建议仓库名为`story-ar-rfc`。上传本项目根目录中的文件与子目录，包括`.gitignore`和`.gitattributes`，使仓库根目录直接包含`README.md`和`SKILL.md`。

使用Git上传时，在项目根目录执行：

```shell
git init -b main
git add .
git commit -m "Add RFC design skill"
git remote add origin <你的GitHub仓库地址>
git push -u origin main
```

已有本地仓库可跳过初始化；已有origin时使用自己的远端配置。ZIP包不包含`.git`目录，解压后也可通过GitHub网页上传源文件。
