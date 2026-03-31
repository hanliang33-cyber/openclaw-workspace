#!/usr/bin/env node
const PptxGenJS = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

// ============================================================
// 配色方案 - 深海蓝专业商务风格
// ============================================================
const NAVY   = "0D2137";
const DBLUE  = "1A3A6B";
const BLUE   = "2563EB";
const SKYBL  = "3B82F6";
const LTBL   = "60A5FA";
const AMBER  = "F59E0B";
const RED    = "DC2626";
const GREEN  = "16A34A";
const TEAL   = "0D9488";
const WHITE  = "FFFFFF";
const BGGRY  = "F8FAFC";
const GRY10  = "F1F5F9";
const GRY20  = "E2E8F0";
const GRY30  = "CBD5E1";
const GRY50  = "94A3B8";
const GRY70  = "475569";
const TEXT   = "1E293B";
const MUTED  = "64748B";

// ============================================================
// 工具函数
// ============================================================
const FONT = { body: "微软雅黑", title: "微软雅黑" };

// 通用添加文字
function txt(slide, text, x, y, w, h, opts) {
  const def = { fontFace: FONT.body };
  if (typeof opts === "object" && opts !== null) {
    slide.addText(text, Object.assign({ x, y, w, h }, def, opts));
  } else {
    slide.addText(text, { x, y, w, h, ...def });
  }
}

// 添加标题文字
function title(slide, text, x, y, w, h, opts) {
  const def = { fontFace: FONT.title };
  slide.addText(text, Object.assign({ x, y, w, h }, def, opts));
}

// 圆角矩形 (x, y, w, h, radius, fillColor, lineColor, lineWidth)
function rrect(slide, x, y, w, h, r, fill, line, lwidth) {
  const opts = {
    x, y, w, h,
    rectRadius: r / 72,
    fill: { color: fill }
  };
  if (line) opts.line = { color: line, width: lwidth || 0.5 };
  slide.addShape("roundRect", opts);
}

// 普通矩形
function rect(slide, x, y, w, h, fill) {
  slide.addShape("rect", { x, y, w, h, fill: { color: fill } });
}

// 椭圆
function oval(slide, x, y, w, h, fill, alpha) {
  const opts = { x, y, w, h, fill: { color: fill } };
  if (alpha !== undefined) opts.fill.transparency = alpha;
  slide.addShape("ellipse", opts);
}

// 页码
function pgnum(slide, n) {
  txt(slide, String(n), 9.3, 5.2, 0.5, 0.3, { fontSize: 9, color: GRY50, align: "right" });
}

// ============================================================
// 渲染函数
// ============================================================

function renderCover(slide, d) {
  rect(slide, 0, 0, 10, 5.63, NAVY);
  oval(slide, 6.5, -1.5, 5.5, 5.5, DBLUE);
  oval(slide, 7.2, -0.8, 4, 4, BLUE, 60);
  oval(slide, 7.8, -0.2, 2.8, 2.8, SKYBL, 70);
  rect(slide, 0, 0, 0.15, 5.63, AMBER);
  rrect(slide, 0.6, 1.3, 1.8, 0.35, 4, AMBER, null);
  txt(slide, "PROFESSIONAL", 0.6, 1.3, 1.8, 0.35, { fontSize: 9, color: NAVY, bold: true, align: "center", valign: "middle", charSpacing: 2 });
  title(slide, d.title, 0.6, 1.85, 5.5, 1.6, { fontSize: 32, color: WHITE, bold: true, valign: "top" });
  txt(slide, d.subtitle, 0.6, 3.5, 5.5, 0.5, { fontSize: 14, color: GRY30, valign: "top" });
  rect(slide, 0.6, 4.1, 2.5, 0.03, AMBER);
  txt(slide, d.date + "  |  " + d.presenter, 0.6, 4.3, 5, 0.35, { fontSize: 11, color: GRY50 });
  txt(slide, d.company, 0.6, 4.65, 5, 0.35, { fontSize: 11, color: GRY50, bold: true });
}

