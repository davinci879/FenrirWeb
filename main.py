from flask import Flask,request,session,jsonify,send_from_directory,render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash


from datetime import datetime
import uuid
import os,random
import json
import requests
import re
import pymysql
import time
from flask_cors import CORS
from sqlalchemy import or_
from volcenginesdkarkruntime import Ark
from email.header import Header
from email.mime.text import MIMEText
import smtplib
from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525 import models as dysmsapi_20170525_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient
dates = []
for year in range(2026, 1984, -1):
    if year == 2026:
        for month in range(4, 0, -1):
            month = '%02d' % month
            dates.append(f"{year}{month}")
    else:
        for month in range(12, 0, -1):
            month = '%02d' % month
            dates.append(f"{year}{month}")
def send_email(reciever,captcha):
    try:
        nowtime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
        mail_host="smtp.126.com"  #设置服务器
        mail_user="@126.com"    #用户名
        mail_pass=""
        sender = "FENRIR<@126.com>"
        mail_msg = "<h1>欢迎使用 Fenrir V3.4</h1><p></p><p>Fenrir运维</p>"
        message = MIMEText(mail_msg, 'html', 'utf-8')
        message['From'] ="<@126.com>"
        message['To'] = f"User<{reciever[0]}>"
        message["Cc"] = "back<@126.com>"
        subject = f'{captcha} 是你的验证码'
        message['Subject'] = Header(subject, 'utf-8')
        smtpObj = smtplib.SMTP()
        smtpObj.connect(mail_host,25)    # 25 为 SMTP 端口号
        smtpObj.login(mail_user,mail_pass)
        reciever.append("@126.com")
        smtpObj.sendmail(sender, reciever, message.as_string())
        print(f">> 邮件验证码发送成功 收件人：{reciever[0]} 发送时间:{nowtime}")
    except Exception as e:
        print(f'> {reciever[0]} 邮件发送失败',e)

def ai_doubao(in_txt,model):
    client = Ark(ak="", sk="==")
    try:
        messages =[{"role": "user","content": in_txt}]
        completion = client.chat.completions.create(
            model=model,  
            messages=messages)
        reply = completion.choices[0].message.content
        return reply.replace('```','').replace('json','').strip('\n')
    except Exception as e:
        return f"Error Code 102：API调用失败"
app = Flask(__name__)
app.config['SECRET_KEY'] = ''  # 生产环境中应使用随机生成的密钥
app.config['MYSQL_HOST'] = '127.0.0.1:3306'
app.config['MYSQL_USER'] = ''
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = ''

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_id, username, password_hash):
        self.id = user_id
        self.username = username
        self.password_hash = password_hash
@login_manager.user_loader
def load_user(username):
    # 18cf19c412563831.natapp.cc
    conn = pymysql.connect(host='127.0.0.1', port=3306,user='', password='', database='', charset='utf8')
    cursor = conn.cursor()
    sql = f"SELECT * FROM user_reg WHERE user='{username}'" 
    cursor.execute(sql)
    cursor.close()
    user = cursor.fetchone()
    if user:
        return User(user_id=0,username=user[0],password_hash=user[0])
    return None

