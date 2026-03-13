# =====================================================================
# pdf_components.py
# =====================================================================

def sec_cover(context) -> str:
    return f"""
<div class="cover">
  <section>
    <p class="cover-title">รายงานผลการทดสอบเจาะระบบ (Penetration Testing Report)</p>
    <p class="cover-subtitle"><b>โครงการ (Project):</b> {context.project_name}</p>
    <p class="cover-subtitle"><b>เจ้าของโครงการ (Project Owner):</b> {context.project_owner}</p>
    <p class="cover-subtitle"><b>หมายเลขเอกสาร (Job ID):</b> {context.job_id}</p>
    <p class="cover-subtitle"><b>วันที่ทดสอบ:</b> {context.job_started_date} – {context.job_ended_date}</p>
    <p class="cover-subtitle"><b>จัดเตรียมโดย:</b> {context.scanner_name}</p>
    <p class="cover-subtitle"><b>อีเมลสนับสนุน:</b> {context.support_email}</p>
  </section>
</div>
<div class="page-break"></div>
"""


def sec_toc(page_nums: dict) -> str:
    def p(key):
        n = page_nums.get(key)
        return str(n) if n else "—"

    entries = [
        ("1.",  "บทสรุปผู้บริหาร (Executive Summary)",                          "sec1"),
        ("",    "1.1. วัตถุประสงค์และภาพรวมการดำเนินงาน",                       "sec1"),
        ("",    "1.2. สรุปผลการตรวจพบช่องโหว่",                                 "sec1"),
        ("",    "1.3. Vulnerability Dashboard",                                  "sec1"),
        ("",    "1.4. สรุปผลการประเมินรายสินทรัพย์",                            "sec1"),
        ("",    "1.5. ข้อเสนอแนะเชิงกลยุทธ์สำหรับผู้บริหาร",                   "sec1"),
        ("2.",  "ขอบเขตการดำเนินงาน (Scope of Work)",                           "sec2"),
        ("",    "2.1. ขอบเขตของสินทรัพย์ที่ทำการตรวจสอบ",                      "sec2"),
        ("",    "2.2. สถาปัตยกรรมการทดสอบและเทคโนโลยีที่ใช้",                  "sec2"),
        ("",    "2.3. ขั้นตอนการทดสอบด้วยระบบอัตโนมัติ",                        "sec2"),
        ("3.",  "รายละเอียดผลการทดสอบเจาะระบบ (Technical Findings)",            "sec3"),
        ("",    "3.1. รูปแบบการนำเสนอรายงานผลการตรวจพบ",                        "sec3"),
        ("",    "3.2. รายละเอียดช่องโหว่",                                       "sec3"),
        ("4.",  "สถานะการจัดการช่องโหว่ (Vulnerability Lifecycle Tracking)",    "sec4"),
        ("",    "4.1. นิยามสถานะการดำเนินงาน",                                  "sec4"),
        ("5.",  "บทสรุปและข้อเสนอแนะ (Conclusion and Recommendations)",         "sec5"),
        ("",    "5.1. บทสรุปภาพรวมความปลอดภัย",                                 "sec5"),
        ("",    "5.2. การประเมินประสิทธิภาพของระบบ Security Worker",             "sec5"),
        ("",    "5.3. ข้อเสนอแนะเพื่อการปรับปรุง",                              "sec5"),
        ("ผ1.", "ภาคผนวก 1: รายละเอียดวิธีการและขั้นตอนการตรวจประเมิน",        "app1"),
        ("ผ2.", "ภาคผนวก 2: เกณฑ์การประเมินระดับความเสี่ยง (Risk Rating)",     "app2"),
    ]

    rows = ""
    for num, title, key in entries:
        is_header = bool(num)
        weight    = "font-weight:600;" if is_header else "font-weight:400; padding-left:20px;"
        rows += f"""
  <div class="toc-row">
    <span class="toc-num">{num}</span>
    <span class="toc-title" style="{weight}">{title}</span>
    <span class="toc-dots"></span>
    <span class="toc-page">{p(key)}</span>
  </div>"""

    return f"""
<div data-anchor="toc"></div>
<section>
  <p class="text-center cover-title">สารบัญ</p>
  <div class="toc-table">{rows}</div>
</section>
<div class="page-break"></div>
"""