function renderToc(slide, d, n) {
  rect(slide, 0, 0, 3.2, 5.63, NAVY);
  title(slide, "CONTENTS", 0.4, 0.5, 2.8, 0.4, { fontSize: 11, color: GRY50, charSpacing: 3 });
  title(slide, "目录", 0.4, 0.9, 2.8, 0.6, { fontSize: 28, color: WHITE, bold: true });
  rect(slide, 0.4, 1.6, 1.2, 0.04, AMBER);
  txt(slide, String(n), 0.4, 5.1, 1, 0.35, { fontSize: 10, color: GRY50 });
  d.items.forEach(function(item, i) {
    var y = 0.8 + i * 0.9;
    var isFirst = i === 0;
    oval(slide, 3.6, y + 0.15, 0.35, 0.35, isFirst ? BLUE : GRY20);
    txt(slide, String(i + 1).padStart(2, "0"), 3.6, y + 0.15, 0.35, 0.35, { fontSize: 11, color: isFirst ? WHITE : GRY70, align: "center", valign: "middle", bold: true });
    txt(slide, item, 4.15, y + 0.08, 5.4, 0.45, { fontSize: 15, color: TEXT, valign: "middle" });
    if (i < d.items.length - 1) rect(slide, 4.15, y + 0.65, 5.3, 0.01, GRY10);
  });
}

function renderSection(slide, d, n) {
  rect(slide, 0, 0, 10, 5.63, NAVY);
  oval(slide, 5.5, -2, 7, 7, DBLUE);
  oval(slide, 7, -1, 4.5, 4.5, BLUE, 50);
  rect(slide, 0, 0, 0.15, 5.63, AMBER);
  title(slide, d.title, 0.6, 1.2, 3, 1.8, { fontSize: 100, color: WHITE, bold: true, transparency: 20 });
  title(slide, d.subtitle, 0.6, 3.0, 5.5, 0.8, { fontSize: 26, color: WHITE, bold: true });
  rect(slide, 0.6, 3.85, 2, 0.04, AMBER);
  txt(slide, String(n), 0.6, 5.1, 1, 0.35, { fontSize: 10, color: GRY50 });
}

function renderContentLeft(slide, d, n) {
  rect(slide, 0, 0, 10, 0.06, BLUE);
  rect(slide, 0, 0.06, 3.5, 5.57, NAVY);
  title(slide, d.section || "SECTION", 0.4, 0.5, 2.8, 0.35, { fontSize: 10, color: GRY50, charSpacing: 2 });
  title(slide, d.title, 0.4, 1.0, 2.8, 2.5, { fontSize: 20, color: WHITE, bold: true });
  oval(slide, 1.8, 3.8, 1.8, 1.8, BLUE, 70);
  d.points.forEach(function(p, i) {
    var y = 0.5 + i * 1.15;
    rrect(slide, 3.9, y + 0.05, 1.3, 0.38, 4, BLUE, null);
    txt(slide, p.label, 3.9, y + 0.05, 1.3, 0.38, { fontSize: 10, color: WHITE, align: "center", valign: "middle", bold: true });
    txt(slide, p.desc, 5.35, y, 4.3, 0.5, { fontSize: 12, color: TEXT, valign: "middle" });
  });
  if (d.highlight) {
    rrect(slide, 3.9, 4.75, 5.7, 0.55, 6, AMBER, AMBER, 1);
    txt(slide, d.highlight, 4.05, 4.75, 5.4, 0.55, { fontSize: 11, color: AMBER, valign: "middle", bold: true });
  }
  pgnum(slide, n);
}