def build_query_reexam(name,app_num,ipc_class,decision_num,re_applicant,re_patentee,re_code,legal_base,decision_revise,decision_date,decision_result,decision_text,reexam_type,year):
    
    conditions = []
    if name:
        if " or " in name.lower():
        # 处理可能的 or 和 and 逻辑
            sub_conditions = [f"name LIKE '%{part}%'" for part in name.lower().split(" or ")]
            conditions.append("(" + " OR ".join(sub_conditions) + ")")
        elif " and " in name.lower():
            sub_conditions = [f"name LIKE '%{part}%'" for part in name.lower().split(" and ")]
            conditions.append("(" + " AND ".join(sub_conditions) + ")")
        else:
            conditions.append(f"name LIKE '%{name}%'")
    if app_num:
        if " or " in app_num.lower():
        # 处理可能的 or 和 and 逻辑
            sub_conditions = [f"app_num LIKE '%{part}%'" for part in app_num.lower().split(" or ")]
            conditions.append("(" + " OR ".join(sub_conditions) + ")")
        elif " and " in app_num.lower():
            sub_conditions = [f"app_num LIKE '%{part}%'" for part in app_num.lower().split(" and ")]
            conditions.append("(" + " AND ".join(sub_conditions) + ")")
        else:
            conditions.append(f"app_num LIKE '%{app_num}%'")
    if ipc_class:
        if " or " in ipc_class.lower():
        # 处理可能的 or 和 and 逻辑
            sub_conditions = [f"ipc_class LIKE '%{part}%'" for part in ipc_class.lower().split(" or ")]
            conditions.append("(" + " OR ".join(sub_conditions) + ")")
        elif " and " in ipc_class.lower():
            sub_conditions = [f"ipc_class LIKE '%{part}%'" for part in ipc_class.lower().split(" and ")]
            conditions.append("(" + " AND ".join(sub_conditions) + ")")
        else:
            conditions.append(f"ipc_class LIKE '%{ipc_class}%'")
    if decision_num:
        if " or " in decision_num.lower():
        # 处理可能的 or 和 and 逻辑
            sub_conditions = [f"decision_num LIKE '%{part}%'" for part in decision_num.lower().split(" or ")]
            conditions.append("(" + " OR ".join(sub_conditions) + ")")
        elif " and " in decision_num.lower():
            sub_conditions = [f"decision_num LIKE '%{part}%'" for part in decision_num.lower().split(" and ")]
            conditions.append("(" + " AND ".join(sub_conditions) + ")")
        else:
            conditions.append(f"decision_num LIKE '%{decision_num}%'")
    if decision_date:
        if " or " in decision_date.lower():
        # 处理可能的 or 和 and 逻辑
            sub_conditions = [f"decision_date LIKE '%{part}%'" for part in decision_date.lower().split(" or ")]
            conditions.append("(" + " OR ".join(sub_conditions) + ")")
        elif " and " in decision_date.lower():
            sub_conditions = [f"decision_date LIKE '%{part}%'" for part in decision_date.lower().split(" and ")]
            conditions.append("(" + " AND ".join(sub_conditions) + ")")
        else:
            conditions.append(f"decision_date LIKE '%{decision_date}%'")
    if re_applicant:
        if " or " in re_applicant.lower():
        # 处理可能的 or 和 and 逻辑
            sub_conditions = [f"re_applicant LIKE '%{part}%'" for part in re_applicant.lower().split(" or ")]
            conditions.append("(" + " OR ".join(sub_conditions) + ")")
        elif " and " in re_applicant.lower():
            sub_conditions = [f"re_applicant LIKE '%{part}%'" for part in re_applicant.lower().split(" and ")]
            conditions.append("(" + " AND ".join(sub_conditions) + ")")
        else:
            conditions.append(f"re_applicant LIKE '%{re_applicant}%'")
    if re_patentee:
        if " or " in re_patentee.lower():
        # 处理可能的 or 和 and 逻辑
            sub_conditions = [f"re_patentee LIKE '%{part}%'" for part in re_patentee.lower().split(" or ")]
            conditions.append("(" + " OR ".join(sub_conditions) + ")")
        elif " and " in re_patentee.lower():
            sub_conditions = [f"re_patentee LIKE '%{part}%'" for part in re_patentee.lower().split(" and ")]
            conditions.append("(" + " AND ".join(sub_conditions) + ")")
        else:
            conditions.append(f"re_patentee LIKE '%{re_patentee}%'")
    if re_code:
        if " or " in re_code.lower():
        # 处理可能的 or 和 and 逻辑
            sub_conditions = [f"re_code LIKE '%{part}%'" for part in re_code.lower().split(" or ")]
            conditions.append("(" + " OR ".join(sub_conditions) + ")")
        elif " and " in re_code.lower():
            sub_conditions = [f"re_code LIKE '%{part}%'" for part in re_code.lower().split(" and ")]
            conditions.append("(" + " AND ".join(sub_conditions) + ")")
        else:
            conditions.append(f"re_code LIKE '%{re_code}%'")
    if legal_base:
        if " or " in legal_base.lower():
        # 处理可能的 or 和 and 逻辑
            sub_conditions = [f"legal_base LIKE '%{part}%'" for part in legal_base.lower().split(" or ")]
            conditions.append("(" + " OR ".join(sub_conditions) + ")")
        elif " and " in legal_base.lower():
            sub_conditions = [f"legal_base LIKE '%{part}%'" for part in legal_base.lower().split(" and ")]
            conditions.append("(" + " AND ".join(sub_conditions) + ")")
        else:
            conditions.append(f"legal_base LIKE '%{legal_base}%'")
    if decision_revise:
        if " or " in decision_revise.lower():
        # 处理可能的 or 和 and 逻辑
            sub_conditions = [f"decision_revise LIKE '%{part}%'" for part in decision_revise.lower().split(" or ")]
            conditions.append("(" + " OR ".join(sub_conditions) + ")")
        elif " and " in decision_revise.lower():
            sub_conditions = [f"decision_revise LIKE '%{part}%'" for part in decision_revise.lower().split(" and ")]
            conditions.append("(" + " AND ".join(sub_conditions) + ")")
        else:
            conditions.append(f"decision_revise LIKE '%{decision_revise}%'")
    if decision_text:
        if " or " in decision_text.lower():
        # 处理可能的 or 和 and 逻辑
            sub_conditions = [f"decision_text LIKE '%{part}%'" for part in decision_text.lower().split(" or ")]
            conditions.append("(" + " OR ".join(sub_conditions) + ")")
        elif " and " in decision_text.lower():
            sub_conditions = [f"decision_text LIKE '%{part}%'" for part in decision_text.lower().split(" and ")]
            conditions.append("(" + " AND ".join(sub_conditions) + ")")
        else:
            conditions.append(f"decision_text LIKE '%{decision_text}%'")
    if decision_result != '全部':
        conditions.append(f"decision_result LIKE '%{decision_result}%'")
    elif decision_result == '全部':
        if reexam_type == 'wx':
            conditions.append(f"(decision_result LIKE '%全部无效%' OR decision_result LIKE '%部分无效%' OR decision_result LIKE '%维持有效%')")
        elif reexam_type == 'fs':
            conditions.append(f"(decision_result LIKE '%维持驳回%' OR decision_result LIKE '%撤消驳回%')")
    # 组合所有条件，使用 AND 连接
    if conditions:
        where_clause = " AND ".join(conditions)
        sql_query = f"SELECT * FROM reexam_{reexam_type}_{year} WHERE {where_clause}"
    else:
        sql_query = f"SELECT * FROM reexam_{reexam_type}_{year} WHERE 1=1"
    sql_query += ' order by rand() LIMIT 10'
    return sql_query
    