def sec1_executive_summary(context) -> str:
    asset_rows = ""
    for a in context.assets:
        status_cls = a['status'].lower().replace(' ', '-')
        asset_rows += f"""
      <tr>
        <td>{a['asset_id']}</td>
        <td>{a['asset_name']}</td>
        <td>{a['target']}</td>
        <td>{a['hc_cnt']}</td>
        <td><span class="badge {status_cls}">{a['status']}</span></td>
      </tr>"""

    return f"""
<div data-anchor="sec1"></div>
<section>
  <p class="header1">1. บทสรุปผู้บริหาร (Executive Summary)</p>
  <div class="tab">
    <p class="header2">1.1. วัตถุประสงค์และภาพรวมการดำเนินงาน (Project Objective &amp; Overview)</p>
    <p><span class="tab"></span>การทดสอบเจาะระบบ (Penetration Testing) สำหรับโครงการ <b>{context.project_name}</b> มีวัตถุประสงค์หลักเพื่อประเมินระดับความมั่นคงปลอดภัยและค้นหาช่องโหว่เชิงรุก โดยอาศัยเทคโนโลยีการตรวจสอบอัตโนมัติจากระบบ <b>{context.scanner_name}</b> ดำเนินการในรูปแบบ Gray Box Testing</p>
  </div>
  <div class="tab">
    <p class="header2">1.2. สรุปผลการตรวจพบช่องโหว่ (Vulnerability Summary)</p>
    <p><span class="tab"></span>ระบบตรวจพบช่องโหว่จำนวนรวมทั้งหมด <b>{context.total_vulns}</b> รายการ จากสินทรัพย์ทั้งหมด <b>{context.total_asset}</b> รายการ</p>
    <div class="tab">
      <li>Critical (วิกฤต): <b>{context.critical_cnt}</b> รายการ</li>
      <li>High (สูง): <b>{context.high_cnt}</b> รายการ</li>
      <li>Medium (กลาง): <b>{context.medium_cnt}</b> รายการ</li>
      <li>Low (ต่ำ): <b>{context.low_cnt}</b> รายการ</li>
    </div>
  </div>
  <div class="tab">
    <p class="header2">1.3. Vulnerability Dashboard</p>
    <p><span class="tab"></span>[กราฟสรุปช่องโหว่ — placeholder]</p>
  </div>
  <div class="tab">
    <p class="header2">1.4. สรุปผลการประเมินรายสินทรัพย์ (Asset-Based Risk Summary)</p>
    <table>
      <thead><tr><th>Asset ID</th><th>ชื่อสินทรัพย์</th><th>IP/URL</th><th>ช่องโหว่ความรุนแรงสูง</th><th>Status</th></tr></thead>
      <tbody>{asset_rows}</tbody>
    </table>
  </div>
  <div class="tab">
    <p class="header2">1.5. ข้อเสนอแนะเชิงกลยุทธ์สำหรับผู้บริหาร (Management Recommendations)</p>
    <div class="tab">
      <li><b>ระยะสั้น:</b> มอบหมายผู้รับผิดชอบแก้ไขช่องโหว่ระดับวิกฤตและสูง พร้อมทำการทดสอบซ้ำ (Re-testing)</li>
      <li><b>ระยะกลาง:</b> บูรณาการระบบตรวจสอบความปลอดภัยอัตโนมัติเข้ากับวงจรการพัฒนา (DevSecOps)</li>
      <li><b>ระยะยาว:</b> พัฒนาทักษะบุคลากรด้าน Security Coding ตามมาตรฐาน ISO/IEC 27001 หรือ NIST Framework</li>
    </div>
  </div>
</section>
<div class="page-break"></div>
"""