function renderFourCards(slide, d, n) {
  rect(slide, 0, 0, 10, 0.06, BLUE);
  title(slide, d.title, 0.5, 0.3, 9, 0.55, { fontSize: 20, color: TEXT, bold: true });
  if (d.subtitle) txt(slide, d.subtitle, 0.5, 0.85, 9, 0.35, { fontSize: 12, color: MUTED });
  var items = d.items;
  var cardW = 4.3, cardH = 1.8, gapX = 0.4, gapY = 0.3;
  var startX = 0.5, startY = 1.4;
  var pos = [
    [startX, startY],
    [startX + cardW + gapX, startY],
    [startX, startY + cardH + gapY],
    [startX + cardW + gapX, startY + cardH + gapY]
  ];
  items.forEach(function(item, i) {
    var x = pos[i][0], y = pos[i][1];
    rrect(slide, x, y, cardW, cardH, 8, WHITE, GRY20, 0.5);
    rect(slide, x, y, 0.12, cardH, item.color || BLUE);
    var topY = y + 0.2;
    oval(slide, x + 0.3, topY, 0.4, 0.4, item.color || BLUE);
    txt(slide, String(i + 1), x + 0.3, topY, 0.4, 0.4, { fontSize: 13, color: WHITE, align: "center", valign: "middle", bold: true });
    txt(slide, item.name, x + 0.8, topY - 0.05, cardW - 1, 0.45, { fontSize: 14, color: TEXT, bold: true, valign: "middle" });
    rect(slide, x + 0.3, topY + 0.55, cardW - 0.5, 0.015, GRY10);
    item.lines.forEach(function(line, j) {
      txt(slide, "\u2022 " + line, x + 0.3, topY + 0.65 + j * 0.35, cardW - 0.5, 0.35, { fontSize: 11, color: GRY70 });
    });
  });
  pgnum(slide, n);
}

function renderTimeline(slide, d, n) {
  rect(slide, 0, 0, 10, 0.06, BLUE);
  title(slide, d.title, 0.5, 0.3, 9, 0.55, { fontSize: 20, color: TEXT, bold: true });
  var steps = d.steps;
  var lineY = 3.0;
  rect(slide, 1, lineY, 8, 0.04, GRY30);
  steps.forEach(function(step, i) {
    var x = 1.3 + i * (7.4 / Math.max(steps.length - 1, 1));
    oval(slide, x - 0.18, lineY - 0.14, 0.36, 0.36, BLUE);
    oval(slide, x - 0.08, lineY - 0.04, 0.16, 0.16, WHITE);
    txt(slide, step.name, x - 0.8, lineY - 1.0, 1.6, 0.7, { fontSize: 12, color: TEXT, bold: true, align: "center", valign: "bottom" });
    if (step.time) txt(slide, step.time, x - 0.8, lineY - 1.55, 1.6, 0.4, { fontSize: 10, color: MUTED, align: "center" });
    if (step.desc) txt(slide, step.desc, x - 0.8, lineY + 0.4, 1.6, 0.8, { fontSize: 10, color: GRY70, align: "center", valign: "top" });
  });
  pgnum(slide, n);
}

function renderMetrics(slide, d, n) {
  rect(slide, 0, 0, 10, 0.06, BLUE);
  title(slide, d.title, 0.5, 0.3, 9, 0.55, { fontSize: 20, color: TEXT, bold: true });
  var metrics = d.metrics;
  var cardW = 2.8, gap = 0.3;
  var totalW = metrics.length * cardW + (metrics.length - 1) * gap;
  var startX = (10 - totalW) / 2, startY = 1.2;
  metrics.forEach(function(m, i) {
    var x = startX + i * (cardW + gap);
    rrect(slide, x, startY, cardW, 2.2, 8, WHITE, GRY20, 0.5);
    rect(slide, x + 0.3, startY, cardW - 0.6, 0.06, m.color || BLUE);
    txt(slide, m.value, x, startY + 0.3, cardW, 0.9, { fontSize: 36, color: m.color || BLUE, bold: true, align: "center", valign: "middle" });
    txt(slide, m.label, x + 0.2, startY + 1.25, cardW - 0.4, 0.7, { fontSize: 12, color: TEXT, align: "center", valign: "top" });
  });
  if (d.note) txt(slide, d.note, 0.5, 3.7, 9, 0.4, { fontSize: 11, color: MUTED, align: "center" });
  pgnum(slide, n);
}