def build_query_patent(name,app_num,ipc_class,publication_num,publication_type,agency,applicant,inventor,cited_document,related_document, application_date, publication_date, abstract,alltxt,yearmonth):
    query = f"SELECT * FROM patent_des_{yearmonth} WHERE 1=1"
    conditions = []
    if name:
        conditions.append(f"发明名称 LIKE '%{name}%'")
    if app_num:
        conditions.append(f"申请编号 LIKE '%{app_num}%'")
    if ipc_class:
        ipc_class = ipc_class.replace(' ','')
        ipc_class = ipc_class[0:4] + ' ' + ipc_class[4:]
        conditions.append(f"(分类 LIKE '%{ipc_class}%' or 分类 LIKE '%{ipc_class.replace(' ','')}%')")
    if publication_num:
        conditions.append(f"文档编号 LIKE '%{publication_num}%'")
    if publication_type:
        conditions.append(f"文档类型 LIKE '%{publication_type}%'")
    if agency:
        conditions.append(f"代理机构 LIKE '%{agency}%'")
    if applicant:
        conditions.append(f"申请人 LIKE '%{applicant}%'")
    if inventor:
        conditions.append(f"发明人 LIKE '%{inventor}%'")
    # if cited_document:
    #     conditions.append(f"引证文献 LIKE '%{cited_document}%'")
    # if related_document:
    #     conditions.append(f"相关文献 LIKE '%{related_document}%'")
    if application_date:
        conditions.append(f"申请日期 LIKE '%{application_date}%'")
    if publication_date:
        conditions.append(f"公布日期 LIKE '%{publication_date}%'")
    if abstract:
        conditions.append(f"摘要 LIKE '%{abstract}%'")
    if alltxt:
        conditions.append(f"全文 LIKE '%{alltxt}%'")
    if conditions:
        query += " AND " + " AND ".join(conditions)
    query += ' order by rand() LIMIT 10' #DESC
    return query
