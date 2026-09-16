"""Build reviewable WorkBuddy form content, skill archives and provenance. Stdlib only."""
import csv
import hashlib
import json
import sqlite3
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
REPO = BASE.parent.parent
DB = REPO / 'catalog/agency_agents_merged/merged_catalog.db'

AGENTS = [
    ('guan-hanqing', '剧本 关汉卿', '曲圣；连载、小剧场的剧本专家兼制作统筹，让个人与企业自媒体持续更新。',
     '我是剧本 关汉卿（曲圣）。给我一个想法或已有故事，我会按连载、小剧场或短片选择合适流程，先做出能制作的版本。',
     ['aigc-story-production', 'aigc-visual-storyboard', 'aigc-comfyui-delivery']),
    ('wu-daozi', '分镜 吴道子', '画圣；角色美术、场景道具与分镜，守住连载一致性，减少生成返工。',
     '我是分镜 吴道子（画圣）。给我剧本、角色参考或一个画面想法，我来把它拆成可生成、可剪辑的镜头。',
     ['aigc-visual-storyboard']),
    ('li-bai', '提示词 李白', '诗仙·谪仙人；把想法或分镜写成提示词，以自有 ComfyUI 完成生成与本地交付。',
     '我是提示词 李白（诗仙·谪仙人）。给我想法或分镜，以及你已有的 ComfyUI 工作流；我来写提示词、适配生成并核验交付。',
     ['aigc-comfyui-delivery']),
]

SOURCES = [
    ('workbuddy:AiVideoScript', '关汉卿/吴道子/李白', '脚本、镜头描述、画面提示词分层；交付配音字幕文本', '去掉云工具默认适配与固定平台时长'),
    ('workbuddy:NarrativeDesigner', '关汉卿', '人物声线、世界设定、叙事承诺与回收', '去掉游戏引擎、分支游戏规则与错标 anti-distill'),
    ('workbuddy:PromptEngineer', '李白', '具体约束、格式控制、单变量评测和版本追踪', '去掉通用成绩承诺，不外显内部推理链'),
    ('agency_en:academic/academic-narratologist', '关汉卿', '人物欲望与需要、伏笔回收、叙事时间与节奏', '去掉每条建议必须引理论的教学负担'),
    ('agency_en:design/design-visual-storyteller', '吴道子', '视觉情绪弧线、品牌一致性与镜头节奏', '去掉固定机器路径和无依据增长百分比'),
    ('agency_en:project-management/project-management-studio-producer', '关汉卿', '制作范围、资源预算、交付优先级与风险预案', '去掉大制作公司组织、投资回报承诺和供应商流程'),
]

SKILL_SOURCES = [
    ('novel-outline', 'aigc-story-production', '结构化大纲、分集与资产清单', '去除强制确认、长篇爽剧默认规模；无脚本代码复制'),
    ('novel-script', 'aigc-story-production', '动作/对白节拍、估时与上游对账', '去除强制大纲前置、换景免费假设；采用自有 schema'),
    ('novel-characters', 'aigc-visual-storyboard', '身份卡、外观母版、引用与版本', '不携带 Codex imagegen 入口、默认批量出图或运行时'),
    ('novel-art', 'aigc-visual-storyboard', '空间锚点、日夜变体、道具尺度与状态', '不携带可选外部出图；用现有 ComfyUI'),
    ('novel-storyboard', 'aigc-visual-storyboard', '节拍认领、分段、关键帧与批次', '移除 H3 强绑定、15秒硬上限、镜头免费假设和 imagegen'),
]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def body(path):
    text = path.read_text(encoding='utf-8')
    return text.split('---', 2)[2].strip() if text.startswith('---\n') else text.strip()