function renderArch(slide, d, n) {
  rect(slide, 0, 0, 10, 0.06, BLUE);
  title(slide, d.title, 0.5, 0.3, 9, 0.55, { fontSize: 20, color: TEXT, bold: true });
  var layers = d.layers;
  var layerH = 0.85, startY = 1.0, startX = 0.5, labelW = 1.3, contentW = 8.2;
  layers.forEach(function(layer, i) {
    var y = startY + i * layerH;
    var isTop = i === 0;
    rect(slide, startX, y, labelW, layerH - 0.08, isTop ? BLUE : DBLUE);
    txt(slide, layer.name, startX, y, labelW, layerH - 0.08, { fontSize: 12, color: WHITE, bold: true, align: "center", valign: "middle" });
    rrect(slide, startX + labelW + 0.1, y, contentW, layerH - 0.08, 4, WHITE, GRY30, 0.5);
    txt(slide, layer.desc, startX + labelW + 0.25, y, contentW - 0.2, layerH - 0.08, { fontSize: 12, color: TEXT, valign: "middle" });
  });
  var arrowX = startX + labelW / 2;
  for (var i = 0; i < layers.length - 1; i++) {
    var y1 = startY + i * layerH + layerH - 0.08;
    var y2 = startY + (i + 1) * layerH;
    rect(slide, arrowX - 0.02, y1, 0.04, y2 - y1, GRY30);
  }
  pgnum(slide, n);
}

function renderTable(slide, d, n) {
  rect(slide, 0, 0, 10, 0.06, BLUE);
  title(slide, d.title, 0.5, 0.3, 9, 0.55, { fontSize: 20, color: TEXT, bold: true });
  var cases = d.cases;
  var rowH = 0.9, startY = 1.0, col1 = 1.8, col2 = 2.0, col3 = 5.5;
  rect(slide, 0.5, startY, 9, 0.45, NAVY);
  txt(slide, "企业", 0.5, startY, col1, 0.45, { fontSize: 11, color: WHITE, bold: true, align: "center", valign: "middle" });
  txt(slide, "模式", 0.5 + col1, startY, col2, 0.45, { fontSize: 11, color: WHITE, bold: true, align: "center", valign: "middle" });
  txt(slide, "核心做法", 0.5 + col1 + col2, startY, col3, 0.45, { fontSize: 11, color: WHITE, bold: true, align: "center", valign: "middle" });
  cases.forEach(function(c, i) {
    var y = startY + 0.45 + i * rowH;
    var bg = i % 2 === 0 ? WHITE : GRY10;
    rect(slide, 0.5, y, 9, rowH, bg);
    rect(slide, 0.5, y, 9, rowH, GRY20, GRY20, 0.5);
    txt(slide, c.company, 0.6, y, col1 - 0.1, rowH, { fontSize: 12, color: TEXT, bold: true, valign: "middle" });
    txt(slide, c.model, 0.5 + col1, y, col2 - 0.1, rowH, { fontSize: 11, color: BLUE, bold: true, valign: "middle" });
    txt(slide, c.practices.join("\u3001"), 0.5 + col1 + col2, y, col3 - 0.2, rowH, { fontSize: 11, color: GRY70, valign: "middle" });
  });
  pgnum(slide, n);
}

function renderThreeCols(slide, d, n) {
  rect(slide, 0, 0, 10, 0.06, BLUE);
  title(slide, d.title, 0.5, 0.3, 9, 0.55, { fontSize: 20, color: TEXT, bold: true });
  var items = d.items;
  var cardW = 2.9, gap = 0.35;
  var totalW = items.length * cardW + (items.length - 1) * gap;
  var startX = (10 - totalW) / 2, startY = 1.1;
  items.forEach(function(item, i) {
    var x = startX + i * (cardW + gap);
    rrect(slide, x, startY, cardW, 3.6, 8, WHITE, GRY20, 0.5);
    rect(slide, x, startY, cardW, 0.9, item.color || BLUE);
    txt(slide, item.icon || String(i + 1), x, startY, cardW, 0.9, { fontSize: 28, color: WHITE, align: "center", valign: "middle", bold: true });
    txt(slide, item.name, x + 0.15, startY + 1.1, cardW - 0.3, 0.5, { fontSize: 14, color: TEXT, bold: true, align: "center" });
    txt(slide, item.desc, x + 0.15, startY + 1.65, cardW - 0.3, 1.8, { fontSize: 11, color: GRY70, align: "center" });
  });
  pgnum(slide, n);
}