CORS(app)#, origins=["http://127.0.0.1:3306"])
visitor_count = 0
register_data = []
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
cache.init_app(app)
@cache.cached(timeout=60, query_string=True)
@app.route('/api/doubao',methods=['POST'])
def doubao():
    data = request.args
    writetype = data.get('type')
    prompt = data.get('prompt')
    description = ''
    if writetype == 'dynamicanalyze':
        description = "根据技术特征的上下位关系或结构连接关系或工艺流程步骤或成分配比或百分含量，将上述权利要求转为d3.v7.min.js的数据格式，"
        description += "特征位置按照{'nodes':[{ id: '', group: index},{'links':[{ source: '上位特征', target: '下位特征', label: '连接方式'}]}列出，id：专利名称为group:1，各id字符长度应小于10个字符，在id最后用'—'标出该特征所属的权利要求，如—权3，"
        description += "具有成分配比时标出成分含量或百分数，当从属权利要求进一步限定同一成分含量时作为下级特征列出，并且前一级的id的color向后一级的id的color逐渐由浅入深的过渡，尽可能采用偏橙色或蓝色，同级的id的color相同"
    elif writetype == 'analyze':
        description = "根据技术特征的上下位关系或结构连接关系或工艺流程步骤或成分配比或百分含量，将上述权利要求转为d3.v7.min.js的数据格式，按照{'name':'','color':'','children':[]}列出，"
        description += "各name字符长度应小于25个字符，在name最后用'—'标出该特征所属的权利要求，如—权3，具有成分配比时标出成分含量或百分数，当从属权利要求进一步限定同一成分含量时作为下级特征列出，"
        description += "并且前一级的name的color向后一级的name的color逐渐由浅入深的过渡，尽可能采用偏橙色或蓝色，同级的name的color相同。"
    elif writetype == 'description':
        description = "作为一名经验丰富的专利代理人，请以上述内容为基础，撰写一篇内容详尽的专利说明书（无需撰写摘要与权利要求书，按照主题名称、技术领域、背景技术、发明内容、有益效果、附图说明、具体实施方式的顺序撰写"
    elif writetype == 'techfield':
        description = "作为一名经验丰富的专利代理人，请以上述内容为基础，撰写专利说明书的技术领域部分，以'本发明涉及一种'开头，100字以内。"
    elif writetype == 'background':
        description = f"作为一名经验丰富的专利代理人，请以上述内容为基础，撰写专利说明书的背景技术部分。首先，介绍现有技术状况，指出当前技术在这些方面存在的不足和亟待解决的问题。"
        description += "之后，全面检索并阐述全球范围内该技术所属领域的现有技术成果，对比分析它们在技术特性方面的差异，总结现有技术亟待解决的技术问题。"
    elif writetype == 'summary':
        description = f"作为一名经验丰富的专利代理人，请以上述内容为基础，撰写专利说明书的发明内容部分，以'本发明的目的是提供一种'作为开头，500~800字，不要写出有益效果和优点部分。"
    elif writetype == 'benefit':
        description = f"作为一名经验丰富的专利代理人，请以上述内容为基础，撰写专利说明书的有益效果部分，以'本发明的有益效果是：'作为开头，详细阐述其在实际应用场景下，相较于现有技术，在关键性能指标方面实现的具体提升数值或程度，"
        description += "清晰说明这些提升如何切实解决该领域长期存在的痛点问题，带来直接且可量化的有益效果。深入分析其在不同使用条件（如高温、高压、高湿度等极端环境，或低功耗、高频率运行等特殊工况）下，"
        description += "相较于同类技术所展现出的优势，例如稳定性增强、故障率降低、适用范围拓宽等，以实际案例或模拟数据支撑，阐述这些优势转化为的产业应用层面的有益效果，如延长设备使用寿命、减少维护成本等。"
        description += "对专利所属行业产业链上下游产生的积极影响。在制造环节，明确其如何简化工艺流程、提高生产效率、降低次品率；在消费环节，说明如何提升用户体验、增加产品功能多样性等，系统阐述由此带来的贯穿产业链的综合性有益效果。"
    elif writetype == 'abedo':
        description = "作为一名经验丰富的专利代理人，请以上述内容为基础，详细阐述该专利技术在实际应用中的多种具体实施方式。以'以下结合图1~3，通过具体实施例详细说明本发明的具体内容。'开头，3000~5000字。"
        description += "首先，描述基于 [具体技术手段，如传感器类型、控制算法] 搭建的基础实施框架，包括各组成部分的选型、连接方式与工作原理。"
        description += "然后，针对不同应用场景，如家庭日常使用场景、工业复杂生产环境场景，分别说明如何对基础框架进行适应性调整，包括参数优化、模块增减等，"
        description += "以实现专利技术的最佳性能。同时，结合实际案例或实验数据，论证每种实施方式的可行性与有效性。围绕 [专利核心创新点，如新型材料合成工艺、独特的机械传动结构]，全面阐述其具体实施方式。"
        description += "详细说明实施过程中的每一个步骤，包括所需的原材料、设备工具及其操作流程。例如，在新型材料合成工艺中，精确到原材料的配比、添加顺序、反应温度与时间的控制等；对于独特的机械传动结构，"
        description += "描述各零部件的加工精度要求、装配顺序与调试方法。此外，列举在实施过程中可能遇到的问题及对应的解决方案，如材料杂质影响、装配误差调整等，确保实施方式的完整性与可操作性。"
        description += "以 [专利技术应用的具体产品或设备] 为载体，分步骤阐述其具体实施方式。从产品的整体设计思路入手，说明各功能模块的布局与协同工作机制。然后，针对每个功能模块，"
        description += "详细描述其内部结构设计、选用的元器件规格以及制造工艺。同时，对比不同实施方式下产品性能的差异，如不同显示屏对功耗和显示效果的影响，为实施方式的选择提供依据。"
    elif writetype =='claim':
        description = '作为一名经验丰富的专利代理人，请以上述内容为基础，撰写一篇专利权利要求书，尽可能采用功能性描述，以获取最大的保护范围。'
    elif writetype =='reexam_request':
        description = '作为一名经验丰富的专利代理人，请以上述内容为基础，撰写一篇专利复审请求书，阐述本发明符合专利法26条第3款的规定，相对于最接近的现有技术，具备专利法22条第2款规定的新颖性，具备专利法22条第3款规定的创造性。'
    elif writetype =='reexam_valid':
        description = "作为一名经验丰富的专利代理人，请以上述内容为基础，撰写一篇无效宣告请求书，无效理由主要包括：发明/实用新型：技术方案不具备新颖性、创造性（专利法第22条第2款、第3款）、"
        description += "说明书不完整导致无法实施（专利法第26条第3款）、权利要求书未以说明书为依据（专利法第26条第4款）、独立权利要求缺少必要技术特征（实施细则第20条第2款）、对申请文件的修改超出原始记载范围（专利法第33条）、"
        description += "同一发明创造被重复授予专利权（专利法第9条）、分案申请超出原申请范围（实施细则第43条第1款）、未报备保密审查即向外国申请专利（专利法第20条第1款）、图片或照片未清楚显示产品设计（专利法第27条第2款）、"
        description += "平面印刷品仅起标识作用（专利法第25条第6项）。"
    elif writetype =='check':
        description = "按照下述要求，校验上文中的错误。并将结果整理成表格。<br>语法错误：仔细检查说明书中的句子结构，确保主谓宾完整且搭配合理，词性使用准确，杜绝诸如句子成分残缺、词性误用、关联词搭配不当等问题。"
        description += "留意标点符号的正确使用，确保停顿、断句符合语法规范，避免因标点错误导致语义混淆。<br>逻辑缺陷：梳理专利说明书的整体逻辑架构，"
        description += "确保技术背景、发明内容、附图说明、具体实施方式等各个部分之间过渡自然、条理清晰。检查技术问题的提出与发明目的之间的关联性，确保发明目的紧密围绕所阐述的技术问题，不存在逻辑跳跃或偏离。分析技术方案的描述，"
        description += "确保各个技术特征之间的组合和作用关系清晰合理，不存在自相矛盾或含糊不清的表述。在阐述发明的有益效果时，要保证其与技术方案之间存在直接的因果关系，且效果的描述客观、准确、可验证。<br>"
        description += "术语一致性：统一专利说明书中技术术语的使用，确保前后术语含义一致，避免同一概念在不同地方使用不同表述，或者不同概念使用相似表述的情况。对行业内通用术语，要遵循标准的用法；对于自行定义的术语，"
        description += "需在首次出现时明确界定其含义，并在后续内容中保持一致。<br>清晰度与完整性：检查说明书对发明创造的公开是否充分，确保所属技术领域的普通技术人员能够根据说明书的内容实现该发明。所有技术细节，包括材料、尺寸、工艺步骤等，"
        description += "都应描述详尽，避免出现模糊不清或容易引起歧义的语句。对于复杂的技术方案，可通过增加示例、图表注释等方式增强其可读性和可理解性。<br>合规性：对照专利法规及相关审查指南，检查说明书是否符合格式要求、内容要求等规定。"
        description += "确保引用的现有技术文献准确且标注规范，权利要求书与说明书的内容相互支持、范围合理界定。"
    elif writetype =='ipc':
        description ="上述问题可能涉及的专利IPC分类号是什么(5个以内)？可能涉及的技术问题是什么(5个以内)？可能涉及的结构特征是什么(5个以内)？可能涉及的配方是什么(5个以内)？可能涉及的控制方法(5个以内)？<br>按照以下格式提供 {'可能涉及的IPC分类号':[ipc1的小组分类号:ipc1含义,ipc2的小组分类号:ipc2的含义,...], "
        description += "'可能涉及的技术问题':[可能的技术问题1,可能的技术问题2,...],'可能涉及的结构特征':[可能涉及的结构1,可能涉及的结构2,…],'可能涉及的材料配方':[可能涉及的配方1,可能涉及的配方2,…],'可能涉及的控制方法':[可能涉及的控制方法1,可能涉及的控制方法2,…]}"
    elif writetype =='eureka_problem':
        description = "针对上述技术领域和技术问题，提供一些可行的解决方案，如果本领域无法解决问题，可尝试通过跨领域的方式提出解决方案(5个以内)。<br>按照以下格式提供<br>针对技术问题1:[解决方案1,解决方案2,…],针对技术问题2:[解决方案1,解决方案2,…],…"
    elif writetype =='cited':
        description = "针对上述解决方案，检索相关的专利或论文，并总结各文献的主要方案，主要方案部分200~300字。<br>按照以下格式提供：<br>技术问题1:[文献1(文献名称，公开号，公开日):主要方案,文献2(文献名称，公开号，公开日):主要方案,…], "
        description += "技术问题2:[文献1(文献名称，公开号，公开日):主要方案,文献2(文献名称，公开号，公开日):主要方案,…]}"
    elif writetype =='solution':
        description = "参考检索到的技术文献，结合所有已知的前沿技术，可以从哪些部分进行针对性研发，或者针对上述检索获得的解决方案进行哪些实质性改进，可解决上述提到的相应的技术问题。<br>将可能的改进路线，可能涉及的改进结构、配方、算法，"
        description += "研发方向限制在5个以内，并整理成如下格式 {'研发方向1':[具体改进方向1,具体改进方向2,…],'研发方向2':[具体改进方向1,具体改进方向2,…],…,'结构改进':[改进结构1，改进结构2,...],'配方改进':[成分1，成分2,...],'控制方法/算法改进':[算法1，算法2,...]}"
    elif writetype =='solution_out':
        description = "根据上述研发方向和技术文献，撰写专利说明书，不包含具体实施方式，如果涉及新材料请标注出处或制备方法，如果涉及公式请给出推导过程，3000字~5000字，<br>"
        description += "1）背景技术中，介绍相关技术领域的现有技术状况，本领域技术人员曽针对上述问题进行了哪些改进，存在哪些技术瓶颈，导致问题无法被解决<br>2）发明内容中，阐述本方案通过针对上述的改进方向的研究与设计，获得了一种创新方案，有效解决了上述问题。3）在发明内容中描述方案的具体结构、方法、配方等内容，以能够实施为基准<br>"
    elif writetype == 'solution_out_embo':
        description = "根据上述相关技术领域(IPC分类号)、研发方向，撰写具体的实施方案，涉及新材料的请标注出处或制备方法，涉及公式的请给出推导过程，3000字~5000字，<br>"        
        description += "实施例中，描述方案的具体结构、方法、配方等内容，以能够实施为基准<br>进一步阐述本发明的方案中，哪些技术特征不属于本领域公知常识的优势或优点，如何克服了技术偏见，这些改进后的区别特征（发明点）具备专利法22条第3款规定的创造性，通过原理、公式或其他手段详细证明，并给出推导过程"
    prompt = f"{prompt}<br>\n{description}。"
    # R1 ep-20250225155602-f956h
    
    
    # R1-32B ep-20250221141435-svzzd   
    # 256K ep-20250310101508-vcmkn 
    # Doubao-1.5-lite-32k ep-20250410110712-jpz5z
    if writetype in ['solution_out','solution_out_embo','dynamicanalyze','cited']:
        reply = ai_doubao(prompt,'ep--z4wcj')
    elif writetype in ['solution','ipc','eureka_problem']:
        reply = ai_doubao(prompt,'ep--z4wcj')
    elif writetype in ['check']:
        reply = ai_doubao(prompt,'ep--z4wcj')
    elif writetype == 'stock':
        reply = ai_doubao(prompt,'ep--z4wcj')
    else:
        reply = ai_doubao(prompt,'ep--z4wcj')
    # print('WriteType:\n'+writetype + '\nPrompt:\n' + prompt.replace('>>','\n'))
    # open('write_log.txt','a+',encoding='utf-8').write(f'WriteType:\n{writetype}\nPrompt:\n{prompt.replace(">>","\n")}\n')
    return jsonify({"code":"200","model":"doubao","Type":writetype,"prompt":prompt,"reply": reply}), 200


