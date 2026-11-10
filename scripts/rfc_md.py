#!/usr/bin/env python3
"""Assemble and structurally check RFC Markdown. Python 3.10+, standard library.

Business reasoning, quality scoring and review remain the author's responsibility.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import re
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLOTS = {
    '1.1 简介':'intro', '1.2 动机':'motivation', '1.3 目标':'goals',
    '2. 用例分析':'use_cases', '3.1 总体方案':'overall', '3.2 技术选型':'alternatives',
    '3.3 功能与性能设计':'function_performance', '3.4 安全隐私与DFX设计':'dfx',
    '3.5 编程与调用设计':'programming', '3.5.1 编程模型基本设计':'programming_model',
    '3.5.2 接口定义和设计':'interfaces', '3.5.3 编程手册设计':'programming_manual',
    '4. 缺点和 风险':'risks', '5. 现有技术':'prior_art', '6. 未解决问题':'open_questions',
}
SECTION_KEYS = set(SLOTS.values()) | {'appendix'}
META = {'status','authors','created','updated','issue_pr'}
API = {'name','description','prototype','inputs','returns','errors','constraints','changes','example'}

def require(condition, message):
    if not condition:
        raise ValueError(message)

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def assets():
    manifest = read_json(ROOT/'assets/manifest.json')
    for name, expected in manifest['sha256'].items():
        require(digest(ROOT/name)==expected, f'Asset fingerprint changed: {name}. Inspect and adapt mapping before building.')
    source = (ROOT/'assets/reference.md').read_text(encoding='utf-8-sig')
    headings = re.findall(r'^(#{1,6}) (.+)$', source, re.M)[1:]
    fixed = [(marks, title) for marks,title in headings if not title.startswith('3.5.2.')]
    require(set(SLOTS) <= {t for _,t in fixed}, 'Template headings no longer match RFC slots')
    require({t for _,t in fixed} == set(SLOTS)|{'1. 概述','3. 方案设计'}, 'Unexpected template heading; adapt mapping')
    headers = []
    for line in source.splitlines():
        if re.match(r'^\s*\| 参数名称 \|', line):
            headers.append([x.strip() for x in line.strip().strip('|').split('|')])
    require([len(h) for h in headers]==[5,4], 'Expected original API five/four column tables')
    return fixed, headers, manifest

def outside_fences(text):
    marker = None
    for line in text.splitlines():
        match = re.match(r'^\s*(`{3,}|~{3,})(.*)$', line)
        if match:
            fence, rest = match.groups()
            if marker is None:
                marker = fence
            elif fence[0]==marker[0] and len(fence)>=len(marker) and not rest.strip():
                marker = None
            continue
        if marker is None:
            yield line
    require(marker is None, 'Unclosed Markdown fence')

def content(value, label):
    require(isinstance(value,str) and value.strip(), f'{label}: nonempty text required')
    require(value.strip() not in {'无','同上','待补充'}, f'{label}: substantive explanation required')
    require(not re.search(r'(?i)(?<![\w])(?:xxx|TODO|TBD|Your_community)(?![\w])|YYYY-MM-DD', value), f'{label}: unresolved template placeholder')
    require(not re.search(r'^\s*(?:\.{3}|…|\.\.\.)\s*$', value, re.M), f'{label}: standalone ellipsis')

def rows(values, count, label):
    require(isinstance(values,list) and values, f'{label}: at least one row, including reason if not applicable')
    for row in values:
        require(isinstance(row,list) and len(row)==count, f'{label}: expected {count} columns')
        for cell in row:
            content(cell,label)

def validate(payload, headings):
    require(isinstance(payload,dict) and set(payload)=={'title','metadata','sections','apis'}, 'Expected title, metadata, sections, apis')
    content(payload['title'],'title')
    require('\n' not in payload['title'] and not payload['title'].startswith('#'), 'Title must be one plain line')
    meta = payload['metadata']
    require(isinstance(meta,dict) and set(meta)==META, 'Unexpected metadata keys')
    for key,value in meta.items():
        content(value,'metadata.'+key)
        require('\n' not in value, 'Metadata values must be single line')
    require(meta['status'] in {'Draft','Reviewing','Approved','Rejected','Superseded'}, 'Invalid RFC status')
    for key in ('created','updated'):
        require(re.fullmatch(r'\d{4}-\d{2}-\d{2}',meta[key]), f'{key}: YYYY-MM-DD required')
        date.fromisoformat(meta[key])
    require(meta['updated']>=meta['created'], 'updated precedes created')
    pending = bool(re.search(r'待关联|未提供|待确认',meta['issue_pr']))
    require(not pending or meta['status']=='Draft', 'Missing issue/PR: Draft only until association is supplied')
    sections = payload['sections']
    require(isinstance(sections,dict) and set(sections)==SECTION_KEYS, 'Missing or unknown sections')
    levels = {SLOTS[t]:len(m) for m,t in headings if t in SLOTS}
    levels['appendix']=1
    fixed = {t for _,t in headings}
    for key,body in sections.items():
        content(body,'sections.'+key)
        for line in outside_fences(body):
            require(not re.match(r'^\s*\|',line), f'{key}: extra tables forbidden; use original API tables')
            match = re.match(r'^(#{1,6})\s+(.+)$',line)
            if match:
                require(len(match[1])>levels[key] and match[2] not in fixed, f'{key}: heading changes template hierarchy')
    require(isinstance(payload['apis'],list), 'apis must be a list')
    names=[]
    for api in payload['apis']:
        require(isinstance(api,dict) and set(api)==API, 'Unexpected API fields')
        for key in API-{'inputs','returns'}:
            content(api[key],'api.'+key)
            list(outside_fences(api[key]))
            require(not re.search(r'^#{1,6}\s|^\s*\|',api[key],re.M), 'API text cannot inject headings or tables')
        require('\n' not in api['name'] and not re.match(r'^\d+[.、]',api['name']), 'API name must omit numbering')
        rows(api['inputs'],5,'inputs'); rows(api['returns'],4,'returns')
        names.append(api['name'])
    require(len(set(names))==len(names), 'Duplicate API name')

def table(headers, values):
    def escape(text):
        return text.replace('\\','\\\\').replace('|','\\|').replace('\r\n','\n').replace('\r','\n').replace('\n','<br>')
    return '\n'.join('| '+' | '.join(escape(c) for c in row)+' |' for row in [headers,['---']*len(headers),*values])

def render(payload, headings, headers):
    meta=payload['metadata']
    parts=['# '+payload['title'],f"状态（Stutus）：{meta['status']}",f"作者（Authors）：{meta['authors']}",
           f"创建日期（Created）：{meta['created']}",f"更新日期（Updated）：{meta['updated']}",
           f"相关issue/PR：{meta['issue_pr']}",'------']
    for marks,title in headings:
        parts.append(marks+' '+title)
        if title in SLOTS:
            key=SLOTS[title]
            parts.append(payload['sections'][key].strip())
            if key=='interfaces':
                for i,api in enumerate(payload['apis'],1):
                    parts.extend([f"#### 3.5.2.{i} {api['name']}",'- 接口描述：'+api['description'],
                                  '- 接口原型：'+api['prototype'],'- 输入/输出参数：',table(headers[0],api['inputs']),
                                  '- 返回参数：',table(headers[1],api['returns']),'- 异常处理：'+api['errors'],
                                  '- 约束说明：'+api['constraints'],'- 变更说明：'+api['changes'],
                                  '- 调用参考代码：\n\n'+api['example']])
    parts.extend(['------','附录',payload['sections']['appendix'].strip()])
    return '\n\n'.join(parts)+'\n'

def build(payload_path, output, overwrite=False):
    headings,headers,_=assets()
    payload=read_json(payload_path); validate(payload,headings)
    require(output.suffix.lower()=='.md','Output must be Markdown .md')
    require(not output.resolve().is_relative_to(ROOT.resolve()),'Output cannot overwrite files within the skill package')
    require(output.resolve()!=payload_path.resolve(),'Output cannot overwrite payload')
    require(overwrite or not output.exists(),'Output exists; use --overwrite intentionally')
    result=render(payload,headings,headers)
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',newline='\n',dir=output.parent,delete=False) as temp:
        temporary=Path(temp.name); temp.write(result)
    try:
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return {'output':str(output.resolve()),'sha256':digest(output)}

def check(payload_path, document):
    headings,headers,_=assets()
    payload=read_json(payload_path); validate(payload,headings)
    actual=document.read_text(encoding='utf-8-sig')
    issues=[]
    if actual!=render(payload,headings,headers):
        issues.append('Document differs from expected template structure or authored payload')
    try:
        list(outside_fences(actual))
    except ValueError as exc:
        issues.append(str(exc))
    pending=bool(re.search(r'待关联|未提供|待确认',payload['metadata']['issue_pr']))
    return {'structural_pass':not issues,'issues':issues,'api_count':len(payload['apis']),
            'review_ready':not issues and not pending and payload['metadata']['status']=='Reviewing',
            'warnings':['issue/PR待关联，正式提审前补齐'] if pending else [],
            'scope':'Structural and metadata checks only; no semantic, ICSL, scoring or approval certification.'}

def selftest(work_dir):
    work_dir.mkdir(parents=True,exist_ok=True)
    headings,_,_=assets()
    fixture={'title':'RFC结构自测','metadata':{'status':'Draft','authors':'未提供','created':'2026-11-10','updated':'2026-11-10','issue_pr':'待关联（正式提审前补齐）'},
             'sections':{k:'不涉及：本节用于结构自测，不代表业务方案；正式设计应根据需求填写。' for k in SECTION_KEYS},'apis':[]}
    api={'name':'结构自测接口','description':'测试接口模式保留。','prototype':'GET /fixture',
         'inputs':[['value','输入','string','A|B\n可选','a或b']], 'returns':[['ok','boolean','结构校验响应','true/false']],
         'errors':'400：非法输入。','constraints':'仅供临时结构自测。','changes':'测试夹具。','example':'GET /fixture?value=a'}
    checks=0
    with tempfile.TemporaryDirectory(dir=work_dir,prefix='rfc-selftest-') as folder:
        for count in (0,1,3):
            payload=copy.deepcopy(fixture)
            payload['apis']=[dict(copy.deepcopy(api),name=f'结构自测接口{i}') for i in range(count)]
            source=Path(folder)/'payload.json'; source.write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8')
            output=Path(folder)/f'fixture-{count}.md'
            build(source,output)
            require(check(source,output)['structural_pass'],'build/check selftest failed')
            require(not check(source,output)['review_ready'],'Draft incorrectly marked ready')
            if count:
                require('A\\|B<br>可选' in output.read_text(encoding='utf-8'),'Table escaping failed')
            output.write_text(output.read_text(encoding='utf-8')+'\n# 意外新增章\n',encoding='utf-8')
            require(not check(source,output)['structural_pass'],'Template drift not detected')
            checks+=1
        for mutate in (lambda p:p['sections'].pop('dfx'), lambda p:p['sections'].update(intro='TODO'),
                       lambda p:p['sections'].update(intro='| 新表 |'),lambda p:p['metadata'].update(status='Reviewing')):
            payload=copy.deepcopy(fixture); mutate(payload)
            try:
                validate(payload,headings)
            except ValueError:
                checks+=1
            else:
                raise ValueError('Invalid fixture was accepted')
    return {'selftest_pass':True,'cases':checks,'scope':'Structural fixtures only, not business validation.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    commands.add_parser('inspect')
    sub=commands.add_parser('selftest'); sub.add_argument('--work-dir',type=Path,default=Path('work/rfc-selftest'))
    for cmd in ('build','check'):
        sub=commands.add_parser(cmd); sub.add_argument('--input',type=Path,required=True)
        if cmd=='build':
            sub.add_argument('--output',type=Path,required=True); sub.add_argument('--overwrite',action='store_true')
        else:
            sub.add_argument('--doc',type=Path,required=True); sub.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    if args.command=='inspect':
        headings,headers,manifest=assets(); result={'headings':headings,'section_keys':sorted(SECTION_KEYS),'api_headers':headers,**manifest}
    elif args.command=='selftest':
        result=selftest(args.work_dir)
    elif args.command=='build':
        result=build(args.input,args.output,args.overwrite)
    else:
        require(not args.report.resolve().is_relative_to(ROOT.resolve()), 'Report cannot overwrite skill package files')
        require(args.report.resolve() not in {args.input.resolve(),args.doc.resolve()}, 'Report cannot overwrite payload or RFC')
        result=check(args.input,args.doc); args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
    return 1 if result.get('structural_pass') is False else 0

if __name__=='__main__':
    try:
        sys.exit(main())
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr);sys.exit(2)