def build():
    con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    provenance = []
    for agent_id, targets, kept, removed in SOURCES:
        row = dict(con.execute('SELECT * FROM agents WHERE agent_id=?', (agent_id,)).fetchone())
        source = REPO / row['local_agent_path']
        bindings = [dict(x) for x in con.execute('SELECT skill_slug,local_skill_path FROM agent_skills WHERE agent_id=?', (agent_id,))]
        provenance.append(dict(agent_id=agent_id, name=row['name_zh'] or row['name_en'],
            source_path=row['local_agent_path'], source_commit=row['source_commit'], sha256=digest(source),
            targets=targets, retained=kept, discarded=removed, bound_skills=bindings,
            decision='remix-method-only; no original runtime or whole package imported'))
    skill_sources = []
    for slug, target, kept, removed in SKILL_SOURCES:
        source = Path('/Users/wangyao/.codex/skills') / slug / 'SKILL.md'
        skill_sources.append(dict(source_skill=slug, source_locator=f'local-skill:{slug}',
            sha256=digest(source), target_skill=target, retained=kept, discarded=removed,
            source_license='Apache-2.0 declared in source metadata', decision='method-remix; original executable not copied'))
    for slug, path, target, decision in [
        ('novel-writing', 'sources/workbuddy-experts/plugins/narrative-designer/skills/novel-writing/SKILL.md', 'aigc-story-production', 'retain world/foreshadowing state method; do not invent novel CLI'),
        ('prompt-engineer', 'sources/workbuddy-experts/plugins/prompt-engineer/skills/prompt-engineer/SKILL.md', 'aigc-comfyui-delivery', 'retain structured prompt/evaluation/versioning method'),
        ('anti-distill', 'sources/workbuddy-experts/plugins/narrative-designer/skills/anti-distill/SKILL.md', None, 'exclude: actual content is knowledge redaction, mislabelled by parent agent'),
    ]:
        skill_sources.append(dict(source_skill=slug, source_locator=path, sha256=digest(REPO/path), target_skill=target, decision=decision))
    counts = dict(con.execute('SELECT source_id,count(*) FROM agents GROUP BY source_id'))
    con.close()
    write_json(BASE/'provenance.json', dict(catalog_counts=counts, source_agents=provenance, source_skills=skill_sources,
        excluded=['LibTV/Liblib', 'ListenHub', 'ChatCut', 'paid editing and asset services', 'private MCP', '.NET',
                  'original Remotion/HyperFrames runtime packages', 'provider-bound video-prompt agent'],
        packaging='direct self-contained files; no symlink runtime'))
    pub = BASE/'publication'
    pub.mkdir(exist_ok=True)
    rows = []
    for slug, name, description, welcome, skills in AGENTS:
        prompt = body(BASE/'agents'/f'{slug}.md')
        # Embedded skill bodies preserve capability when the web form cannot bind local skills.
        prompt += '\n\n# 随包技能操作规范（已内嵌，可直接执行）\n'
        for skill in skills:
            prompt += f'\n## {skill}\n\n' + body(BASE/'skills'/skill/'SKILL.md') + '\n'
        (pub/f'{slug}-system.md').write_text(prompt, encoding='utf-8')
        fields = dict(name=name, description=description, welcome=welcome, system_prompt=prompt, skills=skills,
                      publication_status='prepared', third_party_connectors=[])
        write_json(pub/f'{slug}-fields.json', fields)
        with zipfile.ZipFile(pub/f'{slug}.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.write(BASE/'agents'/f'{slug}.md', f'agents/{slug}.md')
            for skill in skills:
                archive.write(BASE/'skills'/skill/'SKILL.md', f'skills/{skill}/SKILL.md')
        rows.append(dict(name=name, slug=slug, skills=';'.join(skills), prompt_chars=len(prompt), status='prepared'))
    with (pub/'agent-list.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    if not (pub/'status.json').exists():
        write_json(pub/'status.json', {'agents':{slug:{'name':name,'status':'prepared','id':None} for slug,name,*_ in AGENTS}})
    print(json.dumps({'catalog_counts':counts,'agents':rows,'provenance_agents':len(provenance),'source_skills':len(skill_sources)}, ensure_ascii=False))

if __name__ == '__main__':
    build()