@app.route('/design')
def design():
    return send_from_directory('.', 'design.html')
    
@app.route('/api/captcha', methods=['POST'])
def captcha():
    global register_data
    data = request.args
    if not data:
        return jsonify({"Status":"Error","message": "请输入用户名和手机号/邮箱"}), 201
    username =  data.get('username')
    phoneOrEmail = data.get('phoneOrEmail')
    captcha = random.randint(100000,999999)
    params={'code':''}
    params['code'] = captcha
    if '@' not in phoneOrEmail:
        SMS_Send([phoneOrEmail],str(params)).main()
        print('短信验证码发送成功')
    else:
        send_email([phoneOrEmail],captcha)
    register_data.append({'username': username, 'phoneOrEmail': phoneOrEmail, 'captcha': str(captcha)})

    return jsonify({"Status":"OK","message": "验证码发送成功"}), 201
@app.route('/register')
def register():
    return send_from_directory('.', 'register.html')
@app.route('/postregister', methods=['POST'])
def register_post():
    global register_data
    data = request.args

    username = data.get('username')
    password = data.get('password')
    phoneOrEmail = data.get('phoneOrEmail')
    company = data.get('company')
    captcha = data.get('captcha')
    nowtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    compare_data = {'username': username, 'phoneOrEmail': phoneOrEmail, 'captcha': captcha}
    if compare_data not in register_data:
        return jsonify({"Status":"Error","message": "验证码错误"}), 201
    else:
        try:
            register_data.remove({'username': username, 'phoneOrEmail': phoneOrEmail, 'captcha': captcha})
        except:
            pass
        conn = pymysql.connect(host='127.0.0.1', port=3306,user='', password='', database='', charset='utf8')
        cursor = conn.cursor()

        # 验证用户名
        if 'admin' in username or 'Admin' in username or 'fenrir' in username or 'Fenrir' in username:
            return jsonify({"Status":"Error","message": "用户已注册"}), 202
        else:
            sql = f"SELECT * FROM user_reg where user = '{username}'"
            cursor.execute(sql)
            if cursor.fetchone():
                return jsonify({"Status":"Error","message": "用户已注册"}), 202
        # 验证邮箱
        sql = f"SELECT * FROM user_reg where email = '{phoneOrEmail}'"
        cursor.execute(sql)
        if cursor.fetchone():
            return jsonify({"Status":"Error","message": "邮箱已注册"}), 203
        # 插入用户信息到数据库
        sql = f"INSERT INTO user_reg VALUES('{username}','{password}','{phoneOrEmail}','{nowtime}_{company}')"
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"Status":"OK","message": "注册成功"}), 201