def sec2_scope(context) -> str:
    asset_rows = ""
    for i, a in enumerate(context.assets, 1):
        asset_rows += f"<tr><td>{i}</td><td>{a['asset_name']}</td><td>{a['asset_desc']}</td><td>{a['target']}</td></tr>"

    return f"""
<div data-anchor="sec2"></div>
<section>
  <p class="header1">2. ขอบเขตและระเบียบวิธีการปฏิบัติงาน (Scope and Methodology)</p>
  <div class="tab">
    <p class="header2">2.1. ขอบเขตของสินทรัพย์ที่ทำการตรวจสอบ (Audit Scope)</p>
    <table>
      <thead><tr><th>ลำดับที่</th><th>ชื่อระบบ</th><th>รายละเอียด</th><th>IP / URL เป้าหมาย</th></tr></thead>
      <tbody>{asset_rows}</tbody>
    </table>
  </div>
  <div class="tab">
    <p class="header2">2.2. สถาปัตยกรรมการทดสอบและเทคโนโลยีที่ใช้ (Technical Architecture)</p>
    <div class="tab">
      <p>1. <b>Asset Configuration:</b> ระบุเป้าหมายและขอบเขตผ่าน Centralized Management Website</p>
      <p>2. <b>Worker Deployment:</b> ติดตั้ง Security Worker ลงใน Dedicated Pentest Machine</p>
      <p>3. <b>Autonomous Execution:</b> สแกนแบบ Fully Automated ตั้งแต่ Endpoint Discovery จนถึงการวิเคราะห์ช่องโหว่</p>
    </div>
  </div>
  <div class="tab">
    <p class="header2">2.3. ขั้นตอนการทดสอบด้วยระบบอัตโนมัติ (Automated Testing Process)</p>
    <div class="tab">
      <li><b>Stateful Discovery:</b> Browser Automation จัดการ Session และข้ามระบบยืนยันตัวตนได้อัตโนมัติ</li>
      <li><b>Dynamic Traffic Interception:</b> ดักจับ XHR/Fetch เพื่อค้นหา Hidden API Endpoints</li>
      <li><b>Intelligent Payload Injection:</b> Context Analysis เพื่อเลือก Payloads ที่เหมาะสม</li>
      <li><b>PoC Generation:</b> บันทึก Visual Evidence และ cURL Command อัตโนมัติ</li>
    </div>
  </div>
</section>
<div class="page-break"></div>
"""


def sec3_technical_findings(context) -> str:
    vuln_blocks = ""
    for v in context.vulns:
        asset_name = next((a['asset_name'] for a in context.assets if a['asset_id'] == v['asset_related']), v['asset_related'])
        sev_cls    = v['severity'].lower()
        img_tag    = f'<img src="{v["evidence"]}" class="evidence-img">' if v.get('evidence') else '<i>[ไม่มีภาพหลักฐาน]</i>'
        vuln_blocks += f"""
    <div class="vuln-block">
      <p><b>รายละเอียดช่องโหว่หมายเลข: {v['vuln_id']}</b></p>
      <div class="tab">
        <p><b>[ General Information ]</b></p>
        <div class="tab">
          <li>ประเภทช่องโหว่: {v['vuln_type']}</li>
          <li>Severity: <span class="badge {sev_cls}">{v['severity']}</span> &nbsp;|&nbsp; CVSS v3.1: <b>{v['cvss_score']}</b></li>
          <li>Vector: {v['cvss_vector']}</li>
          <li>Status: {v['status']}</li>
        </div>
      </div>
      <div class="tab">
        <p><b>[ Administrative Details ]</b></p>
        <div class="tab">
          <li>Assigned To: {v['dev_name']}</li>
          <li>Verified By: {v['tester_name']}</li>
          <li>Related Asset: {asset_name}</li>
        </div>
      </div>
      <div class="tab">
        <p><b>[ Technical Context ]</b></p>
        <div class="tab">
          <li>Location: {v['target']}</li>
          <li>Parameter: {v['parameter']}</li>
          <li>Description: {v['description_from_library']}</li>
        </div>
      </div>
      <div class="tab">
        <p><b>[ Proof of Concept ]</b></p>
        <div class="tab">
          <li>Payload: <code>{v['payload']}</code></li>
          <li>cURL: <code>{v['curl_command']}</code></li>
          <li>Evidence:</li>
          <div class="img-block">{img_tag}</div>
        </div>
      </div>
      <div class="tab">
        <p><b>[ Recommendation ]</b></p>
        <div class="tab"><li>{v['reccommendation_from_library']}</li></div>
      </div>
      <div class="page-break"></div>
    </div>"""

    return f"""
<div data-anchor="sec3"></div>
<section>
  <p class="header1">3. รายละเอียดผลการทดสอบทางเทคนิค (Technical Findings)</p>
  <div class="tab">
    <p class="header2">3.1. รูปแบบการนำเสนอรายงานผลการตรวจพบ</p>
    <div class="tab">
      <li><b>Technical Evidence:</b> Payload, cURL และภาพถ่ายหน้าจอเพื่อใช้ใน Replication</li>
      <li><b>Accountability &amp; Workflow:</b> Assigned To และ Verified By เพื่อความโปร่งใสใน Remediation Lifecycle</li>
    </div>
  </div>
  <div class="tab">
    <p class="header2">3.2. รายละเอียดช่องโหว่</p>
    {vuln_blocks}
  </div>
</section>
"""


