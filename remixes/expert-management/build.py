"""Package five existing remixes for the WorkBuddy expert resource uploader."""
import json, zipfile, hashlib
from pathlib import Path
BASE=Path(__file__).resolve().parent
REMIX=BASE.parent
AIGC=REMIX/'AIGC_三圣专家团'
ITEMS=[('cfo-zhao-gongming','CFO 赵公明','首席财务官','CFO_赵公明','企业财务助理：现金流、预算、报表、税务与经营决策。'),('cho-zhang-yazi','CHO 张亚子','首席人力资源官兼行政负责人','CHO_张亚子','人力资源、行政运营与组织发展助手。'),('guan-hanqing','剧本 关汉卿','剧本专家与制作统筹',None,'为个人与企业自媒体创作连载、小剧场，兼任三圣专家团制作统筹。'),('wu-daozi','分镜 吴道子','视觉资产与分镜专家',None,'为连载、小剧场和短片设计角色、场景、美术资产与可执行分镜。'),('li-bai','提示词 李白','提示词与 ComfyUI 制作专家',None,'把想法与分镜转成提示词，适配自有 ComfyUI 并交付成片工程。')]
SKILLS={
'finance-ops-portable':('基于用户提供的财务导出制作 CFO 简报、现金流和场景分析。','读取用户授权的利润表、资产负债表、现金流、总账或 CSV；只有利润表也可开始，但明确缺失口径。统一期间、币种、科目与收付/权责口径，记录映射。核算收入、毛利、净利、应收应付、净烧钱率、现金安全垫与 runway；分母无效不硬算。逐项追溯异常至交易。按已有历史比较环比，缺历史不编造。输出管理层摘要、指标表、差异原因、风险与行动项；12 个月基准/上行/下行情景给出驱动因素和敏感性。预算阈值采用公司明确标准，建议值标假设。使用已安装的文件/计算工具，没有工具时交公式和待计算表，不宣称已运行。无遥测、联网更新、QuickBooks API 或外部脚本前置；不代替审批、过账或付款。'),
'hr-admin-portable':('制作岗位画像、招聘面试材料、入职清单和人事行政台账。','岗位画像记录业务目标、职责、必备/加分项、能力维度和成功标准。招聘包按需提供 JD、结构化面试题、STAR 证据及评分锚点；仅据岗位相关事实评估，最终录用由人决定。Offer 是待审批草案，劳动条款需按主体、工作地与当前官方规则核实，不写固定普适法律数字。入职清单覆盖预入职、首日、首周、30/60/90 天、负责人、期限、证明文件与完成状态；权限开通仅列待审批项，不自动执行。行政台账覆盖设备、资产借还、供应商、办公费用和待办。人力报表包含人员口径、入离职、招聘漏斗和培训/绩效汇总；敏感数据最小化、脱敏且限定授权范围。未接入 HR/招聘服务时用用户导出，不自动请求外部服务。'),
'office-tables-portable':('处理财务、人事和行政 CSV/表格台账，保留公式、口径与审计轨迹。','只读取用户指定文件，先识别表头、日期、金额、编码、主键和缺失值；原件只读，结果另存。保留身份证/工号等前导零；金额计算区分币种和税前税后，汇总与明细对账。写出公式和来源范围，不能把未计算公式缓存当结果。已有本地表格工具可用才生成并复读 XLSX；缺环境时交 UTF-8 CSV、公式说明及待处理项，不自动安装工具。输出数据字典、清洗记录、异常清单与汇总，避免无声删除行或覆盖原始数据。')}
def front(name,description):
    return '---\nname: '+name+'\ndescription: '+json.dumps(description,ensure_ascii=False)+'\n---\n\n'
def build():
    records=[]
    for slug,name,profession,folder,desc in ITEMS:
        files={}
        if folder:
            raw=(REMIX/folder/'system_prompt.md').read_text()
            parts=raw.split('\n\n')
            raw='\n\n'.join(parts[2:])
            identity='我是 CHO 张亚子（文昌帝君）' if slug.startswith('cho') else '我是 CFO 赵公明'
            raw=f'你的专业对话身份为“{identity}”。保留角色设定，但不冒充历史人物本人，也不隐瞒 AI 身份。\n\n'+raw
            skills=['finance-ops-portable','office-tables-portable'] if slug.startswith('cfo') else ['hr-admin-portable','office-tables-portable']
            for skill in skills:
                description,body=SKILLS[skill]
                files[f'skills/{skill}/SKILL.md']=(front(skill,description)+body+'\n').encode()
            raw+='\n\n## 随包技能\n按需读取 '+ '、'.join('skills/'+s+'/SKILL.md' for s in skills)+'。这些是便携流程，不宣称保留旧平台市场技能的程序实现。\n'
            avatar=REMIX/folder/'avatar.jpg'
        else:
            raw=(AIGC/'publication'/f'{slug}-system.md').read_text()
            skills=['aigc-story-production','aigc-visual-storyboard','aigc-comfyui-delivery'] if slug=='guan-hanqing' else ['aigc-visual-storyboard'] if slug=='wu-daozi' else ['aigc-comfyui-delivery']
            for skill in skills:
                files[f'skills/{skill}/SKILL.md']=(AIGC/'skills'/skill/'SKILL.md').read_bytes()
            avatar=AIGC/'avatars'/f'{slug}.jpg'
        files[f'agents/{slug}.md']=(front(slug,desc)+raw).encode()
        files['avatars/avatar.jpg']=avatar.read_bytes()
        manifest={'name':slug,'version':'1.0.0','description':desc,'agents':[f'./agents/{slug}.md'],'skills':['./skills'],'expertType':'agent','agentName':slug,'displayName':{'zh':name,'en':name},'profession':{'zh':profession,'en':profession},'displayDescription':{'zh':desc,'en':desc},'avatar':'avatars/avatar.jpg','plugin':slug}
        files['.codebuddy-plugin/plugin.json']=json.dumps(manifest,ensure_ascii=False,indent=2).encode()
        package=BASE/(slug+'.zip')
        with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
            for path,data in files.items(): z.writestr(path,data)
        with zipfile.ZipFile(package) as z: assert z.testzip() is None
        records.append({'slug':slug,'name':name,'description':desc,'skills':skills,'package':package.name,'sha256':hashlib.sha256(package.read_bytes()).hexdigest(),'bytes':package.stat().st_size,'source_folder':folder or 'AIGC_三圣专家团','status':'prepared'})
    (BASE/'packages.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(records,ensure_ascii=False,indent=2))
if __name__=='__main__': build()