@app.route('/postlogin', methods=['POST'])
def postlogin():
    # if current_user.is_authenticated:
    #     return redirect(url_for('/home'))
    data = request.form
    username = data['username']
    password = data['password']
    # remember = True
    # 18cf19c412563831.natapp.cc
    conn = pymysql.connect(host='127.0.0.1', port=3306,user='', password='', database='', charset='utf8')
    cursor = conn.cursor()
    sql = f"SELECT * FROM user_reg where user = '{username}' and password = '{password}'"
    cursor.execute(sql)
    user = cursor.fetchone()
    if not user:
        return jsonify({"Status":"Error","message": "用户名或密码错误"}), 201

    # session['user'] = user[0]
    # session['logged_in'] = True

    # user = User(user_id=0,username=user[0],password_hash=user[1])
    # login_user(user, remember=remember)
    return jsonify({"Status":"OK","message": "登录成功"}), 202
    
@app.route('/postlogout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('/login'))
        
@app.route('/login')
def login():
    return send_from_directory('.', 'login.html')
@app.route('/index')
def page_index():
    return send_from_directory('.', 'index.html')
@app.route('/') 
def page_index_2():
    return send_from_directory('.', 'index.html')
@app.route('/home')
# @login_required
def page_home():
    return send_from_directory('.', 'home.html')
@app.route('/reexam')
def page_reexam():
    return send_from_directory('.', 'reexam.html')
@app.route('/searchreexam', methods=['POST'])
def searchreexam():
    data = request.args

    name = data.get('name')
    ipc_class = data.get('ipc_class')
    app_num = data.get('app_num')
    decision_num = data.get('decision_num')
    re_applicant = data.get('re_applicant')
    re_patentee = data.get('re_patentee')
    re_code = data.get('re_code')
    legal_base = data.get('legal_base')
    decision_revise = data.get('decision_revise')
    decision_date = data.get('decision_date')
    decision_result = data.get('decision_result')
    decision_text  = data.get('decision_text')
    reexam_type = data.get('reexam_type')
    results = []

    if reexam_type == 'wx' and decision_result in ['维持驳回','撤消驳回']:
        return jsonify({
            "count": 0,
            "results": []
        })
    elif reexam_type == 'fs' and decision_result in ['全部无效','部分无效','维持有效']:
        return jsonify({
            "count": 0,
            "results": []
        })
    for year in range(2025,1999,-1):
        if len(results) >= 10:
            connection.close()
            break
        elif (app_num or decision_num or re_code) and results:
            connection.close()
            break
        query = build_query_reexam(name,app_num,ipc_class,decision_num,re_applicant,re_patentee,re_code,legal_base,decision_revise,decision_date,decision_result,decision_text,reexam_type,year)        
        try:
            # 18cf19c412563831.natapp.cc
            connection = pymysql.connect(host='127.0.0.1', port=3306,user='', password='', database='', charset='utf8')
            cursor = connection.cursor()
            cursor.execute(query)
            tmp_results = cursor.fetchall()
            results += tmp_results
            connection.commit()
            def to_dict(case):
                return {
                    "name":case[0],
                    "decision_num":case[1],
                    "re_code": case[2],
                    "app_num": case[3],
                    "ipc_class": case[4],
                    "re_applicant": case[5],
                    "decision_date": case[6],
                    "application_date":case[7],
                    "legal_base": case[11],
                    "decision_revise": case[12],
                    "decision_text": case[13],
                    "decision_result": case[14],
                    "re_patentee": case[15],
                }
        except pymysql.MySQLError as err:
            return jsonify({"error": str(err)}), 500
    return jsonify({
            "count": len(results),
            "results": [to_dict(case) for case in results]
        })
@app.route('/patent')
def page_patent():
    return send_from_directory('.', 'patent.html')

@app.route('/searchpatent', methods=['POST','GET'])
def searchpatent():
    data = request.args

    name = data.get('name')
    app_num = data.get('app_num')
    ipc_class = data.get('ipc_class')
    publication_num = data.get('publication_num')
    publication_type = data.get('publication_type')
    agency = data.get('agency')
    applicant = data.get('applicant')
    inventor = data.get('inventor')
    cited_document = ''#data.get('cited_document')
    related_document = ''#data.get('related_document')
    application_date = data.get('application_date')
    publication_date = data.get('publication_date')
    abstract  = data.get('abstract')
    alltxt = data.get('alltxt')
    year_1 = '2025'
    month_1 = '12'
    results = []
    application_date = application_date.replace('-','')
    
    if len(application_date) >= 6:
        year_1 = application_date[0:4]
        month_1 = application_date[4:6]
        if int(year_1) > 2025:
            year_1 = '2025'
        elif int(year_1) <= 1984:
            year_1 = '1985'
    elif len(application_date) >= 4:
        year_1 = application_date[0:4]
        if int(year_1) > 2025:
            year_1 = '2025'
        elif int(year_1) <= 1984:
            year_1 = '1985'
       
    for year in range(int(year_1),1984,-1):
        for month in range(int(month_1),0,-1):
            if len(results) >= 10:
                break
            elif (app_num or publication_num) and results:
                break
            month = '%02d' % month
            date = f'{year}{month}'
            query = build_query_patent(name,app_num,ipc_class,publication_num,publication_type,agency,applicant,inventor,cited_document,related_document,application_date,publication_date,abstract,alltxt,date)
            try:
                # 18cf19c412563831.natapp.cc
                connection = pymysql.connect(host='127.0.0.1', port=3306,user='', password='', database='', charset='utf8')
                cursor = connection.cursor()
                cursor.execute(query)
                temp_results = cursor.fetchall()
                results += temp_results
                connection.commit()
                def to_dict(case):
                    return {
                        "name":case[6],
                        "ipc_class": case[5],
                        "app_num": case[3],
                        "publication_num":'CN'+case[0]+case[1],
                        "agency": case[11],
                        "applicant": case[9].replace('_',' '),
                        "inventor": case[10],
                        "cited_document": case[7].replace(' ','\n'),
                        "related_document": case[8],
                        "application_date": case[4],
                        "publication_date": case[2],
                        "abstract": case[13],
                        "alltxt":case[14].replace('技术领域\n技术领域','技术领域').replace('背景技术\n背景技术','背景技术').replace('具体实施方式\n具体实施方式','具体实施方式').replace('发明内容\n发明内容','发明内容').replace('附图说明\n附图说明','附图说明').replace('\n\n','\n')
                            }
            except pymysql.MySQLError as err:
                print(jsonify({"error": str(err)}), 500)
    return jsonify({
                "count": len(results),
                "results": [to_dict(case) for case in results]
            })
@app.route('/analyze')
def page_analyze():
    return send_from_directory('.', 'analyze.html')
class SMS_Send:
    def __init__(self, phone_number,params):
        self.phone_number = phone_number
        self.params = params
        pass
    def create_client(self) -> Dysmsapi20170525Client:       
        config = open_api_models.Config(access_key_id='',access_key_secret='',endpoint='dysmsapi.aliyuncs.com')
        return Dysmsapi20170525Client(config)

    def main(self) -> None:
        client = self.create_client()       
        send_sms_request = dysmsapi_20170525_models.SendSmsRequest(sign_name= '',template_code= '',phone_numbers= self.phone_number,template_param= self.params)
        runtime = util_models.RuntimeOptions()
        try:
            client.send_sms_with_options(send_sms_request, runtime)
        except Exception as error:
            # 此处仅做打印展示，请谨慎对待异常处理，在工程项目中切勿直接忽略异常。
            print(error.message)
            # 诊断地址
            print(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)

    async def main_async(self) -> None:
        client = self.create_client()
        send_sms_request = dysmsapi_20170525_models.SendSmsRequest(sign_name= '',template_code= '',phone_numbers= self.phone_number,template_param= self.params)
        runtime = util_models.RuntimeOptions()
        try:
            await client.send_sms_with_options_async(send_sms_request, runtime)
        except Exception as error:
            # 此处仅做打印展示，请谨慎对待异常处理，在工程项目中切勿直接忽略异常。
            print(error.message)
            # 诊断地址
            print(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)
@app.route('/eureka')
def eureka():
    return send_from_directory('.', 'eureka.html')
@app.route('/write')
def write():
    return send_from_directory('.', 'write.html')
@app.route('/stock')
def stock():
    return send_from_directory('.', 'stock.html')

@app.route("/api/getdescription",methods=['POST'])
def getdescription():
    global dates
    data = request.args
    prompt = data.get('prompt').replace('\n','').replace('\'','"').replace(' ','')
    prompt = json.loads(prompt)
    try:
        ipc_array = [item.split(':')[0] for item in prompt["可能涉及的IPC分类号"]]
        conditions_1 = [f"分类 like '%{element}%'" for element in ipc_array]
        # keywords = ai_doubao(';'.join(prompt["可能涉及的技术问题"]) + '从上述内容中提取用于检索文献的关键词,输出格式为[关键词1,关键词2,……]','ep-20240529091520-6zdpl').strip('[]')    
        # keywords_array = [keyword.strip() for keyword in keywords.split(",")]
        # conditions_2 = [f"全文 like '%{element}%'" for element in keywords_array]
    except Exception as e:
        print(e)
        return jsonify({"Status":"OK","results": 'No Results'}), 404
    try:
        # 18cf19c412563831.natapp.cc
        sql = f'select * from PATENT_DES_202207 where ({ " or ".join(conditions_1)})  order by rand() limit 5'   #and ({ " or ".join(conditions_2)})
        conn = pymysql.connect(host='127.0.0.1', port=3306,user='', password='', database='', charset='utf8')
        temp_results = []
        for i in dates:
            try:
                cursor = conn.cursor()
                cursor.execute(sql.replace('PATENT_DES_202207', f'PATENT_DES_{i}'))
                results = cursor.fetchall() # 获取所用登录信息
                for result in results:
                    temp_results.append(f'<专利名称>{result[6]}\n<申请号>{result[3]}\n<公开号>CN{result[0]}{result[1]}\n<公开日>{result[2]}\n<IPC>{result[5]}\n<说明书>{result[14]}'.replace('技术领域\n技术领域','技术领域').replace('背景技术\n背景技术','背景技术').replace('具体实施方式\n具体实施方式','具体实施方式').replace('发明内容\n发明内容','发明内容').replace('附图说明\n附图说明','附图说明').replace('\n\n','\n'))
                if temp_results:
                    return jsonify({"Status":"OK","results": '\n======\n'.join(temp_results)}), 201
            except Exception as e:
                print(e)
    except Exception as e:
        print(e)
    return jsonify({"Status":"OK","results": '\n======\n'.join(temp_results)}), 201
if __name__ == '__main__':
    app.run(debug=False, port=5000)