def sec4_lifecycle(context) -> str:
    rows = ""
    for v in context.vulns:
        asset_name = next((a['asset_name'] for a in context.assets if a['asset_id'] == v['asset_related']), v['asset_related'])
        sts_cls    = v['status'].lower().replace(' ', '-')
        rows += f"<tr><td>{v['vuln_id']}</td><td>{v['vuln_type']}</td><td>{asset_name}</td><td>{v['dev_name']}</td><td>{v['tester_name']}</td><td><span class='badge {sts_cls}'>{v['status']}</span></td></tr>"

    return f"""
<div data-anchor="sec4"></div>
<section>
  <p class="header1">4. สถานะและวงจรการจัดการช่องโหว่ (Vulnerability Lifecycle Tracking)</p>
  <table>
    <thead><tr><th>Vuln ID</th><th>Vuln Type</th><th>Target</th><th>Assigned To</th><th>Verified By</th><th>Status</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  <div class="tab">
    <p class="header2">4.1. นิยามสถานะการดำเนินงาน (Status Definition)</p>
    <div class="tab">
      <li><b>Open:</b> ช่องโหว่ได้รับการยืนยันและบันทึกเข้าสู่ฐานข้อมูลแล้ว รอการวิเคราะห์และมอบหมาย</li>
      <li><b>In Progress:</b> มอบหมายไปยัง Developer แล้ว อยู่ในขั้นตอนการแก้ไข</li>
      <li><b>Fixed / Pending Verification:</b> แก้ไขเสร็จสิ้น รอ Pen Tester ทดสอบซ้ำ (Re-testing)</li>
      <li><b>Mitigated:</b> ดำเนินการบรรเทาความเสี่ยงเบื้องต้นแล้ว</li>
    </div>
  </div>
</section>
<div class="page-break"></div>
"""


def sec5_conclusion(context) -> str:
    return f"""
<div data-anchor="sec5"></div>
<section>
  <p class="header1">5. บทสรุปและข้อเสนอแนะ (Conclusion and Recommendations)</p>
  <div class="tab">
    <p class="header2">5.1. บทสรุปภาพรวมความปลอดภัย (Overall Security Conclusion)</p>
    <p><span class="tab"></span>จากการทดสอบเจาะระบบภายใต้โครงการ <b>{context.project_name}</b> โดยใช้ระบบ <b>{context.scanner_name}</b> พบช่องโหว่รวม <b>{context.total_vulns}</b> รายการ ซึ่งหากไม่ได้รับการแก้ไขอาจส่งผลกระทบต่อ Confidentiality และ Integrity ของข้อมูลในระดับองค์กร</p>
  </div>
  <div class="tab">
    <p class="header2">5.2. การประเมินประสิทธิภาพของระบบ Security Worker</p>
    <div class="tab">
      <li><b>Deep Visibility:</b> ตรวจพบ Shadow API ผ่าน Traffic Interception</li>
      <li><b>Accuracy &amp; Reliability:</b> Dynamic Verification ลด False Positive ได้อย่างมีนัยสำคัญ</li>
      <li><b>Documentation Speed:</b> จัดทำ PoC ได้ทันที ช่วยลดเวลาทำรายงานถึง {context.efficiency}%</li>
    </div>
  </div>
  <div class="tab">
    <p class="header2">5.3. ข้อเสนอแนะเพื่อการปรับปรุง (Strategic Recommendations)</p>
    <div class="tab">
      <li><b>Remediation Priority:</b> เร่งแก้ไข Critical และ High ทั้งหมด พร้อม Re-testing</li>
      <li><b>Integration with DevSecOps:</b> บูรณาการ Security Worker เข้า CI/CD Pipeline</li>
      <li><b>Security Training:</b> ส่งเสริม Secure Coding ตามมาตรฐาน OWASP</li>
    </div>
  </div>
</section>
<div class="page-break"></div>
"""