function renderEnding(slide, d) {
  rect(slide, 0, 0, 10, 5.63, NAVY);
  oval(slide, -2, -2, 6, 6, DBLUE);
  oval(slide, -1, -1, 4, 4, BLUE, 60);
  oval(slide, 6, 2.5, 5, 5, DBLUE);
  oval(slide, 7, 3, 3.5, 3.5, BLUE, 70);
  rect(slide, 0, 0, 0.15, 5.63, AMBER);
  title(slide, d.title, 0.6, 1.8, 6, 1, { fontSize: 42, color: WHITE, bold: true });
  rect(slide, 0.6, 2.9, 2, 0.04, AMBER);
  txt(slide, d.subtitle, 0.6, 3.1, 6, 0.5, { fontSize: 15, color: GRY30 });
  txt(slide, d.contact || "青岛大数据科技公司", 0.6, 4.5, 5, 0.4, { fontSize: 12, color: GRY50, bold: true });
}

// ============================================================
// 主函数
// ============================================================
function main() {
  var opts = {};
  var args = process.argv.slice(2);
  for (var i = 0; i < args.length; i++) {
    if (args[i].startsWith("--")) {
      var k = args[i].slice(2);
      opts[k] = args[i + 1] && !args[i + 1].startsWith("--") ? args[++i] : true;
    }
  }

  var pptx = new PptxGenJS();
  pptx.layout = "LAYOUT_16x9";
  pptx.author = "青岛大数据科技公司";
  pptx.title = "国企四体协同管理数字化解决方案";

  var slides = [];

  // ---- 封面 ----
  slides.push({ type: "cover", title: opts.title || "国企四体协同管理数字化解决方案", subtitle: opts.subtitle || "数智化穿透监管下的体系构建与实践创新", date: opts.date || "2026年3月", presenter: opts.presenter || "亮哥", company: opts.company || "青岛大数据科技公司" });

  // ---- 目录 ----
  slides.push({ type: "toc", items: ["政策背景与监管趋势", "四体协同管理体系", "核心框架与关键工具", "实践案例与成效", "解决方案与服务内容", "合作方式"] });

  // ---- 01 政策背景 ----
  slides.push({ type: "section", title: "01", subtitle: "政策背景与监管趋势" });
  slides.push({ type: "content_left", section: "POLICY", title: "国资监管进入穿透式监管新时代", points: [
    { label: "2015年", desc: "探索建立一体化管理平台" },
    { label: "2019年", desc: "以风险为导向、内控为核心、合规为重点、法律为保障" },
    { label: "2022年", desc: "中央企业合规管理办法要求建立协调运作机制" },
    { label: "2026年", desc: "穿透式监管指导意见标志进入体系化落地阶段" }
  ], highlight: "四全特征：全级次/全链条/全过程/全要素，覆盖十大领域" });
  slides.push({ type: "content_left", section: "CORE", title: "穿透式监管的本质与目标", points: [
    { label: "本质", desc: "标准穿透而非权力穿透，信息穿透而非决策穿透" },
    { label: "目标", desc: "实现放得活管得住" },
    { label: "全级次", desc: "打破层级壁垒，覆盖集团-子公司-孙公司" },
    { label: "全链条", desc: "覆盖上下游产业链，不留监管死角" }
  ], highlight: "本质：标准穿透而非权力穿透，信息穿透而非决策穿透" });

  // ---- 02 四体协同 ----
  slides.push({ type: "section", title: "02", subtitle: "四体协同管理体系" });
  slides.push({ type: "four_cards", title: "四体协同的差异化定位", items: [
    { name: "全面风险管理", color: "2E86AB", lines: ["聚焦战略层", "风险识别、评估、应对", "目标：识大势防大险"] },
    { name: "内部控制", color: "7C3AED", lines: ["聚焦运营层", "不相容职责分离、权限指引", "目标：建机制管日常"] },
    { name: "合规管理", color: "059669", lines: ["聚焦监管层", "外规内化、合规审查", "目标：守底线不越界"] },
    { name: "法务管理", color: "DC2626", lines: ["聚焦权益层", "合同、案件、知识产权", "目标：护权益防纠纷"] }
  ]});
  slides.push({ type: "content_left", section: "SYNERGY", title: "四体协同的核心逻辑", points: [
    { label: "目标统一", desc: "以风险管控为核心，形成有机整体" },
    { label: "流程贯通", desc: "从分散运行向一体化管理转变" },
    { label: "数据共享", desc: "信息互通，打破信息孤岛" },
    { label: "责任共担", desc: "实现1+1+1+1>4的治理效能" }
  ], highlight: "最终目标：风险可控、合规有序、经营高效" });

  // ---- 03 核心框架 ----
  slides.push({ type: "section", title: "03", subtitle: "核心框架与关键工具" });
  slides.push({ type: "four_cards", title: "12345风控组织体系", items: [
    { name: "第一责任人", color: DBLUE, lines: ["董事长/总经理挂帅", "承担主体责任"] },
    { name: "两级管控", color: BLUE, lines: ["母子公司两级管控", "垂直管理穿透"] },
    { name: "三道防线", color: SKYBL, lines: ["业务部门", "合规风险部门", "审计纪检"] },
    { name: "四类人员", color: TEAL, lines: ["分管领导、风控负责人", "专职人员、兼职人员"] }
  ]});
  slides.push({ type: "content_left", section: "TOOLS", title: "三大核心管理工具", points: [
    { label: "风险识别清单", desc: "统一风险描述与分级标准，涵盖战略、财务、运营、合规四大类" },
    { label: "流程管控清单", desc: "明确各节点合规风控审核要求，嵌入核心业务流程" },
    { label: "重点岗位清单", desc: "明确岗位职责与风控要求，建立追责问责机制" }
  ], highlight: "配套机制：五同步、一岗式审查、外规内化四步法、PDCA闭环" });
  slides.push({ type: "timeline", title: "实施路线图", steps: [
    { name: "阶段一", time: "第1-2月", desc: "现状诊断\n体系规划" },
    { name: "阶段二", time: "第3-5月", desc: "制度梳理\n流程优化" },
    { name: "阶段三", time: "第6月", desc: "平台搭建\n上线运行" },
    { name: "持续运营", time: "长期", desc: "培训支持\n迭代优化" }
  ]});

  // ---- 04 实践案例 ----
  slides.push({ type: "section", title: "04", subtitle: "实践案例与成效" });
  slides.push({ type: "table", title: "标杆企业实践", cases: [
    { company: "东方锅炉", model: "1110风险防控体系", practices: ["构建12345组织体系", "672项业务流程线上管控", "大数据风险预警模型"] },
    { company: "北投集团", model: "一手册+两汇编", practices: ["116项制度专项评审", "五同步更新机制", "一体化风险控制矩阵"] },
    { company: "中国石化", model: "五位一体法治格局", practices: ["合规为伞架", "风险为伞面", "内控为伞把"] },
    { company: "中国建材", model: "协同监管+信息化", practices: ["三级垂直化监管链条", "统一信息化平台实时监控"] }
  ]});
  slides.push({ type: "metrics", title: "数字化管理效能提升（参考值）", metrics: [
    { value: "60%+", label: "流程审批效率提升", color: BLUE },
    { value: "45%", label: "风险识别时效提升", color: TEAL },
    { value: "80%", label: "合规检查覆盖率", color: GREEN },
    { value: "3x", label: "问题响应速度提升", color: AMBER }
  ], note: "数据来源：标杆企业实施后平均值，实际效果因企业规模和管理基础不同而有差异" });

  // ---- 05 解决方案 ----
  slides.push({ type: "section", title: "05", subtitle: "解决方案与服务内容" });
  slides.push({ type: "arch", title: "我们的解决方案架构", layers: [
    { name: "应用层", desc: "风险预警大屏 | 合规审查系统 | 内控管理系统 | 法务管理平台" },
    { name: "平台层", desc: "四体协同管理平台 | 统一工作流引擎 | 智能分析引擎" },
    { name: "数据层", desc: "企业风险数据库 | 法规政策库 | 案例知识库 | 指标体系库" },
    { name: "基础设施", desc: "私有化部署 | 混合云架构 | 等保三级认证 | 信创支持" }
  ]});
  slides.push({ type: "three_cols", title: "三阶段服务内容", items: [
    { icon: "1", name: "体系建设", color: BLUE, desc: "四体管理现状诊断\n差距分析\n体系规划设计\n制度流程梳理" },
    { icon: "2", name: "平台搭建", color: TEAL, desc: "协同管理平台开发\n流程配置与嵌入\n系统集成与对接\n数据迁移与清洗" },
    { icon: "3", name: "落地运营", color: GREEN, desc: "人员培训与认证\n试运行与调整\n持续优化迭代\n效果评估报告" }
  ]});

  // ---- 06 合作方式 ----
  slides.push({ type: "section", title: "06", subtitle: "合作方式" });
  slides.push({ type: "four_cards", title: "为什么选择我们", items: [
    { name: "专业团队", color: BLUE, lines: ["行业专家顾问支持", "资深项目经理带队", "复合型实施团队"] },
    { name: "成熟方法", color: TEAL, lines: ["自有方法论体系", "标杆企业实践经验", "快速落地保障"] },
    { name: "技术领先", color: GREEN, lines: ["自主研发平台", "AI+大数据能力", "信创环境适配"] },
    { name: "长期服务", color: AMBER, lines: ["持续运维支持", "定期效果评估", "不断迭代优化"] }
  ]});
  slides.push({ type: "content_left", section: "CONTACT", title: "合作方式与联系方式", points: [
    { label: "服务模式", desc: "定制化开发 + 长期运维 + 持续优化" },
    { label: "部署方式", desc: "私有化部署，支持信创环境" },
    { label: "合作周期", desc: "体系建设3-6个月，持续运维服务" },
    { label: "联系信息", desc: "期待与贵司携手共创合规管理新范式" }
  ]});

  // ---- 结束页 ----
  slides.push({ type: "ending", title: "感谢聆听", subtitle: "期待与贵司携手共创合规管理新范式", contact: "青岛大数据科技公司" });

  // ============================================================
  // 渲染所有幻灯片
  // ============================================================
  slides.forEach(function(s, i) {
    var slide = pptx.addSlide();
    slide.background = { color: WHITE };
    var n = i + 1;
    switch (s.type) {
      case "cover":    renderCover(slide, s); break;
      case "toc":      renderToc(slide, s, n); break;
      case "section":  renderSection(slide, s, n); break;
      case "content_left": renderContentLeft(slide, s, n); break;
      case "four_cards": renderFourCards(slide, s, n); break;
      case "timeline": renderTimeline(slide, s, n); break;
      case "metrics":  renderMetrics(slide, s, n); break;
      case "arch":     renderArch(slide, s, n); break;
      case "table":    renderTable(slide, s, n); break;
      case "three_cols": renderThreeCols(slide, s, n); break;
      case "ending":   renderEnding(slide, s); break;
    }
  });

  var out = opts.output || "../ppt-output/国企四体协同管理v3.pptx";
  var dir = path.dirname(path.resolve(out));
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  pptx.writeFile({ fileName: out }).then(function() {
    console.log("OK: " + path.resolve(out));
  }).catch(function(e) {
    console.error("Error:", e.message);
    process.exit(1);
  });
}

main();