def appendix1() -> str:
    return """
<div data-anchor="app1"></div>
<section>
  <p class="header1">ภาคผนวก 1: รายละเอียดวิธีการและขั้นตอนการตรวจประเมิน</p>
  <p><span class="tab"></span>อ้างอิงตามมาตรฐานสากล OWASP Top 10:2021 และ NIST SP 800-115</p>
  <div class="tab">
    <p class="header2">1. การรวบรวมข้อมูล (Information Gathering)</p>
    <div class="tab">
      <li><b>Active Reconnaissance:</b> Browser Automation สำรวจโครงสร้างเว็บแอปพลิเคชัน</li>
      <li><b>Network Traffic Interception:</b> Playwright ดักจับ XHR/Fetch เพื่อค้นหา API Endpoint</li>
      <li><b>DNS &amp; Service Discovery:</b> ตรวจสอบ DNS และหมายเลขไอพีเพื่อกำหนดขอบเขต</li>
    </div>
  </div>
  <div class="tab">
    <p class="header2">2. การระบุและวิเคราะห์ช่องโหว่ (Vulnerability Identification)</p>
    <div class="tab">
      <li><b>Monkey Patching Technology:</b> สอดแทรก Probes เข้าไปใน Browser Runtime</li>
      <li><b>Context-Aware Fuzzing:</b> วิเคราะห์บริบทพารามิเตอร์ก่อนส่ง Probe Strings</li>
      <li><b>Vulnerability Library Matching:</b> เปรียบเทียบกับคลังข้อมูลมาตรฐาน (SQLi, XSS, Path Traversal)</li>
    </div>
  </div>
  <div class="tab">
    <p class="header2">3. การทดสอบการบุกรุกเพื่อยืนยันผล (Exploitation &amp; Verification)</p>
    <div class="tab">
      <li><b>Dynamic Payload Injection:</b> ส่ง Non-destructive Payloads เพื่อยืนยันช่องโหว่</li>
      <li><b>Automated Confirmation Signal:</b> รอรับสัญญาณยืนยัน เช่น XSS_CONFIRMED</li>
      <li><b>Access Control Testing:</b> ทดสอบ Privilege Escalation ด้วยสิทธิ์จำกัด</li>
    </div>
  </div>
  <div class="tab">
    <p class="header2">4. การวิเคราะห์ผลและจัดทำรายงาน (Analysis &amp; Documentation)</p>
    <div class="tab">
      <li><b>Evidence Collection:</b> บันทึกภาพหน้าจอและ cURL อัตโนมัติ</li>
      <li><b>Vulnerability Lifecycle Mapping:</b> นำข้อมูลเข้าระบบ Assign และเตรียม Re-test</li>
    </div>
  </div>
</section>
<div class="page-break"></div>
"""


def appendix2() -> str:
    return """
<div data-anchor="app2"></div>
<section>
  <p class="header1">ภาคผนวก 2: เกณฑ์การประเมินระดับความเสี่ยง (Risk Rating)</p>
  <div class="tab">
    <p class="header2">1. OWASP Risk Rating</p>
    <p><span class="tab"></span>ความเสี่ยง (Risk) = ความเป็นไปได้ (Likelihood) × ผลกระทบ (Impact)</p>
    <div class="tab">
      <p class="header3">1.1. ตัวแปรที่ใช้ในการคำนวณ</p>
      <div class="tab">
        <li><b>Threat Agent Factors:</b> Skill Level, Motive, Size</li>
        <li><b>Vulnerability Factors:</b> Ease of discovery, Ease of exploit, Awareness, Intrusion detection</li>
        <li><b>Technical Impact:</b> Confidentiality, Integrity, Availability, Accountability</li>
        <li><b>Business Impact:</b> Financial, Reputation, Compliance, Privacy</li>
      </div>
      <p class="header3">1.2. ระดับความเสี่ยงโดยรวม</p>
      <table>
        <thead><tr><th>คะแนน</th><th>ระดับความเสี่ยง</th></tr></thead>
        <tbody>
          <tr><td>0 – 3</td><td>ต่ำ</td></tr>
          <tr><td>3 – 6</td><td>ปานกลาง</td></tr>
          <tr><td>6 – 9</td><td>สูง</td></tr>
        </tbody>
      </table>
    </div>
  </div>
  <div class="tab">
    <p class="header2">2. CVSS v3.1 Rating</p>
    <table>
      <thead><tr><th>คะแนน</th><th>ระดับความเสี่ยง</th></tr></thead>
      <tbody>
        <tr><td>0.0</td><td>ไม่มีความเสี่ยง</td></tr>
        <tr><td>0.1 – 3.9</td><td>ต่ำ</td></tr>
        <tr><td>4.0 – 6.9</td><td>ปานกลาง</td></tr>
        <tr><td>7.0 – 8.9</td><td>สูง</td></tr>
        <tr><td>9.0 – 10.0</td><td>สูงมาก (Critical)</td></tr>
      </tbody>
    </table>
  </div>
</section>
<div class="page-break"></div>
"""